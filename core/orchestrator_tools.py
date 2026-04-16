from typing import List, Dict, Any

# Ferramentas exclusivas para o Orquestrador (Tier 0 / Hermes)
# Estas ferramentas focam em Auditoria, Governança e Delegação.

ORCHESTRATOR_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "audit_missions",
            "description": "Lista missões existentes em data/missions para evitar reduntância ou duplicidade de trabalho.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_ledger",
            "description": "Lê o Shared Ledger (AGENTS.md) para entender o status atual de todas as tarefas e agentes.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_mission",
            "description": "Inspeciona os detalhes de uma missão específica para retomar o trabalho ou auditar qualidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mission_id": {"type": "string", "description": "ID da missão (ex: wf-LoginDashboard-123)"}
                },
                "required": ["mission_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "deploy_workflow",
            "description": "Dispara um novo Workflow via Engine. Hermes DEVE delegar para um Lead (Tier 2), NUNCA para um Worker (Tier 3) diretamente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nome descritivo do workflow."},
                    "lead_agent": {"type": "string", "enum": ["lead_frontend", "lead_backend", "lead_devops", "lead_data", "lead_security"]},
                    "instruction": {"type": "string", "description": "A instrução técnica detalhada para o Lead."}
                },
                "required": ["name", "lead_agent", "instruction"]
            }
        }
    }
]
