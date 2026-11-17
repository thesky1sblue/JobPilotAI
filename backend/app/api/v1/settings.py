from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/")
async def get_settings():
    return {
        "llm_provider": settings.llm_provider,
        "discovery_schedule_morning": settings.discovery_schedule_morning,
        "discovery_schedule_evening": settings.discovery_schedule_evening,
        "scheduler_timezone": settings.scheduler_timezone,
        "app_env": settings.app_env,
    }
