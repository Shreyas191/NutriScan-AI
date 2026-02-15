"""
NutriScan AI Agent — autonomous health analysis agent.

Supports both Gemini (free tier, default) and Claude (for hackathon).

Instead of a fixed pipeline, the AI acts as a reasoning agent that:
  - Decides which tool to call next
  - Validates results and self-corrects (e.g. retries OCR)
  - Explains its reasoning at every step
  - Adapts based on what it finds

Architecture:
  1. Define tools (wrappers around existing service functions)
  2. Send initial message + PDF context to the AI
  3. Loop: AI responds with function call → execute → feed result back
  4. Loop ends when AI responds with text only (final answer)
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from app.config import settings
from app.services.ocr_service import extract_text, OCRResult
from app.services.biomarker_extractor import extract_biomarkers
from app.services.deficiency_engine import detect_deficiencies
from app.services.explanation_generator import generate_explanations
from app.services.food_recommender import recommend_foods
from app.services import instacart
from app.models.biomarker import (
    Biomarker,
    Deficiency,
    Explanation,
    FoodRecommendation,
)

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 15  # Safety cap — agent stops after this many tool calls


# ---------------------------------------------------------------------------
# Agent state — accumulated results across the loop
# ---------------------------------------------------------------------------
@dataclass
class AgentState:
    """Mutable state that persists across agent iterations."""

    # Raw inputs
    pdf_bytes: bytes = b""
    dietary_preferences: list[str] = field(default_factory=list)

    # Accumulated results
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    ocr_method: str = ""

    biomarkers: list[Biomarker] = field(default_factory=list)
    deficiencies: list[Deficiency] = field(default_factory=list)
    explanations: list[Explanation] = field(default_factory=list)
    food_recommendations: list[FoodRecommendation] = field(default_factory=list)
    cart_items: list[dict] = field(default_factory=list)
    shop_all_url: str = ""

    # Reasoning trace
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)


@dataclass
class ReasoningStep:
    """One step in the agent's reasoning trace."""
    step_number: int
    action: str  # e.g. "tool_call" or "reasoning"
    tool_name: str | None = None
    reasoning: str = ""
    result_summary: str = ""
    timestamp: float = 0.0


# ---------------------------------------------------------------------------
# Tool definitions — neutral format, converted per-provider at runtime
# ---------------------------------------------------------------------------

AGENT_TOOLS: list[dict[str, Any]] = [
    {
        "name": "extract_text_from_pdf",
        "description": (
            "Extract text from the uploaded PDF lab report. "
            "Uses pdfplumber for digital PDFs and Tesseract OCR for scanned PDFs. "
            "Returns the extracted text, confidence score (0-1), and method used."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "force_ocr": {
                    "type": "boolean",
                    "description": "If true, force Tesseract OCR. Use if initial extraction returned very little text.",
                },
            },
        },
    },
    {
        "name": "extract_biomarkers",
        "description": (
            "Send the OCR text to an AI model to extract structured biomarker data. "
            "Returns a list of biomarkers with test name, value, unit, and reference range. "
            "Call AFTER extract_text_from_pdf."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text_override": {
                    "type": "string",
                    "description": "Optional override text instead of using the OCR result.",
                },
            },
        },
    },
    {
        "name": "detect_deficiencies",
        "description": (
            "Run deficiency detection on extracted biomarkers. "
            "Uses clinical thresholds to classify each biomarker. "
            "Call AFTER extract_biomarkers."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "generate_explanations",
        "description": (
            "Generate plain-English explanations for each detected deficiency. "
            "Call AFTER detect_deficiencies, only if deficiencies were found."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "recommend_foods",
        "description": (
            "Generate food and supplement recommendations based on deficiencies. "
            "Respects dietary preferences. Call AFTER detect_deficiencies."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "dietary_preferences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Dietary restrictions like 'vegan', 'lactose-free'.",
                },
            },
        },
    },
    {
        "name": "build_instacart_cart",
        "description": (
            "Build Instacart shopping cart URLs from food recommendations. "
            "This is typically the final step. Call AFTER recommend_foods."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


# ---------------------------------------------------------------------------
# System prompt — instructs the AI to be an autonomous agent
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """You are the NutriScan AI Agent — an autonomous health analysis assistant.

You have access to tools that let you analyze a patient's lab report PDF and generate personalized nutrition recommendations.

## Your Mission
Analyze the uploaded PDF lab report end-to-end:
1. Extract text from the PDF
2. Parse biomarker values from the text
3. Detect any deficiencies
4. If deficiencies are found, generate explanations and food recommendations
5. Build an Instacart grocery cart with the recommended items

## How to Behave
- **Think step by step.** Before each tool call, briefly explain your reasoning.
- **Validate your results.** If OCR confidence is low (<50%), mention it. If very few biomarkers are found, consider if the text quality is sufficient.
- **Self-correct.** If the initial OCR extraction returns very little text (<50 characters), retry with force_ocr=true to use Tesseract.
- **Adapt.** If no deficiencies are detected, skip explanations and food recommendations — just report the good news.
- **Be thorough.** Complete ALL steps — don't stop after extracting biomarkers.
- **Report dietary preferences.** If the user has dietary preferences, pass them to the recommend_foods tool.

## Important Rules
- You are NOT a doctor. Never diagnose conditions.
- Never recommend specific supplement dosages.
- Always encourage consulting a healthcare provider.
- Be clear, actionable, and non-alarmist.

## When You're Done
After completing all steps, provide a brief final summary mentioning:
- How many biomarkers were found
- How many deficiencies were detected
- What food categories were recommended
- That the Instacart cart is ready

Keep your final summary to 2-3 sentences."""


# ---------------------------------------------------------------------------
# Tool execution — maps tool names to actual functions
# ---------------------------------------------------------------------------

async def _execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    state: AgentState,
) -> str:
    """
    Execute a tool and return the result as a string.
    Also updates AgentState with the results.
    """
    try:
        if tool_name == "extract_text_from_pdf":
            force_ocr = tool_input.get("force_ocr", False)

            if force_ocr:
                from app.services.ocr_service import _extract_with_tesseract
                ocr_result = _extract_with_tesseract(state.pdf_bytes)
            else:
                ocr_result = await extract_text(state.pdf_bytes)

            state.ocr_text = ocr_result.text
            state.ocr_confidence = ocr_result.confidence
            state.ocr_method = ocr_result.method

            text_preview = ocr_result.text[:500] + "..." if len(ocr_result.text) > 500 else ocr_result.text

            return json.dumps({
                "success": True,
                "method": ocr_result.method,
                "confidence": ocr_result.confidence,
                "character_count": len(ocr_result.text),
                "page_count": ocr_result.page_count,
                "text_preview": text_preview,
            })

        elif tool_name == "extract_biomarkers":
            text = tool_input.get("text_override") or state.ocr_text
            if not text:
                return json.dumps({"success": False, "error": "No OCR text available. Run extract_text_from_pdf first."})

            biomarkers = await extract_biomarkers(text)
            state.biomarkers = biomarkers

            return json.dumps({
                "success": True,
                "biomarker_count": len(biomarkers),
                "biomarkers": [
                    {
                        "test_name": b.test_name,
                        "value": b.value,
                        "unit": b.unit,
                        "reference_range": b.reference_range,
                        "flag": b.flag,
                    }
                    for b in biomarkers
                ],
            })

        elif tool_name == "detect_deficiencies":
            if not state.biomarkers:
                return json.dumps({"success": False, "error": "No biomarkers available. Run extract_biomarkers first."})

            deficiencies = detect_deficiencies(state.biomarkers)
            state.deficiencies = deficiencies

            return json.dumps({
                "success": True,
                "deficiency_count": len(deficiencies),
                "deficiencies": [
                    {
                        "name": d.biomarker.test_name,
                        "value": d.biomarker.value,
                        "unit": d.biomarker.unit,
                        "severity": d.severity.value,
                        "percentage_of_normal": d.percentage_of_normal,
                    }
                    for d in deficiencies
                ],
            })

        elif tool_name == "generate_explanations":
            if not state.deficiencies:
                return json.dumps({"success": False, "error": "No deficiencies found. Run detect_deficiencies first."})

            explanations = await generate_explanations(state.deficiencies)
            state.explanations = explanations

            return json.dumps({
                "success": True,
                "explanation_count": len(explanations),
                "explanations": [
                    {"title": e.title, "severity": e.severity.value, "text": e.text}
                    for e in explanations
                ],
            })

        elif tool_name == "recommend_foods":
            if not state.deficiencies:
                return json.dumps({"success": False, "error": "No deficiencies found. Run detect_deficiencies first."})

            prefs = tool_input.get("dietary_preferences") or state.dietary_preferences or None
            recommendations = await recommend_foods(state.deficiencies, prefs)
            state.food_recommendations = recommendations

            return json.dumps({
                "success": True,
                "recommendation_count": len(recommendations),
                "recommendations": [
                    {
                        "emoji": r.emoji,
                        "name": r.name,
                        "nutrient": r.nutrient,
                        "amount": r.amount,
                        "category": r.category,
                    }
                    for r in recommendations
                ],
            })

        elif tool_name == "build_instacart_cart":
            if not state.food_recommendations:
                return json.dumps({"success": False, "error": "No food recommendations. Run recommend_foods first."})

            result = await instacart.create_shopping_list(state.food_recommendations)

            state.cart_items = result["cart_items"]
            state.shop_all_url = result["shop_all_url"]

            return json.dumps({
                "success": True,
                "cart_item_count": len(result["cart_items"]),
                "shop_all_url": result["shop_all_url"],
                "api_used": result.get("api_used", False),
                "items": [
                    {"name": item["name"], "instacart_url": item["instacart_url"]}
                    for item in result["cart_items"]
                ],
            })

        else:
            return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        logger.error("Tool %s failed: %s", tool_name, e)
        return json.dumps({"success": False, "error": str(e)})


# ---------------------------------------------------------------------------
# Agent loop — Gemini implementation with function calling
# ---------------------------------------------------------------------------

async def _run_agent_gemini(
    pdf_bytes: bytes,
    dietary_preferences: list[str] | None = None,
    on_step: Callable[[ReasoningStep], Any] | None = None,
) -> AgentState:
    """Run the agent using Gemini function calling (google.genai SDK)."""
    from google.genai import types

    from app.services.gemini_client import get_client

    state = AgentState(
        pdf_bytes=pdf_bytes,
        dietary_preferences=dietary_preferences or [],
    )

    client = get_client()

    # Convert tool definitions to Gemini FunctionDeclarations
    function_declarations = []
    for tool_def in AGENT_TOOLS:
        fd = types.FunctionDeclaration(
            name=tool_def["name"],
            description=tool_def["description"],
            parameters=tool_def.get("parameters", {"type": "object", "properties": {}}),
        )
        function_declarations.append(fd)

    gemini_tool = types.Tool(function_declarations=function_declarations)

    # Build initial message
    pref_text = ""
    if dietary_preferences:
        pref_text = f"\n\nDietary preferences: {', '.join(dietary_preferences)}"

    initial_message = (
        f"I've uploaded a lab report PDF ({len(pdf_bytes):,} bytes). "
        f"Please analyze it completely — extract biomarkers, detect deficiencies, "
        f"generate explanations, recommend foods, and build an Instacart cart."
        f"{pref_text}"
    )

    # Chat history for multi-turn conversation
    contents: list[types.Content] = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=initial_message)],
        )
    ]

    step_number = 0

    for iteration in range(MAX_ITERATIONS):
        logger.info("Agent iteration %d/%d", iteration + 1, MAX_ITERATIONS)

        # Call Gemini
        response = client.models.generate_content(
            model=settings.GEMINI_FLASH_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=AGENT_SYSTEM_PROMPT,
                tools=[gemini_tool],
                temperature=0.2,
                max_output_tokens=4096,
            ),
        )

        # Process response parts
        function_calls = []
        text_parts = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_calls.append(part.function_call)
                elif part.text:
                    text_parts.append(part.text)

        # Record any reasoning text
        if text_parts:
            step_number += 1
            reasoning_text = " ".join(text_parts)
            step = ReasoningStep(
                step_number=step_number,
                action="reasoning",
                reasoning=reasoning_text,
                timestamp=time.time(),
            )
            state.reasoning_steps.append(step)
            if on_step:
                on_step(step)

        # If no function calls, agent is done
        if not function_calls:
            logger.info("Agent finished — no more function calls")
            break

        # Add the model's response to contents
        contents.append(response.candidates[0].content)

        # Execute each function call and build responses
        function_response_parts = []
        for fc in function_calls:
            step_number += 1
            tool_name = fc.name
            tool_args = dict(fc.args) if fc.args else {}

            logger.info("Agent calling tool: %s", tool_name)

            # Execute the tool
            result_str = await _execute_tool(tool_name, tool_args, state)
            result_data = json.loads(result_str)

            # Record step
            summary = _summarize_result(tool_name, result_data)
            step = ReasoningStep(
                step_number=step_number,
                action="tool_call",
                tool_name=tool_name,
                reasoning=f"Calling {tool_name}",
                result_summary=summary,
                timestamp=time.time(),
            )
            state.reasoning_steps.append(step)
            if on_step:
                on_step(step)

            # Build function response part
            function_response_parts.append(
                types.Part.from_function_response(
                    name=tool_name,
                    response=result_data,
                )
            )

        # Send function results back to Gemini
        contents.append(
            types.Content(
                role="user",
                parts=function_response_parts,
            )
        )

    else:
        logger.warning("Agent hit max iterations (%d)", MAX_ITERATIONS)

    return state


# ---------------------------------------------------------------------------
# Agent loop — Claude implementation (kept for future hackathon use)
# ---------------------------------------------------------------------------

async def _run_agent_claude(
    pdf_bytes: bytes,
    dietary_preferences: list[str] | None = None,
    on_step: Callable[[ReasoningStep], Any] | None = None,
) -> AgentState:
    """Run the agent using Claude tool_use."""
    from app.services.claude_client import get_client, SONNET

    # Convert tool defs to Claude format
    claude_tools = []
    for tool_def in AGENT_TOOLS:
        claude_tools.append({
            "name": tool_def["name"],
            "description": tool_def["description"],
            "input_schema": tool_def.get("parameters", {"type": "object", "properties": {}}),
        })

    client = get_client()
    state = AgentState(
        pdf_bytes=pdf_bytes,
        dietary_preferences=dietary_preferences or [],
    )

    pref_text = ""
    if dietary_preferences:
        pref_text = f"\n\nDietary preferences: {', '.join(dietary_preferences)}"

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                f"I've uploaded a lab report PDF ({len(pdf_bytes):,} bytes). "
                f"Please analyze it completely — extract biomarkers, detect deficiencies, "
                f"generate explanations, recommend foods, and build an Instacart cart."
                f"{pref_text}"
            ),
        }
    ]

    step_number = 0

    for iteration in range(MAX_ITERATIONS):
        logger.info("Agent iteration %d/%d", iteration + 1, MAX_ITERATIONS)

        response = client.messages.create(
            model=SONNET,
            max_tokens=4096,
            system=AGENT_SYSTEM_PROMPT,
            tools=claude_tools,
            messages=messages,
        )

        tool_uses = []
        text_parts = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
                step_number += 1
                step = ReasoningStep(
                    step_number=step_number,
                    action="reasoning",
                    reasoning=block.text,
                    timestamp=time.time(),
                )
                state.reasoning_steps.append(step)
                if on_step:
                    on_step(step)

            elif block.type == "tool_use":
                tool_uses.append(block)

        if not tool_uses:
            logger.info("Agent finished — no more tool calls")
            break

        tool_results = []
        for tool_use in tool_uses:
            step_number += 1
            logger.info("Agent calling tool: %s", tool_use.name)

            result_str = await _execute_tool(tool_use.name, tool_use.input, state)
            result_data = json.loads(result_str)
            summary = _summarize_result(tool_use.name, result_data)

            step = ReasoningStep(
                step_number=step_number,
                action="tool_call",
                tool_name=tool_use.name,
                reasoning=f"Calling {tool_use.name}",
                result_summary=summary,
                timestamp=time.time(),
            )
            state.reasoning_steps.append(step)
            if on_step:
                on_step(step)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": result_str,
            })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    else:
        logger.warning("Agent hit max iterations (%d)", MAX_ITERATIONS)

    return state


# ---------------------------------------------------------------------------
# Public API — routes to the correct provider
# ---------------------------------------------------------------------------

async def run_agent(
    pdf_bytes: bytes,
    dietary_preferences: list[str] | None = None,
    on_step: Callable[[ReasoningStep], Any] | None = None,
) -> AgentState:
    """
    Run the NutriScan AI Agent.

    Uses Gemini by default, Claude if AI_PROVIDER=claude.

    Args:
        pdf_bytes: Raw PDF file bytes.
        dietary_preferences: Optional dietary restrictions.
        on_step: Optional callback for each reasoning step (for streaming).

    Returns:
        AgentState with all accumulated results.
    """
    if settings.AI_PROVIDER == "claude":
        logger.info("Running agent with Claude")
        return await _run_agent_claude(pdf_bytes, dietary_preferences, on_step)
    else:
        logger.info("Running agent with Gemini")
        return await _run_agent_gemini(pdf_bytes, dietary_preferences, on_step)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _summarize_result(tool_name: str, result: dict) -> str:
    """Create a human-readable summary of a tool result."""
    if not result.get("success"):
        return f"❌ Failed: {result.get('error', 'Unknown error')}"

    summaries = {
        "extract_text_from_pdf": (
            f"📄 Extracted {result.get('character_count', 0):,} chars "
            f"via {result.get('method', '?')} "
            f"({result.get('confidence', 0) * 100:.0f}% confidence)"
        ),
        "extract_biomarkers": (
            f"🔬 Found {result.get('biomarker_count', 0)} biomarkers"
        ),
        "detect_deficiencies": (
            f"⚠️ Detected {result.get('deficiency_count', 0)} deficiencies"
            if result.get("deficiency_count", 0) > 0
            else "✅ No deficiencies detected"
        ),
        "generate_explanations": (
            f"💡 Generated {result.get('explanation_count', 0)} explanations"
        ),
        "recommend_foods": (
            f"🥗 Recommended {result.get('recommendation_count', 0)} foods/supplements"
        ),
        "build_instacart_cart": (
            f"🛒 Built cart with {result.get('cart_item_count', 0)} items"
        ),
    }

    return summaries.get(tool_name, f"✅ {tool_name} completed")
