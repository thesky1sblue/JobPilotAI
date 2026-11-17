import pytest
from app.core.scheduler import init_scheduler, start_scheduler, stop_scheduler, get_scheduler_status

def test_scheduler_initialization():
    scheduler = init_scheduler()
    assert scheduler is not None
    job_ids = [j.id for j in scheduler.get_jobs()]
    assert "morning_discovery" in job_ids
    assert "evening_discovery" in job_ids

@pytest.mark.asyncio
async def test_scheduler_status():
    start_scheduler()
    status = get_scheduler_status()
    assert status["running"] is True
    assert len(status["jobs"]) >= 2
    stop_scheduler()
    status_after = get_scheduler_status()
    assert status_after["running"] is False
