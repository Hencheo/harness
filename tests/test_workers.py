import asyncio
import pytest
import os
import json
from unittest.mock import AsyncMock, MagicMock
from core.event_bus import EventBus
from core.store import StateStore
from core.worker import HarnessWorker
from core.engineering import ToolOffloader, ContextCompactor

@pytest.mark.asyncio
async def test_tool_offloading_logic():
    # Setup
    store = StateStore("data/test_offload.db")
    await store.initialize()
    offloader = ToolOffloader(store, char_limit=10) # Very small limit for test
    
    agent_id = "test-agent"
    tool_name = "huge_log_tool"
    massive_data = "This is a very long string that should be offloaded."
    
    result = await offloader.offload_if_needed(agent_id, tool_name, massive_data)
    
    assert "Reference ID" in result
    assert "Snippet (Head)" in result
    
    # Verify it's in the store
    key = f"tool_out_{tool_name}"
    latest = await store.get_latest_state(agent_id, key)
    assert latest is not None
    assert latest["value"] == massive_data
    
    # Cleanup
    if os.path.exists("data/test_offload.db"):
        os.remove("data/test_offload.db")

@pytest.mark.asyncio
async def test_worker_lifecycle_with_mock_llm():
    bus = EventBus()
    store = StateStore("data/test_worker.db")
    await store.initialize()
    
    # Mock LLM
    mock_llm = MagicMock()
    mock_llm.chat_completion = AsyncMock()
    mock_llm.estimate_tokens = MagicMock(return_value=10)
    
    # Simulate a tool call response from LLM
    # We must use proper attribute setting to avoid MagicMock 'name' issues
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "ls"
    mock_tool_call.function.arguments = '{"path": "/"}'
    
    mock_response = MagicMock()
    mock_response.tool_calls = [mock_tool_call]
    mock_response.content = None
    mock_llm.chat_completion.return_value = mock_response

    worker = HarnessWorker("tester", "You are a test agent", bus, store, mock_llm)
    
    # We'll capture the tool.execute event
    received_events = []
    async def capture_event(data):
        received_events.append(data)
    await bus.subscribe("tool.execute", capture_event)
    
    # Manual trigger of handle_task
    task_data = {
        "correlation_id": "wf-1:task-1",
        "payload": {"goal": "list files"}
    }
    await worker.handle_task(task_data)
    
    await asyncio.sleep(0.5)
    
    assert len(received_events) == 1
    assert received_events[0]["payload"]["command"] == "ls"
    assert received_events[0]["correlation_id"] == "wf-1:task-1"
    
    await bus.close()
    if os.path.exists("data/test_worker.db"):
        os.remove("data/test_worker.db")

@pytest.mark.asyncio
async def test_context_compaction_trigger():
    # This just tests if should_compact works
    compactor = ContextCompactor(token_limit=20)
    messages = [
        {"role": "system", "content": "A" * 50}, # ~12 tokens
        {"role": "user", "content": "B" * 50}    # ~12 tokens
    ]
    # Estimate: (50+50)//4 = 25 tokens. 25 > 20. Should compact.
    estimate_func = lambda x: len(x) // 4
    assert compactor.should_compact(messages, estimate_func) is True
