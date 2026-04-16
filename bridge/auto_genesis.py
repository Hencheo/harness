#!/usr/bin/env python3
import sys
import os

# RITUAL DE GÊNESE (Auto-Spawner 2.0)
# Este script é o único caminho para a criação de novos agentes trabalhadores (Tier 3).
# Ele obriga a injeção do DNA Harness (Lei do UV, Pesquisa, etc).

TEMPLATE = """import asyncio
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

# DNA do Trabalhador Especialista (Tier 3)
# Base de Conhecimento: {tech_name}
# Descobertas e Padrões (2026): {research_summary}

persona = \"\"\"You are a {agent_display_name} Specialist Agent (Tier 3).
Your isolated goal is: {goal}.

### CORE DIRECTIVES (Harness Tier 3):
1. **CHAIN OF COMMAND:** You report directly to {lead_agent}. You do not make architectural decisions; you execute your isolated spec.
2. **THE LAW OF UV / ISOLATION:** Every Python project MUST use `uv init` and `.venv`. Node/Go projects must use local scope. No global installs.
3. **TECH EXPERTISE:** {expertise_clauses}
\"\"\"

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("{agent_id}", persona, bus, store, llm, tier=3)
    await worker.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
"""

def genesis_protocol(agent_id, tech_name, lead_agent, goal, research_summary, expertise_clauses):
    print(f"[GENESIS] Initiating Spawn Protocol for: {agent_id} (Under {lead_agent})")
    
    # --- ANTI-LAZY LOCK (v3.2) ---
    if len(research_summary) < 100:
        print("[ERROR] GENESIS ABORTED: Research summary is too short.")
        print("[FIX] Hermes, you are being lazy. Go to the web and research the LATEST standards before spawning.")
        sys.exit(1)
        
    prohibited_terms = ["manual spawn", "internal knowledge", "standard expert", "boilerplate"]
    if any(term in research_summary.lower() for term in prohibited_terms):
        print(f"[ERROR] GENESIS ABORTED: Prohibited 'lazy' terms found in research summary.")
        print("[FIX] You must use REAL research data from 2026, not your internal memories.")
        sys.exit(1)
    # -----------------------------

    agent_display_name = tech_name.upper()
    
    agent_code = TEMPLATE.format(
        tech_name=tech_name,
        research_summary=research_summary,
        agent_display_name=agent_display_name,
        goal=goal,
        lead_agent=lead_agent,
        expertise_clauses=expertise_clauses,
        agent_id=agent_id
    )
    
    file_path = f"agents/{agent_id}.py"
    with open(file_path, "w") as f:
        f.write(agent_code)
        
    print(f"[GENESIS] Tier 3 Worker Born: {file_path}")
    print(f"[GENESIS] System updated. The Daemon will adopt this worker on the next loop.")

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("Usage: python3 bridge/auto_genesis.py <agent_id> <tech_name> <lead_agent> <goal> <research_summary_text> <expertise_clauses>")
        print("Hermes Constraint: You MUST use web_search to populate the research_summary_text BEFORE calling this script.")
        sys.exit(1)
    
    genesis_protocol(
        agent_id=sys.argv[1],
        tech_name=sys.argv[2],
        lead_agent=sys.argv[3],
        goal=sys.argv[4],
        research_summary=sys.argv[5],
        expertise_clauses=sys.argv[6]
    )
