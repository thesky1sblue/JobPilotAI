# JobPilot AI — Development Guide

## Prerequisites

- Python 3.12+ (or 3.13)
- Node.js 18+ & npm / pnpm
- Docker & Docker Compose
- PostgreSQL 16 & Redis 7 (or run via Docker Compose)

## Quick Start

### 1. Environment Configuration

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Ensure `GEMINI_API_KEY` or `ANTHROPIC_API_KEY` is configured.

### 2. Running Services with Docker Compose

Start PostgreSQL and Redis:

```bash
docker compose up -d postgres redis
```

### 3. Backend Setup

Navigate to the `backend` directory:

```bash
cd backend
pip install -r requirements.txt
```

Run database migrations:

```bash
alembic upgrade head
```

Seed the 50 initial watchlist companies:

```bash
python3 -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.services.company_service import seed_initial_companies

async def main():
    async with AsyncSessionLocal() as session:
        count = await seed_initial_companies(session)
        print(f'Successfully seeded {count} companies.')

asyncio.run(main())
"
```

Start the FastAPI development server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive OpenAPI docs will be available at: [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Running Backend Tests

Run unit and integration tests using pytest:

```bash
cd backend
pytest tests/ -v
```

### 5. Frontend Dashboard Setup

From the project root:

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be accessible at [http://localhost:3000](http://localhost:3000).

## Code Architecture Guidelines

- **Agents**: Extend `BaseAgent` in `backend/app/agents/base.py`. Implement async `_execute(input_data)`.
- **Connectors**: Extend `BaseConnector` in `backend/app/connectors/base.py`. Implement `fetch_jobs` and `parse_job`.
- **Database Models**: All models inherit from `app.core.database.Base` using modern SQLAlchemy 2.0 `Mapped` and `mapped_column`.
