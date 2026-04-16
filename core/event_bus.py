import json
import asyncio
from datetime import datetime
from uuid import uuid4
from typing import Callable, Optional, Dict, Any
from redis.asyncio import Redis
from pydantic import BaseModel, Field

class EventPayload(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    topic: str
    sender: str
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None

class EventBus:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.redis = Redis(host=host, port=port, db=db, decode_responses=True)
        self.pubsub = None
        self._listener_task = None
        self._callbacks: Dict[str, List[Callable]] = {}

    async def publish(self, topic: str, sender: str, payload: Dict[str, Any], correlation_id: Optional[str] = None):
        event = EventPayload(
            topic=topic,
            sender=sender,
            payload=payload,
            correlation_id=correlation_id
        )
        await self.redis.publish(topic, event.model_dump_json())
        return event.id

    async def get_subscriber_count(self, topic: str) -> int:
        """Returns the number of active subscribers for a given topic."""
        res = await self.redis.pubsub_numsub(topic)
        # Returns a list like [(b'topic', count)]
        if res and len(res) > 0:
            return res[0][1]
        return 0

    async def subscribe(self, topic: str, callback: Callable):
        if topic not in self._callbacks:
            self._callbacks[topic] = []
        self._callbacks[topic].append(callback)

        if not self.pubsub:
            self.pubsub = self.redis.pubsub()
            if topic == "*":
                await self.pubsub.psubscribe(topic)
            else:
                await self.pubsub.subscribe(topic)
            self._listener_task = asyncio.create_task(self._main_listener())
        else:
            if topic == "*":
                await self.pubsub.psubscribe(topic)
            else:
                await self.pubsub.subscribe(topic)

    async def _main_listener(self):
        try:
            async for message in self.pubsub.listen():
                if message["type"] in ["message", "pmessage"]:
                    topic = message["channel"] if message["type"] == "message" else message["pattern"]
                    data = json.loads(message["data"])
                    
                    # Exact match dispatch
                    if topic in self._callbacks:
                        for cb in self._callbacks[topic]:
                            asyncio.create_task(cb(data))
                    
                    # Wildcard dispatch
                    if "*" in self._callbacks:
                        for cb in self._callbacks["*"]:
                            asyncio.create_task(cb(data))
        except Exception as e:
            print(f"EventBus Listener Error: {e}")

    async def close(self):
        if self._listener_task:
            self._listener_task.cancel()
        if self.pubsub:
            await self.pubsub.aclose()
        await self.redis.aclose()
