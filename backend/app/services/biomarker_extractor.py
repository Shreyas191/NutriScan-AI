"""
Biomarker Extractor — uses AI to extract structured biomarker data from OCR text.
Supports Gemini (default) and Claude (future).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.models.biomarker import Biomarker
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a clinical lab report parser. You will receive raw OCR text from a blood test report.

Your task:
1. Find ALL biomarker test results in the text.
2. For each biomarker, extract: test name, numeric value, unit, and reference range.
3. Set the flag to "LOW" if the value is below the reference range, "HIGH" if above, or null if normal.

Rules:
- Only extract results that have a clear numeric value.
- Use the exact test name as written in the report.
- If a reference range is given as "30-100", keep that format.
- Be precise with units — do not guess.

Return your answer as a JSON object with a single key "biomarkers" containing an array.
Each biomarker object must have: test_name (string), value (number), unit (string), reference_range (string), flag (string or null).

Example:
{"biomarkers": [{"test_name": "Vitamin D, 25-Hydroxy", "value": 18.5, "unit": "ng/mL", "reference_range": "30-100", "flag": "LOW"}]}

IMPORTANT: Return ONLY the JSON object, no other text."""


async def extract_biomarkers(ocr_text: str) -> list[Biomarker]:
    """
    Extract structured biomarker data from raw OCR text.

    Args:
        ocr_text: Raw text from OCR processing of a lab report PDF.

    Returns:
        List of validated Biomarker objects.
    """
    if settings.AI_PROVIDER == "gemini":
        return await _extract_with_gemini(ocr_text)
    else:
        return await _extract_with_claude(ocr_text)


async def _extract_with_gemini(ocr_text: str) -> list[Biomarker]:
    """Extract biomarkers using Gemini."""
    from app.services.gemini_client import get_client, FLASH

    client = get_client()
    prompt = f"{SYSTEM_PROMPT}\n\nExtract all biomarkers from this lab report:\n\n{ocr_text}"

    response = client.models.generate_content(
        model=FLASH,
        contents=prompt,
        config={"temperature": 0.1, "max_output_tokens": 2048},
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
        raw_biomarkers = data.get("biomarkers", [])
        return [Biomarker(**b) for b in raw_biomarkers]
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Failed to parse Gemini biomarker response: %s", e)
        logger.debug("Raw response: %s", text[:500])
        return []


async def _extract_with_claude(ocr_text: str) -> list[Biomarker]:
    """Extract biomarkers using Claude (kept for future use)."""
    from app.services.claude_client import get_client, HAIKU

    EXTRACTION_TOOL: dict[str, Any] = {
        "name": "save_biomarkers",
        "description": "Save the list of biomarkers extracted from a lab report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "biomarkers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "test_name": {"type": "string"},
                            "value": {"type": "number"},
                            "unit": {"type": "string"},
                            "reference_range": {"type": "string"},
                            "flag": {"type": "string"},
                        },
                        "required": ["test_name", "value", "unit", "reference_range"],
                    },
                },
            },
            "required": ["biomarkers"],
        },
    }

    client = get_client()
    response = client.messages.create(
        model=HAIKU,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "save_biomarkers"},
        messages=[{"role": "user", "content": f"Extract all biomarkers from this lab report:\n\n{ocr_text}"}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "save_biomarkers":
            raw_biomarkers = block.input.get("biomarkers", [])
            return [Biomarker(**b) for b in raw_biomarkers]

    return []
