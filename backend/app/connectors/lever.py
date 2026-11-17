import httpx
from typing import List, Dict, Any
from app.connectors.base import BaseConnector
import structlog

logger = structlog.get_logger()

class LeverConnector(BaseConnector):
    source_name = "lever"
    BASE_URL = "https://api.lever.co/v0/postings"

    async def fetch_jobs(self, company_identifier: str, **kwargs) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/{company_identifier}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params={"mode": "json", "limit": 250})
                if response.status_code == 404:
                    logger.warning("lever.not_found", company=company_identifier)
                    return []
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error("lever.error", company=company_identifier, error=str(e))
            return []

    async def parse_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        cats = raw_job.get("categories", {})
        parts = [raw_job.get("text", ""), raw_job.get("descriptionPlain", "")]
        for s in raw_job.get("lists", []):
            parts.append(f"{s.get('text','')}: {', '.join(s.get('content',[]))}")
        return {
            "source": "lever",
            "source_id": raw_job.get("id", ""),
            "title": raw_job.get("text", ""),
            "description": "\n\n".join(filter(None, parts)),
            "location": cats.get("location", ""),
            "department": cats.get("department", ""),
            "commitment": cats.get("commitment", ""),
            "application_url": raw_job.get("applyUrl", raw_job.get("hostedUrl", "")),
            "posted_at": None,
            "raw_payload": raw_job,
        }
