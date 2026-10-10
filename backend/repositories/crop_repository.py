"""
backend/repositories/crop_repository.py
=======================================
Repository for accessing Crop, Disease, and ModelVersion entities.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Crop, Disease, ModelVersion
from .base import BaseRepository


class CropRepository(BaseRepository[Crop]):
    def __init__(self, session: AsyncSession):
        super().__init__(Crop, session)

    async def get_by_name(self, name: str) -> Optional[Crop]:
        """Fetch crop by unique lower-cased name."""
        stmt = select(Crop).where(Crop.name == name.strip().lower())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_supported_crops(self) -> Sequence[Crop]:
        """Fetch all crops currently marked as is_supported=True."""
        stmt = select(Crop).where(Crop.is_supported.is_(True)).order_by(Crop.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_crops(self) -> Sequence[Crop]:
        """Fetch all crops registered in the database."""
        stmt = select(Crop).order_by(Crop.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_crop_with_diseases(self, crop_name: str) -> Optional[Crop]:
        """Fetch crop including all mapped disease records via eager loading."""
        stmt = (
            select(Crop)
            .where(Crop.name == crop_name.strip().lower())
            .options(selectinload(Crop.diseases))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_diseases_by_crop_id(self, crop_id: int) -> Sequence[Disease]:
        """Fetch all diseases recognized for a specific crop ID."""
        stmt = select(Disease).where(Disease.crop_id == crop_id).order_by(Disease.label)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_disease_by_label(self, crop_id: int, label: str) -> Optional[Disease]:
        """Fetch a specific disease record by crop ID and model label."""
        stmt = select(Disease).where(
            Disease.crop_id == crop_id,
            Disease.label == label.strip(),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_active_model_version(self, crop_id: int) -> Optional[ModelVersion]:
        """Fetch the currently active model version for a crop."""
        stmt = select(ModelVersion).where(
            ModelVersion.crop_id == crop_id,
            ModelVersion.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()
