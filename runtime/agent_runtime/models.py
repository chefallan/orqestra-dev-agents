from __future__ import annotations

from typing import Any, Dict, List, Optional

from enum import Enum

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    PRODUCT_MANAGER = "product_manager"
    SYSTEM_ARCHITECT = "system_architect"
    WEBAPP_BUILDER = "webapp_builder"
    SECURITY_AUDITOR = "security_auditor"
    QA_RELIABILITY = "qa_reliability"
    DOCUMENTATION_AGENT = "documentation_agent"
    MEMORY_STEWARD = "memory_steward"


class TaskType(str, Enum):
    ORCHESTRATE_GOAL = "orchestrate_goal"
    PROMPT_ENHANCE = "prompt_enhance"
    CONTEXT_INDEX = "context_index"
    PRODUCT_FRAME = "product_frame"
    ARCHITECTURE_DESIGN = "architecture_design"
    BUILD_SLICE = "build_slice"
    SECURITY_AUDIT = "security_audit"
    QA_VERIFY = "qa_verify"
    DOCS_UPDATE = "docs_update"
    MEMORY_SNAPSHOT = "memory_snapshot"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CreateRunRequest(BaseModel):
    objective: str = Field(min_length=4)
    context: Dict[str, Any] = Field(default_factory=dict)


class EnhancePromptRequest(BaseModel):
    title: str = Field(min_length=3)
    seed_prompt: str = Field(min_length=10)
    target_file: str = ""
    bypass_cooldown: bool = False


class TaskRecord(BaseModel):
    id: str
    run_id: str
    tenant_id: str
    parent_task_id: Optional[str] = None
    depends_on: List[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2
    role: AgentRole
    task_type: TaskType
    objective: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    created_at: str
    updated_at: str


class MemoryUpsertRequest(BaseModel):
    key: str = Field(min_length=3)
    memory_type: str = Field(min_length=2)
    tags: str = ""
    content: str = Field(min_length=1)
    source: str = ""


class RunView(BaseModel):
    run_id: str
    tenant_id: str
    objective: str
    status: TaskStatus
    created_at: str
    updated_at: str
    completed_tasks: int
    failed_tasks: int
    queued_tasks: int
    running_tasks: int
    dead_letter_tasks: int
