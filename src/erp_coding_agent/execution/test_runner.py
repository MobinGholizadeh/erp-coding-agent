from typing import List, Any, Optional
import shlex

from .process_runner import ProcessRunner
from .models.test_result import TestResult

class TestRunner:
    def __init__(self, command: str, parser: Any, process_runner: ProcessRunner):
        self.command_parts = shlex.split(command)
        self.parser = parser
        self.runner = process_runner

    async def run(self, extra_args: Optional[List[str]] = None) -> TestResult:
        cmd = list(self.command_parts)
        if extra_args:
            cmd.extend(extra_args)
            
        res = await self.runner.run(cmd)
        passed, failed, skipped, failures = self.parser.parse(res.stdout, res.stderr)
        
        return TestResult(
            success=res.success,
            exit_code=res.exit_code,
            duration_ms=res.duration_ms,
            passed=passed,
            failed=failed,
            skipped=skipped,
            failures=failures
        )
