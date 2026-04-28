"""Password hashing and session token generation."""

import asyncio
import secrets

import bcrypt

from src.core.logging import get_logger

logger = get_logger(__name__)


# --- Password Hashing ---

def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


async def verify_password_async(plain: str, hashed: str) -> bool:
    """Async wrapper for verify_password (avoids greenlet_spawn issues)."""
    return await asyncio.to_thread(verify_password, plain, hashed)


# --- Session Tokens ---

def generate_session_token() -> str:
    """Generate a 64-char hex token for Redis session storage."""
    return secrets.token_hex(32)
