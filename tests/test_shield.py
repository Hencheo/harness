import asyncio
import pytest
import os
from core.event_bus import EventBus
from core.store import StateStore
from core.parser import WorkflowDef, TaskDef
from core.engine import HarnessEngine, TaskStatus
from core.policies.guardrails import guardrails
from core.mcp_server import ToolRegistry

@pytest.mark.asyncio
async def test_policy_logic():
    # Test allowed
    auth, reason = guardrails.is_authorized("agent-1", "execute", {"command": "ls", "args": ["-la"]})
    assert auth == "ALLOWED"
    
    # Test blocked command
    auth, reason = guardrails.is_authorized("agent-1", "execute", {"command": "rm", "args": ["-rf", "/"]})
    assert auth == "DENIED"
    assert "not in the allowed list" in reason or "pattern" in reason

    # Test blocked pattern even if command allowed (security bypass attempt)
    # If echo is allowed but we try to inject | or rm
    auth, reason = guardrails.is_authorized("agent-1", "execute", {"command": "echo", "args": ["hello", "|", "rm", "-rf", "/"]})
    assert auth == "DENIED"
    assert "pattern" in reason

@pytest.mark.asyncio
async def test_shielded_orchestration():
    bus = EventBus()
    store = StateStore("data/test_shield.db")
    await store.initialize()
    engine = HarnessEngine(bus, store)
    
    # Define a malicious workflow
    malicious_wf = WorkflowDef(
        name="Malicious Workflow",
        tasks=[
            TaskDef(id="evil_task", agent="tool_registry", payload={"command": "rm", "args": ["-rf", "/"]})
        ]
    )
    
    wf_id = await engine.start_workflow(malicious_wf)
    await asyncio.sleep(0.5)
    
    # Check that it was failed by the shield
    assert engine.active_workflows[wf_id]["status"]["evil_task"] == TaskStatus.FAILED
    assert engine.active_workflows[wf_id]["results"]["evil_task"]["error"] == "Security Denied"
    
    await bus.close()
    if os.path.exists("data/test_shield.db"):
        os.remove("data/test_shield.db")

@pytest.mark.asyncio
async def test_real_tool_execution():
    bus = EventBus()
    store = StateStore("data/test_tool.db")
    await store.initialize()
    
    registry = ToolRegistry(bus)
    await registry.start()
    
    engine = HarnessEngine(bus, store)
    
    # Define a legit workflow
    legit_wf = WorkflowDef(
        name="Legit Workflow",
        tasks=[
            TaskDef(id="check_files", agent="tool_registry", payload={"command": "ls", "args": ["-l"]})
        ]
    )
    
    wf_id = await engine.start_workflow(legit_wf)
    
    # Wait for completion
    await asyncio.sleep(1.0)
    
    assert engine.active_workflows[wf_id]["status"]["check_files"] == TaskStatus.COMPLETED
    assert "result" in engine.active_workflows[wf_id]["results"]["check_files"]
    
    await bus.close()
    if os.path.exists("data/test_tool.db"):
        os.remove("data/test_tool.db")
