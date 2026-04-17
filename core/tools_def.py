from typing import List, Dict, Any

# Tool Definitions for OpenAI/Fireworks Function Calling
HARNESS_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "ls",
            "description": "List files in the current workspace or a specific directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The path to list. Defaults to '.' (workspace root)."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cat",
            "description": "Read the content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file to read."}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new file or overwrite an existing one with specific content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "The name of the file to write."},
                    "content": {"type": "string", "description": "The text content to write to the file."}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mkdir",
            "description": "Create a new directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The name of the directory to create."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a bash command in the workspace. Use for complex operations like 'pip install', 'python3 run.py', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to execute."}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_approval",
            "description": "SOLICITA APROVAÇÃO HUMANA (via Hermes). O Lead DEVE usar isso para validar o código do Tier 3 antes da entrega final.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "O que precisa ser aprovado e por que."},
                    "context": {"type": "string", "description": "Snippet ou resumo do código a ser revisado."}
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_task",
            "description": "Delegate a task to a Tier 3 worker or the QA Auditor. You must specify the agent name and the specific instructions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_agent": {"type": "string", "description": "Name of the agent to delegate to (e.g., worker_react, lead_qa_auditor)."},
                    "instruction": {"type": "string", "description": "Detailed specs for the agent to execute."}
                },
                "required": ["target_agent", "instruction"]
            }
        }
    }
]
