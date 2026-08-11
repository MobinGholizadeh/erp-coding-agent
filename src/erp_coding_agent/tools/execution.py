from pydantic import BaseModel
import shlex

from .base import BaseTool, ToolPermission
from .security import SecurityManager
from ..config.settings import BuildSettings, TestSettings

class BuildInput(BaseModel):
    pass

class BuildOutput(BaseModel):
    success: bool
    output: str

class BuildTool(BaseTool):
    name = "build"
    description = "Compile or build the project."
    input_schema = BuildInput
    output_schema = BuildOutput
    permissions = [ToolPermission.EXECUTE_COMMANDS]

    def __init__(self, security: SecurityManager, build_settings: BuildSettings):
        self.security = security
        self.command = shlex.split(build_settings.command)

    async def execute(self) -> BuildOutput:
        code, stdout, stderr = await self.security.run_controlled_command(
            self.command, 
            cwd=str(self.security.root)
        )
        return BuildOutput(success=(code == 0), output=stdout if code == 0 else stderr)


class TestInput(BaseModel):
    pass

class TestOutput(BaseModel):
    success: bool
    output: str

class TestTool(BaseTool):
    name = "test"
    description = "Run the project's test suite."
    input_schema = TestInput
    output_schema = TestOutput
    permissions = [ToolPermission.EXECUTE_COMMANDS]

    def __init__(self, security: SecurityManager, test_settings: TestSettings):
        self.security = security
        self.command = shlex.split(test_settings.command)

    async def execute(self) -> TestOutput:
        code, stdout, stderr = await self.security.run_controlled_command(
            self.command, 
            cwd=str(self.security.root)
        )
        return TestOutput(success=(code == 0), output=stdout if code == 0 else stderr)
