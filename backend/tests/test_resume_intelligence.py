import pytest
from app.agents.resume_intelligence import ResumeIntelligenceAgent
from app.services.pdf_service import pdf_service
import os

@pytest.mark.asyncio
async def test_resume_tailoring():
    agent = ResumeIntelligenceAgent()
    candidate = {
        "full_name": "Akash Nandy",
        "email": "akashnandy01@gmail.com",
        "phone": "+91 9330136009",
        "location": "Chennai / Kolkata, India",
    }
    facts = [
        {"type": "skill", "data": {"name": "Python"}},
        {"type": "skill", "data": {"name": "TensorFlow"}},
        {"type": "experience", "data": {"role": "Data Science Intern", "company": "ARDENT", "period": "2024", "description": ["Trained ML models"]}},
        {"type": "project", "data": {"name": "Echocheck", "technologies": ["Python", "Flask"], "description": ["NLP classification"]}},
        {"type": "education", "data": {"degree": "MCA", "institution": "VIT Chennai", "year": "2025"}},
    ]
    job = {
        "title": "AI / ML Engineer",
        "company": "Swiggy",
        "description": "Looking for Python AI/ML engineer with deep learning expertise.",
        "required_skills": ["Python", "TensorFlow", "FastAPI"],
    }
    result = await agent.run({
        "candidate": candidate,
        "candidate_facts": facts,
        "job": job,
    })
    assert result["status"] == "success"
    data = result["data"]
    assert "tailored_data" in data
    assert os.path.exists(data["pdf_path"])
    assert data["tailored_data"]["full_name"] == "Akash Nandy"
