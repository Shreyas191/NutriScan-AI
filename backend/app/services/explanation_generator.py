"""
Explanation Generator — uses Groq (Llama 3.3) to produce clear, non-alarmist
plain-English explanations of each deficiency.
"""

from __future__ import annotations

import logging

from app.models.biomarker import Deficiency, Explanation

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a health communication assistant for NutriScan AI.

Your job is to explain lab result deficiencies in plain English.

Tone requirements:
- Clear and easy to understand (no medical jargon)
- Actionable — tell the user what they can do
- Non-alarmist — do not scare the user
- Non-diagnostic — you are NOT a doctor
- Always encourage consulting a healthcare provider

Structure each explanation as 2-3 sentences covering:
1. What the result means in simple terms
2. Possible symptoms or effects
3. What the user can do about it (diet, supplements, see a doctor)

IMPORTANT: Never make specific dosage recommendations. Never diagnose conditions."""


async def generate_explanations(deficiencies: list[Deficiency]) -> list[Explanation]:
    """Generate plain-English explanations for a list of deficiencies using Groq."""
    if not deficiencies:
        return []

    from app.services.gemini_client import chat_with_fallback

    explanations: list[Explanation] = []

    for deficiency in deficiencies:
        biomarker = deficiency.biomarker
        severity_label = deficiency.severity.value.capitalize()

        response = await chat_with_fallback(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Explain this lab result to a patient:\n\n"
                    f"Test: {biomarker.test_name}\n"
                    f"Result: {biomarker.value} {biomarker.unit}\n"
                    f"Normal Range: {biomarker.reference_range}\n"
                    f"Severity: {severity_label}\n\n"
                    f"Provide a clear, plain-English explanation in 2-3 sentences."
                )},
            ],
            max_tokens=512,
            temperature=0.3,
        )

        text = (response.choices[0].message.content or "").strip()
        explanations.append(
            Explanation(
                title=f"{biomarker.test_name} — {severity_label} Deficiency",
                severity=deficiency.severity,
                text=text,
            )
        )

    return explanations
