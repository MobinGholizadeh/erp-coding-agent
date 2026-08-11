from pydantic import BaseModel

class ProcessResult(BaseModel):
    success: bool
    exit_code: int
    duration_ms: int
    stdout: str
    stderr: str
