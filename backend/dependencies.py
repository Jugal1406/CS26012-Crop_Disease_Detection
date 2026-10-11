"""
backend/dependencies.py
=======================
FastAPI dependency functions for authentication and security via Clerk.
"""

from typing import Dict, Any, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from clerk_auth import AuthenticationError, verify_clerk_token
from services.auth_service import AuthService


def get_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract Bearer token from the Authorization header.
    Rejects malformed or missing headers with 401 Unauthorized.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[1]


# Alias for test suite compatibility
def verify_firebase_id_token(token: str):
    return verify_clerk_token(token)


async def get_current_user(
    token: str = Depends(get_bearer_token),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts, verifies the Clerk JWT token,
    and returns the local PostgreSQL user profile.
    If the user has authenticated with Clerk but is not yet synced in PostgreSQL,
    it automatically synchronizes the identity idempotently.
    """
    try:
        claims = verify_firebase_id_token(token)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    user = await auth_service.get_user_profile_by_uid(claims["uid"])
    if not user:
        # If user is verified by Clerk but not yet synced locally, sync now
        user = await auth_service.sync_clerk_user(
            token=token,
            display_name=None,
        )

    return user
