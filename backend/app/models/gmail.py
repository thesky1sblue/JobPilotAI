import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class GmailMessage(Base):
    __tablename__ = "gmail_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(255), index=True)
    sender: Mapped[str] = mapped_column(String(500))
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recipient: Mapped[str] = mapped_column(String(500))
    subject: Mapped[str] = mapped_column(String(1000))
    snippet: Mapped[str] = mapped_column(Text)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    classification: Mapped[str] = mapped_column(String(50), default="acknowledgement")  # acknowledgement, assessment, interview, rejection, update, other
    confidence_score: Mapped[float] = mapped_column(default=0.9)
    action_required: Mapped[bool] = mapped_column(Boolean, default=False)
    action_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    linked_company_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    linked_application_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("applications.id"), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
