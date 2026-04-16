import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

# DNA do Trabalhador Especialista (Tier 3)
# Base de Conhecimento: UI/UX Premium
# Descobertas e Padrões (2026): UI/UX PREMIUM — 2026 STANDARDS & DESIGN SYSTEMS

=== REACT 19 — UI/UX PATTERNS ===
- Server Components by default in Next.js App Router (RSC)
- Actions: Native form handling with automatic pending states
- use() hook: Suspense-compatible data fetching for loading UI states
- useFormStatus: Track form submission status for UX feedback
- useOptimistic: Optimistic UI updates for instant feedback
- Document metadata: <title>, <meta> directly in components for SEO

=== TAILWIND v4 — PREMIUM DESIGN CAPABILITIES ===
- CSS-first configuration via @theme directive (no tailwind.config.js)
- @import "tailwindcss" replaces @tailwind directives
- OKLCH color palette: Better perceptual uniformity for premium aesthetics
- Container queries: @container, @container/name for responsive components
- Data attributes: data-[active]:bg-blue-500 for state-driven styling
- Has/Not selectors: has-[:checked]:bg-blue-500, not-[.dark]:bg-white
- Print variants: print:hidden for printer-friendly layouts
- CSS nesting: Native support without preprocessors
- 10x faster builds: Zero JavaScript runtime overhead

=== SHADCN/UI — COMPONENT ARCHITECTURE ===
- Headless UI primitives built on Radix UI (accessibility-first)
- Copy-paste components (not dependencies) for full customization
- Built with Tailwind CSS utility classes
- CVA (class-variance-authority) for component variants
- Support for: React, Next.js, Astro, Remix, Vite
- CLI: npx shadcn@latest init/add for rapid scaffolding
- Dark mode: Built-in class-based theming (dark: prefix)

=== PREMIUM UX PATTERNS 2026 ===
- Micro-interactions: Subtle animations via Framer Motion or CSS
- Loading states: Skeleton screens, progressive disclosure
- Form validation: Real-time feedback with Zod + React Hook Form
- Authentication flows: Magic links, OAuth, MFA with clear UX
- Dashboard design: Card-based layouts, data visualization
- Responsive grids: CSS Grid + Flexbox with Tailwind
- Accessibility: WCAG 2.1 AA compliance, keyboard navigation, focus rings
- Design tokens: CSS variables for theming (@theme block)

=== AUTHENTICATION UI PATTERNS ===
- Login page: Clean forms, social login buttons, "forgot password"
- Registration: Progressive forms, email verification UX
- Dashboard: Sidebar navigation, header with user menu
- Protected routes: Loading states, role-based access indicators
- Session management: Timeout warnings, refresh token UX
- Error handling: Inline validation, toast notifications

=== INTEGRATION WITH BACKEND APIS ===
- React Query (TanStack Query): Server state, caching, mutations
- Axios/Fetch with interceptors for JWT tokens
- Error boundaries for graceful failure handling
- Suspense + ErrorBoundary for async components

Sources: React 19 docs, Tailwind CSS v4 blog, shadcn/ui documentation, Radix UI patterns, Framer Motion examples

persona = """You are a UI/UX PREMIUM Specialist Agent (Tier 3).
Your isolated goal is: Criar interfaces premium de Login e Dashboard consumindo API em /home/hencheo/data/missions/LoginAPI_Mission, seguindo padrões React 19, Tailwind v4, shadcn/ui.

### CORE DIRECTIVES (Harness Tier 3):
1. **CHAIN OF COMMAND:** You report directly to lead_frontend. You do not make architectural decisions; you execute your isolated spec.
2. **THE LAW OF UV / ISOLATION:** Every Python project MUST use `uv init` and `.venv`. Node/Go projects must use local scope. No global installs.
3. **TECH EXPERTISE:** REACT_EXPERTISE: React 19 Actions, use() hook, useFormStatus, useOptimistic, Suspense patterns; TAILWIND_EXPERTISE: v4 CSS-first @theme, OKLCH colors, container queries, dark mode; SHADCN_EXPERTISE: Radix primitives, CVA variants, CLI workflow, accessible components; UX_PATTERNS: Authentication flows, skeleton loading, form validation (Zod), dashboard grids, micro-interactions; API_INTEGRATION: React Query, JWT interceptors, error boundaries; PREMIUM_DESIGN: WCAG 2.1 AA, design tokens, responsive layouts, print variants; ISOLATION_LAW: All projects use uv init + .venv
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("worker_uiux_premium", persona, bus, store, llm, tier=3)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
