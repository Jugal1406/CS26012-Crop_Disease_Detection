"""
backend/services/auth_service.py
================================
Service layer handling authentication logic, Clerk token verification,
and synchronization with the PostgreSQL database.
"""

from typing import Any, Dict, Optional
import re
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from clerk_auth import verify_clerk_token, get_clerk_user_profile, AuthenticationError
from repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def sync_clerk_user(
        self,
        token: str,
        display_name: Optional[str] = None,
        preferred_language: str = "en",
    ) -> Dict[str, Any]:
        """
        Verify the Clerk session token and synchronize the user with PostgreSQL.

        Security:
          - Never trusts a client-sent UID.
          - The user ID is extracted ONLY from verified cryptographic token claims.
          - Verified email and profile details are retrieved from Clerk.
        """
        claims = verify_clerk_token(token)
        clerk_id = claims["uid"]

        # Fetch verified profile from Clerk API if available
        clerk_profile = await get_clerk_user_profile(clerk_id)
        email = clerk_profile.get("email") if clerk_profile else None
        token_name = clerk_profile.get("display_name") if clerk_profile else None
        phone = clerk_profile.get("phone_number") if clerk_profile else None

        # Display name priority: explicit client request vs Clerk profile name fallback
        explicit_name = display_name.strip() if display_name and display_name.strip() else None

        user = await self.user_repo.sync_clerk_user(
            clerk_id=clerk_id,
            display_name=explicit_name,
            email=email,
            phone_number=phone,
            preferred_language=preferred_language,
            fallback_display_name=token_name,
        )

        return {
            "id": str(user.id),
            "auth_provider": user.auth_provider,
            "auth_provider_user_id": user.auth_provider_user_id,
            "display_name": user.display_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "preferred_language": user.preferred_language,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    async def sync_firebase_user(
        self,
        id_token: str,
        display_name: Optional[str] = None,
        preferred_language: str = "en",
    ) -> Dict[str, Any]:
        """Alias for backward compatibility."""
        return await self.sync_clerk_user(
            token=id_token,
            display_name=display_name,
            preferred_language=preferred_language,
        )

    async def get_user_profile_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Retrieve local user profile by Clerk UID or fallback."""
        user = await self.user_repo.get_by_provider_uid(uid, provider="clerk")
        if not user:
            user = await self.user_repo.get_by_provider_uid(uid, provider="firebase")
        if not user:
            return None
        return {
            "id": str(user.id),
            "auth_provider": user.auth_provider,
            "auth_provider_user_id": user.auth_provider_user_id,
            "display_name": user.display_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "preferred_language": user.preferred_language,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    async def update_user_profile(
        self,
        user_id: str,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        preferred_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update authenticated user profile with phone normalization and duplicate check."""
        parsed_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id

        norm_phone = None
        if phone_number is not None:
            cleaned = re.sub(r"[\s\-\(\)]", "", phone_number.strip())
            if cleaned:
                if re.match(r"^\d{10}$", cleaned):
                    norm_phone = f"+91{cleaned}"
                elif re.match(r"^\+\d{10,15}$", cleaned):
                    norm_phone = cleaned
                else:
                    raise ValueError(
                        "Invalid phone number format. Please provide a 10-digit number or E.164 format (e.g. +919876543210)."
                    )

                existing = await self.user_repo.get_by_phone(norm_phone)
                if existing and existing.id != parsed_id:
                    raise ValueError("Phone number is already associated with another account.")
            else:
                norm_phone = ""

        if preferred_language is not None and preferred_language not in ["en", "hi", "gu"]:
            raise ValueError("Supported languages: 'en', 'hi', 'gu'.")

        user = await self.user_repo.update_profile(
            user_id=parsed_id,
            display_name=display_name,
            phone_number=norm_phone,
            preferred_language=preferred_language,
        )
        if not user:
            raise KeyError("User not found.")

        await self.session.commit()
        await self.session.refresh(user)

        return {
            "id": str(user.id),
            "auth_provider": user.auth_provider,
            "auth_provider_user_id": user.auth_provider_user_id,
            "display_name": user.display_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "preferred_language": user.preferred_language,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    async def update_language_preference(
        self, user_id: str, language_code: str
    ) -> Optional[Dict[str, Any]]:
        """Update preferred language in PostgreSQL and return updated profile."""
        parsed_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        user = await self.user_repo.update_language_preference(parsed_id, language_code)
        if not user:
            return None
        await self.session.commit()
        await self.session.refresh(user)
        return {
            "id": str(user.id),
            "auth_provider": user.auth_provider,
            "auth_provider_user_id": user.auth_provider_user_id,
            "display_name": user.display_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "preferred_language": user.preferred_language,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
