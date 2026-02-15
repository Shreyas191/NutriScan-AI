"""
SQLAlchemy ORM models for NutriScan AI.

Tables:
  - users            — synced from Clerk (user_id, email, role)
  - lab_reports      — uploaded PDF metadata
  - biomarker_results — extracted biomarker values per report
  - deficiency_records — detected deficiencies with severity
  - recommendations  — food/supplement recs linked to deficiencies
  - analytics_events — lightweight event tracking
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Users (synced from Clerk)
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clerk_user_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    lab_reports: Mapped[list["LabReport"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Lab Reports
# ---------------------------------------------------------------------------
class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(
        String(1000), nullable=False, comment="Supabase Storage path"
    )
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="uploaded", nullable=False,
        comment="uploaded | processing | analyzed | failed"
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    analyzed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="lab_reports")
    biomarker_results: Mapped[list["BiomarkerResult"]] = relationship(
        back_populates="lab_report", cascade="all, delete-orphan"
    )
    deficiency_records: Mapped[list["DeficiencyRecord"]] = relationship(
        back_populates="lab_report", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_lab_reports_user_uploaded", "user_id", "uploaded_at"),
    )


# ---------------------------------------------------------------------------
# Biomarker Results
# ---------------------------------------------------------------------------
class BiomarkerResult(Base):
    __tablename__ = "biomarker_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lab_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lab_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_name: Mapped[str] = mapped_column(String(300), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_range: Mapped[str] = mapped_column(String(100), nullable=False)
    flag: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="LOW | HIGH | null"
    )

    # Relationships
    lab_report: Mapped["LabReport"] = relationship(back_populates="biomarker_results")

    __table_args__ = (
        Index("ix_biomarker_results_report", "lab_report_id"),
    )


# ---------------------------------------------------------------------------
# Deficiency Records
# ---------------------------------------------------------------------------
class DeficiencyRecord(Base):
    __tablename__ = "deficiency_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lab_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lab_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_name: Mapped[str] = mapped_column(String(300), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_range: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="normal | insufficient | severe"
    )
    percentage_of_normal: Mapped[float] = mapped_column(Float, nullable=False)
    explanation_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    lab_report: Mapped["LabReport"] = relationship(back_populates="deficiency_records")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="deficiency_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_deficiency_records_report", "lab_report_id"),
    )


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------
class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    deficiency_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deficiency_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    emoji: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    nutrient: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), default="food", nullable=False,
        comment="food | supplement"
    )

    # Relationships
    deficiency_record: Mapped["DeficiencyRecord"] = relationship(
        back_populates="recommendations"
    )

    __table_args__ = (
        Index("ix_recommendations_deficiency", "deficiency_record_id"),
    )


# ---------------------------------------------------------------------------
# Analytics Events (lightweight tracking)
# ---------------------------------------------------------------------------
class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="e.g. pdf_uploaded, analysis_completed, cart_generated, instacart_redirect"
    )
    metadata_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Optional JSON metadata blob"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_analytics_events_type_created", "event_type", "created_at"),
    )
