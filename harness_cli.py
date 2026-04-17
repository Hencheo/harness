import asyncio
import sys
import os
import json
import pathlib
from dotenv import load_dotenv
from aioconsole import ainput
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown

# Load environment variables
load_dotenv()
from core.event_bus import EventBus
from core.ui.dashboard import HarnessDashboard
from core.llm import HarnessLLM
from core.orchestrator_tools import ORCHESTRATOR_TOOLS

class HermesOrchestrator:
    """Bridge between the LLM and the Harness Engine for Tier 0 governance."""
    def __init__(self, bus: EventBus, console: Console):
        self.bus = bus
        self.console = console

    async def execute_tool(self, tool_call):
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        self.console.print(f"[dim italic]Hermes calling tool: {name}({args})[/]")
        
        if name == "audit_missions":
            missions_dir = pathlib.Path("/home/hencheo/data/missions")
            if not missions_dir.exists(): return "No missions directory found."
            missions = [d.name for d in missions_dir.iterdir() if d.is_dir()]
            return f"Existing missions: {missions}"
            
        elif name == "read_ledger":
            try:
                with open("AGENTS.md", "r") as f:
                    return f.read()
            except Exception as e:
                return f"Error reading ledger: {e}"
                
        elif name == "inspect_mission":
            m_id = args.get("mission_id")
            path = pathlib.Path(f"/home/hencheo/data/missions/{m_id}")
            if not path.exists(): return f"Mission {m_id} not found."
            files = [f.name for f in path.glob("*")]
            return f"Mission {m_id} contains: {files}. To read a specific file, Hermes must delegate to a Lead."
            
        elif name == "deploy_workflow":
            # Hierarchy Enforcement: Ensure it's delegating to a LEAD
            lead = args.get("lead_agent")
            if not lead.startswith("lead_"):
                return "FAIL: Hermes must delegate to a Lead (Tier 2), not directly to a worker."
            
            payload = {
                "workflow": {
                    "name": args.get("name"),
                    "tasks": [
                        {
                            "id": "initial_lead_task",
                            "agent": lead,
                            "payload": {"instruction": args.get("instruction")},
                            "depends_on": []
                        },
                        {
                            "id": "qa_audit_task",
                            "agent": "lead_qa_auditor",
                            "payload": {"instruction": "Audite agressivamente o código entregue pelo Lead. Verifique falhas de segurança e crie testes rigorosos para o código."},
                            "depends_on": ["initial_lead_task"]
                        }
                    ]
                }
            }
            await self.bus.publish(topic="harness.mission.deploy", sender="hermes_cli", payload=payload)
            return f"SUCCESS: Mission '{args.get('name')}' deployed to {lead} and lead_qa_auditor via Harness Engine."
            
        return f"Unknown tool: {name}"

async def run_cockpit():
    bus = EventBus()
    dashboard = HarnessDashboard(bus)
    console = Console()
    
    try:
        llm = HarnessLLM() 
    except ValueError:
        llm = None

    orchestrator = HermesOrchestrator(bus, console)
    await dashboard.start()
    
    console.print(Panel("[bold cyan]HARNESS COCKPIT - PROTOCOLO 10-5-1 ATIVO[/]", subtitle="v3.2 - Governance Mode"))
    console.print("[dim]Comandos: 'exit', 'status', 'approve <id>', 'deny <id>' ou converse com Hermes.[/]\n")

    # Load Foundation Laws
    soul_path = pathlib.Path("Hermes_SOUL.md")
    soul_content = soul_path.read_text() if soul_path.exists() else "Follow hierarchy 10-5-1."
    
    hermes_prompt = f"""{soul_content}
    
    CURRENT CONTEXT:
    - You are operating via the Harness CLI.
    - [STRICT RULE]: NEVER output Markdown code blocks (```) or implementations in your chat response.
    - Summarize technical plans in high-level bullet points only.
    - Before suggesting ANY new mission, you MUST call 'audit_missions' and 'read_ledger' to see if the work is already in progress.
    - If a mission exists, suggest resuming it or inspecting it via Tools.
    - NEVER delegate directly to Tier 3 agents (workers). Always delegate to the appropriate Lead (Tier 2).
    """
    
    chat_history = [{"role": "system", "content": hermes_prompt}]
    
    # Approval mediation queue
    pending_approvals = asyncio.Queue()
    async def on_approval_requested(data):
        await pending_approvals.put(data)
    await bus.subscribe("approval.requested", on_approval_requested)

    with Live(dashboard._make_layout(), refresh_per_second=4) as live:
        async def ui_refresh_loop():
            while True:
                live.update(dashboard._make_layout())
                await asyncio.sleep(0.5)
        
        refresh_task = asyncio.create_task(ui_refresh_loop())

        while True:
            try:
                # Check for pending approvals and let Hermes speak first
                if not pending_approvals.empty():
                    app_data = await pending_approvals.get_nowait()
                    payload = app_data.get("payload", {})
                    corr_id = app_data.get("correlation_id")
                    
                    system_alert = (
                        f"[HIERARCHY ALERT] Lead Agent '{payload.get('agent')}' is requesting human approval!\n"
                        f"Reason: {payload.get('reason')}\n"
                        f"Context: {payload.get('context')}\n"
                        f"Correlation ID: {corr_id}\n\n"
                        "Hermes, analyze this request and present it to the Human for a decision. Ask if they want to 'approve [ID]' or 'deny [ID]'."
                    )
                    chat_history.append({"role": "system", "content": system_alert})
                    # We enter the talk loop directly with this context
                else:
                    line = await ainput("HERMES > ")
                    if not line: continue
                    
                    cmd = line.strip().split()
                    if cmd[0] == "exit": break
                    if cmd[0] in ["status", "approve", "deny"]:
                        # Handle CLI commands
                        if cmd[0] == "approve" and len(cmd) > 1:
                            await bus.publish(topic="approval.response", sender="human", payload={"decision": "granted"}, correlation_id=cmd[1])
                            console.print(f"[bold green]Approved {cmd[1]}[/]")
                        elif cmd[0] == "deny" and len(cmd) > 1:
                            await bus.publish(topic="approval.response", sender="human", payload={"decision": "denied"}, correlation_id=cmd[1])
                            console.print(f"[bold red]Denied {cmd[1]}[/]")
                        continue
                    chat_history.append({"role": "user", "content": line})
                    
                    while True: # Tool loop for Hermes
                        response = await llm.chat_completion(chat_history, tools=ORCHESTRATOR_TOOLS)
                        
                        if response.tool_calls:
                            chat_history.append({
                                "role": "assistant",
                                "content": response.content or "",
                                "tool_calls": [
                                    {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} 
                                    for tc in response.tool_calls
                                ]
                            })
                            
                            for tc in response.tool_calls:
                                result = await orchestrator.execute_tool(tc)
                                chat_history.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": result})
                            
                            continue # Let Hermes think again with tool results
                        else:
                            reply = response.content
                            chat_history.append({"role": "assistant", "content": reply})
                            console.print(Panel(Markdown(reply), title="[bold green]UI-HERMES[/]", border_style="green"))
                            break

            except KeyboardInterrupt: break
            except Exception as e:
                console.print(f"[red]CLI Error: {e}[/]")

    refresh_task.cancel()
    await bus.close()
    print("[CLI] Cockpit Disconnected.")

if __name__ == "__main__":
    asyncio.run(run_cockpit())
