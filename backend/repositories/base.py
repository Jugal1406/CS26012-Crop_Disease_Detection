"""
backend/repositories/base.py
============================
Abstract Base Repository establishing session lifecycle patterns.
"""

from typing import Generic, TypeVar, Type, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository providing core CRUD helpers.
    Subclasses define entity-specific query logic.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id_val) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return await self.session.get(self.model, id_val)

    async def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[ModelType]:
        """Fetch multiple records with pagination."""
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, instance: ModelType) -> ModelType:
        """Add and flush an instance to the session."""
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Delete an instance from the session."""
        await self.session.delete(instance)
        await self.session.flush()
