import pytest
from pydantic import BaseModel
from typing import List, Optional

from erp_coding_agent.agent.controller.agent_controller import AgentController
from erp_coding_agent.agent.controller.state_machine import AgentState
from erp_coding_agent.llm.client import MockLLM
from erp_coding_agent.llm.models import LLMResponse
from erp_coding_agent.tools.registry import ToolRegistry
from erp_coding_agent.tools.base import BaseTool, ToolPermission

class DummyToolInput(BaseModel):
    pass

class DummyToolOutput(BaseModel):
    success: bool

class DummyTool(BaseTool):
    name = "dummy_tool"
    description = "A dummy tool"
    input_schema = DummyToolInput
    output_schema = DummyToolOutput
    permissions = [ToolPermission.READ_ONLY]

    async def execute(self) -> DummyToolOutput:
        return DummyToolOutput(success=True)


@pytest.fixture
def mock_llm():
    return MockLLM()

@pytest.fixture
def tool_registry():
    registry = ToolRegistry()
    registry.register(DummyTool())
    return registry


@pytest.mark.asyncio
async def test_agent_controller_success_flow(mock_llm, tool_registry):
    # 1. Planner Response
    plan_json = {
        "steps": [{"id": 1, "description": "do something", "expected_outcome": "done"}],
        "initial_context_queries": []
    }
    mock_llm.queue_response(LLMResponse(
        content="", 
        structured_data=plan_json
    ))
    
    # 2. Execution Loop - Tool Call
    tool_call_json = {
        "thought": "I should call the dummy tool",
        "tool": "dummy_tool",
        "arguments": {}
    }
    mock_llm.queue_response(LLMResponse(
        content="",
        structured_data=tool_call_json
    ))
    
    # 3. Execution Loop - Submit Solution
    submit_json = {
        "thought": "I am done.",
        "tool": "submit_solution",
        "arguments": {"summary": "Finished."}
    }
    mock_llm.queue_response(LLMResponse(
        content="",
        structured_data=submit_json
    ))
    
    controller = AgentController(llm_client=mock_llm, tool_registry=tool_registry, max_attempts=5)
    
    result = await controller.run_task("Test task")
    
    assert result == "Finished."
    
    # Verify state transitions
    history = controller.state_machine.history
    states = [event.details["to"] for event in history if event.event_type == "STATE_TRANSITION"]
    
    assert states == [
        AgentState.PLANNING.value,
        AgentState.RETRIEVING_CONTEXT.value,
        AgentState.EXECUTING.value,
        AgentState.VALIDATING.value,
        AgentState.COMPLETED.value
    ]
    
    # Verify actions
    actions = [event.event_type for event in history]
    assert "PLAN_GENERATED" in actions
    assert "LLM_THOUGHT" in actions
    assert "TOOL_CALL" in actions
    assert "TOOL_RESULT" in actions
    assert "SUBMIT_SOLUTION_CALLED" in actions

@pytest.mark.asyncio
async def test_agent_controller_max_attempts(mock_llm, tool_registry):
    # 1. Planner Response
    plan_json = {
        "steps": [{"id": 1, "description": "do something", "expected_outcome": "done"}],
        "initial_context_queries": []
    }
    mock_llm.queue_response(LLMResponse(
        content="", 
        structured_data=plan_json
    ))
    
    # Provide no other queued responses; MockLLM will just return defaults (no structured data)
    # This will trigger the loop but fail to find a tool, looping until max_attempts.
    
    controller = AgentController(llm_client=mock_llm, tool_registry=tool_registry, max_attempts=2)
    
    result = await controller.run_task("Test task")
    
    assert "Max attempts" in result
    assert controller.state_machine.current_state == AgentState.FAILED
