import pytest
from app.agents.application_prep import ApplicationPreparationAgent
from app.agents.verification import ApplicationVerificationAgent
from app.agents.tracking import ApplicationTrackingAgent
from app.agents.company_intel import CompanyIntelligenceAgent
from app.agents.notification import NotificationAgent

@pytest.mark.asyncio
async def test_application_prep_agent():
    agent = ApplicationPreparationAgent()
    res = await agent.run({
        "portal_url": "https://boards.greenhouse.io/swiggy/jobs/123",
        "candidate": {
            "full_name": "Akash Nandy",
            "email": "akashnandy01@gmail.com",
            "phone": "+91 9330136009",
            "linkedin_url": "https://linkedin.com/in/akashnandy",
        },
        "resume_path": "/path/to/resume.pdf",
    })
    assert res["status"] == "success"
    assert res["data"]["portal_type"] == "greenhouse"
    assert res["data"]["is_ready"] is True
    assert res["data"]["prepared_answers"]["first_name"] == "Akash"

@pytest.mark.asyncio
async def test_verification_agent():
    agent = ApplicationVerificationAgent()
    res = await agent.run({
        "candidate": {"full_name": "Akash Nandy"},
        "job": {
            "title": "Software Development Engineer",
            "company": "Swiggy",
            "application_url": "https://boards.greenhouse.io/swiggy/jobs/123",
        },
        "prepared_application": {"attached_resume": "/path/to/resume.pdf"},
    })
    assert res["status"] == "success"
    assert res["data"]["is_valid"] is True
    assert res["data"]["requires_human_approval"] is True

@pytest.mark.asyncio
async def test_company_intel_agent():
    agent = CompanyIntelligenceAgent()
    res = await agent.run({
        "company_name": "Swiggy",
        "careers_url": "https://jobs.lever.co/swiggy",
    })
    assert res["status"] == "success"
    assert res["data"]["ats_platform"] == "lever"
    assert res["data"]["ats_identifier"] == "swiggy"

@pytest.mark.asyncio
async def test_notification_agent():
    agent = NotificationAgent()
    res = await agent.run({
        "event_type": "new_match",
        "data": {"title": "AI/ML Engineer", "company": "Zomato", "score": 92.5},
    })
    assert res["status"] == "success"
    assert "92%" in res["data"]["title"] or "92" in res["data"]["title"]

@pytest.mark.asyncio
async def test_tracking_agent_duplicate():
    agent = ApplicationTrackingAgent()
    res = await agent.run({
        "action": "check_duplicate",
        "job_id": "job-123",
        "existing_applications": [{"job_id": "job-123"}],
    })
    assert res["status"] == "success"
    assert res["data"]["is_duplicate"] is True
    assert res["data"]["can_apply"] is False
