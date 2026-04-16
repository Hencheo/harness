from typing import Dict, List, Any, Optional
import shlex

class PolicyEngine:
    def __init__(self):
        # Default policy: Deny all, allow specific
        self.allowed_commands = ["ping", "ls", "cat", "echo", "pwd", "write_file", "mkdir", "run_command", "python3", "pip"]
        self.blocked_patterns = ["rm -rf", "sudo", "chmod", "chown", ">", "|", "&"]

    def is_authorized(self, agent_id: str, action: str, params: Dict[str, Any]) -> tuple[str, str]:
        """
        Validates if an action is authorized.
        Returns (status: "ALLOWED" | "DENIED" | "NEEDS_APPROVAL", reason: str)
        """
        # 1. Check if the tool/action itself is listed
        command = params.get("command", "")
        args = params.get("args", [])
        
        full_command = f"{command} {' '.join(shlex.quote(str(a)) for a in args)}".strip()

        # Rules for Approval (Stateful or sensitive)
        commands_requiring_approval = ["run_command", "cat"] 

        # 2. Block prohibited patterns (Blacklist)
        for pattern in self.blocked_patterns:
            if pattern in full_command:
                return "DENIED", f"Rule Deny: Prohibited pattern '{pattern}' detected in command."

        # 3. Check for specific commands that require manual approval
        if command in commands_requiring_approval:
            return "NEEDS_APPROVAL", f"Rule Approval: Command '{command}' requires human sign-off."

        # 4. Check against allowed command list (Whitelist)
        if command not in self.allowed_commands:
            return "DENIED", f"Rule Deny: Command '{command}' is not in the allowed list for agent {agent_id}."

        return "ALLOWED", "Authorized"

# Singleton instance
guardrails = PolicyEngine()
