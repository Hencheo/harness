from typing import List, Dict, Any
from core.store import StateStore

class ToolOffloader:
    def __init__(self, state_store: StateStore, char_limit: int = 10000):
        self.store = state_store
        self.char_limit = char_limit

    async def offload_if_needed(self, agent_id: str, tool_name: str, output: Any) -> Any:
        # We only offload strings for now
        if not isinstance(output, str):
            return output
            
        if len(output) > self.char_limit:
            print(f"[ENGINEERING] Offloading mass output from {tool_name} ({len(output)} chars)")
            state_id = await self.store.set_state(agent_id, "offload", f"tool_out_{tool_name}", output)
            
            # Return a condensed version + reference
            head = output[:1000]
            tail = output[-1000:]
            return (
                f"[OFFLOADED DATA - Reference ID: {state_id}]\n"
                f"Content exceeds limit. Snippet (Head):\n{head}\n"
                "...\n"
                f"Snippet (Tail):\n{tail}\n"
                f"[Use 'read_state' tool with ID {state_id} to see full content]"
            )
        return output

class ContextCompactor:
    def __init__(self, token_limit: int = 30000):
        self.token_limit = token_limit

    def should_compact(self, messages: List[Dict[str, str]], estimate_func: Any) -> bool:
        total_text = "".join([m["content"] for m in messages])
        return estimate_func(total_text) > self.token_limit

    async def compact(self, messages: List[Dict[str, str]], llm_client: Any) -> List[Dict[str, str]]:
        print("[ENGINEERING] Compacting context window...")
        # Keep system prompt and target task
        system_msg = messages[0] if messages[0]["role"] == "system" else None
        
        # Summarize the middle part
        to_summarize = messages[1:-1]
        if not to_summarize:
            return messages
            
        summary_prompt = "Summarize the following interaction history into a concise technical snapshot, preserving state and key facts:"
        summary_input = "\n".join([f"{m['role']}: {m['content']}" for m in to_summarize])
        
        summary_result = await llm_client.chat_completion([
            {"role": "system", "content": "You are a context compactor."},
            {"role": "user", "content": f"{summary_prompt}\n\n{summary_input}"}
        ])
        
        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        new_messages.append({"role": "assistant", "content": f"[Context Compacted Snapshot]: {summary_result.content}"})
        new_messages.append(messages[-1])
        
        return new_messages
