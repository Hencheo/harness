import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

# DNA do Trabalhador Especialista (Tier 3)
# Base de Conhecimento: React + Tailwind CSS
# Descobertas e Padrões (2026): REACT 19 + TAILWIND CSS v4.0 — 2026 STANDARDS DISCOVERY

=== TAILWIND v4.0 MAJOR CHANGES ===
- CSS-first configuration: tailwind.config.js removed. Configuration moved to CSS using @theme directive
- @import "tailwindcss" replaces @tailwind directives for base/components/utilities
- New @theme block for defining custom theme variables, colors, fonts directly in CSS
- Built-in CSS import handling, eliminates need for separate build tools for simple projects
- Vite 6 integration via @tailwindcss/vite plugin
- Performance: Up to 10x faster build times, zero JavaScript runtime overhead
- New color palette: OKLCH-based default colors, improved perceptual uniformity
- Container queries built-in: @container, @container/name syntax
- Data attributes variant: data-[active]:bg-blue-500
- Has selector support: has-[:checked]:bg-blue-500
- Not selector variant: not-[.dark]:bg-white
- Print variant: print:hidden for printer-specific styling
- Supports CSS nesting out of the box

=== REACT 19 — CURRENT PATTERNS ===
- Server Components by default in Next.js App Router (RSC architecture)
- Actions: Native form handling without useState/useEffect ceremony
- use() hook: Suspense-compatible data fetching mechanism
- Context as provider: <Context> directly usable as JSX element
- Document metadata support: <title>, <meta> usable directly in components
- Asset loading: Prefetch/preload via React APIs
- Improved hydration with progressive enhancement

=== RECOMMENDED STACK 2026 ===
- Vite 6 + React 19 + Tailwind v4 as primary toolchain
- shadcn/ui components: Radix primitives + Tailwind styling (industry norm for modern apps)
- Biome or OXC: Replacing ESLint/Prettier (Rust-based, 10x faster)
- TypeScript 5.4+: Strict mode enabled always
- React Query (TanStack Query): Server state management
- Zustand: Client state management (lighter than Redux)
- React Router v7 or TanStack Router for routing

=== CSS ARCHITECTURE PATTERNS ===
- Utility-first methodology maintained and optimized
- Component abstraction via @apply discouraged in v4 (favor composition)
- CVA (class-variance-authority) for component variant management
- tailwind-merge for conflicting class resolution
- clsx/cn pattern for conditional class joining

=== ACCESSIBILITY & DESIGN SYSTEMS ===
- Radix UI primitives for accessibility (headless components)
- Tailwind CSS forms plugin for normalized form elements
- prefers-reduced-motion media query support built-in
- Dark mode via class strategy (dark: prefix)
- Responsive design: sm:, md:, lg:, xl:, 2xl: breakpoints

Sources: Tailwind CSS Blog 2024-2025 updates, React.dev official docs, Vite 6 release notes, shadcn/ui component patterns

persona = """You are a REACT + TAILWIND CSS Specialist Agent (Tier 3).
Your isolated goal is: Implementar interfaces modernas React 19 com Tailwind v4, seguindo padrões utility-first, acessibilidade e design systems.

### CORE DIRECTIVES (Harness Tier 3):
1. **CHAIN OF COMMAND:** You report directly to lead_frontend. You do not make architectural decisions; you execute your isolated spec.
2. **THE LAW OF UV / ISOLATION:** Every Python project MUST use `uv init` and `.venv`. Node/Go projects must use local scope. No global installs.
3. **TECH EXPERTISE:** REACT_EXPERTISE: Vite 6 builds, Server Components, Actions, use() hook, Suspense patterns; TAILWIND_EXPERTISE: CSS-first config (@theme), @import directives, OKLCH colors, container queries, CVA variants, clsx/cn utilities; COMPONENT_ARCHITECTURE: shadcn/ui, Radix primitives, tailwind-merge; TOOLCHAIN: Biome/OXC linter, TypeScript strict, Zustand state, React Query; ISOLATION_LAW: All projects use uv init + .venv, no global installs
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("worker_react_tailwind", persona, bus, store, llm)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
