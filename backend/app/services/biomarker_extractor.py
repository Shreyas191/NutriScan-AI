"""
Biomarker Extractor — uses Groq (Llama 3.3) to extract structured biomarker data from OCR text.
"""

from __future__ import annotations

import json
import logging

from app.models.biomarker import Biomarker

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

Return ONLY a JSON object with a single key "biomarkers" containing an array.
Each biomarker object must have: test_name (string), value (number), unit (string), reference_range (string), flag (string or null).

Example:
{"biomarkers": [{"test_name": "Vitamin D, 25-Hydroxy", "value": 18.5, "unit": "ng/mL", "reference_range": "30-100", "flag": "LOW"}]}"""


async def extract_biomarkers(ocr_text: str) -> list[Biomarker]:
    """Extract structured biomarker data from raw OCR text using Groq."""
    from app.services.gemini_client import chat_with_fallback

    response = await chat_with_fallback(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract all biomarkers from this lab report:\n\n{ocr_text}"},
        ],
        response_format={"type": "json_object"},
        max_tokens=2048,
        temperature=0,
    )

    try:
        data = json.loads(response.choices[0].message.content)
        return [Biomarker(**b) for b in data.get("biomarkers", [])]
    except Exception as e:
        logger.error("Failed to parse biomarkers: %s", e)
        return []
