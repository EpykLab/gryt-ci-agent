"""
Encryption utilities for the agent

Reuses same encryption logic as main API
"""

from cryptography.fernet import Fernet
from agent.env_loader import get_env


def get_encryption_key() -> bytes:
    """Get encryption key from environment"""
    key_str = get_env("GRYT_ENCRYPTION_KEY", required=True)
    return key_str.encode()


def decrypt_string(encrypted: str) -> str | None:
    """Decrypt a Fernet-encrypted string"""
    if not encrypted:
        return None

    key = get_encryption_key()
    f = Fernet(key)
    decrypted_bytes = f.decrypt(encrypted.encode())
    return decrypted_bytes.decode()
