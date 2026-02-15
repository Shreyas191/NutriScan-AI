"""
Pydantic models for biomarker data, deficiencies, and recommendations.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------
class Severity(str, Enum):
    NORMAL = "normal"
    INSUFFICIENT = "insufficient"
    SEVERE = "severe"


# ---------------------------------------------------------------------------
# Biomarker — a single lab test result
# ---------------------------------------------------------------------------
class Biomarker(BaseModel):
    """One row extracted from a lab report."""

    test_name: str = Field(..., description="Name of the lab test, e.g. 'Vitamin D, 25-Hydroxy'")
    value: float = Field(..., description="Numeric result value")
    unit: str = Field(..., description="Unit of measurement, e.g. 'ng/mL'")
    reference_range: str = Field(..., description="Normal reference range, e.g. '30–100'")
    flag: Optional[str] = Field(None, description="Flag such as 'LOW' or 'HIGH', if any")


# ---------------------------------------------------------------------------
# Deficiency — a detected issue
# ---------------------------------------------------------------------------
class Deficiency(BaseModel):
    """A biomarker classified as deficient."""

    biomarker: Biomarker
    severity: Severity
    percentage_of_normal: float = Field(
        ..., ge=0, le=100, description="How close to the normal range minimum (0-100)"
    )


# ---------------------------------------------------------------------------
# Explanation — AI-generated plain-English summary
# ---------------------------------------------------------------------------
class Explanation(BaseModel):
    """Plain-English explanation of a deficiency."""

    title: str = Field(..., description="Short title, e.g. 'Vitamin D — Severe Deficiency'")
    severity: Severity
    text: str = Field(..., description="Multi-sentence plain-English explanation")


# ---------------------------------------------------------------------------
# FoodRecommendation
# ---------------------------------------------------------------------------
class FoodRecommendation(BaseModel):
    """A single food or supplement recommendation."""

    emoji: str = Field(..., description="Emoji representing the food, e.g. '🐟'")
    name: str = Field(..., description="Food name, e.g. 'Wild Salmon'")
    nutrient: str = Field(..., description="Target nutrient, e.g. 'Vitamin D'")
    amount: str = Field(..., description="Nutrient amount per serving, e.g. '570 IU per 3 oz'")
    category: str = Field("food", description="'food' or 'supplement'")


# ---------------------------------------------------------------------------
# Full analysis result
# ---------------------------------------------------------------------------
class AnalysisResult(BaseModel):
    """Complete output from the analysis pipeline."""

    biomarkers: list[Biomarker]
    deficiencies: list[Deficiency]
    explanations: list[Explanation]
    food_recommendations: list[FoodRecommendation]
