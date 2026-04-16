import os
from typing import Dict, Any, List
from core.event_bus import EventBus

class LedgerManager:
    def __init__(self, event_bus: EventBus, filename: str = "AGENTS.md"):
        self.bus = event_bus
        self.filename = filename
        self.current_state: Dict[str, Dict[str, str]] = {} # wf_id -> {task_id: status}

    async def start(self):
        print(f"[LEDGER] Initializing Shared Ledger at {self.filename}...")
        # Clear or initialize file
        with open(self.filename, "w") as f:
            f.write("# HARNESS SHARED LEDGER\n\n")
            f.write("Status actualizado em tempo real pelo Harness Engine.\\n\n")
            f.write("| Workflow | Task | Status | Result |\n")
            f.write("|----------|------|--------|--------|\n")

        await self.bus.subscribe("engine.status_updated", self.on_status_updated)
        await self.bus.subscribe("task.completed", self.on_task_completed)
        await self.bus.subscribe("tool.execute", self.on_tool_execute)
        self.tool_activity: List[str] = []

    async def on_status_updated(self, data: Dict[str, Any]):
        payload = data.get("payload", {})
        wf_id = payload.get("wf_id")
        task_id = payload.get("task_id")
        status = payload.get("status")
        
        if wf_id not in self.current_state:
            self.current_state[wf_id] = {}
        
        self.current_state[wf_id][task_id] = f"[{status}]"
        self._sync_to_file()

    async def on_task_completed(self, data: Dict[str, Any]):
        correlation_id = data.get("correlation_id")
        if not correlation_id or ":" not in correlation_id:
            return
        
        # We need to extract the base wf_id and task_id (ignoring tool_call_id part if present)
        wf_id, task_id = correlation_id.split(":", 1)
        if ":" in task_id: # cases like wf_id:task_id:tool_id
            task_id = task_id.split(":")[0]

        res_snippet = str(data.get("payload", {}).get("result", data.get("payload", {})))[:100] + "..."
        
        if wf_id in self.current_state:
            self.current_state[wf_id][task_id] = f"[COMPLETED] | {res_snippet}"
            self._sync_to_file()

    async def on_tool_execute(self, data: Dict[str, Any]):
        sender = data.get("sender", "unknown")
        payload = data.get("payload", {})
        command = payload.get("command")
        args = payload.get("args")
        
        entry = f"- **{sender}**: `{command}` {args}"
        self.tool_activity.append(entry)
        if len(self.tool_activity) > 10:
            self.tool_activity.pop(0) # Keep last 10
        self._sync_to_file()

    def _sync_to_file(self):
        try:
            with open(self.filename, "w") as f:
                f.write("# HARNESS SHARED LEDGER\n\n")
                f.write("> **Status**: Monitorado em tempo real.\n\n")
                f.write("| Workflow | Task | Status | Details |\n")
                f.write("|----------|------|--------|---------|\n")
                
                for wf_id, tasks in self.current_state.items():
                    for t_id, status in tasks.items():
                        # Splitting status and result if available and piped
                        parts = status.split(" | ")
                        stat = parts[0]
                        detail = parts[1] if len(parts) > 1 else "-"
                        f.write(f"| {wf_id} | {t_id} | {stat} | {detail} |\n")
                
                if self.tool_activity:
                    f.write("\n## Real-Time Activity\n\n")
                    for act in self.tool_activity:
                        f.write(f"{act}\n")
        except Exception as e:
            print(f"[LEDGER_ERROR] Failed to sync AGENTS.md: {e}")
