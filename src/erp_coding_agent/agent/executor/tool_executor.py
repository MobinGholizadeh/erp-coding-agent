from typing import Any, Dict
from pydantic import BaseModel
from ...tools.registry import ToolRegistry

class ToolExecutorError(Exception):
    pass

class ToolExecutor:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Locates the tool in the registry, validates arguments against its schema,
        and executes it, returning a string representation of the result.
        """
        if tool_name == "submit_solution":
            # This is a special virtual tool handled by the loop/controller.
            # If it reaches here, we just return the summary.
            return arguments.get("summary", "Task completed.")

        try:
            tool = self.registry.get_tool(tool_name)
        except KeyError:
            return f"Error: Tool '{tool_name}' not found."

        try:
            # Validate input arguments
            validated_args = tool.input_schema.model_validate(arguments)
        except Exception as e:
            return f"Error validating arguments for '{tool_name}': {str(e)}"

        try:
            # Execute the tool
            # Pydantic v2 model_dump returns a dict of the validated fields
            result = await tool.execute(**validated_args.model_dump())
            
            if isinstance(result, BaseModel):
                return result.model_dump_json()
            return str(result)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"
