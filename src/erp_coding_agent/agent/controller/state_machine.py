from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime, timezone

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

class AgentState(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    RETRIEVING_CONTEXT = "RETRIEVING_CONTEXT"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class AgentEvent(BaseModel):
    timestamp: datetime = Field(default_factory=_now_utc)
    event_type: str
    details: Dict[str, Any] = Field(default_factory=dict)

