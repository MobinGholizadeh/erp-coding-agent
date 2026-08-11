from abc import ABC, abstractmethod
from enum import Enum
from typing import Type, Any, List, Dict
from pydantic import BaseModel

class ToolPermission(str, Enum):
    READ_ONLY = "read_only"
    MODIFY_FILES = "modify_files"
    EXECUTE_COMMANDS = "execute_commands"
    NETWORK_ACCESS = "network_access"

class BaseTool(ABC):
    """Abstract base class for all tools."""
    name: str
    description: str
    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]
    permissions: List[ToolPermission]

    @abstractmethod
    async def execute(self, **kwargs) -> BaseModel:
        """Execute the tool with the given arguments."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema.model_json_schema()
            }
        }
