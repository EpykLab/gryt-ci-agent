"""
Job execution engine for the agent

Executes jobs in isolated Docker containers
"""

import os
import base64
import tempfile
import shutil
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import docker
from docker.errors import DockerException, ImageNotFound, ContainerError
from git import Repo
from git.exc import GitCommandError

from agent.crypto import decrypt_string

logger = logging.getLogger(__name__)


def _clean_json_output(output: str) -> str:
    """
    Clean up JSON output by parsing and re-formatting.
    If output is valid JSON, return it compactly formatted.
    Otherwise, return the original output.
    """
    try:
        parsed = json.loads(output.strip())
        return json.dumps(parsed, separators=(',', ':'))
    except (json.JSONDecodeError, ValueError):
        # Not JSON, return as-is
        return output


def _fix_permissions_recursive(path: Path):
    """
    Fix permissions recursively on a directory to allow deletion.
    Docker creates files as root, so we need to chmod them before deletion.
    """
    import subprocess
    try:
        # Use chmod to recursively fix permissions
        result = subprocess.run(
            ['chmod', '-R', 'u+rwX', str(path)],
            check=True,
            capture_output=True,
            timeout=30
        )
        logger.debug(f"Fixed permissions on {path}")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        # If chmod fails, try with sudo (for local testing)
        # In production, the agent should have proper permissions
        logger.warning(f"chmod failed, trying with sudo: {e}")
        try:
            result = subprocess.run(
                ['sudo', '-n', 'chmod', '-R', 'u+rwX', str(path)],
                check=True,
                capture_output=True,
                timeout=30
            )
            logger.debug(f"Fixed permissions on {path} with sudo")
        except Exception as e2:
            # Last resort: ignore permission errors
            logger.warning(f"Failed to fix permissions even with sudo: {e2}")
            pass


class JobExecutionError(Exception):
    """Raised when job execution fails"""
    pass


class DockerJobExecutor:
    """Executes jobs in Docker containers"""

    def __init__(
        self,
        docker_client: Optional[docker.DockerClient] = None,
        workspace_dir: str = "/tmp/gryt-agent-jobs",
        default_image: str = "ghcr.io/epyklab/gryt/pipeline:latest"
    ):
        """
        Initialize Docker job executor

        Args:
            docker_client: Docker client (if None, will create one)
            workspace_dir: Base directory for job workspaces
            default_image: Default Docker image for jobs
        """
        self.docker_client = docker_client or docker.from_env()
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.default_image = default_image

        # Verify Docker is accessible
        try:
            self.docker_client.ping()
            logger.info("Docker connection established")
        except DockerException as e:
            raise JobExecutionError(f"Failed to connect to Docker: {e}")

    def execute_job(
        self,
        job_id: int,
        pipeline_b64: str,
        git_url: Optional[str] = None,
        git_branch: Optional[str] = "main",
        github_token_encrypted: Optional[str] = None,
        docker_image: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        cpu_limit: Optional[str] = None,
        memory_limit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a job in a Docker container

        Args:
            job_id: Unique job ID
            pipeline_b64: Base64-encoded gryt pipeline
            git_url: Optional Git repository URL
            git_branch: Branch to clone
            github_token_encrypted: Encrypted GitHub token
            docker_image: Docker image to use (default: self.default_image)
            env_vars: Environment variables to pass to container
            cpu_limit: CPU limit (e.g., "1.0" for 1 CPU)
            memory_limit: Memory limit (e.g., "512m")

        Returns:
            Dict with execution results
        """
        workspace = None
        container = None
        start_time = datetime.utcnow()

        try:
            # Create workspace
            workspace = self._create_workspace(job_id)
            logger.info(f"[Job {job_id}] Created workspace: {workspace}")

            # Clone repository if specified
            if git_url:
                self._clone_repository(
                    workspace=workspace,
                    git_url=git_url,
                    branch=git_branch,
                    github_token_encrypted=github_token_encrypted
                )
                logger.info(f"[Job {job_id}] Cloned repository")

            # Write pipeline file
            self._write_pipeline_file(workspace, pipeline_b64)
            logger.info(f"[Job {job_id}] Wrote pipeline file")

            # Pull Docker image
            image = docker_image or self.default_image
            self._ensure_image(image)

            # Run job in container
            result = self._run_in_container(
                job_id=job_id,
                workspace=workspace,
                image=image,
                env_vars=env_vars or {},
                cpu_limit=cpu_limit,
                memory_limit=memory_limit
            )

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            logger.info(
                f"[Job {job_id}] Completed in {duration:.2f}s. "
                f"Exit code: {result['exit_code']}"
            )

            result["duration_seconds"] = duration
            result["started_at"] = start_time.isoformat()
            result["completed_at"] = end_time.isoformat()

            return result

        except Exception as e:
            logger.error(f"[Job {job_id}] Execution failed: {e}")
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "duration_seconds": duration,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "error": str(e)
            }

        finally:
            # Cleanup
            if workspace and workspace.exists():
                try:
                    # Fix permissions before deletion (Docker creates files as root)
                    _fix_permissions_recursive(workspace)
                    shutil.rmtree(workspace)
                    logger.info(f"[Job {job_id}] Cleaned up workspace")
                except Exception as e:
                    logger.warning(f"[Job {job_id}] Failed to cleanup workspace: {e}")

    def _create_workspace(self, job_id: int) -> Path:
        """Create temporary workspace for job"""
        workspace = self.workspace_dir / f"job-{job_id}-{datetime.utcnow().timestamp()}"
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def _clone_repository(
        self,
        workspace: Path,
        git_url: str,
        branch: str,
        github_token_encrypted: Optional[str]
    ):
        """Clone Git repository into workspace"""
        # Decrypt token if provided
        git_url_with_auth = git_url
        if github_token_encrypted:
            try:
                token = decrypt_string(github_token_encrypted)
                if git_url.startswith("https://"):
                    git_url_with_auth = git_url.replace("https://", f"https://{token}@")
            except Exception as e:
                logger.warning(f"Failed to decrypt GitHub token: {e}")

        repo_path = workspace / "repo"
        logger.info(f"Cloning {git_url} (branch: {branch}) to {repo_path}")
        
        try:
            repo = Repo.clone_from(
                url=git_url_with_auth,
                to_path=str(repo_path),
                branch=branch,
                depth=1
            )
            
            # Verify clone was successful
            if not repo_path.exists() or not (repo_path / ".git").exists():
                raise JobExecutionError(f"Clone completed but repository directory is invalid")
            
            # Count files to verify content
            file_count = len(list(repo_path.rglob("*")))
            logger.info(f"Successfully cloned repository with {file_count} files/directories")
            
        except GitCommandError as e:
            raise JobExecutionError(f"Failed to clone repository (GitCommandError): {e}")
        except Exception as e:
            logger.error(f"Unexpected error during clone: {type(e).__name__}: {e}")
            raise JobExecutionError(f"Failed to clone repository: {e}")

    def _write_pipeline_file(self, workspace: Path, pipeline_b64: str):
        """Write decoded pipeline to workspace"""
        try:
            pipeline_content = base64.b64decode(pipeline_b64).decode('utf-8')

            # If repo was cloned, write to repo dir, otherwise workspace root
            repo_dir = workspace / "repo"
            target_dir = repo_dir if repo_dir.exists() else workspace

            # Create .gryt directory for database
            (target_dir / ".gryt").mkdir(exist_ok=True)

            # Write pipeline as Python file (gryt expects .py files)
            pipeline_file = target_dir / "pipeline.py"
            pipeline_file.write_text(pipeline_content)
        except Exception as e:
            raise JobExecutionError(f"Failed to write pipeline file: {e}")

    def _ensure_image(self, image: str):
        """Ensure Docker image is available (pull if needed)"""
        try:
            self.docker_client.images.get(image)
            logger.info(f"Image {image} already exists")
        except ImageNotFound:
            logger.info(f"Pulling image {image}...")
            try:
                self.docker_client.images.pull(image)
                logger.info(f"Image {image} pulled successfully")
            except DockerException as e:
                raise JobExecutionError(f"Failed to pull image {image}: {e}")

    def _run_in_container(
        self,
        job_id: int,
        workspace: Path,
        image: str,
        env_vars: Dict[str, str],
        cpu_limit: Optional[str],
        memory_limit: Optional[str]
    ) -> Dict[str, Any]:
        """Execute gryt in Docker container"""

        # Determine working directory
        repo_dir = workspace / "repo"
        work_dir = repo_dir if repo_dir.exists() else workspace

        # Container configuration
        command = ["gryt", "run", "pipeline.py"]

        volumes = {
            str(work_dir): {"bind": "/workspace", "mode": "rw"}
        }

        environment = {
            "GRYT_WORKSPACE": "/workspace",
            **env_vars
        }

        # Resource limits
        host_config_kwargs = {}
        if cpu_limit:
            # CPU limit as nano CPUs (1 CPU = 1e9 nano CPUs)
            host_config_kwargs["nano_cpus"] = int(float(cpu_limit) * 1e9)
        if memory_limit:
            host_config_kwargs["mem_limit"] = memory_limit

        try:
            # Run container
            container = self.docker_client.containers.run(
                image=image,
                command=command,
                volumes=volumes,
                environment=environment,
                working_dir="/workspace",
                detach=False,
                remove=True,
                stdout=True,
                stderr=True,
                **host_config_kwargs
            )

            # Container ran successfully
            output = container.decode('utf-8') if isinstance(container, bytes) else str(container)
            # Clean up JSON output if applicable
            clean_output = _clean_json_output(output)

            return {
                "success": True,
                "exit_code": 0,
                "stdout": clean_output,
                "stderr": ""
            }

        except ContainerError as e:
            # Container exited with non-zero exit code
            logger.warning(f"[Job {job_id}] Container exited with code {e.exit_status}")

            stdout = e.stderr.decode('utf-8') if e.stderr else ""

            return {
                "success": False,
                "exit_code": e.exit_status,
                "stdout": stdout,
                "stderr": stdout
            }

        except DockerException as e:
            raise JobExecutionError(f"Docker execution failed: {e}")


# Singleton executor
_executor = None


def get_executor() -> DockerJobExecutor:
    """Get or create singleton executor"""
    global _executor
    if _executor is None:
        default_image = os.getenv("GRYT_DOCKER_IMAGE", "ghcr.io/epyklab/gryt/pipeline:latest")
        _executor = DockerJobExecutor(default_image=default_image)
    return _executor
