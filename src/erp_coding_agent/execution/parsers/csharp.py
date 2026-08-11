import re
from typing import List, Tuple
from ..models.build_result import BuildError
from ..models.test_result import TestFailure

class CSharpBuildParser:
    def parse(self, stdout: str, stderr: str) -> List[BuildError]:
        errors = []
        combined = stdout + "\n" + stderr
        
        # Matches typical MSBuild error:
        # Program.cs(12,34): error CS0103: The name 'xyz' does not exist in the current context
        # File path can contain spaces and might not have column
        # e.g., File.cs(12): error CS1002: ; expected
        # e.g., File.cs(12,34,12,40): error CS...
        
        # We will parse the standard form: File(line,col): error CODE: Message
        pattern = re.compile(
            r'^\s*(?P<file>[^(]+)\((?P<line>\d+)(?:,(?P<col>\d+))?(?:,\d+,\d+)?\):\s+error\s+(?P<code>[A-Z0-9]+):\s+(?P<msg>.+)$', 
            re.MULTILINE
        )
        
        for match in pattern.finditer(combined):
            line = int(match.group('line')) if match.group('line') else None
            col = int(match.group('col')) if match.group('col') else None
            
            errors.append(BuildError(
                file=match.group('file').strip(),
                line=line,
                column=col,
                code=match.group('code').strip(),
                message=match.group('msg').strip()
            ))
            
        return errors

class CSharpTestParser:
    def parse(self, stdout: str, stderr: str) -> Tuple[int, int, int, List[TestFailure]]:
        combined = stdout + "\n" + stderr
        passed = 0
        failed = 0
        skipped = 0
        failures = []
        
        # Look for summary line:
        # Passed!  - Failed:     0, Passed:    10, Skipped:     0, Total:    10, Duration: ...
        # Failed!  - Failed:     1, Passed:    10, Skipped:     0, Total:    11, Duration: ...
        summary_pattern = re.compile(r'(?:Passed!|Failed!)\s*-\s*Failed:\s*(?P<failed>\d+),\s*Passed:\s*(?P<passed>\d+),\s*Skipped:\s*(?P<skipped>\d+)')
        summary_match = summary_pattern.search(combined)
        
        if summary_match:
            failed = int(summary_match.group('failed'))
            passed = int(summary_match.group('passed'))
            skipped = int(summary_match.group('skipped'))
            
        # Look for specific failures
        # Failed Test.Namespace.Method [XX ms]
        # Error Message:
        #  System.Exception : ...
        # Stack Trace:
        #  at ...
        
        # Simple extraction for demo: lines containing "Failed " followed by test name
        fail_name_pattern = re.compile(r'^\s*Failed\s+(.*?)\s+\[', re.MULTILINE)
        
        for match in fail_name_pattern.finditer(combined):
            failures.append(TestFailure(
                name=match.group(1).strip(),
                message="Check test logs for details." # In a full parser, we'd extract the Error Message block
            ))
            
        return (passed, failed, skipped, failures)
