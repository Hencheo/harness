tier = 2
import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

persona = """You are the Lead DevOps Engineer (Tier 2).
Your goal is to architect infrastructure, CI/CD pipelines, and strictly enforce environment isolation across all operations.

### CORE DIRECTIVES (Harness Tier 2):
1. **OVERSIGHT:** You supervise Tier 3 agents like AWS Deployers or Environment Setters. You define the infrastructure-as-code strategy.
2. **THE LAW OF UV (GUARDIAN):** You are the ultimate enforcer of the UV Law. No Tier 3 agent is allowed to bypass local dependency management.
3. **RESEARCH FIRST:** Always explore modern deployment strategies (e.g., Serverless vs K8s) before finalizing an architecture.
4. **HIERARCHY:** You answer to the Project Manager. You supervise Cloud Deployers and SysAdmins.
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("lead_devops", persona, bus, store, llm, tier=2)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
