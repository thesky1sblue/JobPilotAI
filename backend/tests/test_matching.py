import pytest
from app.agents.matching import MatchingAgent, classify

@pytest.mark.asyncio
async def test_matching_with_matching_skills():
    agent = MatchingAgent()
    result = await agent.run({
        "job": {"title": "Python Developer", "required_skills": ["python", "fastapi"], "location": "Remote", "experience_min": None},
        "candidate_facts": [{"type": "skill", "data": {"name": "Python"}}, {"type": "skill", "data": {"name": "FastAPI"}}],
        "preferences": {"target_roles": ["Python Developer"], "preferred_locations": ["Remote"], "experience_years": 0},
    })
    assert result["status"] == "success"
    assert result["data"]["overall_score"] > 70
    assert result["data"]["classification"] in ("strong", "good")

@pytest.mark.asyncio
async def test_matching_no_skills():
    agent = MatchingAgent()
    result = await agent.run({
        "job": {"title": "Java Developer", "required_skills": ["java", "spring"], "location": "Bangalore", "experience_min": None},
        "candidate_facts": [],
        "preferences": {"preferred_locations": ["Bangalore"], "experience_years": 0},
    })
    assert result["status"] == "success"

def test_classify():
    assert classify(90) == "strong"
    assert classify(75) == "good"
    assert classify(60) == "review"
    assert classify(40) == "low"

@pytest.mark.asyncio
async def test_ineligible_experience():
    agent = MatchingAgent()
    result = await agent.run({
        "job": {"title": "Senior Engineer", "required_skills": [], "location": "Bangalore", "experience_min": 5},
        "candidate_facts": [],
        "preferences": {"experience_years": 0},
    })
    assert result["data"]["is_eligible"] == False
