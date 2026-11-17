import httpx
from typing import List, Dict, Any
from app.connectors.base import BaseConnector
import structlog

logger = structlog.get_logger()

class GreenhouseConnector(BaseConnector):
    source_name = "greenhouse"
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    async def fetch_jobs(self, company_identifier: str, **kwargs) -> List[Dict[str, Any]]:
        url = f"{self.BASE_URL}/{company_identifier}/jobs"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params={"content": "true"})
                if response.status_code == 404:
                    logger.warning("greenhouse.not_found", company=company_identifier)
                    return []
                response.raise_for_status()
                return response.json().get("jobs", [])
        except Exception as e:
            logger.error("greenhouse.error", company=company_identifier, error=str(e))
            return []

    async def parse_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": "greenhouse",
            "source_id": str(raw_job.get("id", "")),
            "title": raw_job.get("title", ""),
            "description": raw_job.get("content", ""),
            "location": raw_job.get("location", {}).get("name", ""),
            "department": (raw_job.get("departments") or [{}])[0].get("name", ""),
            "application_url": raw_job.get("absolute_url", ""),
            "posted_at": raw_job.get("updated_at"),
            "raw_payload": raw_job,
        }
