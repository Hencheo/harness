import asyncio
import pytest
import os
from core.event_bus import EventBus
from core.store import StateStore
from core.middleware import SandwichMiddleware, AuditMiddleware

@pytest.mark.asyncio
async def test_event_bus():
    bus = EventBus()
    received = []

    async def callback(data):
        received.append(data)

    await bus.subscribe("test.topic", callback)
    await asyncio.sleep(0.1)  # Wait for subscription
    
    payload = {"msg": "hello harness"}
    event_id = await bus.publish("test.topic", "tester", payload)
    
    await asyncio.sleep(0.5)  # Wait for processing
    
    assert len(received) == 1
    assert received[0]["payload"] == payload
    assert received[0]["sender"] == "tester"
    
    await bus.close()

@pytest.mark.asyncio
async def test_state_store():
    db_path = "data/test_persist.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    store = StateStore(db_path)
    await store.initialize()
    
    agent_id = "agent-001"
    session_id = "sess-abc"
    key = "last_command"
    value = {"cmd": "ls", "status": "ok"}
    
    state_id = await store.set_state(agent_id, session_id, key, value)
    assert state_id is not None
    
    latest = await store.get_latest_state(agent_id, key)
    assert latest is not None
    assert latest["value"] == value
    assert latest["agent_id"] == agent_id

@pytest.mark.asyncio
async def test_sandwich_middleware():
    mw_manager = SandwichMiddleware()
    mw_manager.add(AuditMiddleware())
    
    data = {"id": "req-1", "action": "think"}
    
    # Run pre
    processed_pre = await mw_manager.run_pre(data)
    assert processed_pre == data
    
    # Run post
    processed_post = await mw_manager.run_post({"result": "done"})
    assert processed_post == {"result": "done"}

if __name__ == "__main__":
    asyncio.run(test_event_bus())
    asyncio.run(test_state_store())
    print("Manual tests passed!")
