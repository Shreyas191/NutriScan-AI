"""
Food Recommender — uses AI to generate evidence-based food and
supplement recommendations for detected deficiencies.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.models.biomarker import Deficiency, FoodRecommendation
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a nutrition expert assistant for NutriScan AI.

Your task is to recommend foods and supplements to help correct nutrient deficiencies.

Rules:
- Recommend 4-6 foods and 1 supplement per deficiency.
- All recommendations must be evidence-based.
- Include the approximate nutrient amount per serving.
- Use a single relevant emoji for each item.
- Respect dietary preferences if provided (e.g., if "vegan", do not suggest meat or dairy).
- Mark supplements with category "supplement" and foods with "food".
- Do NOT recommend specific dosages for supplements — just name the supplement type.
- Use common, easily available grocery items.

Return your answer as a JSON object with a single key "recommendations" containing an array.
Each recommendation object must have: emoji (string), name (string), nutrient (string), amount (string), category ("food" or "supplement").

Example:
{"recommendations": [{"emoji": "🐟", "name": "Wild Salmon", "nutrient": "Vitamin D", "amount": "570 IU per 3 oz", "category": "food"}]}

IMPORTANT: Return ONLY the JSON object, no other text."""


async def recommend_foods(
    deficiencies: list[Deficiency],
    dietary_preferences: list[str] | None = None,
) -> list[FoodRecommendation]:
    """
    Generate food and supplement recommendations for detected deficiencies.

    Args:
        deficiencies: List of detected deficiencies.
        dietary_preferences: Optional list like ["vegan", "lactose-free"].

    Returns:
        List of FoodRecommendation objects.
    """
    if not deficiencies:
        return []

    if settings.AI_PROVIDER == "gemini":
        return await _recommend_with_gemini(deficiencies, dietary_preferences)
    else:
        return await _recommend_with_claude(deficiencies, dietary_preferences)


def _build_deficiency_prompt(
    deficiencies: list[Deficiency],
    dietary_preferences: list[str] | None = None,
) -> str:
    """Build the deficiency summary for the prompt."""
    deficiency_lines = []
    for d in deficiencies:
        b = d.biomarker
        deficiency_lines.append(
            f"- {b.test_name}: {b.value} {b.unit} "
            f"(normal: {b.reference_range}) — {d.severity.value}"
        )

    pref_text = ""
    if dietary_preferences:
        pref_text = f"\n\nDietary preferences to respect: {', '.join(dietary_preferences)}"

    return (
        f"Recommend foods and supplements for these deficiencies:\n\n"
        f"{chr(10).join(deficiency_lines)}"
        f"{pref_text}"
    )


async def _recommend_with_gemini(
    deficiencies: list[Deficiency],
    dietary_preferences: list[str] | None,
) -> list[FoodRecommendation]:
    """Recommend foods using Gemini."""
    from app.services.gemini_client import get_client, FLASH

    client = get_client()
    user_prompt = _build_deficiency_prompt(deficiencies, dietary_preferences)
    prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

    response = client.models.generate_content(
        model=FLASH,
        contents=prompt,
        config={"temperature": 0.3, "max_output_tokens": 2048},
    )

    text = response.text.strip()

    # Clean markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
        raw = data.get("recommendations", [])
        return [FoodRecommendation(**r) for r in raw]
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Failed to parse Gemini food recommendations: %s", e)
        logger.debug("Raw response: %s", text[:500])
        return []


async def _recommend_with_claude(
    deficiencies: list[Deficiency],
    dietary_preferences: list[str] | None,
) -> list[FoodRecommendation]:
    """Recommend foods using Claude (kept for future use)."""
    from app.services.claude_client import get_client, HAIKU

    RECOMMENDATION_TOOL: dict[str, Any] = {
        "name": "save_recommendations",
        "description": "Save the list of food and supplement recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "emoji": {"type": "string"},
                            "name": {"type": "string"},
                            "nutrient": {"type": "string"},
                            "amount": {"type": "string"},
                            "category": {"type": "string", "enum": ["food", "supplement"]},
                        },
                        "required": ["emoji", "name", "nutrient", "amount", "category"],
                    },
                },
            },
            "required": ["recommendations"],
        },
    }

    client = get_client()
    user_prompt = _build_deficiency_prompt(deficiencies, dietary_preferences)

    response = client.messages.create(
        model=HAIKU,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=[RECOMMENDATION_TOOL],
        tool_choice={"type": "tool", "name": "save_recommendations"},
        messages=[{"role": "user", "content": user_prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "save_recommendations":
            raw = block.input.get("recommendations", [])
            return [FoodRecommendation(**r) for r in raw]

    return []
