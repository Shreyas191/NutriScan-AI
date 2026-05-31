"""
Analysis Pipeline — orchestrates the full PDF → deficiency → cart flow.

The agent runs for the streaming/reasoning UX. After it finishes, every step
is guaranteed to complete via deterministic fallbacks — regardless of what
order (or whether) the agent called each tool.
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

    ocr_text: str = ""
    ocr_confidence: float = 0.0
    ocr_method: str = ""

    biomarkers: list[Biomarker] = field(default_factory=list)
    deficiencies: list[Deficiency] = field(default_factory=list)
    explanations: list[Explanation] = field(default_factory=list)
    food_recommendations: list[FoodRecommendation] = field(default_factory=list)

    cart_items: list[dict] = field(default_factory=list)
    shopping_links: dict[str, str] = field(default_factory=dict)
    shop_all_url: str = ""

    reasoning_steps: list[ReasoningStep] = field(default_factory=list)


def _state_to_result(state: AgentState) -> PipelineResult:
    return PipelineResult(
        ocr_text=state.ocr_text,
        ocr_confidence=state.ocr_confidence,
        ocr_method=state.ocr_method,
        biomarkers=state.biomarkers,
        deficiencies=state.deficiencies,
        explanations=state.explanations,
        food_recommendations=state.food_recommendations,
        cart_items=state.cart_items,
        shopping_links=state.shopping_links,
        shop_all_url=state.shop_all_url,
        reasoning_steps=state.reasoning_steps,
    )


async def _ensure_complete(state: AgentState) -> None:
    """
    Deterministic safety net — runs any step the agent skipped or failed.
    Called after the agent loop regardless of what it did.
    """
    # 1. OCR
    if not state.ocr_text:
        logger.info("Fallback: running OCR")
        from app.services.ocr_service import extract_text
        ocr = await extract_text(state.pdf_bytes)
        state.ocr_text = ocr.text
        state.ocr_confidence = ocr.confidence
        state.ocr_method = ocr.method

    # 2. Biomarker extraction
    if not state.biomarkers and state.ocr_text:
        logger.info("Fallback: extracting biomarkers")
        from app.services.biomarker_extractor import extract_biomarkers
        state.biomarkers = await extract_biomarkers(state.ocr_text)

    # 3. Deficiency detection
    if not state.deficiencies and state.biomarkers:
        logger.info("Fallback: detecting deficiencies")
        from app.services.deficiency_engine import detect_deficiencies
        state.deficiencies = detect_deficiencies(state.biomarkers)

    # 4. Explanations
    if not state.explanations and state.deficiencies:
        logger.info("Fallback: generating explanations")
        from app.services.explanation_generator import generate_explanations
        state.explanations = await generate_explanations(state.deficiencies)

    # 5. Food recommendations
    if not state.food_recommendations and state.deficiencies:
        logger.info("Fallback: recommending foods")
        from app.services.food_recommender import recommend_foods
        state.food_recommendations = await recommend_foods(
            state.deficiencies,
            state.dietary_preferences or None,
        )

    # 6. Shopping cart
    if not state.cart_items and state.food_recommendations:
        logger.info("Fallback: building shopping cart")
        from app.services import shopping
        cart_result = await shopping.create_shopping_links(state.food_recommendations)
        state.cart_items = cart_result["cart_items"]
        state.shopping_links = cart_result["shopping_links"]
        state.shop_all_url = cart_result["shopping_links"].get("walmart", "")


async def run_pipeline(
    pdf_bytes: bytes,
    dietary_preferences: list[str] | None = None,
    on_step: Callable[[ReasoningStep], Any] | None = None,
) -> PipelineResult:
    """
    Run the NutriScan AI Agent, then guarantee all steps completed.

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

    await _ensure_complete(state)

    result = _state_to_result(state)

    logger.info(
        "Pipeline complete — %d biomarkers, %d deficiencies, %d recommendations, %d cart items",
        len(result.biomarkers),
        len(result.deficiencies),
        len(result.food_recommendations),
        len(result.cart_items),
    )

    return result
