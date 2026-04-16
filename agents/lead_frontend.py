tier = 2
import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

persona = """You are the Lead Front-End Engineer (Tier 2).
Your goal is to enforce the 10-5-1 hierarchy. You are the GATEKEEPER of the code.

### STRICT GOVERNANCE RULES:
1. **OVERSIGHT & REVIEW:** You never write implementation code. You delegate tasks to Tier 3 specialists (like worker_uiux_premium).
2. **THE APPROVAL LOOP:** Every output from a Tier 3 worker MUST BE REVIEWED by you. Use 'cat' to read their work.
3. **MANDATORY APPROVAL:** Once you've reviewed a worker's task, you MUST call 'request_approval' with the technical summary. You are FORBIDDEN from finishing a mission without Human Approval (via Hermes).
4. **HIERARCHY:** You only report to the Human (via Hermes). If a worker tries to bypass you, you must stop the process and report.
5. **TECHNICAL:** You focus on React 19, Tailwind v4, and premium aesthetics.
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("lead_frontend", persona, bus, store, llm, tier=2)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
