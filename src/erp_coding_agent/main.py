from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from .config.settings import get_settings
from .logging.logger import logger
from .error_handling.exceptions import AgentException
from .services.task_manager import get_task_manager
from .api.v1.tasks import router as tasks_router
from .api.v1.health import router as health_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Application starting up...", extra={"agent_state": "INITIALIZING"})
    task_manager = get_task_manager()
    logger.info("Application initialized successfully", extra={"agent_state": "READY"})
    yield
    logger.info("Application shutting down...", extra={"agent_state": "EXITING"})
    # Cancel any running background tasks gracefully
    for task_id in list(task_manager._running_jobs.keys()):
        await task_manager.cancel_task(task_id)

app = FastAPI(
    title="ERP Coding Agent API",
    description="API gateway for the ERP autonomous coding agent.",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AgentException)
async def agent_exception_handler(request, exc: AgentException):
    logger.error(f"Agent Exception: {exc.message}", extra={"exc_info": True})
    return JSONResponse(
        status_code=500,
        content={"message": exc.message, "type": exc.__class__.__name__},
    )

# Root level health for convenience
@app.get("/health")
async def health_check():
    return {"status": "ok", "version": app.version}

# API v1 routers
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(tasks_router)
app.include_router(api_v1_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

