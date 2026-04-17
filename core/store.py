import aiosqlite
import json
import os
from uuid import uuid4
from datetime import datetime
from typing import Optional, Any, Dict, List

class StateStore:
    def __init__(self, db_path: str = "data/persist.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    key TEXT,
                    value JSONB,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.commit()

    async def set_state(self, agent_id: str, session_id: str, key: str, value: Any):
        state_id = str(uuid4())
        value_json = json.dumps(value)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO agent_state (id, agent_id, session_id, key, value)
                VALUES (?, ?, ?, ?, ?)
            """, (state_id, agent_id, session_id, key, value_json))
            await db.commit()
        return state_id

    async def get_state(self, agent_id: str, key: str) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM agent_state 
                WHERE agent_id = ? AND key = ?
                ORDER BY created_at DESC
            """, (agent_id, key)) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    val = item["value"]
                    if isinstance(val, str):
                        try:
                            item["value"] = json.loads(val)
                        except:
                            pass # Keep as string if not valid JSON
                    results.append(item)
                return results

    async def get_latest_state(self, agent_id: str, key: str) -> Optional[Dict[str, Any]]:
        states = await self.get_state(agent_id, key)
        return states[0] if states else None
