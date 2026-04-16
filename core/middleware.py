from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseMiddleware(ABC):
    @abstractmethod
    async def pre_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executed before the LLM or tool call."""
        pass

    @abstractmethod
    async def post_process(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Executed after the LLM or tool call."""
        pass

class SandwichMiddleware:
    def __init__(self):
        self.middlewares = []

    def add(self, middleware: BaseMiddleware):
        self.middlewares.append(middleware)

    async def run_pre(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for mw in self.middlewares:
            data = await mw.pre_process(data)
        return data

    async def run_post(self, data: Dict[str, Any]) -> Dict[str, Any]:
        for mw in reversed(self.middlewares):
            data = await mw.post_process(data)
        return data

# Example implementation for logging/auditing
class AuditMiddleware(BaseMiddleware):
    async def pre_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[AUDIT] Pre-processing request: {input_data.get('id', 'N/A')}")
        return input_data

    async def post_process(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        print(f"[AUDIT] Post-processing response")
        return output_data
