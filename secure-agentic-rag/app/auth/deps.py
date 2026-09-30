"""
FastAPI dependency providers for authentication and database access.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import decode_access_token
from app.db.database import Database

# Global DB instance (initialized on app start or lazy loaded)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_db: Optional[Database] = None


def get_db() -> Database:
    """Return the application database singleton."""
    global _db
    if _db is None:
        db_path = _PROJECT_ROOT / "data" / "app.db"
        _db = Database(db_path)
    return _db


security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    """
    Extract and verify the current authenticated user from Bearer token.
    Raises 401 Unauthorized if token is missing or invalid.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Sanitize password hash from user object
    user.pop("password_hash", None)
    return user
