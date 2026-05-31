"""
NutriScan AI Agent — autonomous health analysis agent powered by Gemini.

Instead of a fixed pipeline, the AI acts as a reasoning agent that:
  - Decides which tool to call next
  - Validates results and self-corrects (e.g. retries OCR)
  - Explains its reasoning at every step
  - Adapts based on what it finds

Architecture:
  1. Define tools as Gemini FunctionDeclarations
  2. Send initial message + PDF context to Gemini
  3. Loop: Gemini responds with function_call → execute → feed result back
  4. Loop ends when Gemini responds with text only (final answer)
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
from app.services.food_recommender import recommend_foods
from app.services import shopping
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
    shopping_links: dict[str, str] = field(default_factory=dict)
    shop_all_url: str = ""  # Deprecated, kept for backward compat temporarily

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
# Tool definitions
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
        "name": "build_shopping_carts",
        "description": (
            "Build shopping cart links for Walmart and Amazon. "
            "This is typically the final step. Call AFTER recommend_foods."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]


# ---------------------------------------------------------------------------
# System prompt — instructs Claude to be an autonomous agent
# ---------------------------------------------------------------------------

AGENT_SYSTEM_PROMPT = """You are the NutriScan AI Agent — an autonomous health analysis assistant.

You have access to tools that let you analyze a patient's lab report PDF and generate personalized nutrition recommendations.

## Your Mission
Analyze the uploaded PDF lab report end-to-end:
1. Extract text from the PDF
2. Parse biomarker values from the text
3. Detect any deficiencies
4. If deficiencies are found, generate explanations and food recommendations
5. Build shopping carts for Walmart and Amazon with the recommended items

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
- That the Walmart cart is ready

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

        elif tool_name == "build_shopping_carts":
            if not state.food_recommendations:
                return json.dumps({"success": False, "error": "No food recommendations. Run recommend_foods first."})

            result = await shopping.create_shopping_links(state.food_recommendations)

            state.cart_items = result["cart_items"]
            state.shopping_links = result["shopping_links"]
            # Backwards compat
            state.shop_all_url = result["shopping_links"].get("walmart", "")

            return json.dumps({
                "success": True,
                "cart_item_count": len(result["cart_items"]),
                "shopping_links": result["shopping_links"],
            })

        else:
            return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        logger.error("Tool %s failed: %s", tool_name, e)
        return json.dumps({"success": False, "error": str(e)})


# ---------------------------------------------------------------------------
# Agent loop — Groq / OpenAI-style tool calling
# ---------------------------------------------------------------------------

def _build_groq_tools() -> list[dict[str, Any]]:
    """Convert AGENT_TOOLS to OpenAI/Groq function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t.get("parameters", {"type": "object", "properties": {}}),
            },
        }
        for t in AGENT_TOOLS
    ]


async def run_agent(
    pdf_bytes: bytes,
    dietary_preferences: list[str] | None = None,
    on_step: Callable[[ReasoningStep], Any] | None = None,
) -> AgentState:
    """
    Run the NutriScan AI Agent using Groq (Llama 3.3 70B).

    Args:
        pdf_bytes: Raw PDF file bytes.
        dietary_preferences: Optional dietary restrictions.
        on_step: Optional callback for each reasoning step (for streaming).

    Returns:
        AgentState with all accumulated results.
    """
    from app.services.gemini_client import tool_chat_with_fallback

    state = AgentState(
        pdf_bytes=pdf_bytes,
        dietary_preferences=dietary_preferences or [],
    )

    pref_text = ""
    if dietary_preferences:
        pref_text = f"\n\nDietary preferences: {', '.join(dietary_preferences)}"

    tools = _build_groq_tools()

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"I've uploaded a lab report PDF ({len(pdf_bytes):,} bytes). "
                f"Please analyze it completely — extract biomarkers, detect deficiencies, "
                f"generate explanations, recommend foods, and build a Walmart cart."
                f"{pref_text}"
            ),
        },
    ]

    step_number = 0

    for iteration in range(MAX_ITERATIONS):
        logger.info("Agent iteration %d/%d", iteration + 1, MAX_ITERATIONS)

        response = await tool_chat_with_fallback(
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1024,
        )

        msg = response.choices[0].message

        # Capture any text reasoning
        if msg.content:
            step_number += 1
            step = ReasoningStep(
                step_number=step_number,
                action="reasoning",
                reasoning=msg.content,
                timestamp=time.time(),
            )
            state.reasoning_steps.append(step)
            if on_step:
                on_step(step)

        # No tool calls → agent is done
        if not msg.tool_calls:
            logger.info("Agent finished — no more tool calls")
            break

        # Append assistant message with tool calls to history.
        # Convert to plain dict and drop `reasoning`/`reasoning_content` so
        # thinking models (Scout, Qwen3) don't trigger a 400 on the next turn.
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_msg)

        # Execute each tool call
        for tc in msg.tool_calls:
            step_number += 1
            logger.info("Agent calling tool: %s", tc.function.name)

            tool_args = json.loads(tc.function.arguments or "{}") or {}
            result_str = await _execute_tool(tc.function.name, tool_args, state)
            result_data = json.loads(result_str)
            summary = _summarize_result(tc.function.name, result_data)

            step = ReasoningStep(
                step_number=step_number,
                action="tool_call",
                tool_name=tc.function.name,
                reasoning=f"Calling {tc.function.name}",
                result_summary=summary,
                timestamp=time.time(),
            )
            state.reasoning_steps.append(step)
            if on_step:
                on_step(step)

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str,
            })

    else:
        logger.warning("Agent hit max iterations (%d)", MAX_ITERATIONS)

    return state


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
        "build_shopping_carts": (
            f"🛒 Built shopping carts for multiple marketplaces"
        ),
    }

    return summaries.get(tool_name, f"✅ {tool_name} completed")
