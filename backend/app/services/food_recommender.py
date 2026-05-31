"""
Food Recommender — uses Groq (Llama 3.3) to generate evidence-based food and
supplement recommendations for detected deficiencies.
"""

from __future__ import annotations

import json
import logging

from app.models.biomarker import Deficiency, FoodRecommendation

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

Return ONLY a JSON object with a single key "recommendations" containing an array.
Each recommendation object must have: emoji (string), name (string), nutrient (string), amount (string), category ("food" or "supplement").

Example:
{"recommendations": [{"emoji": "🐟", "name": "Wild Salmon", "nutrient": "Vitamin D", "amount": "570 IU per 3 oz", "category": "food"}]}"""


async def recommend_foods(
    deficiencies: list[Deficiency],
    dietary_preferences: list[str] | None = None,
) -> list[FoodRecommendation]:
    """Generate food and supplement recommendations for detected deficiencies using Groq."""
    if not deficiencies:
        return []

    from app.services.gemini_client import chat_with_fallback

    deficiency_lines = [
        f"- {d.biomarker.test_name}: {d.biomarker.value} {d.biomarker.unit} "
        f"(normal: {d.biomarker.reference_range}) — {d.severity.value}"
        for d in deficiencies
    ]
    pref_text = ""
    if dietary_preferences:
        pref_text = f"\n\nDietary preferences to respect: {', '.join(dietary_preferences)}"

    response = await chat_with_fallback(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Recommend foods and supplements for these deficiencies:\n\n"
                f"{chr(10).join(deficiency_lines)}{pref_text}"
            )},
        ],
        response_format={"type": "json_object"},
        max_tokens=2048,
        temperature=0,
    )

    try:
        data = json.loads(response.choices[0].message.content)
        return [FoodRecommendation(**r) for r in data.get("recommendations", [])]
    except Exception as e:
        logger.error("Failed to parse food recommendations: %s", e)
        return []
