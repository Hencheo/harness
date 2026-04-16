import os
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import httpx

class HarnessLLM:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.fireworks.ai/inference/v1", model: str = "accounts/fireworks/routers/kimi-k2p5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("FIREWORKS_API_KEY")
        self.base_url = base_url
        self.model = model
        
        if not self.api_key:
            raise ValueError(
                "API Key missing. Please set OPENAI_API_KEY or FIREWORKS_API_KEY in your environment or .env file."
            )

        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def chat_completion(self, messages: List[Dict[str, str]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.3,
            }
            if tools and isinstance(tools, list) and len(tools) > 0:
                kwargs["tools"] = tools

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except Exception as e:
            print(f"[LLM_ERROR] Failed to call LLM: {e}")
            raise e

    def estimate_tokens(self, text: str) -> int:
        # Simple heuristic: ~4 chars per token
        return len(text) // 4
