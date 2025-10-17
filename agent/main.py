"""
Gryt CI Agent - FastAPI Service

Receives job execution requests from main API and runs them in Docker
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, status
from pydantic import BaseModel, Field

from agent.executor import get_executor, JobExecutionError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class JobExecutionRequest(BaseModel):
    """Request to execute a job"""
    job_id: int = Field(..., description="Unique job ID")
    pipeline_b64: str = Field(..., description="Base64-encoded gryt pipeline")
    git_url: Optional[str] = Field(None, description="Git repository URL")
    git_branch: Optional[str] = Field("main", description="Git branch to clone")
    github_token_encrypted: Optional[str] = Field(None, description="Encrypted GitHub token")
    docker_image: Optional[str] = Field(None, description="Docker image to use")
    env_vars: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    cpu_limit: Optional[str] = Field(None, description="CPU limit (e.g., '1.0')")
    memory_limit: Optional[str] = Field(None, description="Memory limit (e.g., '512m')")
    callback_url: Optional[str] = Field(None, description="URL to POST results to")


class JobExecutionResponse(BaseModel):
    """Response from job execution"""
    job_id: int
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    started_at: str
    completed_at: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    docker_available: bool


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    job_id: Optional[int] = None


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    # Startup
    logger.info("Starting Gryt CI Agent...")

    # Initialize executor (verifies Docker connection)
    try:
        executor = get_executor()
        logger.info("Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Gryt CI Agent...")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Gryt CI Agent",
    description="Isolated job execution agent for Gryt CI",
    version="0.1.0",
    lifespan=lifespan
)


# ============================================================================
# Authentication
# ============================================================================

def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify API key from header"""
    expected_key = os.getenv("AGENT_API_KEY")

    if not expected_key:
        logger.error("AGENT_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent not configured properly"
        )

    if x_api_key != expected_key:
        logger.warning(f"Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return x_api_key


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "Gryt CI Agent",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint (no authentication required)"""
    docker_available = False

    try:
        executor = get_executor()
        executor.docker_client.ping()
        docker_available = True
    except Exception as e:
        logger.warning(f"Docker health check failed: {e}")

    return HealthResponse(
        status="healthy" if docker_available else "degraded",
        version="0.1.0",
        docker_available=docker_available
    )


@app.post("/jobs/execute", response_model=JobExecutionResponse)
async def execute_job(
    request: JobExecutionRequest,
    api_key: str = Header(..., alias="X-API-Key")
):
    """
    Execute a job in Docker container

    Requires X-API-Key header for authentication
    """
    # Verify API key
    verify_api_key(api_key)

    logger.info(f"Received job execution request: job_id={request.job_id}")

    try:
        # Get executor
        executor = get_executor()

        # Execute job
        result = executor.execute_job(
            job_id=request.job_id,
            pipeline_b64=request.pipeline_b64,
            git_url=request.git_url,
            git_branch=request.git_branch,
            github_token_encrypted=request.github_token_encrypted,
            docker_image=request.docker_image,
            env_vars=request.env_vars,
            cpu_limit=request.cpu_limit,
            memory_limit=request.memory_limit
        )

        # TODO: If callback_url is provided, POST results to it
        if request.callback_url:
            logger.info(f"Callback URL provided: {request.callback_url} (not implemented yet)")

        return JobExecutionResponse(
            job_id=request.job_id,
            success=result["success"],
            exit_code=result["exit_code"],
            stdout=result["stdout"],
            stderr=result["stderr"],
            duration_seconds=result["duration_seconds"],
            started_at=result["started_at"],
            completed_at=result["completed_at"],
            error=result.get("error")
        )

    except JobExecutionError as e:
        logger.error(f"Job execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job execution failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("AGENT_PORT", "8080"))
    host = os.getenv("AGENT_HOST", "0.0.0.0")

    uvicorn.run(
        "agent.main:app",
        host=host,
        port=port,
        log_level="info"
    )
