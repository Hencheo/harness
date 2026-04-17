import asyncio
import json
from enum import Enum
from typing import Dict, List, Any, Optional
from core.event_bus import EventBus
from core.store import StateStore
from core.parser import WorkflowDef, TaskDef
from core.policies.guardrails import guardrails
import os

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    STALLED = "STALLED"

class HarnessEngine:
    def __init__(self, event_bus: EventBus, state_store: StateStore):
        self.bus = event_bus
        self.store = state_store
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.blocked_tasks: Dict[str, int] = {} # (wf_id, task_id) -> total_failure_count

    async def start_workflow(self, workflow_def: WorkflowDef):
        workflow_id = f"wf-{workflow_def.name}-{id(workflow_def)}"
        
        # Initialize status for all tasks
        tasks_status = {t.id: TaskStatus.PENDING for t in workflow_def.tasks}
        
        # Create Mission Workspace
        workspace_path = f"/home/hencheo/data/missions/{workflow_id}"
        os.makedirs(workspace_path, exist_ok=True)
        print(f"[ENGINE] Workspace created: {workspace_path}")

        self.active_workflows[workflow_id] = {
            "def": workflow_def,
            "status": tasks_status,
            "results": {},
            "workspace": workspace_path
        }

        # Persist initial state
        await self.store.set_state("engine", workflow_id, "status", tasks_status)

        # Start listening for completion and approval events
        await self.bus.subscribe("tool.execute", self.on_tool_execute)
        await self.bus.subscribe("task.completed", self.on_task_completed)
        await self.bus.subscribe("task.failed", self.on_task_failed)
        await self.bus.subscribe("system.health", self.on_health_ping)
        await self.bus.subscribe("approval.response", self.on_approval_response)
        
        # Trigger initial tasks
        await self._dispatch_available_tasks(workflow_id)
        return workflow_id

    async def start_mission_listener(self):
        """Listens for externally deployed missions via Redis."""
        print("[ENGINE] Mission Listener Active: Monitoring 'harness.mission.deploy'")
        await self.bus.subscribe("harness.mission.deploy", self.on_mission_deploy)
        
        # Start the Watchdog to detect stalled agents
        self._watchdog_task = asyncio.create_task(self._watchdog_loop())

    async def _watchdog_loop(self):
        """Periodically scans for stalled agents and the tasks assigned to them."""
        import time
        while True:
            try:
                await asyncio.sleep(30)
                now = time.time()
                
                # Scan all active agents in the store
                # Note: This requires the store to have a way to list keys, 
                # but for now we'll check agents we know about from current workflows.
                agents_to_check = set()
                for wf in self.active_workflows.values():
                    for task in wf["def"].tasks:
                        agents_to_check.add(task.agent)
                
                for agent in agents_to_check:
                    # Fix: get_latest_state takes (agent_id, key)
                    last_ping_data = await self.store.get_latest_state(agent, "last_ping")
                    if last_ping_data:
                        last_ping = last_ping_data["value"]
                        if (now - float(last_ping)) > 60:
                            # Agent is STALLED
                            await self._handle_stalled_agent(agent)
            except Exception as e:
                print(f"[ENGINE_WATCHDOG_ERROR] {e}")

    async def _handle_stalled_agent(self, agent_name: str):
        """Marks all tasks assigned to the stalled agent as STALLED."""
        for wf_id, wf in self.active_workflows.items():
            for task_id, status in wf["status"].items():
                if status in [TaskStatus.DISPATCHED, TaskStatus.RUNNING]:
                    # Find task def to check agent
                    task_def = next((t for t in wf["def"].tasks if t.id == task_id), None)
                    if task_def and task_def.agent == agent_name:
                        print(f"[ENGINE] [WATCHDOG] Agent {agent_name} stalled. Marking task {task_id} as STALLED.")
                        wf["status"][task_id] = TaskStatus.STALLED
                        await self.bus.publish(
                            topic="engine.status_updated",
                            sender="engine",
                            payload={"wf_id": wf_id, "task_id": task_id, "status": TaskStatus.STALLED},
                            correlation_id=f"{wf_id}:{task_id}"
                        )


    async def on_mission_deploy(self, data: Dict[str, Any]):
        """Callback for when a new mission is requested externally."""
        try:
            payload = data.get("payload", {})
            if "workflow" in payload:
                wf_data = payload["workflow"]
                wf_def = WorkflowDef(**wf_data)
                wf_id = await self.start_workflow(wf_def)
                print(f"[ENGINE] External Mission Deployed: {wf_id}")
                
                # Report back to the bus that mission was received
                await self.bus.publish(
                    topic="harness.mission.acknowledged",
                    sender="engine",
                    payload={"wf_id": wf_id, "status": "started"},
                    correlation_id=data.get("correlation_id")
                )
        except Exception as e:
            print(f"[ENGINE_ERROR] Failed to deploy external mission: {e}")

    async def on_approval_response(self, data: Dict[str, Any]):
        correlation_id = data.get("correlation_id")
        decision = data.get("payload", {}).get("decision")
        
        if not correlation_id or ":" not in correlation_id:
            return

        wf_id, task_id = correlation_id.split(":", 1)
        
        if wf_id in self.active_workflows:
            print(f"[ENGINE] Approval response for {task_id}: {decision}")
            if decision == "granted":
                # Find the task definition
                task_def = next((t for t in self.active_workflows[wf_id]["def"].tasks if t.id == task_id), None)
                if task_def:
                    await self._execute_task(wf_id, task_def)
            else:
                self.active_workflows[wf_id]["status"][task_id] = TaskStatus.FAILED
                self.active_workflows[wf_id]["results"][task_id] = {"error": "Approval Denied"}
                await self.store.set_state("engine", wf_id, f"error_{task_id}", "User denied execution")
                await self._dispatch_available_tasks(wf_id)

    async def on_tool_execute(self, data: Dict[str, Any]):
        """Intercepts 'request_approval' tool from agents."""
        payload = data.get("payload", {})
        command = payload.get("command")
        if command == "request_approval":
            correlation_id = data.get("correlation_id")
            if not correlation_id or ":" not in correlation_id: return
            
            args = payload.get("args", {})
            parts = correlation_id.split(":")
            wf_id = parts[0]
            task_id = parts[1]
            
            print(f"[ENGINE] [HIERARCHY] Agent {data.get('sender')} requesting Human Approval via Hermes.")
            if wf_id in self.active_workflows:
                self.active_workflows[wf_id]["status"][task_id] = TaskStatus.WAITING_APPROVAL
            
            await self.bus.publish(
                topic="approval.requested",
                sender="engine",
                payload={
                    "task_id": task_id, 
                    "reason": args.get("reason"), 
                    "context": args.get("context"),
                    "agent": data.get("sender")
                },
                correlation_id=correlation_id
            )

    async def on_task_failed(self, data: Dict[str, Any]):
        """Handles explicit task failure reports from agents."""
        correlation_id = data.get("correlation_id")
        if not correlation_id or ":" not in correlation_id: return

        wf_id, task_id = correlation_id.split(":", 1)
        payload = data.get("payload", {})
        error_msg = payload.get("error", "Unknown error")
        
        print(f"[ENGINE] [FAILURE] Task {task_id} reported failure: {error_msg}")
        
        if wf_id in self.active_workflows:
            wf = self.active_workflows[wf_id]
            
            # Circuit Breaker Logic
            block_key = f"{wf_id}:{task_id}"
            fail_count = self.blocked_tasks.get(block_key, 0) + 1
            self.blocked_tasks[block_key] = fail_count
            
            if fail_count >= 5:
                print(f"[ENGINE] [CIRCUIT_BREAKER] Task {task_id} BLOCKED after {fail_count} failures.")
                wf["status"][task_id] = TaskStatus.FAILED
                await self.bus.publish(
                    topic="engine.status_updated",
                    sender="engine",
                    payload={"wf_id": wf_id, "task_id": task_id, "status": "BLOCKED"},
                    correlation_id=correlation_id
                )
                return

            retries = wf["results"].get(f"{task_id}_retries", 0)
            
            if retries < 3:
                print(f"[ENGINE] [SRE_RETRY] Scheduling retry {retries+1}/3 for {task_id}...")
                wf["results"][f"{task_id}_retries"] = retries + 1
                wf["status"][task_id] = TaskStatus.PENDING
                
                # Exponential backoff (2^retries seconds)
                await asyncio.sleep(2 ** retries)
                await self._dispatch_available_tasks(wf_id)
            else:
                print(f"[ENGINE] [DLQ] Task {task_id} exceeded max retries. Moving to Dead Letter Queue.")
                wf["status"][task_id] = TaskStatus.FAILED
                await self.bus.publish(
                    topic="task.dlq",
                    sender="engine",
                    payload={"wf_id": wf_id, "task_id": task_id, "error": error_msg, "trace": payload.get("trace")},
                    correlation_id=correlation_id
                )

    async def on_health_ping(self, data: Dict[str, Any]):
        """Updates agent health status in the store."""
        sender = data.get("sender")
        payload = data.get("payload", {})
        # Standardize: agent_id is the agent name, session_id is "global" for heartbeats
        await self.store.set_state(sender, "global", "last_ping", data.get("timestamp"))
        await self.store.set_state(sender, "global", "health", payload.get("status"))

    async def on_task_completed(self, data: Dict[str, Any]):
        correlation_id = data.get("correlation_id")
        if not correlation_id or ":" not in correlation_id:
            return

        wf_id, task_id = correlation_id.split(":", 1)
        
        if wf_id in self.active_workflows:
            wf = self.active_workflows[wf_id]
            task_def = next((t for t in wf["def"].tasks if t.id == task_id), None)
            
            # --- Verification Layer (V) & Ralph Loop ---
            if task_def and hasattr(task_def, "verification_cmd") and task_def.verification_cmd:
                print(f"[ENGINE] [LAYER V] Executing deterministic validation for {task_id}: {task_def.verification_cmd}")
                cmd = task_def.verification_cmd
                workspace_cwd = wf["workspace"]
                
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=workspace_cwd
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    retries = wf["results"].get(f"{task_id}_retries", 0)
                    if retries < getattr(task_def, "max_retries", 3):
                        print(f"[ENGINE] [RALPH LOOP] Validation failed for {task_id}. Re-queueing (Retry {retries+1}/{getattr(task_def, 'max_retries', 3)})")
                        wf["results"][f"{task_id}_retries"] = retries + 1
                        
                        # Add feedback to payload to inform the agent of the error
                        task_def.payload["validation_feedback"] = f"Command failed: {cmd}\nExit Code: {process.returncode}\nSTDOUT:\n{stdout.decode()}\nSTDERR:\n{stderr.decode()}"
                        
                        wf["status"][task_id] = TaskStatus.PENDING
                        await self.bus.publish(
                            topic="engine.status_updated",
                            sender="engine",
                            payload={"wf_id": wf_id, "task_id": task_id, "status": f"RETRY ({retries+1})"},
                            correlation_id=correlation_id
                        )
                        await self._dispatch_available_tasks(wf_id)
                        return
                    else:
                        print(f"[ENGINE] [RALPH LOOP] Max retries reached for {task_id}. Escalating to FAILED.")
                        wf["status"][task_id] = TaskStatus.FAILED
                        wf["results"][task_id] = {"error": "Validation Loop Exhausted", "stdout": stdout.decode(), "stderr": stderr.decode()}
                        await self.bus.publish(
                            topic="engine.status_updated",
                            sender="engine",
                            payload={"wf_id": wf_id, "task_id": task_id, "status": TaskStatus.FAILED},
                            correlation_id=correlation_id
                        )
                        return
                else:
                    print(f"[ENGINE] [LAYER V] Validation passed for {task_id}.")

            print(f"[ENGINE] Task completed: {task_id} in workflow {wf_id}")
            self.active_workflows[wf_id]["status"][task_id] = TaskStatus.COMPLETED
            self.active_workflows[wf_id]["results"][task_id] = data["payload"]
            
            # Persist update
            await self.store.set_state("engine", wf_id, f"result_{task_id}", data["payload"])
            
            await self.bus.publish(
                topic="engine.status_updated",
                sender="engine",
                payload={"wf_id": wf_id, "task_id": task_id, "status": TaskStatus.COMPLETED},
                correlation_id=correlation_id
            )
            
            await self._dispatch_available_tasks(wf_id)

    async def _dispatch_available_tasks(self, wf_id: str):
        wf = self.active_workflows[wf_id]
        wf_def = wf["def"]
        
        all_completed = True
        for task in wf_def.tasks:
            if wf["status"][task.id] != TaskStatus.COMPLETED:
                all_completed = False
                if wf["status"][task.id] == TaskStatus.PENDING:
                    # Check dependencies
                    ready = True
                    for dep in task.depends_on:
                        if wf["status"].get(dep) != TaskStatus.COMPLETED:
                            ready = False
                            break
                    
                    if ready:
                        await self._dispatch_task(wf_id, task)
        
        if all_completed:
            await self._check_ralph_loop(wf_id)

    async def _check_ralph_loop(self, wf_id: str):
        wf = self.active_workflows[wf_id]
        print(f"[ENGINE] Workflow {wf_id} completed. Running Ralph Loop check...")
        
        # Simple heuristic for now: check the result of the last task for 'goal_met'
        # In a real scenario, this would involve an Auditor Agent.
        last_task_id = wf["def"].tasks[-1].id
        last_result = wf["results"].get(last_task_id, {})
        
        goal_met = last_result.get("goal_met", True) # Default to True for now
        
        if not goal_met:
            print(f"[ENGINE] GOAL NOT MET. Re-entering Ralph Loop for {wf_id}...")
            # Reset workflow logic (Simple version: reset all to PENDING)
            for t_id in wf["status"]:
                wf["status"][t_id] = TaskStatus.PENDING
            await self._dispatch_available_tasks(wf_id)
        else:
            print(f"[ENGINE] Goal attained for {wf_id}. Finalized.")

    async def _dispatch_task(self, wf_id: str, task: TaskDef):
        print(f"[ENGINE] Evaluating task: {task.id} (Agent: {task.agent})")
        
        # Security Check (Phase 3: The Shield)
        is_tool = task.agent == "tool_registry" or "command" in task.payload
        if is_tool:
            status, reason = guardrails.is_authorized(task.agent, "execute", task.payload)
            if status == "DENIED":
                print(f"[ENGINE] [SECURITY DENIED] Task {task.id}: {reason}")
                self.active_workflows[wf_id]["status"][task.id] = TaskStatus.FAILED
                self.active_workflows[wf_id]["results"][task.id] = {"error": "Security Denied", "reason": reason}
                await self.store.set_state("engine", wf_id, f"error_{task.id}", reason)
                return
            elif status == "NEEDS_APPROVAL":
                print(f"[ENGINE] [WAITING APPROVAL] Task {task.id}: {reason}")
                self.active_workflows[wf_id]["status"][task.id] = TaskStatus.WAITING_APPROVAL
                await self.bus.publish(
                    topic="approval.requested",
                    sender="engine",
                    payload={"task_id": task.id, "reason": reason, "command": task.payload.get("command")},
                    correlation_id=f"{wf_id}:{task.id}"
                )
                return

        await self._execute_task(wf_id, task)

    async def _execute_task(self, wf_id: str, task: TaskDef):
        is_tool = task.agent == "tool_registry" or "command" in task.payload
        self.active_workflows[wf_id]["status"][task.id] = TaskStatus.DISPATCHED
        
        await self.bus.publish(
            topic="engine.status_updated",
            sender="engine",
            payload={"wf_id": wf_id, "task_id": task.id, "status": TaskStatus.DISPATCHED},
            correlation_id=f"{wf_id}:{task.id}"
        )

        enriched_payload = task.payload.copy()
        enriched_payload["workspace_path"] = self.active_workflows[wf_id]["workspace"]
        
        for dep in task.depends_on:
            enriched_payload[f"prev_{dep}"] = self.active_workflows[wf_id]["results"].get(dep)

        topic = "tool.execute" if is_tool else f"agent.{task.agent}"
        
        await self.bus.publish(
            topic=topic,
            sender="engine",
            payload=enriched_payload,
            correlation_id=f"{wf_id}:{task.id}"
        )
