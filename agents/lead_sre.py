tier = 1
import asyncio
import json
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.worker import HarnessWorker

persona = """You are the Lead SRE Sentinel (Tier 1). 
Your mission is the stability and self-healing of the Harness Multi-Agent Swarm.

CORE DIRECTIVES:
1. AUTO-REMEDIATION: If you detect a 'task.failed' with 'ModuleNotFoundError', you MUST run 'run_command' with 'uv add <package>' to fix the environment. 
2. DISPATCHER: If you see a 'task.dlq' (max retries exhausted), analyze the traceback. If it's a transient infra issue, try one last 'clean' spawn or report to Hermes.
3. HEALTH MONITOR: Track 'system.health' pings. If an agent goes dark (>60s), report 'STALLED' and suggest a restart.
4. TIER 1 AUTHORITY: You are authorized to run shell commands (run_command) to manage the environment and fix dependencies.
5. **IMPLEMENTATION INTEGRITY:** Documentation MUST NOT lie. NEVER document or test a class (e.g., MetricsCollector) that has not been physically implemented in the codebase. Verify file contents before marking a task as COMPLETED.
6. **SRE HYGIENE:** Ensure all monitoring scripts handle missing dependencies (like psutil) gracefully without crashing.

### PROTOCOL FOR task.failed / task.dlq:
When you receive an error, don't just report it. FIX IT.
- Error: "ModuleNotFoundError: No module named 'X'" -> run_command("uv add X")
- Error: "Permission denied" -> Verify current user and suggest chmod/chown via report.
- Error: "Connection refused" -> Check if Redis or target service is running.
"""

async def main():
    bus = EventBus()
    store = StateStore()
    await store.initialize()
    llm = HarnessLLM()

    worker = HarnessWorker("lead_sre", persona, bus, store, llm, tier=1)
    await worker.start()

    # SRE Special: Subscribe to failures and DLQ as if they were tasks
    # We wrap them to match the expected 'agent.lead_sre' payload format
    
    async def failure_bridge(data):
        sender = data.get("sender")
        # AMNESTY PROTOCOL: SRE does not attempt to fix itself or other Tier 1 regulators
        # to avoid infinite recursive failure loops.
        tier1_agents = ["lead_sre", "lead_qa_auditor", "lead_sre_remora"]
        if sender in tier1_agents:
            # We don't print here to avoid flooding logs if it was already looping
            return
            
        print(f"[SRE] Intercepted failure from {sender}. Analyzing remediation...")
        # Map failure event to a task-like payload for the SRE to process
        payload = {
            "type": "REMEDIATION_REQUEST",
            "source_topic": data.get("topic"),
            "event_data": data.get("payload"),
            "correlation_id": data.get("correlation_id")
        }
        await worker.handle_task({"payload": payload, "correlation_id": f"sre-remedy-{data.get('id')}"})

    await bus.subscribe("task.failed", failure_bridge)
    await bus.subscribe("task.dlq", failure_bridge)
    
    # We could also subscribe to system.health for monitoring
    # but for now let's focus on active remediation.

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()

if __name__ == "__main__":
    asyncio.run(main())
