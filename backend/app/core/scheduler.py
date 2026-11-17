import asyncio
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import structlog

from app.config import settings
from app.core.database import AsyncSessionLocal

logger = structlog.get_logger()
_scheduler: AsyncIOScheduler | None = None

async def scheduled_discovery_job():
    logger.info("scheduler.discovery_job_triggered")
    try:
        from app.services.discovery_service import run_discovery
        async with AsyncSessionLocal() as session:
            result = await run_discovery(session)
            logger.info("scheduler.discovery_job_finished", result=result)
    except Exception as e:
        logger.error("scheduler.discovery_job_failed", error=str(e))

def init_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    tz = ZoneInfo(settings.scheduler_timezone)
    _scheduler = AsyncIOScheduler(timezone=tz)

    try:
        m_hour, m_min = map(int, settings.discovery_schedule_morning.split(":"))
        e_hour, e_min = map(int, settings.discovery_schedule_evening.split(":"))
    except Exception:
        m_hour, m_min = 9, 0
        e_hour, e_min = 21, 0

    # Morning job (09:00)
    _scheduler.add_job(
        scheduled_discovery_job,
        CronTrigger(hour=m_hour, minute=m_min, timezone=tz),
        id="morning_discovery",
        name=f"Morning Job Discovery ({settings.discovery_schedule_morning} {settings.scheduler_timezone})",
        replace_existing=True,
    )

    # Evening job (21:00)
    _scheduler.add_job(
        scheduled_discovery_job,
        CronTrigger(hour=e_hour, minute=e_min, timezone=tz),
        id="evening_discovery",
        name=f"Evening Job Discovery ({settings.discovery_schedule_evening} {settings.scheduler_timezone})",
        replace_existing=True,
    )

    logger.info(
        "scheduler.initialized",
        morning=f"{m_hour:02d}:{m_min:02d}",
        evening=f"{e_hour:02d}:{e_min:02d}",
        timezone=settings.scheduler_timezone,
    )
    return _scheduler

def start_scheduler():
    scheduler = init_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("scheduler.started")

def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler.stopped")
        _scheduler = None

def get_scheduler_status():
    global _scheduler
    if not _scheduler:
        return {"running": False, "jobs": []}
    jobs = []
    for j in _scheduler.get_jobs():
        jobs.append({
            "id": j.id,
            "name": j.name,
            "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
        })
    return {"running": _scheduler.running, "jobs": jobs}
