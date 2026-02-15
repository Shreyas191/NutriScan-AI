"""
Explanation Generator — uses AI to produce clear, non-alarmist,
plain-English explanations of each deficiency.
"""

from __future__ import annotations

import logging

from app.models.biomarker import Deficiency, Explanation, Severity
from app.config import settings

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


async def generate_explanations(
    deficiencies: list[Deficiency],
) -> list[Explanation]:
    """
    Generate plain-English explanations for a list of deficiencies.

    Args:
        deficiencies: List of detected deficiencies with severity info.

    Returns:
        List of Explanation objects with titles and text.
    """
    if not deficiencies:
        return []

    if settings.AI_PROVIDER == "gemini":
        return await _generate_with_gemini(deficiencies)
    else:
        return await _generate_with_claude(deficiencies)


async def _generate_with_gemini(deficiencies: list[Deficiency]) -> list[Explanation]:
    """Generate explanations using Gemini."""
    from app.services.gemini_client import get_client, FLASH

    client = get_client()
    explanations: list[Explanation] = []

    for deficiency in deficiencies:
        biomarker = deficiency.biomarker
        severity_label = deficiency.severity.value.capitalize()

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Explain this lab result to a patient:\n\n"
            f"Test: {biomarker.test_name}\n"
            f"Result: {biomarker.value} {biomarker.unit}\n"
            f"Normal Range: {biomarker.reference_range}\n"
            f"Severity: {severity_label}\n\n"
            f"Provide a clear, plain-English explanation in 2-3 sentences."
        )

        response = client.models.generate_content(
            model=FLASH,
            contents=prompt,
            config={"temperature": 0.3, "max_output_tokens": 512},
        )

        text = response.text.strip()

        explanations.append(
            Explanation(
                title=f"{biomarker.test_name} — {severity_label} Deficiency",
                severity=deficiency.severity,
                text=text,
            )
        )

    return explanations


async def _generate_with_claude(deficiencies: list[Deficiency]) -> list[Explanation]:
    """Generate explanations using Claude (kept for future use)."""
    from app.services.claude_client import get_client, SONNET

    client = get_client()
    explanations: list[Explanation] = []

    for deficiency in deficiencies:
        biomarker = deficiency.biomarker
        severity_label = deficiency.severity.value.capitalize()

        user_message = (
            f"Explain this lab result to a patient:\n\n"
            f"Test: {biomarker.test_name}\n"
            f"Result: {biomarker.value} {biomarker.unit}\n"
            f"Normal Range: {biomarker.reference_range}\n"
            f"Severity: {severity_label}\n\n"
            f"Provide a clear, plain-English explanation in 2-3 sentences."
        )

        response = client.messages.create(
            model=SONNET,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        text = response.content[0].text.strip()

        explanations.append(
            Explanation(
                title=f"{biomarker.test_name} — {severity_label} Deficiency",
                severity=deficiency.severity,
                text=text,
            )
        )

    return explanations
