import pytest
from app.agents.extraction import ExtractionAgent, extract_skills_from_text, extract_experience

@pytest.mark.asyncio
async def test_extraction_basic():
    agent = ExtractionAgent()
    result = await agent.run({
        "raw_job": {
            "title": "Python Developer",
            "description": "We are looking for a Python developer with experience in FastAPI, PostgreSQL and Docker. Fresher or 0-1 year experience welcome.",
            "location": "Remote",
            "source": "greenhouse",
            "source_id": "123",
            "application_url": "https://example.com/apply",
        }
    })
    assert result["status"] == "success"
    assert "python" in result["data"]["required_skills"]
    assert result["data"]["location_type"] == "remote"

def test_extract_skills():
    skills = extract_skills_from_text("Strong Python and FastAPI skills required. Knowledge of Docker a plus.")
    assert "python" in skills
    assert "fastapi" in skills
    assert "docker" in skills

def test_extract_experience_fresher():
    exp = extract_experience("Fresher or recent graduate preferred.")
    assert exp == 0

def test_extract_experience_years():
    exp = extract_experience("Requires 3+ years of experience in software development.")
    assert exp == 3
