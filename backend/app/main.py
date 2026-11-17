from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import structlog

from app.config import settings
from app.core.redis_client import get_redis, close_redis
from app.api.v1.router import api_router

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting JobPilot AI backend...")
    os.makedirs(settings.upload_dir, exist_ok=True)
    try:
        await get_redis()
    except Exception as e:
        logger.warning("Redis not available at startup", error=str(e))
    logger.info("JobPilot AI backend ready.")
    yield
    await close_redis()
    logger.info("JobPilot AI backend stopped.")

app = FastAPI(
    title="JobPilot AI",
    description="Personal multi-agent recruitment intelligence platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0", "service": "JobPilot AI"}
