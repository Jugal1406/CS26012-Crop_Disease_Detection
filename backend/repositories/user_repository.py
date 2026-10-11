"""
backend/repositories/user_repository.py
=======================================
Repository for querying and managing User entities in PostgreSQL.
"""

from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_provider_uid(
        self, provider_uid: str, provider: str = "firebase"
    ) -> Optional[User]:
        """Fetch user by external auth provider's UID (e.g. Firebase UID)."""
        stmt = select(User).where(
            User.auth_provider == provider,
            User.auth_provider_user_id == provider_uid,
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email address."""
        if not email:
            return None
        stmt = select(User).where(User.email == email.strip().lower())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_phone(self, phone_number: str) -> Optional[User]:
        """Fetch user by phone number."""
        if not phone_number:
            return None
        stmt = select(User).where(User.phone_number == phone_number.strip())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def sync_clerk_user(
        self,
        clerk_id: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        preferred_language: str = "en",
        fallback_display_name: Optional[str] = None,
    ) -> User:
        """
        Synchronize an authenticated Clerk user with PostgreSQL.
        - If user already exists by Clerk user ID: updates non-empty fields and returns existing record.
        - If user exists by verified email: links the Clerk user ID and updates provider to 'clerk'.
        - If new user: creates and persists local User record with unique UUID.
        Idempotent and guarantees single record per Clerk identity.
        """
        user = await self.get_by_provider_uid(clerk_id, provider="clerk")

        if not user and email:
            user = await self.get_by_email(email)
            if user:
                user.auth_provider = "clerk"
                user.auth_provider_user_id = clerk_id

        if user:
            updated = False
            # If explicit display_name was provided by caller, update it
            if display_name and display_name.strip() and user.display_name != display_name.strip():
                user.display_name = display_name.strip()
                updated = True
            elif not user.display_name and fallback_display_name and fallback_display_name.strip():
                user.display_name = fallback_display_name.strip()
                updated = True

            if email and (not user.email or user.email != email.strip().lower()):
                user.email = email.strip().lower()
                updated = True
            # Only set phone_number if user has none recorded
            if phone_number and not user.phone_number:
                user.phone_number = phone_number.strip()
                updated = True
            # Only set preferred_language if user has no language preference configured
            if preferred_language and not user.preferred_language:
                user.preferred_language = preferred_language
                updated = True
            if updated:
                await self.session.flush()
            return user

        initial_name = display_name or fallback_display_name
        new_user = User(
            id=uuid.uuid4(),
            auth_provider="clerk",
            auth_provider_user_id=clerk_id,
            display_name=initial_name.strip() if initial_name else None,
            email=email.strip().lower() if email else None,
            phone_number=phone_number.strip() if phone_number else None,
            preferred_language=preferred_language or "en",
            is_active=True,
        )
        self.session.add(new_user)
        await self.session.flush()
        return new_user

    async def sync_firebase_user(
        self,
        uid: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
        preferred_language: str = "en",
    ) -> User:
        """Legacy Firebase sync method preserved for backwards compatibility."""
        return await self.sync_clerk_user(
            clerk_id=uid,
            display_name=display_name,
            email=email,
            phone_number=phone_number,
            preferred_language=preferred_language,
        )

    async def update_language_preference(
        self, user_id: uuid.UUID, language_code: str
    ) -> Optional[User]:
        """Update the preferred language setting for an authenticated user."""
        user = await self.get_by_id(user_id)
        if user and user.preferred_language != language_code:
            user.preferred_language = language_code
            await self.session.flush()
        return user

    async def update_profile(
        self,
        user_id: uuid.UUID,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        preferred_language: Optional[str] = None,
    ) -> Optional[User]:
        """Update authenticated user profile fields without touching auth identity."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        if display_name is not None and display_name.strip():
            user.display_name = display_name.strip()
        if phone_number is not None:
            user.phone_number = phone_number.strip() if phone_number.strip() else None
        if preferred_language is not None and preferred_language in ["en", "hi", "gu"]:
            user.preferred_language = preferred_language
        await self.session.flush()
        return user
