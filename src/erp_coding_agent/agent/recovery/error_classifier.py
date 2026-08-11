from enum import Enum
from typing import Optional, Union
from ...execution.models.build_result import BuildResult
from ...execution.models.test_result import TestResult

class ErrorCategory(str, Enum):
    COMPILATION = "COMPILATION"
    TYPE_ERROR = "TYPE_ERROR"
    IMPORT_ERROR = "IMPORT_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    TEST_FAILURE = "TEST_FAILURE"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    UNKNOWN = "UNKNOWN"

class ErrorClassifier:
    @staticmethod
    def classify(result: Union[BuildResult, TestResult]) -> ErrorCategory:
        if isinstance(result, TestResult):
            if not result.success:
                return ErrorCategory.TEST_FAILURE
            return ErrorCategory.UNKNOWN

        if isinstance(result, BuildResult):
            if not result.success:
                # A simple heuristic based classifier
                for error in result.errors:
                    msg = error.message.lower()
                    if "import" in msg or "module not found" in msg or "cannot find module" in msg:
                        return ErrorCategory.IMPORT_ERROR
                    if "type" in msg or "assignable" in msg or (error.code and ("CS0029" in error.code or "TS2322" in error.code)):
                        return ErrorCategory.TYPE_ERROR
                    if "namespace" in msg or (error.code and ("CS0246" in error.code or "TS2304" in error.code)):
                        return ErrorCategory.DEPENDENCY_ERROR
                return ErrorCategory.COMPILATION
                
        return ErrorCategory.UNKNOWN
