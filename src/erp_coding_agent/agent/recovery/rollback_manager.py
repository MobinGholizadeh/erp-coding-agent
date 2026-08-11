import logging
from ...tools.registry import ToolRegistry

class RollbackManager:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.logger = logging.getLogger(__name__)

    async def create_checkpoint(self, message: str) -> bool:
        """
        Takes a snapshot of the repository state using the git_checkpoint tool.
        """
        try:
            tool = self.registry.get_tool("git_checkpoint")
            result = await tool.execute(message=message)
            self.logger.info(f"Checkpoint created: {result.message}")
            return result.success
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            return False

    async def rollback(self) -> bool:
        """
        Reverts the repository to the last checkpoint using the git_rollback tool.
        """
        try:
            tool = self.registry.get_tool("git_rollback")
            result = await tool.execute()
            self.logger.warning(f"Rollback executed: {result.message}")
            return result.success
        except Exception as e:
            self.logger.error(f"Failed to rollback: {e}")
            return False
