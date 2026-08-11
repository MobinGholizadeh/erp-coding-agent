from pydantic import BaseModel, Field
from typing import List, Optional

class BuildError(BaseModel):
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    code: Optional[str] = None
    message: str

class BuildResult(BaseModel):
    success: bool
    exit_code: int
    duration_ms: int
    errors: List[BuildError] = Field(default_factory=list)
