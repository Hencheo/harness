import asyncio
import sys
import json
import os
import subprocess
import time
from pathlib import Path

# Add parent directory to path to import core
sys.path.append(str(Path(__file__).parent.parent))

from core.event_bus import EventBus
from core.parser import WorkflowDef

async def main():
    if len(sys.argv) < 2:
        print("Usage: python deploy_mission.py <mission_json_file_or_string>")
        sys.exit(1)

    input_data = sys.argv[1]
    
    # Try to load as file first
    if os.path.exists(input_data):
        with open(input_data, "r") as f:
            mission_data = json.load(f)
    else:
        # Otherwise treat as raw JSON string
        try:
            mission_data = json.loads(input_data)
        except json.JSONDecodeError:
            print("Error: Input is neither a valid file path nor a valid JSON string.")
            sys.exit(1)

    # Validate mission structure
    try:
        if "workflow" in mission_data:
            wf_data = mission_data["workflow"]
        else:
            wf_data = mission_data
        
        # Validation via Pydantic
        WorkflowDef(**wf_data)
        
        bus = EventBus()
        
        # --- AUTO-ACTIVATION CHECK ---
        count = await bus.get_subscriber_count("harness.mission.deploy")
        if count == 0:
            print("[BRIDGE] Harness Cockpit not detected. Launching automatically...")
            # Command to launch in a new terminal tab (GNOME Terminal / Zorin OS)
            cmd = [
                "gnome-terminal", 
                "--", 
                "/home/hencheo/.gemini/antigravity/scratch/harness/start_cockpit.sh"
            ]
            try:
                subprocess.Popen(cmd)
                print("[BRIDGE] Waiting for Engine initialization...")
                time.sleep(4) # Give it time to boot and subscribe
            except Exception as e:
                print(f"[BRIDGE_ERROR] Could not auto-launch Cockpit: {e}")
        # -----------------------------

        print(f"[BRIDGE] Deploying mission: {wf_data.get('name', 'Unnamed')}")
        
        await bus.publish(
            topic="harness.mission.deploy",
            sender="hermes_bridge",
            payload={"workflow": wf_data}
        )
        
        await bus.close()
        print("[BRIDGE] Mission successfully published to Harness Event Bus.")
        
    except Exception as e:
        print(f"[BRIDGE_ERROR] Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
