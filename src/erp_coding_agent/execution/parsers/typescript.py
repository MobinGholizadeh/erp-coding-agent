import re
from typing import List, Tuple
from ..models.build_result import BuildError
from ..models.test_result import TestFailure

class TypeScriptBuildParser:
    def parse(self, stdout: str, stderr: str) -> List[BuildError]:
        errors = []
        combined = stdout + "\n" + stderr
        
        # Matches typical tsc error:
        # src/file.ts(10,5): error TS2322: Type 'string' is not assignable to type 'number'.
        pattern = re.compile(
            r'^\s*(?P<file>[^(]+)\((?P<line>\d+),(?P<col>\d+)\):\s+error\s+(?P<code>TS\d+):\s+(?P<msg>.+)$', 
            re.MULTILINE
        )
        
        for match in pattern.finditer(combined):
            errors.append(BuildError(
                file=match.group('file').strip(),
                line=int(match.group('line')),
                column=int(match.group('col')),
                code=match.group('code').strip(),
                message=match.group('msg').strip()
            ))
            
        return errors

class TypeScriptTestParser:
    def parse(self, stdout: str, stderr: str) -> Tuple[int, int, int, List[TestFailure]]:
        combined = stdout + "\n" + stderr
        passed = 0
        failed = 0
        skipped = 0
        failures = []
        
        # Matches Jest summary:
        # Tests:       1 failed, 2 passed, 3 total
        summary_pattern = re.compile(r'Tests:\s+(?:(?P<failed>\d+)\s+failed,?)?\s*(?:(?P<passed>\d+)\s+passed,?)?\s*(?:(?P<total>\d+)\s+total)?')
        summary_match = summary_pattern.search(combined)
        
        if summary_match:
            failed_str = summary_match.group('failed')
            passed_str = summary_match.group('passed')
            
            if failed_str:
                failed = int(failed_str)
            if passed_str:
                passed = int(passed_str)
                
        # Find failed test names
        #  FAIL  src/App.test.tsx
        #   ● renders learn react link
        fail_name_pattern = re.compile(r'^\s*●\s+(.*?)$', re.MULTILINE)
        for match in fail_name_pattern.finditer(combined):
            failures.append(TestFailure(
                name=match.group(1).strip(),
                message="Check jest output for details."
            ))
            
        return (passed, failed, skipped, failures)
