import pytest
from app.agents.cover_letter import CoverLetterAgent
import os

@pytest.mark.asyncio
async def test_cover_letter_generation():
    agent = CoverLetterAgent()
    candidate = {
        "full_name": "Akash Nandy",
        "email": "akashnandy01@gmail.com",
        "phone": "+91 9330136009",
        "location": "Chennai / Kolkata, India",
        "summary": "AI/ML Engineer with strong software engineering skills",
    }
    facts = [
        {"type": "skill", "data": {"name": "Python"}},
        {"type": "skill", "data": {"name": "TensorFlow"}},
        {"type": "project", "data": {"name": "Echocheck"}},
    ]
    job = {
        "title": "AI / ML Engineer",
        "company": "Swiggy",
        "description": "Building next-generation intelligent dispatch and food recommendation algorithms.",
    }
    result = await agent.run({
        "candidate": candidate,
        "candidate_facts": facts,
        "job": job,
    })
    assert result["status"] == "success"
    data = result["data"]
    assert len(data["cover_letter_text"]) > 100
    assert os.path.exists(data["pdf_path"])
