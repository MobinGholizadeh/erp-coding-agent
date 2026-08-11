import asyncio
import time
from typing import List
from pathlib import Path

from .models.process_result import ProcessResult

class ProcessExecutionError(Exception):
    pass

class ProcessRunner:
    def __init__(self, cwd: str, timeout_seconds: int = 60, max_output_chars: int = 100000):
        self.cwd = Path(cwd).resolve()
        self.timeout = timeout_seconds
        self.max_output = max_output_chars

    async def run(self, command: List[str]) -> ProcessResult:
        """
        Executes a command safely without shell exposure.
        Enforces timeout and truncates excessive output.
        """
        if not self.cwd.exists() or not self.cwd.is_dir():
            raise ProcessExecutionError(f"Working directory does not exist: {self.cwd}")

        start_time = time.monotonic()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(self.cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                # Cancel the process on timeout
                try:
                    process.terminate()
                    await process.wait()
                except ProcessLookupError:
                    pass
                
                duration_ms = int((time.monotonic() - start_time) * 1000)
                return ProcessResult(
                    success=False,
                    exit_code=-1,
                    duration_ms=duration_ms,
                    stdout="",
                    stderr=f"Process timed out after {self.timeout} seconds."
                )

            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            
            # Truncate if too long
            if len(stdout) > self.max_output:
                stdout = stdout[:self.max_output] + "\n... [Truncated]"
            if len(stderr) > self.max_output:
                stderr = stderr[:self.max_output] + "\n... [Truncated]"

            exit_code = process.returncode or 0
            duration_ms = int((time.monotonic() - start_time) * 1000)
            
            return ProcessResult(
                success=(exit_code == 0),
                exit_code=exit_code,
                duration_ms=duration_ms,
                stdout=stdout,
                stderr=stderr
            )
            
        except Exception as e:
            raise ProcessExecutionError(f"Failed to execute process: {str(e)}") from e
