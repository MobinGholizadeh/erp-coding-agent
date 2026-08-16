from enum import Enum
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class ToolCallFunction(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: ToolCallFunction

class Message(BaseModel):
    role: Role
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class ToolFunction(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]

class Tool(BaseModel):
    type: str = "function"
    function: ToolFunction

class LLMRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    model: Optional[str] = None
    response_format: Optional[Dict[str, Any]] = None
    tools: Optional[List[Tool]] = None

class LLMResponse(BaseModel):
    content: Optional[str] = None
    usage: TokenUsage = Field(default_factory=TokenUsage)
    structured_data: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[ToolCall]] = None
    model: Optional[str] = None
