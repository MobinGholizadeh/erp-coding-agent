from typing import Optional
from ...execution.build_runner import BuildRunner
from ...execution.test_runner import TestRunner
from ...agent.controller.agent_controller import AgentController
from .rollback_manager import RollbackManager
from .retry_policy import RetryPolicy, RecoveryLimitReached
from .error_classifier import ErrorClassifier
from .error_context import ContextBuilder
import logging

class RecoveryManager:
    def __init__(
        self,
        controller: AgentController,
        build_runner: BuildRunner,
        test_runner: TestRunner,
        rollback_manager: RollbackManager,
        retry_policy: RetryPolicy
    ):
        self.controller = controller
        self.build_runner = build_runner
        self.test_runner = test_runner
        self.rollback = rollback_manager
        self.retry_policy = retry_policy
        self.context_builder = ContextBuilder(controller.registry)
        self.logger = logging.getLogger(__name__)

    async def run_with_recovery(self, original_task: str) -> str:
        self.retry_policy.reset()
        
        # Initial checkpoint
        await self.rollback.create_checkpoint("Pre-task execution")
        
        current_task = original_task
        
        while True:
            try:
                # 1. Execute agent task
                result = await self.controller.run_task(current_task)
                
                # 2. Build Validation
                build_result = await self.build_runner.run()
                if not build_result.success:
                    self.logger.warning("Build failed, initiating recovery.")
                    self.retry_policy.increment()
                    category = ErrorClassifier.classify(build_result)
                    
                    context = await self.context_builder.build(
                        original_task=original_task,
                        current_plan=None, # In a real impl, we'd extract the current plan from state_machine history
                        category=category,
                        previous_attempts=self.retry_policy.current_attempt,
                        build_result=build_result
                    )
                    
                    current_task = f"The previous execution failed with a build error. Please fix it.\n\nContext:\n{context.model_dump_json(indent=2)}"
                    continue

                # 3. Test Validation
                test_result = await self.test_runner.run()
                if not test_result.success:
                    self.logger.warning("Tests failed, initiating recovery.")
                    self.retry_policy.increment()
                    category = ErrorClassifier.classify(test_result)
                    
                    context = await self.context_builder.build(
                        original_task=original_task,
                        current_plan=None,
                        category=category,
                        previous_attempts=self.retry_policy.current_attempt,
                        test_result=test_result
                    )
                    
                    current_task = f"The previous execution failed with a test error. Please fix it.\n\nContext:\n{context.model_dump_json(indent=2)}"
                    continue

                # Success
                return "Task completed and passed all build/test validations."

            except RecoveryLimitReached:
                self.logger.error("Recovery limit reached. Rolling back.")
                await self.rollback.rollback()
                return "Task failed and was rolled back due to unrecoverable errors."
            except Exception as e:
                self.logger.error(f"Unexpected error in recovery loop: {e}", exc_info=True)
                await self.rollback.rollback()
                return f"Task failed unexpectedly: {e}"
