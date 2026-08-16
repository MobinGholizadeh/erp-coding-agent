from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    id: Optional[str] = None
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None

class SymbolReference(BaseModel):
    source: str
    source_label: str
    type: str

class DependencyInfo(BaseModel):
    target: str
    target_label: str
    type: str
    
class ContextResponse(BaseModel):
    context: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
