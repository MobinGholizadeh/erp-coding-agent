import pytest
from pydantic import BaseModel
from typing import List
from erp_coding_agent.tools.base import BaseTool, ToolPermission
from erp_coding_agent.tools.registry import ToolRegistry

class DummyInput(BaseModel):
    arg1: str

class DummyOutput(BaseModel):
    res: str

class DummyTool(BaseTool):
    name = "dummy"
    description = "A dummy tool."
    input_schema = DummyInput
    output_schema = DummyOutput
    permissions = [ToolPermission.READ_ONLY]

    async def execute(self, arg1: str) -> DummyOutput:
        return DummyOutput(res=arg1)

def test_registry():
    registry = ToolRegistry()
    tool = DummyTool()
    
    registry.register(tool)
    
    assert registry.get_tool("dummy") == tool
    assert len(registry.get_all_tools()) == 1
    
    with pytest.raises(ValueError):
        registry.register(tool) # Already registered
        
    with pytest.raises(KeyError):
        registry.get_tool("nonexistent")

def test_registry_schemas():
    registry = ToolRegistry()
    registry.register(DummyTool())
    
    schemas = registry.get_all_schemas()
    assert len(schemas) == 1
    
    schema = schemas[0]
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "dummy"
    assert "arg1" in schema["function"]["parameters"]["properties"]
