from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class CreateTaskRequest(BaseModel):
    instruction: str = Field(..., description="The user or system prompt detailing the coding task.")
    repository: str = Field(default="/workspace/ERP", description="Root repository path for code operations.")
    max_attempts: Optional[int] = Field(default=None, description="Optional maximum execution attempts for this task.")

class CreateTaskResponse(BaseModel):
    task_id: str
    status: str

class EventResponse(BaseModel):
    timestamp: datetime
    type: str
    details: Dict[str, Any] = Field(default_factory=dict)

class TaskResponse(BaseModel):
    task_id: str
    instruction: str
    repository: str
    status: str
    attempt: int = 0
    max_attempts: int = 5
    plan: List[str] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    tests: List[Dict[str, Any]] = Field(default_factory=list)
    events: List[EventResponse] = Field(default_factory=list)
    result: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CancelTaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class HealthResponse(BaseModel):
    status: str
    version: str

class StatusResponse(BaseModel):
    status: str
    agent_state: str
    active_tasks: int
    total_tasks: int
