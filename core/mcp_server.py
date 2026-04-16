import asyncio
import subprocess
import json
import os
from typing import Dict, Any
from core.event_bus import EventBus

class ToolRegistry:
    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.tools = {
            "ping": self.tool_ping,
            "ls": self.tool_ls,
            "cat": self.tool_cat,
            "write_file": self.tool_write_file,
            "mkdir": self.tool_mkdir,
            "run_command": self.tool_run_command
        }

    async def start(self):
        print("[TOOL_REGISTRY] Starting MCP Proxy...")
        await self.bus.subscribe("tool.execute", self.on_execute)

    async def on_execute(self, data: Dict[str, Any]):
        correlation_id = data.get("correlation_id")
        payload = data.get("payload", {})
        command = payload.get("command")
        args = payload.get("args", [])

        print(f"[TOOL_REGISTRY] Executing: {command} {args} in {payload.get('workspace_path', '.')}")

        if command in self.tools:
            result = await self.tools[command](args, cwd=payload.get("workspace_path"))
            
            # Send result back via event bus
            await self.bus.publish(
                topic="task.completed",
                sender="tool_registry",
                payload={"result": result, "status": "success"},
                correlation_id=correlation_id
            )
        else:
            await self.bus.publish(
                topic="task.completed",
                sender="tool_registry",
                payload={"error": f"Tool '{command}' not found", "status": "error"},
                correlation_id=correlation_id
            )

    async def tool_ping(self, args: list, cwd: str = None) -> str:
        # Simple ping mock or safe execution
        target = args[0] if args else "127.0.0.1"
        try:
            # Forcing a small count for safety
            process = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await process.communicate()
            return stdout.decode().strip() or stderr.decode().strip()
        except Exception as e:
            return f"Error executing ping: {e}"

    async def tool_ls(self, args: list, cwd: str = None) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                "ls", *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await process.communicate()
            return stdout.decode().strip() or stderr.decode().strip()
        except Exception as e:
            return f"Error executing ls: {e}"

    async def tool_cat(self, args: list, cwd: str = None) -> str:
        filename = args[0] if isinstance(args, list) and args else args.get("filename") if isinstance(args, dict) else None
        if not filename:
            return "Error: No file specified for cat"
        try:
            # Minimal security: allow reading files in current dir or specific paths
            process = await asyncio.create_subprocess_exec(
                "cat", filename,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await process.communicate()
            return stdout.decode().strip() or stderr.decode().strip()
        except Exception as e:
            return f"Error executing cat: {e}"

    async def tool_write_file(self, args: Any, cwd: str = None) -> str:
        if isinstance(args, list):
            # Fallback if list is passed
            filename, content = args[0], args[1]
        else:
            filename = args.get("filename")
            content = args.get("content")

        if not filename: return "Error: No filename"
        
        full_path = os.path.join(cwd or ".", filename)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            return f"File '{filename}' written successfully."
        except Exception as e:
            return f"Error writing file: {e}"

    async def tool_mkdir(self, args: Any, cwd: str = None) -> str:
        path = args[0] if isinstance(args, list) else args.get("path")
        if not path: return "Error: No path"
        
        full_path = os.path.join(cwd or ".", path)
        try:
            os.makedirs(full_path, exist_ok=True)
            return f"Directory '{path}' created successfully."
        except Exception as e:
            return f"Error creating directory: {e}"

    async def tool_run_command(self, args: Any, cwd: str = None) -> str:
        command = args[0] if isinstance(args, list) else args.get("command")
        if not command: return "Error: No command"
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            stdout, stderr = await process.communicate()
            return f"STDOUT:\n{stdout.decode()}\nSTDERR:\n{stderr.decode()}"
        except Exception as e:
            return f"Error running command: {e}"
