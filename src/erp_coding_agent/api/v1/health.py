from fastapi import APIRouter, Depends
from ...services.task_manager import TaskManager, get_task_manager
from .schemas import HealthResponse, StatusResponse

router = APIRouter(tags=["Health & Status"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for the AI Gateway."""
    return HealthResponse(status="ok", version="0.1.0")

@router.get("/status", response_model=StatusResponse)
async def get_system_status(task_manager: TaskManager = Depends(get_task_manager)):
    """Provides current agent operational status and active background workload."""
    stats = task_manager.get_system_status()
    return StatusResponse(**stats)
