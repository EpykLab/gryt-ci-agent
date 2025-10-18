"""
Environment variable loader with fallback to .envrc file
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

_env_cache: Optional[Dict[str, str]] = None


def _load_envrc_file() -> Dict[str, str]:
    """Load environment variables from .envrc file"""
    env_vars = {}
    
    current_dir = Path.cwd()
    envrc_path = current_dir / ".envrc"
    
    # Try parent directories
    if not envrc_path.exists():
        for parent in current_dir.parents:
            candidate = parent / ".envrc"
            if candidate.exists():
                envrc_path = candidate
                break
    
    # Check common installation paths
    if not envrc_path.exists():
        common_paths = [
            Path("/opt/gryt-ci-agent/.envrc"),
            Path.home() / "gryt-ci-agent" / ".envrc",
        ]
        for path in common_paths:
            if path.exists():
                envrc_path = path
                break
    
    if not envrc_path.exists():
        logger.warning("No .envrc file found")
        return env_vars
    
    logger.info(f"Loading environment variables from {envrc_path}")
    
    try:
        with open(envrc_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('export '):
                    line = line[7:]
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if value and value[0] in ('"', "'") and value[-1] == value[0]:
                        value = value[1:-1]
                    
                    env_vars[key] = value
    
    except Exception as e:
        logger.error(f"Error reading .envrc file: {e}")
    
    return env_vars


def get_env(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Get environment variable with fallback to .envrc file"""
    global _env_cache
    
    value = os.getenv(key)
    if value is not None:
        return value
    
    if _env_cache is None:
        _env_cache = _load_envrc_file()
    
    value = _env_cache.get(key)
    if value is not None:
        return value
    
    if required:
        raise ValueError(
            f"{key} environment variable not set. "
            f"Set it in the system environment or in .envrc file."
        )
    
    return default
