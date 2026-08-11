import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic import BaseModel
from typing import List

from erp_coding_agent.agent.recovery.recovery_manager import RecoveryManager
from erp_coding_agent.agent.recovery.rollback_manager import RollbackManager
from erp_coding_agent.agent.recovery.retry_policy import RetryPolicy
from erp_coding_agent.execution.build_runner import BuildRunner
from erp_coding_agent.execution.test_runner import TestRunner
from erp_coding_agent.execution.models.build_result import BuildResult, BuildError
from erp_coding_agent.execution.models.test_result import TestResult
from erp_coding_agent.agent.controller.agent_controller import AgentController
from erp_coding_agent.tools.registry import ToolRegistry
from erp_coding_agent.tools.base import BaseTool, ToolPermission

class DummyCheckpointTool(BaseTool):
    name = "git_checkpoint"
    description = "Dummy checkpoint tool"
    input_schema = BaseModel
    permissions = [ToolPermission.MODIFY_FILES]

    async def execute(self, message: str = ""):
        class Res:
            success = True
            message = "ok"
        return Res()

class DummyRollbackTool(BaseTool):
    name = "git_rollback"
    description = "Dummy rollback tool"
    input_schema = BaseModel
    permissions = [ToolPermission.MODIFY_FILES]

    async def execute(self):
        class Res:
            success = True
            message = "ok"
        return Res()

class DummyDiffTool(BaseTool):
    name = "git_diff"
    description = "Dummy diff tool"
    input_schema = BaseModel
    permissions = [ToolPermission.READ_ONLY]

    async def execute(self):
        return "fake diff"


@pytest.fixture
def mock_registry():
    registry = ToolRegistry()
    registry.register(DummyCheckpointTool())
    registry.register(DummyRollbackTool())
    registry.register(DummyDiffTool())
    return registry


@pytest.mark.asyncio
async def test_recovery_manager_success_after_retry(mock_registry):
    controller = AsyncMock(spec=AgentController)
    controller.registry = mock_registry
    controller.run_task.return_value = "Task finished"
    
    build_runner = AsyncMock(spec=BuildRunner)
    
    # 1st build fails, 2nd build succeeds
    build_runner.run.side_effect = [
        BuildResult(success=False, exit_code=1, duration_ms=100, errors=[BuildError(message="Syntax error")]),
        BuildResult(success=True, exit_code=0, duration_ms=100)
    ]
    
    test_runner = AsyncMock(spec=TestRunner)
    test_runner.run.return_value = TestResult(success=True)
    
    rollback_mgr = RollbackManager(mock_registry)
    # Spy on rollback manager methods to track calls
    rollback_mgr.create_checkpoint = AsyncMock(wraps=rollback_mgr.create_checkpoint)
    rollback_mgr.rollback = AsyncMock(wraps=rollback_mgr.rollback)
    
    retry_policy = RetryPolicy(max_attempts=3)
    
    manager = RecoveryManager(
        controller=controller,
        build_runner=build_runner,
        test_runner=test_runner,
        rollback_manager=rollback_mgr,
        retry_policy=retry_policy
    )
    
    res = await manager.run_with_recovery("Do some work")
    
    assert "Task completed" in res
    assert controller.run_task.call_count == 2
    assert build_runner.run.call_count == 2
    assert test_runner.run.call_count == 1
    rollback_mgr.create_checkpoint.assert_called_once()
    rollback_mgr.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_recovery_manager_rollback_on_max_attempts(mock_registry):
    controller = AsyncMock(spec=AgentController)
    controller.registry = mock_registry
    controller.run_task.return_value = "Task finished"
    
    build_runner = AsyncMock(spec=BuildRunner)
    
    # Build always fails
    build_runner.run.return_value = BuildResult(success=False, exit_code=1, duration_ms=100, errors=[BuildError(message="Syntax error")])
    
    test_runner = AsyncMock(spec=TestRunner)
    test_runner.run.return_value = TestResult(success=True)
    
    rollback_mgr = RollbackManager(mock_registry)
    rollback_mgr.create_checkpoint = AsyncMock(wraps=rollback_mgr.create_checkpoint)
    rollback_mgr.rollback = AsyncMock(wraps=rollback_mgr.rollback)
    
    retry_policy = RetryPolicy(max_attempts=2)
    
    manager = RecoveryManager(
        controller=controller,
        build_runner=build_runner,
        test_runner=test_runner,
        rollback_manager=rollback_mgr,
        retry_policy=retry_policy
    )
    
    res = await manager.run_with_recovery("Do some work")
    
    assert "rolled back" in res
    assert controller.run_task.call_count == 2
    assert build_runner.run.call_count == 2
    rollback_mgr.create_checkpoint.assert_called_once()
    rollback_mgr.rollback.assert_called_once()
