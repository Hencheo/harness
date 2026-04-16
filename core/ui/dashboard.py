import asyncio
from datetime import datetime
from typing import Dict, List, Any
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Console
from core.event_bus import EventBus

class HarnessDashboard:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.console = Console()
        self.layout = Layout()
        self.agent_status: Dict[str, str] = {} # agent_name -> status
        self.event_log: List[str] = []
        self.active_dags: Dict[str, Dict[str, str]] = {} # wf_id -> {task_id: status}

    async def start(self):
        print("[DASHBOARD] Monitoring System Events...")
        await self.bus.subscribe("worker.registered", self.on_worker_registered)
        await self.bus.subscribe("engine.status_updated", self.on_status_updated)
        await self.bus.subscribe("task.completed", self.on_task_completed)
        await self.bus.subscribe("approval.requested", self.on_approval_requested)
        await self.bus.subscribe("*", self.on_any_event)
        
        # Initial ping to discover existing workers
        await asyncio.sleep(0.5)
        await self.bus.publish("system.ping", sender="dashboard", payload={})

    async def on_worker_registered(self, data: Dict[str, Any]):
        payload = data.get("payload", {})
        name = payload.get("name")
        tier = payload.get("tier", 3)
        self.agent_status[name] = {"status": "IDLE", "tier": tier}

    async def on_status_updated(self, data: Dict[str, Any]):
        payload = data.get("payload", {})
        wf_id = payload.get("wf_id")
        task_id = payload.get("task_id")
        status = payload.get("status")
        
        if wf_id not in self.active_dags:
            self.active_dags[wf_id] = {}
        self.active_dags[wf_id][task_id] = status

    async def on_task_completed(self, data: Dict[str, Any]):
        sender = data.get("sender", "unknown")
        if sender in self.agent_status:
            self.agent_status[sender]["status"] = "IDLE"
        self.event_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] Task completed by {sender}")

    async def on_approval_requested(self, data: Dict[str, Any]):
        payload = data.get("payload", {})
        self.event_log.append(f"[bold red][{datetime.now().strftime('%H:%M:%S')}] APPROVAL REQUIRED: {payload.get('command')}[/]")

    async def on_any_event(self, data: Dict[str, Any]):
        topic = data.get("topic", "unknown")
        sender = data.get("sender", "unknown")
        
        # Track agent activity by topic
        if topic.startswith("agent."):
            agent_name = topic.split(".")[1]
            if agent_name in self.agent_status:
                self.agent_status[agent_name]["status"] = "BUSY"
        
        if topic not in ["engine.status_updated", "worker.registered"]:
            # Add to traffic log
            clean_payload = str(data.get("payload", {}))[:30] + "..."
            self.event_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {sender} -> {topic} {clean_payload}")
            if len(self.event_log) > 10:
                self.event_log.pop(0)

    def _make_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=10)
        )
        layout["body"].split_row(
            Layout(name="agents", ratio=1),
            Layout(name="dags", ratio=2)
        )

        # Header
        layout["header"].update(Panel(Text("HARNESS MULTI-AGENT COCKPIT", justify="center", style="bold blue")))

        # Agents Table
        agent_table = Table(title="Live Hierarchy (10-5-1)")
        agent_table.add_column("Tier", justify="center")
        agent_table.add_column("Agent")
        agent_table.add_column("Status")
        
        # Sort by Tier then by Name
        sorted_agents = sorted(self.agent_status.items(), key=lambda x: (x[1].get('tier', 3), x[0]))
        
        for agent, info in sorted_agents:
            status = info.get("status", "IDLE")
            tier = info.get("tier", 3)
            color = "green" if status == "IDLE" else "yellow"
            tier_color = "bold cyan" if tier == 2 else "white"
            agent_table.add_row(f"[{tier_color}]T{tier}[/]", agent, f"[{color}]{status}[/]")
        layout["agents"].update(Panel(agent_table))

        # DAGS Table
        dag_table = Table(title="Active Workflows")
        dag_table.add_column("Workflow")
        dag_table.add_column("Tasks Status")
        for wf_id, tasks in self.active_dags.items():
            status_summary = " ".join([f"{t}:[bold]{s}[/]" for t, s in tasks.items()])
            dag_table.add_row(wf_id, status_summary)
        layout["dags"].update(Panel(dag_table))

        # Footer (Log)
        log_text = Text.from_markup("\n".join(self.event_log))
        layout["footer"].update(Panel(log_text, title="Event Bus Traffic (Live)"))

        return layout
