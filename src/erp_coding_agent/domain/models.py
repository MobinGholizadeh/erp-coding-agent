from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from .states import TaskStatus

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

class Event(BaseModel):
    timestamp: datetime = Field(default_factory=_now_utc)
    type: str
    details: Dict[str, Any] = Field(default_factory=dict)

class Task(BaseModel):
    task_id: str
    instruction: str
    repository: str
    status: TaskStatus = Field(default=TaskStatus.IDLE)
    attempt: int = Field(default=0)
    max_attempts: int = Field(default=5)
    plan: List[str] = Field(default_factory=list)
    files_changed: List[str] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    tests: List[Dict[str, Any]] = Field(default_factory=list)
    events: List[Event] = Field(default_factory=list)
    result: Optional[str] = None
    created_at: datetime = Field(default_factory=_now_utc)
    updated_at: datetime = Field(default_factory=_now_utc)

