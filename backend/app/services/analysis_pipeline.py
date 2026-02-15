"""
Analysis Pipeline — orchestrates the full PDF → deficiency → cart flow.

Uses the NutriScan AI Agent for autonomous, reasoning-driven analysis.
The agent decides which tools to call, validates quality, and self-corrects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from app.models.biomarker import (
    Biomarker,
    Deficiency,
    Explanation,
    FoodRecommendation,
)
from app.services.agent import AgentState, ReasoningStep, run_agent

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete result from the analysis pipeline."""

    # OCR
    ocr_text: str = ""
    ocr_confidence: float = 0.0
    ocr_method: str = ""

    # Biomarkers
    biomarkers: list[Biomarker] = field(default_factory=list)

    # Deficiencies
    deficiencies: list[Deficiency] = field(default_factory=list)

    # AI explanations
    explanations: list[Explanation] = field(default_factory=list)

    # Food recommendations
    food_recommendations: list[FoodRecommendation] = field(default_factory=list)

    # Instacart cart
    cart_items: list[dict] = field(default_factory=list)
    shop_all_url: str = ""

    # Agent reasoning trace
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)


def _state_to_result(state: AgentState) -> PipelineResult:
    """Convert AgentState to PipelineResult."""
    return PipelineResult(
        ocr_text=state.ocr_text,
        ocr_confidence=state.ocr_confidence,
        ocr_method=state.ocr_method,
        biomarkers=state.biomarkers,
        deficiencies=state.deficiencies,
        explanations=state.explanations,
        food_recommendations=state.food_recommendations,
        cart_items=state.cart_items,
        shop_all_url=state.shop_all_url,
        reasoning_steps=state.reasoning_steps,
    )


async def run_pipeline(
    pdf_bytes: bytes,
    dietary_preferences: list[str] | None = None,
    on_step: Callable[[ReasoningStep], Any] | None = None,
) -> PipelineResult:
    """
    Run the NutriScan AI Agent on a PDF lab report.

    The agent autonomously decides what to do, validates results,
    and self-corrects when needed.

    Args:
        pdf_bytes: Raw PDF file bytes.
        dietary_preferences: Optional dietary restrictions (e.g. ["vegan"]).
        on_step: Optional callback for each reasoning step (for streaming).

    Returns:
        PipelineResult with all extracted data, analysis, and cart URLs.
    """
    logger.info("Starting NutriScan AI Agent...")

    state = await run_agent(
        pdf_bytes=pdf_bytes,
        dietary_preferences=dietary_preferences,
        on_step=on_step,
    )

    result = _state_to_result(state)

    logger.info(
        "Agent complete — %d biomarkers, %d deficiencies, %d recommendations, %d reasoning steps",
        len(result.biomarkers),
        len(result.deficiencies),
        len(result.food_recommendations),
        len(result.reasoning_steps),
    )

    return result
