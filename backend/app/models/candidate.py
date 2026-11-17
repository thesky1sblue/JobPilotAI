import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, Boolean, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base

class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(255), default="Candidate")
    email: Mapped[str] = mapped_column(String(255), unique=True, default="candidate@example.com")
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    experience_years: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    resumes: Mapped[List["Resume"]] = relationship(back_populates="candidate")
    facts: Mapped[List["CandidateFact"]] = relationship(back_populates="candidate")
    preferences: Mapped[Optional["JobPreference"]] = relationship(back_populates="candidate", uselist=False)

class Resume(Base):
    __tablename__ = "resumes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    file_path: Mapped[str] = mapped_column(String(1000))
    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(10))
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_original: Mapped[bool] = mapped_column(Boolean, default=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    candidate: Mapped["CandidateProfile"] = relationship(back_populates="resumes")

class CandidateFact(Base):
    __tablename__ = "candidate_facts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"))
    fact_type: Mapped[str] = mapped_column(String(50))
    fact_data: Mapped[dict] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(100), default="resume")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    candidate: Mapped["CandidateProfile"] = relationship(back_populates="facts")

class JobPreference(Base):
    __tablename__ = "job_preferences"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidate_profiles.id"), unique=True)
    target_roles: Mapped[list] = mapped_column(JSONB, default=list)
    preferred_locations: Mapped[list] = mapped_column(JSONB, default=list)
    work_types: Mapped[list] = mapped_column(JSONB, default=list)
    min_salary: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_salary: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    experience_level: Mapped[str] = mapped_column(String(50), default="fresher")
    experience_years: Mapped[float] = mapped_column(Float, default=0.0)
    discovery_morning: Mapped[str] = mapped_column(String(10), default="09:00")
    discovery_evening: Mapped[str] = mapped_column(String(10), default="21:00")
    discovery_timezone: Mapped[str] = mapped_column(String(50), default="Asia/Kolkata")
    llm_provider: Mapped[str] = mapped_column(String(50), default="gemini")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    candidate: Mapped["CandidateProfile"] = relationship(back_populates="preferences")
