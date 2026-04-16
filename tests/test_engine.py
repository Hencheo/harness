import asyncio
import pytest
import os
from core.event_bus import EventBus
from core.store import StateStore
from core.parser import load_workflow
from core.engine import HarnessEngine, TaskStatus

@pytest.mark.asyncio
async def test_full_orchestration_loop():
    # Setup
    bus = EventBus()
    store = StateStore("data/test_engine.db")
    await store.initialize()
    engine = HarnessEngine(bus, store)
    
    # Load workflow
    wf_path = "workflows/mock_workflow.yaml"
    wf_def = load_workflow(wf_path)
    
    # Start engine
    wf_id = await engine.start_workflow(wf_def)
    assert wf_id is not None
    
    # Check if first task was dispatched
    # Wait a bit for async tasks
    await asyncio.sleep(0.5)
    assert engine.active_workflows[wf_id]["status"]["scan_logs"] == TaskStatus.DISPATCHED
    
    # Simulate Worker for 'scan_logs'
    # The worker listens on 'agent.debugger'
    async def mock_worker(data):
        print(f"[MOCK WORKER] Processing: {data['id']}")
        # Post completion back to engine
        await bus.publish(
            topic="task.completed",
            sender="worker-debugger",
            payload={"analysis": "found issues"},
            correlation_id=data.get("correlation_id")
        )

    # We need to manually simulate the work because we don't have a real worker running
    # but the engine is already subscribed to 'task.completed'.
    # So we just push a message to 'task.completed' with the right correlation_id.
    
    correlation_id = f"{wf_id}:scan_logs"
    await bus.publish(
        topic="task.completed",
        sender="worker-debugger",
        payload={"analysis": "found issues"},
        correlation_id=correlation_id
    )
    
    # Wait for engine to process completion and dispatch next task
    await asyncio.sleep(1.0)
    
    # Check status
    assert engine.active_workflows[wf_id]["status"]["scan_logs"] == TaskStatus.COMPLETED
    assert engine.active_workflows[wf_id]["status"]["mitigate_issue"] == TaskStatus.DISPATCHED
    
    # --- Simulation Phase 2: Ralph Loop Re-entry ---
    # Simulate 'mitigate_issue' failing the goal
    correlation_id_2 = f"{wf_id}:mitigate_issue"
    await bus.publish(
        topic="task.completed",
        sender="worker-devops",
        payload={"result": "restarted", "goal_met": False},
        correlation_id=correlation_id_2
    )
    
    await asyncio.sleep(1.0)
    
    # Should be back to PENDING or DISPATCHED for initial tasks
    assert engine.active_workflows[wf_id]["status"]["scan_logs"] in [TaskStatus.PENDING, TaskStatus.DISPATCHED]
    print("[TEST] Ralph Loop Re-entry detected successfully!")

    # Cleanup
    await bus.close()
    if os.path.exists("data/test_engine.db"):
        os.remove("data/test_engine.db")

if __name__ == "__main__":
    asyncio.run(test_full_orchestration_loop())
    print("Full orchestration test passed!")
