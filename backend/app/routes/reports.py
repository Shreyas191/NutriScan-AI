"""
Reports API — upload, analyse, and retrieve lab report results.

Endpoints:
  POST /api/upload          — Upload PDF + run agent (JSON response)
  POST /api/upload/stream   — Upload PDF + run agent (SSE streaming response)
  GET  /api/reports/{id}    — Retrieve full analysis results
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.analysis_pipeline import PipelineResult, run_pipeline
from app.services.agent import ReasoningStep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Reports"])

# ---------------------------------------------------------------------------
# In-memory store  (MVP — will be replaced with DB persistence later)
# ---------------------------------------------------------------------------
_reports: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------
class UploadResponse(BaseModel):
    report_id: str
    filename: str
    message: str


class BiomarkerResponse(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: str
    flag: str | None = None


class DeficiencyResponse(BaseModel):
    name: str
    value: float
    unit: str
    normal_range: str
    severity: str
    percentage: float


class ExplanationResponse(BaseModel):
    title: str
    severity: str
    explanation: str


class CartItemResponse(BaseModel):
    id: int
    name: str
    emoji: str
    nutrient: str
    amount: str
    category: str
    quantity: int
    instacart_url: str


class ReasoningStepResponse(BaseModel):
    step_number: int
    action: str
    tool_name: str | None = None
    reasoning: str
    result_summary: str


class AnalysisResponse(BaseModel):
    report_id: str
    status: str
    biomarkers: list[BiomarkerResponse]
    deficiencies: list[DeficiencyResponse]
    explanations: list[ExplanationResponse]
    cart_items: list[CartItemResponse]
    shop_all_url: str
    ocr_confidence: float
    ocr_method: str
    reasoning_steps: list[ReasoningStepResponse]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _validate_upload(file: UploadFile) -> None:
    """Validate uploaded file is a PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted",
        )


def _parse_preferences(dietary_preferences: str) -> list[str] | None:
    """Parse comma-separated dietary preferences."""
    if not dietary_preferences:
        return None
    return [p.strip() for p in dietary_preferences.split(",") if p.strip()]


def _build_analysis_response(report_id: str, pr: PipelineResult) -> AnalysisResponse:
    """Transform PipelineResult to AnalysisResponse."""
    return AnalysisResponse(
        report_id=report_id,
        status="analyzed",
        biomarkers=[
            BiomarkerResponse(
                test_name=b.test_name,
                value=b.value,
                unit=b.unit,
                reference_range=b.reference_range,
                flag=b.flag,
            )
            for b in pr.biomarkers
        ],
        deficiencies=[
            DeficiencyResponse(
                name=d.biomarker.test_name,
                value=d.biomarker.value,
                unit=d.biomarker.unit,
                normal_range=d.biomarker.reference_range,
                severity=d.severity.value,
                percentage=d.percentage_of_normal,
            )
            for d in pr.deficiencies
        ],
        explanations=[
            ExplanationResponse(
                title=e.title,
                severity=e.severity.value,
                explanation=e.text,
            )
            for e in pr.explanations
        ],
        cart_items=[
            CartItemResponse(
                id=i + 1,
                name=item["name"],
                emoji=item["emoji"],
                nutrient=item["nutrient"],
                amount=item["amount"],
                category=item["category"],
                quantity=1,
                instacart_url=item["instacart_url"],
            )
            for i, item in enumerate(pr.cart_items)
        ],
        shop_all_url=pr.shop_all_url,
        ocr_confidence=pr.ocr_confidence,
        ocr_method=pr.ocr_method,
        reasoning_steps=[
            ReasoningStepResponse(
                step_number=s.step_number,
                action=s.action,
                tool_name=s.tool_name,
                reasoning=s.reasoning,
                result_summary=s.result_summary,
            )
            for s in pr.reasoning_steps
        ],
    )


# ---------------------------------------------------------------------------
# POST /api/upload — JSON response
# ---------------------------------------------------------------------------
@router.post("/upload", response_model=UploadResponse)
async def upload_report(
    file: UploadFile = File(...),
    dietary_preferences: str = Form(""),
):
    """Upload a PDF lab report and run the AI agent analysis."""
    _validate_upload(file)

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10 MB limit",
        )

    prefs = _parse_preferences(dietary_preferences)
    report_id = str(uuid.uuid4())

    try:
        logger.info("Starting agent for report %s (%s)", report_id, file.filename)
        pipeline_result = await run_pipeline(contents, prefs)
    except Exception as e:
        logger.error("Agent failed for report %s: %s", report_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )

    _reports[report_id] = {
        "filename": file.filename,
        "pipeline_result": pipeline_result,
        "dietary_preferences": prefs,
    }

    return UploadResponse(
        report_id=report_id,
        filename=file.filename or "report.pdf",
        message=f"Analysis complete — {len(pipeline_result.deficiencies)} deficiencies found",
    )


# ---------------------------------------------------------------------------
# POST /api/upload/stream — SSE streaming response
# ---------------------------------------------------------------------------
@router.post("/upload/stream")
async def upload_report_stream(
    file: UploadFile = File(...),
    dietary_preferences: str = Form(""),
):
    """
    Upload a PDF and stream the AI agent's reasoning steps in real-time.

    Returns Server-Sent Events (SSE):
      - event: step  → agent reasoning/tool call step
      - event: done  → final report_id when complete
      - event: error → if something goes wrong
    """
    _validate_upload(file)

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10 MB limit",
        )

    prefs = _parse_preferences(dietary_preferences)
    report_id = str(uuid.uuid4())

    async def event_stream():
        """Generate SSE events as the agent runs."""
        step_queue: asyncio.Queue[ReasoningStep | None] = asyncio.Queue()

        def on_step(step: ReasoningStep):
            """Callback from the agent — queue steps for SSE."""
            step_queue.put_nowait(step)

        # Run the agent in a background task
        async def run_agent_task():
            try:
                result = await run_pipeline(contents, prefs, on_step=on_step)
                _reports[report_id] = {
                    "filename": file.filename,
                    "pipeline_result": result,
                    "dietary_preferences": prefs,
                }
                return result
            finally:
                step_queue.put_nowait(None)  # Signal completion

        task = asyncio.create_task(run_agent_task())

        # Stream steps as they arrive
        while True:
            step = await step_queue.get()
            if step is None:
                break  # Agent is done

            event_data = json.dumps({
                "step_number": step.step_number,
                "action": step.action,
                "tool_name": step.tool_name,
                "reasoning": step.reasoning,
                "result_summary": step.result_summary,
            })
            yield f"event: step\ndata: {event_data}\n\n"

        # Wait for the task to finish and get result
        try:
            result = await task
            done_data = json.dumps({
                "report_id": report_id,
                "deficiency_count": len(result.deficiencies),
                "biomarker_count": len(result.biomarkers),
                "recommendation_count": len(result.food_recommendations),
            })
            yield f"event: done\ndata: {done_data}\n\n"
        except Exception as e:
            error_data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# GET /api/reports/{report_id}
# ---------------------------------------------------------------------------
@router.get("/reports/{report_id}", response_model=AnalysisResponse)
async def get_report(report_id: str):
    """Retrieve the full analysis results for a report."""
    if report_id not in _reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    data = _reports[report_id]
    pr: PipelineResult = data["pipeline_result"]

    return _build_analysis_response(report_id, pr)
