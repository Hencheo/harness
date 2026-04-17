import asyncio
import os
import signal
import sys
import importlib.util
import pathlib
from dotenv import load_dotenv

load_dotenv()
from core.event_bus import EventBus
from core.store import StateStore
from core.engine import HarnessEngine
from core.ui.ledger import LedgerManager
from core.llm import HarnessLLM
from core.worker import HarnessWorker
from core.mcp_server import ToolRegistry

PID_FILE = "daemon.pid"

def check_lock():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            # Check if process is actually running
            os.kill(old_pid, 0)
            print(f"[DAEMON_ERROR] Harness Daemon is already running (PID: {old_pid}).")
            sys.exit(1)
        except (OSError, ValueError, ProcessLookupError):
            # Process not running, stale lock file
            os.remove(PID_FILE)

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

async def run_daemon():
    check_lock()
    print("[DAEMON] Starting Harness Core Services...")
    
    # 1. Foundation
    bus = EventBus()
    store = StateStore("data/harness_live.db")
    await store.initialize()
    
    # 2. Orchestra
    engine = HarnessEngine(bus, store)
    ledger = LedgerManager(bus)
    tools = ToolRegistry(bus)
    
    # 3. LLM 
    try:
        llm = HarnessLLM() 
    except ValueError as e:
        print(f"[DAEMON_FATAL] LLM Initialization Error: {e}")
        await bus.close()
        return

    # 4. Dynamic Agent Discovery & Loading
    import importlib.util
    import pathlib

    agent_tasks = []
    agents_dir = pathlib.Path("agents")
    
    print("[DAEMON] Scanning for specialized agents...")
    
    for agent_file in agents_dir.glob("*.py"):
        if agent_file.name == "__init__.py":
            continue
            
        agent_name = agent_file.stem
        print(f"[DAEMON] Spawning worker for agent: {agent_name}")
        
        # We assume every agent file defines a persona string if we were to import it,
        # but the current architecture has each agent as a separate script.
        # So for the Daemon to run them internally, we can either:
        # A) Import the persona from the file (if exported)
        # B) Just know their names and keep the HarnessWorker instances here.
        
        # Let's try to load the 'persona' variable from the module if it exists,
        # otherwise use a fallback.
        spec = importlib.util.spec_from_file_location(agent_name, agent_file)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            persona = getattr(module, "persona", f"You are {agent_name} expert.")
            tier = getattr(module, "tier", 3)
        except Exception as e:
            print(f"[DAEMON_WARN] Could not extract DNA from {agent_name}: {e}")
            persona = f"You are {agent_name} expert."
            tier = 3

        worker = HarnessWorker(agent_name, persona, bus, store, llm, tier=tier)
        await worker.start()
        agent_tasks.append(asyncio.create_task(asyncio.sleep(3600))) # Dummy tasks to keep the logic for now
    
    # 5. Start Core Services
    await ledger.start()
    await tools.start()
    await engine.start_mission_listener()
    
    print(f"[DAEMON] All services active. {len(agent_tasks)} workers monitoring the bus.")
    
    # 6. Keep alive until signal
    try:
        while True:
            await asyncio.sleep(3600)
    except (asyncio.CancelledError, KeyboardInterrupt):
        print("[DAEMON] Shutdown signal received.")
    finally:
        print("[DAEMON] Cleaning up workers...")
        for t in agent_tasks:
            t.cancel()
        await bus.close()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        print("[DAEMON] Core Offline.")

if __name__ == "__main__":
    try:
        asyncio.run(run_daemon())
    except KeyboardInterrupt:
        pass
