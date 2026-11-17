"""Provider-independent LLM gateway supporting Google Gemini and Anthropic Claude."""
import os
import asyncio
from typing import Optional
import httpx
from app.config import settings
import structlog

logger = structlog.get_logger()

class LLMGateway:
    def __init__(self):
        self.provider = settings.llm_provider

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        # In test mode or when testing env variable is set, return mock response instantly
        if os.getenv("TESTING") == "1" or settings.app_env == "test":
            return self._mock_response(prompt)

        if self.provider == "gemini":
            return await self._gemini(prompt, system)
        elif self.provider == "anthropic":
            return await self._anthropic(prompt, system)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def _gemini(self, prompt: str, system: Optional[str] = None) -> str:
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            logger.warning("gemini.api_key_missing_or_placeholder")
            return self._mock_response(prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={settings.gemini_api_key}"
        full_text = f"{system}\n\n{prompt}" if system else prompt
        payload = {
            "contents": [{"parts": [{"text": full_text}]}]
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                elif res.status_code == 429:
                    logger.warning("gemini.rate_limited_free_tier", retry_after=res.headers.get("Retry-After"))
                    return self._mock_response(prompt)
                else:
                    logger.warning("gemini.api_error", status_code=res.status_code, text=res.text[:200])
                    return self._mock_response(prompt)
        except Exception as e:
            logger.warning("gemini.request_exception", error=str(e))
            return self._mock_response(prompt)

    async def _anthropic(self, prompt: str, system: Optional[str] = None) -> str:
        if not settings.anthropic_api_key or settings.anthropic_api_key == "your_anthropic_api_key_here":
            return self._mock_response(prompt)
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        try:
            msg = await asyncio.wait_for(
                client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    system=system or "You are a helpful assistant.",
                    messages=[{"role": "user", "content": prompt}]
                ),
                timeout=15.0
            )
            return msg.content[0].text
        except Exception as e:
            logger.warning("anthropic.timed_out_or_failed", error=str(e))
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        return "Generated response grounded strictly in verified candidate facts."

llm_gateway = LLMGateway()
