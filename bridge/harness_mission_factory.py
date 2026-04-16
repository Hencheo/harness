#!/usr/bin/env python3
import sys
import json
import subprocess
import os
from pathlib import Path

# This script helps Hermes (the agent) to quickly formulate 
# and deploy missions to the Harness without manual JSON formatting.

def create_mission(name, tasks_data):
    """
    tasks_data should be a list of tuples: (task_id, agent_name, payload_dict, depends_on_list)
    """
    mission = {
        "name": name,
        "tasks": []
    }
    
    for t_id, agent, payload, deps in tasks_data:
        mission["tasks"].append({
            "id": t_id,
            "agent": agent,
            "payload": payload,
            "depends_on": deps
        })
    
    # Save temporary mission file
    mission_file = f"data/missions/temp_{name.lower().replace(' ', '_')}.json"
    os.makedirs("data/missions", exist_ok=True)
    
    with open(mission_file, "w") as f:
        json.dump(mission, f, indent=2)
    
    print(f"[FACTORY] Mission prepared: {mission_file}")
    
    # Call the deploy bridge
    cmd = ["python3", "bridge/deploy_mission.py", mission_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[FACTORY] SUCCESS: Mission deployed to Harness.")
        print(result.stdout)
    else:
        print("[FACTORY] ERROR: Deployment failed.")
        print(result.stderr)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Internal usage for Hermes agent.")
        sys.exit(1)
        
    # Implementation for CLI if needed, but primarily intended for direct import or subprocess call by the agent
    pass
