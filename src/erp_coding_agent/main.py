from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config.settings import get_settings
from .logging.logger import logger
from .domain.models import Task
from .error_handling.exceptions import AgentException

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("Application starting up...", extra={"agent_state": "INITIALIZING"})
    # Initialization logic will go here
    logger.info("Application initialized successfully", extra={"agent_state": "READY"})
    yield
    logger.info("Application shutting down...", extra={"agent_state": "EXITING"})

app = FastAPI(
    title="ERP Coding Agent API",
    description="API gateway for the ERP autonomous coding agent.",
    version="0.1.0",
    lifespan=lifespan
)

@app.exception_handler(AgentException)
async def agent_exception_handler(request, exc: AgentException):
    logger.error(f"Agent Exception: {exc.message}", extra={"exc_info": True})
    return JSONResponse(
        status_code=500,
        content={"message": exc.message, "type": exc.__class__.__name__},
    )

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": app.version}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
