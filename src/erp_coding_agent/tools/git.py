from pydantic import BaseModel, Field
from typing import Optional

from .base import BaseTool, ToolPermission
from .security import SecurityManager

class GitStatusInput(BaseModel):
    pass

class GitStatusOutput(BaseModel):
    status: str
    exit_code: int

class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Get the current git status."
    input_schema = GitStatusInput
    output_schema = GitStatusOutput
    permissions = [ToolPermission.READ_ONLY, ToolPermission.EXECUTE_COMMANDS]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self) -> GitStatusOutput:
        code, stdout, stderr = await self.security.run_controlled_command(
            ["git", "status"], 
            cwd=str(self.security.root)
        )
        return GitStatusOutput(status=stdout if code == 0 else stderr, exit_code=code)


class GitDiffInput(BaseModel):
    pass

class GitDiffOutput(BaseModel):
    diff: str
    exit_code: int

class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "Get the current git diff."
    input_schema = GitDiffInput
    output_schema = GitDiffOutput
    permissions = [ToolPermission.READ_ONLY, ToolPermission.EXECUTE_COMMANDS]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self) -> GitDiffOutput:
        code, stdout, stderr = await self.security.run_controlled_command(
            ["git", "diff"], 
            cwd=str(self.security.root)
        )
        return GitDiffOutput(diff=stdout if code == 0 else stderr, exit_code=code)


class GitCheckpointInput(BaseModel):
    message: str = Field(description="The commit message for the checkpoint.")

class GitCheckpointOutput(BaseModel):
    success: bool
    output: str

class GitCheckpointTool(BaseTool):
    name = "git_checkpoint"
    description = "Create a git checkpoint (add all and commit)."
    input_schema = GitCheckpointInput
    output_schema = GitCheckpointOutput
    permissions = [ToolPermission.MODIFY_FILES, ToolPermission.EXECUTE_COMMANDS]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self, message: str) -> GitCheckpointOutput:
        # Add all
        add_code, add_out, add_err = await self.security.run_controlled_command(
            ["git", "add", "."], 
            cwd=str(self.security.root)
        )
        if add_code != 0:
            return GitCheckpointOutput(success=False, output=f"Failed to add: {add_err}")
            
        # Commit
        commit_code, commit_out, commit_err = await self.security.run_controlled_command(
            ["git", "commit", "-m", message], 
            cwd=str(self.security.root)
        )
        
        # Git commit returns 1 if nothing to commit
        success = commit_code == 0 or "nothing to commit" in commit_out
        return GitCheckpointOutput(success=success, output=commit_out if success else commit_err)


class GitRollbackInput(BaseModel):
    commit_hash: Optional[str] = Field(default=None, description="The commit hash to rollback to. Defaults to HEAD.")

class GitRollbackOutput(BaseModel):
    success: bool
    output: str

class GitRollbackTool(BaseTool):
    name = "git_rollback"
    description = "Rollback changes (git reset --hard)."
    input_schema = GitRollbackInput
    output_schema = GitRollbackOutput
    permissions = [ToolPermission.MODIFY_FILES, ToolPermission.EXECUTE_COMMANDS]

    def __init__(self, security: SecurityManager):
        self.security = security

    async def execute(self, commit_hash: Optional[str] = None) -> GitRollbackOutput:
        target = commit_hash if commit_hash else "HEAD"
        code, stdout, stderr = await self.security.run_controlled_command(
            ["git", "reset", "--hard", target], 
            cwd=str(self.security.root)
        )
        
        return GitRollbackOutput(success=(code == 0), output=stdout if code == 0 else stderr)
