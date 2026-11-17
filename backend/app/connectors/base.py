from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseConnector(ABC):
    source_name: str = ""

    @abstractmethod
    async def fetch_jobs(self, company_identifier: str, **kwargs) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def parse_job(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        pass

    async def fetch_all_for_company(self, company_identifier: str) -> List[Dict[str, Any]]:
        jobs = await self.fetch_jobs(company_identifier)
        return [await self.parse_job(j) for j in jobs]
