"""
Encryption utilities for the agent

Reuses same encryption logic as main API
"""

import os
from cryptography.fernet import Fernet


def get_encryption_key() -> bytes:
    """Get encryption key from environment"""
    key_str = os.getenv("GRYT_ENCRYPTION_KEY")

    if not key_str:
        raise ValueError(
            "GRYT_ENCRYPTION_KEY environment variable not set. "
            "This should be the same key used by the main Gryt CI API."
        )

    return key_str.encode()


def decrypt_string(encrypted: str) -> str | None:
    """Decrypt a Fernet-encrypted string"""
    if not encrypted:
        return None

    key = get_encryption_key()
    f = Fernet(key)
    decrypted_bytes = f.decrypt(encrypted.encode())
    return decrypted_bytes.decode()
