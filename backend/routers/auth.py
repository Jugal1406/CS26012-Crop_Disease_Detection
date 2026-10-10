"""
backend/routers/auth.py
=======================
Authentication endpoints for Clerk user synchronization and session verification.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_bearer_token, get_current_user
from clerk_auth import AuthenticationError
from services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class UserSyncRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field("en", max_length=10)


class UserProfileResponse(BaseModel):
    id: str
    auth_provider: str
    auth_provider_user_id: str
    display_name: Optional[str]
    email: Optional[str]
    phone_number: Optional[str]
    preferred_language: str
    is_active: bool
    created_at: Optional[str]


class AuthSyncResponse(BaseModel):
    status: str
    message: str
    user: UserProfileResponse


@router.post(
    "/sync",
    response_model=AuthSyncResponse,
    summary="Synchronize authenticated Clerk user with PostgreSQL",
    description=(
        "Verifies the Clerk JWT session token in the Authorization header. "
        "Finds or creates the user in PostgreSQL and stores their display name."
    ),
)
async def sync_user(
    body: Optional[UserSyncRequest] = None,
    token: str = Depends(get_bearer_token),
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(db)
    display_name = body.display_name if body else None
    preferred_lang = body.preferred_language if body and body.preferred_language else "en"

    try:
        user_data = await auth_service.sync_clerk_user(
            token=token,
            display_name=display_name,
            preferred_language=preferred_lang,
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synchronize user profile: {str(exc)}",
        )

    return AuthSyncResponse(
        status="success",
        message="User profile synchronized successfully",
        user=UserProfileResponse(**user_data),
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current authenticated user profile",
    description="Returns the current user profile from PostgreSQL after verifying the Clerk session token.",
)
async def get_me(
    current_user: dict = Depends(get_current_user),
):
    return UserProfileResponse(**current_user)


class LanguagePreferenceRequest(BaseModel):
    preferred_language: str = Field(
        ...,
        max_length=10,
        description="Preferred language code: 'en', 'hi', or 'gu'",
        examples=["hi"],
    )


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    preferred_language: Optional[str] = Field(None, max_length=10)


@router.patch(
    "/profile",
    response_model=UserProfileResponse,
    summary="Update authenticated user profile",
    description="Updates user display name, phone number, and preferred language. Email is read-only.",
)
@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="Update authenticated user profile (alias)",
    description="Updates user display name, phone number, and preferred language.",
    include_in_schema=False,
)
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auth_service = AuthService(db)
    try:
        updated = await auth_service.update_user_profile(
            user_id=current_user["id"],
            display_name=body.display_name,
            phone_number=body.phone_number,
            preferred_language=body.preferred_language,
        )
        return UserProfileResponse(**updated)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )


@router.patch(
    "/preferences",
    response_model=UserProfileResponse,
    summary="Update authenticated farmer's preferred language",
    description="Updates the user's preferred language ('en', 'hi', 'gu') in PostgreSQL.",
)
async def update_preferences(
    body: LanguagePreferenceRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lang = body.preferred_language.strip().lower()
    if lang not in ["en", "hi", "gu"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported language code. Supported: 'en', 'hi', 'gu'.",
        )
    auth_service = AuthService(db)
    updated_user = await auth_service.update_language_preference(
        user_id=current_user["id"], language_code=lang
    )
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return UserProfileResponse(**updated_user)
