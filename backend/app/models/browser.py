import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class BrowserSession(Base):
    __tablename__ = "browser_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("workflow_runs.id"), nullable=True)
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)
    portal_url: Mapped[str] = mapped_column(String(1500))
    portal_type: Mapped[str] = mapped_column(String(100), default="custom")  # greenhouse, lever, workday, custom
    status: Mapped[str] = mapped_column(String(50), default="initialized")  # initialized, navigating, inspecting, filled, validated, submitted, blocked_anti_bot, failed
    anti_bot_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    anti_bot_details: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    detected_fields: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    staged_answers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    resume_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    cover_letter_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    pre_submit_screenshot_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    post_submit_screenshot_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    submission_success: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    error_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
