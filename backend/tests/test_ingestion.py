import pytest
import os
from sqlalchemy import select
from app.services.ingestion_service import ingest_resume
from app.models.candidate import CandidateProfile, Resume, CandidateFact, JobPreference

@pytest.mark.asyncio
async def test_ingest_akash_resume(db_session):
    resume_path = "/Users/akash/Documents/autojob/Akash_s_Resume_new.pdf"
    assert os.path.exists(resume_path)

    result = await ingest_resume(resume_path, db_session)
    assert result["name"] == "Akash Nandy"
    assert "akashnandy" in result["email"]
    assert result["facts_count"] > 5

    # Check CandidateProfile
    cand = (await db_session.execute(select(CandidateProfile))).scalar_one()
    assert cand.full_name == "Akash Nandy"
    assert cand.email == "akashnandy01@gmail.com"

    # Check Resume record
    resumes = (await db_session.execute(select(Resume))).scalars().all()
    assert len(resumes) >= 1
    assert resumes[0].file_name == "Akash_s_Resume_new.pdf"

    # Check CandidateFacts
    facts = (await db_session.execute(select(CandidateFact))).scalars().all()
    assert len(facts) >= 5
    skill_facts = [f for f in facts if f.fact_type == "skill"]
    assert len(skill_facts) > 0

    # Check JobPreference
    prefs = (await db_session.execute(select(JobPreference))).scalar_one()
    assert "Software Development / SDE" in prefs.target_roles or "AI / ML Engineer" in prefs.target_roles
