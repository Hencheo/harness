import asyncio
import json
from typing import Dict, List, Any, Optional
from core.event_bus import EventBus
from core.store import StateStore
from core.llm import HarnessLLM
from core.engineering import ToolOffloader, ContextCompactor
from core.tools_def import HARNESS_TOOLS

class HarnessWorker:
    def __init__(self, name: str, persona: str, event_bus: EventBus, state_store: StateStore, llm: HarnessLLM, tier: int = 3):
        self.name = name
        self.persona = persona
        self.bus = event_bus
        self.store = state_store
        self.llm = llm
        self.tier = tier
        
        self.offloader = ToolOffloader(state_store)
        self.compactor = ContextCompactor()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.pending_tool_results: Dict[str, asyncio.Future] = {}

    async def start(self):
        print(f"[WORKER] Agent {self.name} (Tier {self.tier}) initialized and listening...")
        await self.bus.subscribe("system.ping", self.on_ping)
        await self.register()
        await self.bus.subscribe(f"agent.{self.name}", self.handle_task)
        await self.bus.subscribe("task.completed", self.on_internal_task_completed)

    async def register(self):
        await self.bus.publish(
            topic="worker.registered",
            sender=self.name,
            payload={"name": self.name, "tier": self.tier, "status": "IDLE"}
        )

    async def on_ping(self, data: Dict[str, Any]):
        await self.register()

    async def on_internal_task_completed(self, data: Dict[str, Any]):
        correlation_id = data.get("correlation_id")
        if correlation_id in self.pending_tool_results:
            future = self.pending_tool_results[correlation_id]
            if not future.done():
                future.set_result(data.get("payload"))

    async def handle_task(self, data: Dict[str, Any]):
        correlation_id = data.get("correlation_id")
        payload = data.get("payload", {})
        workspace_path = payload.get("workspace_path", ".")
        
        # 0. Check for offloaded payloads in the incoming data
        for key, val in payload.items():
            if isinstance(val, dict) and val.get("status") == "success" and "result" in val:
                payload[key] = await self.offloader.offload_if_needed(self.name, key, val["result"])

        # 1. Prepare/Maintain context
        session_id = correlation_id.split(":")[0] if correlation_id else "global"
        if session_id not in self.active_sessions:
            extended_persona = f"{self.persona}\n\nYour current workspace is: {workspace_path}\nAll file operations will be relative to this path."
            self.active_sessions[session_id] = {
                "history": [{"role": "system", "content": extended_persona}],
                "workspace_path": workspace_path
            }
        
        history = self.active_sessions[session_id]["history"]
        
        # Add current task/observation to history
        history.append({"role": "user", "content": json.dumps(payload)})
        
        # 2. Compact if needed
        if self.compactor.should_compact(history, self.llm.estimate_tokens):
            self.active_sessions[session_id] = await self.compactor.compact(history, self.llm)
            history = self.active_sessions[session_id]

        # 3. Reasoning (LLM Call)
        # 3. Reasoning Loop (Tool-Reasoning)
        # TIER GUARDRAIL: Restrict tools based on agent level
        available_tools = HARNESS_TOOLS
        if self.tier == 2:
            # Leads can ONLY Read and Delegate. They CANNOT write or execute implementation commands.
            forbidden_tools = ["write_file", "replace_file_content", "run_command", "multi_replace_file_content"]
            available_tools = [t for t in HARNESS_TOOLS if t["function"]["name"] not in forbidden_tools]
            print(f"[GUARDRAIL] Tier 2 Agent {self.name} restricted to PLANNING tools only.")

        while True:
            print(f"[WORKER] {self.name} (T{self.tier}) thinking about task (Loop)...")
            response = await self.llm.chat_completion(history, tools=available_tools)
            
            # 4. Handle Output
            if response.tool_calls:
                # Store tool calls message in history (required by OpenAI spec)
                history.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in response.tool_calls
                    ]
                })

                # Handle multiple tool calls
                for tool_call in response.tool_calls:
                    # Create a unique correlation ID for this tool call to wait for it
                    # We use the original correlation_id + tool_call_id
                    t_corr_id = f"{correlation_id}:{tool_call.id}"
                    self.pending_tool_results[t_corr_id] = asyncio.get_event_loop().create_future()
                    
                    await self._emit_tool_call(t_corr_id, tool_call, session_id)
                    
                    # Wait for result
                    try:
                        result_payload = await asyncio.wait_for(self.pending_tool_results[t_corr_id], timeout=60.0)
                        result_content = json.dumps(result_payload.get("result", result_payload.get("error", "No result")))
                    except asyncio.TimeoutError:
                        result_content = "Error: Tool execution timed out."
                    finally:
                        del self.pending_tool_results[t_corr_id]

                    # Append tool result to history
                    history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": result_content
                    })
                
                # Continue loop to let LLM process the results
                continue
            else:
                # Final Answer reach - Break Loop
                history.append({"role": "assistant", "content": response.content})
                await self._emit_completion(correlation_id, response.content)
                break

    async def _emit_tool_call(self, correlation_id: str, tool_call: Any, session_id: str):
        # Translate LLM tool call to Harness Event
        try:
            workspace_path = self.active_sessions[session_id].get("workspace_path", ".")
            payload = {
                "command": tool_call.function.name,
                "args": json.loads(tool_call.function.arguments),
                "workspace_path": workspace_path
            }
            print(f"[WORKER] {self.name} calling tool: {payload['command']} (Workspace: {workspace_path})")
            await self.bus.publish(
                topic="tool.execute",
                sender=self.name,
                payload=payload,
                correlation_id=correlation_id
            )
        except Exception as e:
            print(f"[WORKER_ERROR] Failed to parse tool call: {e}")

    async def _emit_completion(self, correlation_id: str, content: str):
        print(f"[WORKER] {self.name} finished task.")
        await self.bus.publish(
            topic="task.completed",
            sender=self.name,
            payload={"answer": content},
            correlation_id=correlation_id
        )
