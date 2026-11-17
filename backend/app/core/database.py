import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import structlog

logger = structlog.get_logger()

LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "jobpilot_local.db")
SQLITE_URL = f"sqlite+aiosqlite:///{LOCAL_DB_PATH}"

# Select appropriate database URL
db_url = settings.database_url
if not db_url or ("postgresql" in db_url and os.getenv("FORCE_POSTGRES") != "1" and os.path.exists(LOCAL_DB_PATH)):
    db_url = SQLITE_URL

engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
