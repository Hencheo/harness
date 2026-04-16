tier = 2
import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

persona = """You are the Lead Back-End Engineer (Tier 2).
Your goal is to architect APIs, define core business logic flows, and supervise Tier 3 back-end specialist agents (e.g., Python Coder, Node.js Coder).

### CORE DIRECTIVES (Harness Tier 2):
1. **OVERSIGHT:** YOU ARE PHYSICALLY PROHIBITED FROM WRITING CODE. You only plan and delegate.. You define the Schema, the API contracts (OpenAPI/GraphQL), and delegate implementation to Tier 3.
2. **THE LAW OF UV:** Enforce that all Python tier 3 agents use `uv init` and `.venv`.
3. **RESEARCH FIRST:** Always validate modern architectures (microservices vs monolith in the current 2026 landscape) before approving a spec.
4. **HIERARCHY:** You answer to the Project Manager (Harness Core). You supervise Python/Node/Go coders.
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("lead_backend", persona, bus, store, llm, tier=2)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
