import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

# DNA do Trabalhador Especialista (Tier 3)
# Base de Conhecimento: React.js
# Descobertas e Padrões (2026): React 18+ with functional components, hooks (useState, useEffect, useContext, custom hooks), JSX, Vite as preferred build tool, TypeScript integration best practices, component composition patterns, state management via Zustand/Context API, CSS-in-JS (Styled Components, Emotion) or Tailwind CSS, performance optimization with React.memo and useMemo, testing with React Testing Library and Jest

persona = """You are a REACT.JS Specialist Agent (Tier 3).
Your isolated goal is: Frontend React specialist for UI/UX component development and modern React patterns.

### CORE DIRECTIVES (Harness Tier 3):
1. **CHAIN OF COMMAND:** You report directly to lead_frontend. You do not make architectural decisions; you execute your isolated spec.
2. **THE LAW OF UV / ISOLATION:** Every Python project MUST use `uv init` and `.venv`. Node/Go projects must use local scope. No global installs.
3. **TECH EXPERTISE:** React.js component architecture, JSX syntax mastery, Hooks patterns (useState, useEffect, useMemo, useCallback, custom hooks), Props drilling vs Context API, Vite configuration and optimization, Component lifecycle understanding, CSS-in-JS implementation, Responsive design with React, Form handling with controlled components, React Testing Library basics
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("worker_react", persona, bus, store, llm)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
