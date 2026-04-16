import asyncio
import sys
import os
import json
from dotenv import load_dotenv
from aioconsole import ainput
from rich.console import Console
from rich.panel import Panel
from rich.live import Live

# Load environment variables from .env
load_dotenv()
from core.event_bus import EventBus
from core.ui.dashboard import HarnessDashboard
from core.llm import HarnessLLM
from core.parser import WorkflowDef, TaskDef

async def run_cockpit():
    # 1. Connect to existing bus
    bus = EventBus()
    dashboard = HarnessDashboard(bus)
    
    # 2. LLM for chat (Only for UI interaction)
    try:
        llm = HarnessLLM() 
    except ValueError:
        llm = None # Chat might be disabled but UI still works

    # 3. Start UI components
    await dashboard.start()
    
    console = Console()
    console.print("\n[bold blue]Harness Cockpit UI (Connected to Daemon).[/]")
    console.print("[dim]Commands: 'exit', 'status', 'approve <id>', 'deny <id>'[/]\n")

    # 4. Prompt System
    hermes_prompt = "You are Hermes, the UI assistant. Reply concisely."
    chat_history = [{"role": "system", "content": hermes_prompt}]

    # 5. UI Loop with Live Dashboard
    with Live(dashboard._make_layout(), refresh_per_second=4) as live:
        async def ui_refresh_loop():
            while True:
                live.update(dashboard._make_layout())
                await asyncio.sleep(0.5)
        
        refresh_task = asyncio.create_task(ui_refresh_loop())

        while True:
            try:
                line = await ainput("HERMES > ")
                if not line: continue
                
                cmd = line.strip().split()
                if cmd[0] == "exit":
                    break
                
                if cmd[0] == "status":
                    # Force immediate refresh
                    live.update(dashboard._make_layout())
                    continue
                
                if cmd[0] == "approve" and len(cmd) > 1:
                    corr_id = cmd[1]
                    await bus.publish(topic="approval.response", sender="human", payload={"decision": "granted"}, correlation_id=corr_id)
                    continue

                # UI Chat (Optional)
                if llm:
                    chat_history.append({"role": "user", "content": line})
                    response = await llm.chat_completion(chat_history)
                    reply = response.content
                    chat_history.append({"role": "assistant", "content": reply})
                    console.print(f"\n[bold green]UI-HERMES:[/] {reply}\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]CLI Error: {e}[/]")

    # Shutdown
    refresh_task.cancel()
    await bus.close()
    print("[CLI] Cockpit Disconnected.")

if __name__ == "__main__":
    asyncio.run(run_cockpit())
