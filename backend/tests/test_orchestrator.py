import pytest
from app.workflows.orchestrator import jobpilot_workflow

@pytest.mark.asyncio
async def test_orchestrator_execution():
    initial_state = {
        "candidate": {
            "full_name": "Akash Nandy",
            "email": "akashnandy01@gmail.com",
            "phone": "+91 9330136009",
            "location": "Bangalore / Remote",
        },
        "candidate_facts": [
            {"type": "skill", "data": {"name": "Python"}},
            {"type": "skill", "data": {"name": "Machine Learning"}},
            {"type": "skill", "data": {"name": "FastAPI"}},
        ],
        "preferences": {
            "target_roles": ["AI / ML Engineer", "Python Developer"],
            "preferred_locations": ["Bangalore", "Remote"],
            "experience_years": 0.5,
        },
        "raw_jobs": [
            {
                "title": "Junior Python Developer",
                "company": "Razorpay",
                "description": "Seeking Python and FastAPI developer with knowledge of machine learning.",
                "location": "Bangalore",
                "source": "lever",
                "source_id": "razorpay-001",
                "application_url": "https://jobs.lever.co/razorpay/001",
            }
        ],
    }

    config = {"configurable": {"thread_id": "test-thread-1"}}
    # Execute workflow up to human approval interrupt
    result = await jobpilot_workflow.ainvoke(initial_state, config=config)

    assert "ranked_jobs" in result
    assert len(result["ranked_jobs"]) > 0
    assert result["approval_status"] == "pending_approval"
    assert result["prepared_application"] is not None
    assert result["prepared_application"]["is_ready_for_review"] is True
    assert result["tailored_resume"] is not None
    assert result["cover_letter"] is not None
