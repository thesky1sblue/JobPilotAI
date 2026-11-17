import pytest

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_get_profile_no_candidate(client):
    response = await client.get("/api/v1/candidate/profile")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_preferences_default(client):
    response = await client.get("/api/v1/candidate/preferences")
    assert response.status_code == 200
    data = response.json()
    assert "target_roles" in data
    assert "Python Developer" in data["target_roles"] or "Software Development / SDE" in data["target_roles"]

@pytest.mark.asyncio
async def test_list_jobs_empty(client):
    response = await client.get("/api/v1/jobs/")
    assert response.status_code == 200
    assert response.json()["jobs"] == []

@pytest.mark.asyncio
async def test_overview_stats_empty(client):
    response = await client.get("/api/v1/jobs/stats/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_jobs_discovered"] == 0
