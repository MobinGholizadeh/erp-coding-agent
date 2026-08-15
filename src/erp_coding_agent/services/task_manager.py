import asyncio
import json
from typing import Dict, List, Optional, Any, AsyncGenerator, Callable
from datetime import datetime, timezone

from ..domain.models import Task, Event, _now_utc
from ..domain.states import TaskStatus, AgentState
from ..agent.controller.agent_controller import AgentController
from ..agent.controller.state_machine import AgentState as ControllerState
from ..llm.client import LLMClient, QwenClient
from ..config.settings import get_settings
from ..tools.registry import ToolRegistry
from ..tools import (
    ReadFileTool, WriteFileTool, CreateFileTool, DeleteFileTool, EditFileTool,
    GitStatusTool, GitDiffTool, GitCheckpointTool, GitRollbackTool,
    SearchCodeTool, FindSymbolTool, FindReferencesTool,
    BuildTool, TestTool, SecurityManager
)

class TaskManager:
    """
    Manages task lifecycle, background execution, cancellation, and event broadcasting.
    """

    def __init__(
        self,
        controller_factory: Optional[Callable[[str], AgentController]] = None,
        llm_client: Optional[LLMClient] = None,
        tool_registry: Optional[ToolRegistry] = None
    ):
        self._tasks: Dict[str, Task] = {}
        self._running_jobs: Dict[str, asyncio.Task] = {}
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._counter: int = 100
        self._controller_factory = controller_factory
        self._llm_client = llm_client
        self._tool_registry = tool_registry
        self._lock = asyncio.Lock()

    def _generate_task_id(self) -> str:
        self._counter += 1
        return f"ERP-{self._counter}"

    def _get_default_controller(self, repo_path: str) -> AgentController:
        if self._controller_factory:
            return self._controller_factory(repo_path)
            
        settings = get_settings()
        llm = self._llm_client or QwenClient(settings.llm)
        
        if self._tool_registry:
            registry = self._tool_registry
        else:
            registry = ToolRegistry()
            security = SecurityManager(repo_settings=settings.repository)
            # Register basic tools
            registry.register(ReadFileTool(security))
            registry.register(WriteFileTool(security))
            registry.register(CreateFileTool(security))
            registry.register(DeleteFileTool(security))
            registry.register(EditFileTool(security))
            registry.register(GitStatusTool(security))
            registry.register(GitDiffTool(security))
            registry.register(GitCheckpointTool(security))
            registry.register(GitRollbackTool(security))
            registry.register(SearchCodeTool(settings.knowledge))
            registry.register(FindSymbolTool(settings.knowledge))
            registry.register(FindReferencesTool(settings.knowledge))
            registry.register(BuildTool(security, settings.build))
            registry.register(TestTool(security, settings.test))

        return AgentController(
            llm_client=llm,
            tool_registry=registry,
            max_attempts=settings.agent.max_attempts
        )

    def create_task(
        self,
        instruction: str,
        repository: str = "/workspace/ERP",
        max_attempts: Optional[int] = None
    ) -> Task:
        task_id = self._generate_task_id()
        settings = get_settings()
        attempts = max_attempts or settings.agent.max_attempts

        task = Task(
            task_id=task_id,
            instruction=instruction,
            repository=repository,
            status=TaskStatus.IDLE,
            max_attempts=attempts
        )

        self._tasks[task_id] = task
        self._subscribers[task_id] = []

        # Emit TASK_CREATED event
        self.emit_event(task_id, "TASK_CREATED", {
            "task_id": task_id,
            "instruction": instruction,
            "repository": repository
        })

        # Start background task execution
        job = asyncio.create_task(self._run_task_job(task_id))
        self._running_jobs[task_id] = job

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    async def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False

        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return False

        job = self._running_jobs.get(task_id)
        if job and not job.done():
            job.cancel()

        task.status = TaskStatus.CANCELLED
        task.updated_at = _now_utc()
        self.emit_event(task_id, "TASK_CANCELLED", {"reason": "User requested cancellation"})
        return True

    def emit_event(self, task_id: str, event_type: str, details: Optional[Dict[str, Any]] = None):
        task = self._tasks.get(task_id)
        payload = details or {}
        event = Event(type=event_type, details=payload)
        
        if task:
            task.events.append(event)
            task.updated_at = _now_utc()

        # Broadcast to active SSE subscriber queues
        queues = self._subscribers.get(task_id, [])
        for q in queues:
            q.put_nowait(event)

    async def subscribe_events(self, task_id: str) -> AsyncGenerator[str, None]:
        task = self._tasks.get(task_id)
        if not task:
            return

        q: asyncio.Queue = asyncio.Queue()
        if task_id not in self._subscribers:
            self._subscribers[task_id] = []
        self._subscribers[task_id].append(q)

        try:
            # Yield initial past events
            for past_event in list(task.events):
                yield self._format_sse(past_event)

            # If task already terminal, close stream
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return

            # Listen for new events
            while True:
                try:
                    event: Event = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield self._format_sse(event)
                    if event.type in ("TASK_COMPLETED", "TASK_FAILED", "TASK_CANCELLED"):
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat comment
                    yield ": ping\n\n"
                    # Check if task finished
                    if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                        break
        finally:
            if task_id in self._subscribers and q in self._subscribers[task_id]:
                self._subscribers[task_id].remove(q)

    def _format_sse(self, event: Event) -> str:
        data = json.dumps({
            "timestamp": event.timestamp.isoformat(),
            "type": event.type,
            "details": event.details
        })
        return f"event: {event.type}\ndata: {data}\n\n"

    async def _run_task_job(self, task_id: str):
        task = self._tasks.get(task_id)
        if not task:
            return

        try:
            task.status = TaskStatus.PLANNING
            task.updated_at = _now_utc()
            self.emit_event(task_id, "PLANNING_STARTED", {"task_id": task_id})

            controller = self._get_default_controller(task.repository)
            
            # Monkey-patch or hook controller state transitions to forward events
            orig_record = controller.state_machine.record_action
            orig_transition = controller.state_machine.transition_to

            def hooked_record(action: str, details: dict):
                orig_record(action, details)
                self.emit_event(task_id, action, details)

            def hooked_transition(next_state: ControllerState, reason: str = ""):
                orig_transition(next_state, reason)
                event_map = {
                    ControllerState.PLANNING: "PLANNING_STARTED",
                    ControllerState.RETRIEVING_CONTEXT: "CONTEXT_RETRIEVED",
                    ControllerState.EXECUTING: "EXECUTION_STARTED",
                    ControllerState.VALIDATING: "VALIDATING_STARTED",
                    ControllerState.COMPLETED: "TASK_COMPLETED",
                    ControllerState.FAILED: "TASK_FAILED",
                    ControllerState.CANCELLED: "TASK_CANCELLED"
                }
                event_name = event_map.get(next_state, "STATE_CHANGED")
                self.emit_event(task_id, event_name, {"state": next_state.value, "reason": reason})

            controller.state_machine.record_action = hooked_record
            controller.state_machine.transition_to = hooked_transition

            task.status = TaskStatus.EXECUTING
            result = await controller.run_task(task.instruction)
            
            task.result = result
            if controller.state_machine.current_state == ControllerState.COMPLETED:
                task.status = TaskStatus.COMPLETED
                self.emit_event(task_id, "TASK_COMPLETED", {"result": result})
            elif controller.state_machine.current_state == ControllerState.CANCELLED:
                task.status = TaskStatus.CANCELLED
                self.emit_event(task_id, "TASK_CANCELLED", {"reason": "Cancelled during execution"})
            else:
                task.status = TaskStatus.FAILED
                self.emit_event(task_id, "TASK_FAILED", {"error": result})

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.updated_at = _now_utc()
            self.emit_event(task_id, "TASK_CANCELLED", {"reason": "Job was cancelled"})
            raise
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.updated_at = _now_utc()
            task.result = str(e)
            self.emit_event(task_id, "TASK_FAILED", {"error": str(e)})
        finally:
            task.updated_at = _now_utc()
            if task_id in self._running_jobs:
                del self._running_jobs[task_id]

    def get_system_status(self) -> Dict[str, Any]:
        active_statuses = {
            TaskStatus.IDLE,
            TaskStatus.PLANNING,
            TaskStatus.RETRIEVING_CONTEXT,
            TaskStatus.EXECUTING,
            TaskStatus.BUILDING,
            TaskStatus.TESTING,
            TaskStatus.ANALYZING_FAILURE,
            TaskStatus.FIXING
        }
        active_count = sum(1 for t in self._tasks.values() if t.status in active_statuses)
        total_count = len(self._tasks)
        agent_state = AgentState.BUSY.value if active_count > 0 else AgentState.READY.value

        return {
            "status": "healthy",
            "agent_state": agent_state,
            "active_tasks": active_count,
            "total_tasks": total_count
        }

# Global singleton instance
_task_manager_instance: Optional[TaskManager] = None

def get_task_manager() -> TaskManager:
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
    return _task_manager_instance

def set_task_manager(tm: TaskManager):
    global _task_manager_instance
    _task_manager_instance = tm
