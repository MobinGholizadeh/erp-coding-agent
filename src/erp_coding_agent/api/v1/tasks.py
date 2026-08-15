from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from ...services.task_manager import TaskManager, get_task_manager
from .schemas import (
    CreateTaskRequest,
    CreateTaskResponse,
    TaskResponse,
    CancelTaskResponse,
    EventResponse
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("", response_model=CreateTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    request: CreateTaskRequest,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    Creates and enqueues a new autonomous coding task.
    """
    task = task_manager.create_task(
        instruction=request.instruction,
        repository=request.repository,
        max_attempts=request.max_attempts
    )
    return CreateTaskResponse(
        task_id=task.task_id,
        status=task.status.value.lower()
    )

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    Retrieves the current execution state, plan, changed files, and event history of a task.
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found."
        )
    return TaskResponse(
        task_id=task.task_id,
        instruction=task.instruction,
        repository=task.repository,
        status=task.status.value,
        attempt=task.attempt,
        max_attempts=task.max_attempts,
        plan=task.plan,
        files_changed=task.files_changed,
        errors=task.errors,
        tests=task.tests,
        events=[
            EventResponse(
                timestamp=e.timestamp,
                type=e.type,
                details=e.details
            )
            for e in task.events
        ],
        result=task.result,
        created_at=task.created_at,
        updated_at=task.updated_at
    )

@router.post("/{task_id}/cancel", response_model=CancelTaskResponse)
async def cancel_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    Cancels an active or queued task.
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found."
        )

    success = await task_manager.cancel_task(task_id)
    if not success:
        return CancelTaskResponse(
            task_id=task_id,
            status=task.status.value,
            message=f"Task '{task_id}' is already in terminal state '{task.status.value}'."
        )

    return CancelTaskResponse(
        task_id=task_id,
        status="cancelled",
        message=f"Task '{task_id}' was successfully cancelled."
    )

@router.get("/{task_id}/events")
async def stream_task_events(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """
    Streams Server-Sent Events (SSE) for task lifecycle, tool calls, and LLM progress.
    """
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found."
        )

    return StreamingResponse(
        task_manager.subscribe_events(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
