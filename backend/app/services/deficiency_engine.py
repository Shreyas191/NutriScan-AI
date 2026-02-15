"""
Deficiency Detection Engine — threshold-based classification of biomarkers.

Classifies biomarker values as normal / insufficient / severe based on
clinically-informed thresholds. Extensible via the THRESHOLDS config.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.models.biomarker import Biomarker, Deficiency, Severity


# ---------------------------------------------------------------------------
# Threshold configuration
# ---------------------------------------------------------------------------
# Each entry maps a test name (lowercase) to its classification rules.
# "low_severe": below this → severe deficiency
# "low_insufficient": below this (but above severe) → insufficient
# "high_insufficient": above this → HIGH insufficient (optional)
# "high_severe": above this → HIGH severe (optional)
#
# We match biomarker test names using substring matching (case-insensitive).
# ---------------------------------------------------------------------------

@dataclass
class ThresholdRule:
    """Classification thresholds for a single biomarker."""
    display_name: str
    low_severe: float | None = None
    low_insufficient: float | None = None
    high_insufficient: float | None = None
    high_severe: float | None = None


THRESHOLDS: dict[str, ThresholdRule] = {
    # --- Vitamin D ---
    "vitamin d": ThresholdRule(
        display_name="Vitamin D",
        low_severe=12.0,      # < 12 ng/mL = severe
        low_insufficient=30.0, # < 30 ng/mL = insufficient
    ),
    # --- Iron / Ferritin ---
    "ferritin": ThresholdRule(
        display_name="Iron (Ferritin)",
        low_severe=10.0,       # < 10 ng/mL = severe
        low_insufficient=20.0, # < 20 ng/mL = insufficient
    ),
    # --- Vitamin B12 ---
    "b12": ThresholdRule(
        display_name="Vitamin B12",
        low_severe=150.0,      # < 150 pg/mL = severe
        low_insufficient=200.0,# < 200 pg/mL = insufficient
    ),
    # --- Folate ---
    "folate": ThresholdRule(
        display_name="Folate",
        low_severe=2.0,        # < 2.0 ng/mL = severe
        low_insufficient=3.0,  # < 3.0 ng/mL = insufficient
    ),
    # --- Calcium ---
    "calcium": ThresholdRule(
        display_name="Calcium",
        low_severe=7.0,        # < 7.0 mg/dL = severe
        low_insufficient=8.5,  # < 8.5 mg/dL = insufficient
        high_insufficient=10.5,# > 10.5 mg/dL = high
    ),
    # --- Hemoglobin ---
    "hemoglobin": ThresholdRule(
        display_name="Hemoglobin",
        low_severe=7.0,        # < 7.0 g/dL = severe
        low_insufficient=12.0, # < 12.0 g/dL = insufficient
    ),
    # --- TSH (Thyroid) ---
    "tsh": ThresholdRule(
        display_name="TSH",
        low_insufficient=0.4,  # < 0.4 mIU/L = low (hyperthyroid)
        high_insufficient=4.0, # > 4.0 mIU/L = high (hypothyroid)
        high_severe=10.0,      # > 10.0 mIU/L = severe
    ),
    # --- Iron (Serum) ---
    "iron": ThresholdRule(
        display_name="Iron",
        low_severe=30.0,       # < 30 µg/dL = severe
        low_insufficient=60.0, # < 60 µg/dL = insufficient
    ),
    # --- Magnesium ---
    "magnesium": ThresholdRule(
        display_name="Magnesium",
        low_severe=1.0,        # < 1.0 mg/dL = severe
        low_insufficient=1.7,  # < 1.7 mg/dL = insufficient
    ),
    # --- Zinc ---
    "zinc": ThresholdRule(
        display_name="Zinc",
        low_severe=40.0,       # < 40 µg/dL = severe
        low_insufficient=60.0, # < 60 µg/dL = insufficient
    ),
}


def _match_threshold(test_name: str) -> ThresholdRule | None:
    """Find a matching threshold rule for a biomarker test name."""
    name_lower = test_name.lower()
    for key, rule in THRESHOLDS.items():
        if key in name_lower:
            return rule
    return None


def _calculate_percentage(
    value: float, threshold: float
) -> float:
    """Calculate how close a value is to the threshold (0-100)."""
    if threshold <= 0:
        return 100.0
    pct = (value / threshold) * 100
    return round(min(pct, 100.0), 1)


def detect_deficiencies(biomarkers: list[Biomarker]) -> list[Deficiency]:
    """
    Classify biomarkers and detect deficiencies.

    Args:
        biomarkers: List of extracted biomarker values.

    Returns:
        List of Deficiency objects for values outside normal range.
    """
    deficiencies: list[Deficiency] = []

    for biomarker in biomarkers:
        rule = _match_threshold(biomarker.test_name)
        if rule is None:
            continue  # No threshold rule for this biomarker

        severity = Severity.NORMAL
        pct = 100.0

        # Check LOW thresholds
        if rule.low_severe is not None and biomarker.value < rule.low_severe:
            severity = Severity.SEVERE
            pct = _calculate_percentage(biomarker.value, rule.low_insufficient or rule.low_severe)
        elif rule.low_insufficient is not None and biomarker.value < rule.low_insufficient:
            severity = Severity.INSUFFICIENT
            pct = _calculate_percentage(biomarker.value, rule.low_insufficient)

        # Check HIGH thresholds
        if rule.high_severe is not None and biomarker.value > rule.high_severe:
            severity = Severity.SEVERE
            pct = _calculate_percentage(rule.high_insufficient or rule.high_severe, biomarker.value)
        elif rule.high_insufficient is not None and biomarker.value > rule.high_insufficient:
            if severity == Severity.NORMAL:  # Don't override a low-severity
                severity = Severity.INSUFFICIENT
                pct = _calculate_percentage(rule.high_insufficient, biomarker.value)

        if severity != Severity.NORMAL:
            deficiencies.append(
                Deficiency(
                    biomarker=biomarker,
                    severity=severity,
                    percentage_of_normal=pct,
                )
            )

    return deficiencies
