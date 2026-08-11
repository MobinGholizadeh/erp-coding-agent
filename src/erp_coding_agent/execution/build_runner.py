from typing import List, Any
import shlex

from .process_runner import ProcessRunner
from .models.build_result import BuildResult

class BuildRunner:
    def __init__(self, command: str, parser: Any, process_runner: ProcessRunner):
        self.command_parts = shlex.split(command)
        self.parser = parser
        self.runner = process_runner

    async def run(self) -> BuildResult:
        res = await self.runner.run(self.command_parts)
        errors = self.parser.parse(res.stdout, res.stderr)
        
        return BuildResult(
            success=res.success,
            exit_code=res.exit_code,
            duration_ms=res.duration_ms,
            errors=errors
        )
