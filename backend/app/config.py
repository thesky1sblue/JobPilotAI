from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://jobpilot:jobpilot_pass@localhost:5432/jobpilot"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-this-secret-key"
    app_env: str = "development"
    log_level: str = "INFO"
    llm_provider: str = "gemini"
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    discovery_schedule_morning: str = "09:00"
    discovery_schedule_evening: str = "21:00"
    scheduler_timezone: str = "Asia/Kolkata"
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 10
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
