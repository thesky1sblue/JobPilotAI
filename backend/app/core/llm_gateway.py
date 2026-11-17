"""Provider-independent LLM gateway."""
import os
import asyncio
from typing import Optional
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
        import google.generativeai as genai
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            logger.warning("gemini.api_key_missing_or_placeholder")
            return self._mock_response(prompt)
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        try:
            # 8-second timeout for async generation call
            response = await asyncio.wait_for(model.generate_content_async(full_prompt), timeout=8.0)
            return response.text
        except Exception as e:
            logger.warning("gemini.async_timed_out_or_failed", error=str(e))
            return self._mock_response(prompt)

    async def _anthropic(self, prompt: str, system: Optional[str] = None) -> str:
        import anthropic
        if not settings.anthropic_api_key or settings.anthropic_api_key == "your_anthropic_api_key_here":
            return self._mock_response(prompt)
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        try:
            msg = await asyncio.wait_for(
                client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    system=system or "You are a helpful assistant.",
                    messages=[{"role": "user", "content": prompt}]
                ),
                timeout=8.0
            )
            return msg.content[0].text
        except Exception as e:
            logger.warning("anthropic.timed_out_or_failed", error=str(e))
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        return "Generated response based on prompt context."

llm_gateway = LLMGateway()
