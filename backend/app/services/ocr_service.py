"""
OCR Service — extracts text from PDF lab reports.

Strategy:
  1. Try pdfplumber first (for digital/text-based PDFs — fast, no OCR needed)
  2. Fall back to Tesseract OCR for scanned PDFs (PDF → images → text)
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of text extraction from a PDF."""
    text: str
    confidence: float  # 0.0 – 1.0
    method: str  # "pdfplumber" or "tesseract"
    page_count: int


async def extract_text(pdf_bytes: bytes) -> OCRResult:
    """
    Extract text from a PDF file.

    Tries digital extraction first (pdfplumber), falls back to
    Tesseract OCR for scanned/image-based PDFs.

    Args:
        pdf_bytes: Raw PDF file content.

    Returns:
        OCRResult with extracted text, confidence, and method used.
    """
    # --- Attempt 1: pdfplumber (digital PDFs) ---
    try:
        result = _extract_with_pdfplumber(pdf_bytes)
        if result and len(result.text.strip()) > 50:
            logger.info(
                "pdfplumber extracted %d chars from %d pages",
                len(result.text), result.page_count,
            )
            return result
    except Exception as e:
        logger.warning("pdfplumber failed: %s", e)

    # --- Attempt 2: Tesseract OCR (scanned PDFs) ---
    try:
        result = _extract_with_tesseract(pdf_bytes)
        logger.info(
            "Tesseract extracted %d chars from %d pages (conf=%.2f)",
            len(result.text), result.page_count, result.confidence,
        )
        return result
    except Exception as e:
        logger.error("Tesseract OCR failed: %s", e)
        raise RuntimeError(f"Could not extract text from PDF: {e}") from e


def _extract_with_pdfplumber(pdf_bytes: bytes) -> OCRResult | None:
    """Extract text from a digital PDF using pdfplumber."""
    pages_text: list[str] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)

    full_text = "\n\n".join(pages_text)

    if not full_text.strip():
        return None

    return OCRResult(
        text=full_text,
        confidence=0.95,  # Digital PDFs have near-perfect extraction
        method="pdfplumber",
        page_count=len(pages_text),
    )


def _extract_with_tesseract(pdf_bytes: bytes) -> OCRResult:
    """Extract text from a scanned PDF using Tesseract OCR."""
    # These are optional heavy dependencies — import only when needed
    from pdf2image import convert_from_bytes
    import pytesseract

    images = convert_from_bytes(pdf_bytes, dpi=300)
    pages_text: list[str] = []
    confidences: list[float] = []

    for img in images:
        # Get detailed data for confidence scoring
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        # Calculate average confidence (ignoring -1 which means no text)
        conf_values = [c for c in data["conf"] if c != -1]
        if conf_values:
            avg_conf = sum(conf_values) / len(conf_values) / 100.0
            confidences.append(avg_conf)

        # Get the text
        text = pytesseract.image_to_string(img)
        pages_text.append(text)

    full_text = "\n\n".join(pages_text)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return OCRResult(
        text=full_text,
        confidence=round(avg_confidence, 3),
        method="tesseract",
        page_count=len(images),
    )
