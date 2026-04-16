import asyncio
import pytest
import os
from core.event_bus import EventBus
from core.store import StateStore
from core.engine import HarnessEngine, TaskStatus
from core.ui.ledger import LedgerManager
from core.parser import WorkflowDef, TaskDef

@pytest.mark.asyncio
async def test_approval_gate_logic():
    bus = EventBus()
    store = StateStore("data/test_interface.db")
    await store.initialize()
    engine = HarnessEngine(bus, store)
    
    # Workflow with a task that requires approval (cat)
    wf_def = WorkflowDef(
        name="ApprovalTest",
        tasks=[
            TaskDef(id="sensitive_task", agent="tool_registry", payload={"command": "cat", "args": ["README.md"]})
        ]
    )
    
    wf_id = await engine.start_workflow(wf_def)
    await asyncio.sleep(0.5)
    
    # Verify it's waiting
    assert engine.active_workflows[wf_id]["status"]["sensitive_task"] == TaskStatus.WAITING_APPROVAL
    
    # Capture the tool execution intent (it should NOT have happened yet)
    tool_exec_events = []
    async def capture_tool(data):
        tool_exec_events.append(data)
    await bus.subscribe("tool.execute", capture_tool)
    
    await asyncio.sleep(0.5)
    assert len(tool_exec_events) == 0
    
    # Grant approval
    await bus.publish(
        topic="approval.response",
        sender="tester",
        payload={"decision": "granted"},
        correlation_id=f"{wf_id}:sensitive_task"
    )
    
    await asyncio.sleep(0.5)
    
    # Now it should be dispatched
    assert engine.active_workflows[wf_id]["status"]["sensitive_task"] == TaskStatus.DISPATCHED
    assert len(tool_exec_events) == 1
    
    await bus.close()
    if os.path.exists("data/test_interface.db"):
        os.remove("data/test_interface.db")

@pytest.mark.asyncio
async def test_ledger_synchronization():
    bus = EventBus()
    ledger = LedgerManager(bus, filename="TEST_AGENTS.md")
    await ledger.start()
    
    # Simulate status update
    await bus.publish(
        topic="engine.status_updated",
        sender="engine",
        payload={"wf_id": "wf-1", "task_id": "test-task", "status": "RUNNING"}
    )
    
    await asyncio.sleep(0.5)
    
    # Check file content
    with open("TEST_AGENTS.md", "r") as f:
        content = f.read()
        assert "wf-1" in content
        assert "test-task" in content
        assert "[RUNNING]" in content

    # Simulate completion
    await bus.publish(
        topic="task.completed",
        sender="agent-1",
        payload={"result": "OK"},
        correlation_id="wf-1:test-task"
    )
    
    await asyncio.sleep(0.5)
    with open("TEST_AGENTS.md", "r") as f:
        content = f.read()
        assert "[COMPLETED]" in content

    if os.path.exists("TEST_AGENTS.md"):
        os.remove("TEST_AGENTS.md")
    await bus.close()
