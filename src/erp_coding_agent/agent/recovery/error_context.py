from pydantic import BaseModel
from typing import Optional, List, Dict
from .error_classifier import ErrorCategory
from ...execution.models.build_result import BuildResult
from ...execution.models.test_result import TestResult
from ...agent.planner.models import Plan
from ...tools.registry import ToolRegistry

class ErrorContext(BaseModel):
    original_task: str
    current_plan: Optional[Plan]
    git_diff: str
    category: ErrorCategory
    build_result: Optional[BuildResult] = None
    test_result: Optional[TestResult] = None
    previous_attempts: int

class ContextBuilder:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def build(
        self, 
        original_task: str, 
        current_plan: Optional[Plan], 
        category: ErrorCategory,
        previous_attempts: int,
        build_result: Optional[BuildResult] = None,
        test_result: Optional[TestResult] = None
    ) -> ErrorContext:
        """
        Gathers contextual information (like diffs) to help the agent fix the error.
        """
        git_diff = ""
        try:
            tool = self.registry.get_tool("git_diff")
            result = await tool.execute()
            git_diff = str(result)
        except Exception:
            git_diff = "Failed to retrieve git diff."

        return ErrorContext(
            original_task=original_task,
            current_plan=current_plan,
            git_diff=git_diff,
            category=category,
            build_result=build_result,
            test_result=test_result,
            previous_attempts=previous_attempts
        )
