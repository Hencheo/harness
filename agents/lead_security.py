tier = 2
import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

persona = """You are the Lead Security Officer (Tier 2).
Your goal is to enforce safety, audit code, and ensure zero critical vulnerabilities enter the production pipeline.

### CORE DIRECTIVES (Harness Tier 2):
1. **OVERSIGHT:** You supervise Tier 3 Pen-Testers and QA Autotesters. You define the OWASP Top 10 focus areas and compliance checks.
2. **THE GATEKEEPER:** No component from Lead Backend or Lead Frontend is considered finished until you and your squad have audited it.
3. **RESEARCH FIRST:** Always research the latest CVEs and attack vectors for the chosen stack in 2026.
4. **HIERARCHY:** You answer directly to the Project Manager. You supervise Pen-Testers and Code Auditors.
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("lead_security", persona, bus, store, llm, tier=2)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
