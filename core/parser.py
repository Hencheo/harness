import yaml
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
# I'll implement a simple cycle check manually 
# to keep it lightweight as per "altissima precisão" and minimal dependencies.

class TaskDef(BaseModel):
    id: str
    agent: str
    payload: Dict[str, Any] = {}
    depends_on: List[str] = []

class WorkflowDef(BaseModel):
    name: str
    tasks: List[TaskDef]

    @field_validator("tasks")
    @classmethod
    def check_cycles(cls, v: List[TaskDef]) -> List[TaskDef]:
        adj = {t.id: t.depends_on for t in v}
        visited = set()
        path = set()

        def visit(node):
            if node in path:
                raise ValueError(f"Cycle detected involving task: {node}")
            if node in visited:
                return
            path.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in adj:
                    raise ValueError(f"Task '{node}' depends on unknown task: '{neighbor}'")
                visit(neighbor)
            path.remove(node)
            visited.add(node)

        for task in adj:
            visit(task)
        return v

def load_workflow(path: str) -> WorkflowDef:
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return WorkflowDef(**data)
