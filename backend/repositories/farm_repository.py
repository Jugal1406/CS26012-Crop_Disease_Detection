"""
backend/repositories/farm_repository.py
=======================================
Repository for querying and managing Farm entities in PostgreSQL.
"""

from typing import Optional, Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Farm
from .base import BaseRepository


class FarmRepository(BaseRepository[Farm]):
    def __init__(self, session: AsyncSession):
        super().__init__(Farm, session)

    async def get_user_primary_farm(self, user_id: uuid.UUID) -> Optional[Farm]:
        """Fetch the first active farm registered by this user."""
        stmt = (
            select(Farm)
            .where(Farm.user_id == user_id, Farm.is_active.is_(True))
            .order_by(Farm.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_user_farms(self, user_id: uuid.UUID) -> Sequence[Farm]:
        """Fetch all active farms owned by the user, ordered by creation date descending."""
        stmt = (
            select(Farm)
            .where(Farm.user_id == user_id, Farm.is_active.is_(True))
            .order_by(Farm.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_user_farms(self, user_id: uuid.UUID) -> Sequence[Farm]:
        """Fetch all farms owned by the user (including inactive)."""
        stmt = (
            select(Farm)
            .where(Farm.user_id == user_id)
            .order_by(Farm.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_farm_by_id(
        self, farm_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Farm]:
        """
        Fetch a specific active farm owned by the user.
        Strictly enforces tenant ownership: filters by BOTH farm_id and user_id.
        """
        stmt = (
            select(Farm)
            .where(
                Farm.id == farm_id,
                Farm.user_id == user_id,
                Farm.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_farm(
        self,
        user_id: uuid.UUID,
        name: str,
        village: str,
        district: str,
        state: str,
        area_hectares: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Farm:
        """Create and persist a new Farm record linked to the authenticated user."""
        farm = Farm(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            village=village,
            district=district,
            state=state,
            area_hectares=area_hectares,
            latitude=latitude,
            longitude=longitude,
            is_active=True,
        )
        self.session.add(farm)
        await self.session.flush()
        return farm
