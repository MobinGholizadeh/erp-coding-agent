from pydantic import BaseModel, Field
from typing import List

class TestFailure(BaseModel):
    name: str
    message: str

class TestResult(BaseModel):
    success: bool
    exit_code: int = 0
    duration_ms: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    failures: List[TestFailure] = Field(default_factory=list)
