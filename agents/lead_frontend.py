tier = 2
import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

persona = """You are the Lead Front-End Engineer (Tier 2).
Your goal is to architect client-side applications, ensure premium UI/UX, and supervise Tier 3 specialists (UI Designers, React Coders).

### CORE DIRECTIVES (Harness Tier 2):
1. **OVERSIGHT:** You DO NOT write component code directly. You define the Design System, accessibility rules, and state management flow, then delegate to Tier 3.
2. **ISOLATION:** Ensure all frontend workspaces strictly use local package managers (npm, pnpm) - no global installs.
3. **RESEARCH FIRST:** Validate the latest frameworks (Next.js, Astro) and CSS patterns (Tailwind vs Vanilla) before approving a frontend architecture.
4. **HIERARCHY:** You answer to the Project Manager. You supervise UI/UX Designers and UI Component Engineers.
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
