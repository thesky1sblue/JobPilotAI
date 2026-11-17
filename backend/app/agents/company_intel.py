"""Company Intelligence Agent — discovers companies, career portals, and ATS endpoints."""
import re
from typing import Dict, Any, List, Optional
from app.agents.base import BaseAgent
import structlog

logger = structlog.get_logger()

KNOWN_ATS_DOMAINS = {
    "boards.greenhouse.io": "greenhouse",
    "job-boards.greenhouse.io": "greenhouse",
    "jobs.lever.co": "lever",
    "myworkdayjobs.com": "workday",
    "smartrecruiters.com": "smartrecruiters",
    "ashbyhq.com": "ashby",
}

class CompanyIntelligenceAgent(BaseAgent):
    name = "company_intelligence_agent"

    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        company_name = input_data.get("company_name", "")
        careers_url = input_data.get("careers_url", "")

        detected_ats = "custom"
        ats_identifier = None

        if careers_url:
            for domain, ats in KNOWN_ATS_DOMAINS.items():
                if domain in careers_url:
                    detected_ats = ats
                    # Try extracting identifier from URL path
                    parts = careers_url.rstrip("/").split("/")
                    if parts:
                        ats_identifier = parts[-1]
                    break

        return {
            "company_name": company_name,
            "careers_url": careers_url,
            "ats_platform": detected_ats,
            "ats_identifier": ats_identifier,
            "verified": bool(careers_url),
        }

company_intel_agent = CompanyIntelligenceAgent()
