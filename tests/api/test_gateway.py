import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from pydantic import BaseModel

from erp_coding_agent.main import app
from erp_coding_agent.services.task_manager import TaskManager, set_task_manager
from erp_coding_agent.agent.controller.agent_controller import AgentController
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
def mock_task_manager():
    mock_llm = MockLLM()
    registry = ToolRegistry()
    registry.register(DummyTool())

    def controller_factory(repo_path: str):
        return AgentController(
            llm_client=mock_llm,
            tool_registry=registry,
            max_attempts=3
        )

    tm = TaskManager(
        controller_factory=controller_factory,
        llm_client=mock_llm,
        tool_registry=registry
    )
    set_task_manager(tm)
    return tm, mock_llm

@pytest.mark.asyncio
async def test_health_endpoints(mock_task_manager):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Top-level health
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # V1 health
        resp_v1 = await client.get("/api/v1/health")
        assert resp_v1.status_code == 200
        assert resp_v1.json()["status"] == "ok"
        assert resp_v1.json()["version"] == "0.1.0"

        # V1 status
        resp_status = await client.get("/api/v1/status")
        assert resp_status.status_code == 200
        data = resp_status.json()
        assert data["status"] == "healthy"
        assert "active_tasks" in data
        assert "total_tasks" in data

@pytest.mark.asyncio
async def test_create_and_get_task(mock_task_manager):
    tm, mock_llm = mock_task_manager

    # Queue mock responses for execution
    mock_llm.queue_response(LLMResponse(
        content="",
        structured_data={
            "steps": [{"id": 1, "description": "do step", "expected_outcome": "done"}],
            "initial_context_queries": []
        }
    ))
    mock_llm.queue_response(LLMResponse(
        content="",
        structured_data={
            "thought": "All done",
            "tool": "submit_solution",
            "arguments": {"summary": "Completed successfully."}
        }
    ))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create task
        resp = await client.post("/api/v1/tasks", json={
            "instruction": "Add customer discount support",
            "repository": "/workspace/ERP"
        })
        assert resp.status_code == 202
        create_data = resp.json()
        assert "task_id" in create_data
        assert create_data["task_id"].startswith("ERP-")

        task_id = create_data["task_id"]

        # Wait briefly for background execution to finish
        await asyncio.sleep(0.5)

        # 2. Get task
        resp_get = await client.get(f"/api/v1/tasks/{task_id}")
        assert resp_get.status_code == 200
        task_data = resp_get.json()
        assert task_data["task_id"] == task_id
        assert task_data["instruction"] == "Add customer discount support"
        assert task_data["status"] == "COMPLETED"
        assert task_data["result"] == "Completed successfully."
        assert len(task_data["events"]) > 0

@pytest.mark.asyncio
async def test_task_not_found(mock_task_manager):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tasks/NONEXISTENT-999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

@pytest.mark.asyncio
async def test_cancel_task(mock_task_manager):
    tm, _ = mock_task_manager

    # Override controller factory to simulate a long running task
    class SlowController(AgentController):
        async def run_task(self, task: str) -> str:
            await asyncio.sleep(5.0)
            return "Done"

    tm._controller_factory = lambda repo: SlowController(
        llm_client=MockLLM(),
        tool_registry=ToolRegistry()
    )

    task = tm.create_task("Long running task to cancel", "/workspace/ERP")
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Cancel the active task
        resp = await client.post(f"/api/v1/tasks/{task.task_id}/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["task_id"] == task.task_id
        assert data["status"] == "cancelled"

        # Verify task is now CANCELLED
        resp_get = await client.get(f"/api/v1/tasks/{task.task_id}")
        assert resp_get.status_code == 200
        assert resp_get.json()["status"] == "CANCELLED"

        # Cancel again (terminal state)
        resp_again = await client.post(f"/api/v1/tasks/{task.task_id}/cancel")
        assert resp_again.status_code == 200
        assert "already in terminal state" in resp_again.json()["message"]


@pytest.mark.asyncio
async def test_stream_task_events(mock_task_manager):
    tm, mock_llm = mock_task_manager

    # Queue mock responses
    mock_llm.queue_response(LLMResponse(
        content="",
        structured_data={
            "steps": [{"id": 1, "description": "step 1", "expected_outcome": "done"}],
            "initial_context_queries": []
        }
    ))
    mock_llm.queue_response(LLMResponse(
        content="",
        structured_data={
            "thought": "finish",
            "tool": "submit_solution",
            "arguments": {"summary": "Done."}
        }
    ))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/tasks", json={
            "instruction": "Test streaming",
            "repository": "/workspace/ERP"
        })
        task_id = resp.json()["task_id"]

        # Stream events
        async with client.stream("GET", f"/api/v1/tasks/{task_id}/events") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
            
            lines = []
            async for line in response.aiter_lines():
                if line:
                    lines.append(line)
                if any("TASK_COMPLETED" in l for l in lines):
                    break

            assert any("TASK_CREATED" in l for l in lines)
