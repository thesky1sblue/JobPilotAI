from abc import ABC, abstractmethod
from typing import Any, Dict
import structlog
from datetime import datetime

logger = structlog.get_logger()

class BaseAgent(ABC):
    name: str = "base_agent"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        start = datetime.utcnow()
        logger.info(f"{self.name}.started")
        try:
            result = await self._execute(input_data)
            duration = (datetime.utcnow() - start).total_seconds()
            logger.info(f"{self.name}.completed", duration=duration)
            return {"status": "success", "data": result, "agent": self.name}
        except Exception as e:
            duration = (datetime.utcnow() - start).total_seconds()
            logger.error(f"{self.name}.failed", error=str(e), duration=duration)
            return {"status": "error", "error": str(e), "agent": self.name}

    @abstractmethod
    async def _execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass
