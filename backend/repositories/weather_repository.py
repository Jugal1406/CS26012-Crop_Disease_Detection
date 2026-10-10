"""
backend/repositories/weather_repository.py
==========================================
Repository for querying and storing WeatherSnapshot entities in PostgreSQL.
"""

from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import WeatherSnapshot
from .base import BaseRepository


class WeatherRepository(BaseRepository[WeatherSnapshot]):
    def __init__(self, session: AsyncSession):
        super().__init__(WeatherSnapshot, session)

    async def get_latest_farm_snapshot(
        self, farm_id: uuid.UUID
    ) -> Optional[WeatherSnapshot]:
        """Fetch the most recent weather snapshot recorded for a farm."""
        stmt = (
            select(WeatherSnapshot)
            .where(WeatherSnapshot.farm_id == farm_id)
            .order_by(WeatherSnapshot.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_weather_snapshot(
        self,
        farm_id: uuid.UUID,
        temperature_c: Optional[float] = None,
        humidity_pct: Optional[float] = None,
        rainfall_mm: Optional[float] = None,
        wind_speed_kmh: Optional[float] = None,
        weather_condition: Optional[str] = None,
        data_source: str = "Open-Meteo",
        recorded_at: Optional[datetime] = None,
        scan_id: Optional[uuid.UUID] = None,
    ) -> WeatherSnapshot:
        """Persist a new normalized weather snapshot in PostgreSQL."""
        snapshot = WeatherSnapshot(
            farm_id=farm_id,
            scan_id=scan_id,
            temperature_c=temperature_c,
            humidity_pct=humidity_pct,
            rainfall_mm=rainfall_mm,
            wind_speed_kmh=wind_speed_kmh,
            weather_condition=weather_condition,
            data_source=data_source,
            recorded_at=recorded_at,
        )
        self.session.add(snapshot)
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot
