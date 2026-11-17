"""Provider-independent LLM gateway."""
from typing import Optional
from app.config import settings

class LLMGateway:
    def __init__(self):
        self.provider = settings.llm_provider

    async def generate(self, prompt: str, system: Optional[str] = None) -> str:
        if self.provider == "gemini":
            return await self._gemini(prompt, system)
        elif self.provider == "anthropic":
            return await self._anthropic(prompt, system)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def _gemini(self, prompt: str, system: Optional[str] = None) -> str:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = model.generate_content(full_prompt)
        return response.text

    async def _anthropic(self, prompt: str, system: Optional[str] = None) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text

llm_gateway = LLMGateway()
