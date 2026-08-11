import re
from typing import List, Tuple
from ..models.build_result import BuildError
from ..models.test_result import TestFailure

class GenericBuildParser:
    def parse(self, stdout: str, stderr: str) -> List[BuildError]:
        errors = []
        combined = stdout + "\n" + stderr
        
        # Super generic fallback parser looking for line indicating error
        # Matches formats like:
        # Error: something went wrong
        # ERROR: something went wrong
        # error: something went wrong
        pattern = re.compile(r'^(?i:error):\s+(.*)$', re.MULTILINE)
        
        for match in pattern.finditer(combined):
            errors.append(BuildError(message=match.group(1).strip()))
            
        # If no strict error lines but exit code was non-zero, we might just put the whole stderr
        if not errors and stderr.strip():
            # Don't capture the entire stderr if it's too long, just the first few lines
            errors.append(BuildError(message=stderr.strip()[:500]))
            
        return errors

class GenericTestParser:
    def parse(self, stdout: str, stderr: str) -> Tuple[int, int, int, List[TestFailure]]:
        # Generic fallback, unable to accurately parse pass/fail counts
        # We look for "FAILED" or "error" but stats will likely be 0
        failures = []
        combined = stdout + "\n" + stderr
        
        # Try to find specific test failure blocks if possible, otherwise just generic
        pattern = re.compile(r'(?i:fail(?:ed|ure)?):\s+(.*)$', re.MULTILINE)
        
        for match in pattern.finditer(combined):
            failures.append(TestFailure(name="Unknown", message=match.group(1).strip()))
            
        failed = len(failures)
        return (0, failed, 0, failures)
