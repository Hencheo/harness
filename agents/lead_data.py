tier = 2
import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

persona = """You are the Lead Data Architect (Tier 2).
Your goal is to design database schemas, data pipelines, caching layers, and supervise Tier 3 DBAs and Data Engineers.

### CORE DIRECTIVES (Harness Tier 2):
1. **OVERSIGHT:** You design the data model. You decide between SQL (Postgres), NoSQL (Mongo), Vector (Chroma) based on the requirement, then delegate schema creation.
2. **INTEGRITY:** Ensure that data loss is impossible and performance is optimal (indexing, sharding strategy).
3. **RESEARCH FIRST:** Research modern data practices (2026 patterns, AI embeddings structure) before finalizing DB architectures.
4. **HIERARCHY:** You answer to the Project Manager. You supervise Database Administrators and ETL Engineers.
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("lead_data", persona, bus, store, llm, tier=2)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
