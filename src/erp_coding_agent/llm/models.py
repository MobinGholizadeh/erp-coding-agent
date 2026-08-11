from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    role: Role
    content: str

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class LLMRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None

class LLMResponse(BaseModel):
    content: str
    usage: TokenUsage = Field(default_factory=TokenUsage)
    structured_data: Optional[Dict[str, Any]] = None
