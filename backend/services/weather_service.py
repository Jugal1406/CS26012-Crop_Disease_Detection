"""
backend/services/weather_service.py
===================================
Weather retrieval and snapshot management for Module 13.
Uses Open-Meteo (Option B) for free, reliable, farm-location-based weather.
Features:
  - Coordinate validation: farms without GPS bypass external calls cleanly.
  - DB caching & freshness policy: snapshots cached for 30 minutes unless forced.
  - Snapshot persistence: stores normalized weather records in PostgreSQL.
  - Secure configuration: reads from config.py / backend/.env.
"""

from datetime import datetime, timezone, timedelta
import logging
from typing import Any, Dict, Optional
import uuid
import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import config
from models import Farm, WeatherSnapshot
from repositories.farm_repository import FarmRepository
from repositories.weather_repository import WeatherRepository

logger = logging.getLogger(__name__)

# WMO Weather Interpretation Codes (WW)
WMO_CODE_MAP: Dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


class WeatherService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.farm_repo = FarmRepository(session)
        self.weather_repo = WeatherRepository(session)

    @staticmethod
    def _interpret_wmo_code(code: Optional[int]) -> str:
        """Map WMO weather code to farmer-friendly descriptive text."""
        if code is None:
            return "Clear"
        return WMO_CODE_MAP.get(code, f"Weather code {code}")

    @staticmethod
    def _format_snapshot(
        farm: Farm, snapshot: WeatherSnapshot, cached: bool = True
    ) -> Dict[str, Any]:
        """Convert a database WeatherSnapshot into standard response format."""
        return {
            "status": "success",
            "farm_id": str(farm.id),
            "farm_name": farm.name,
            "has_location": True,
            "message": "Weather snapshot loaded from cache" if cached else "Live weather retrieved successfully",
            "temperature_c": (
                float(snapshot.temperature_c)
                if snapshot.temperature_c is not None
                else None
            ),
            "humidity_pct": (
                float(snapshot.humidity_pct)
                if snapshot.humidity_pct is not None
                else None
            ),
            "rainfall_mm": (
                float(snapshot.rainfall_mm)
                if snapshot.rainfall_mm is not None
                else None
            ),
            "wind_speed_kmh": (
                float(snapshot.wind_speed_kmh)
                if snapshot.wind_speed_kmh is not None
                else None
            ),
            "weather_condition": snapshot.weather_condition,
            "data_source": snapshot.data_source or "Open-Meteo",
            "recorded_at": (
                snapshot.recorded_at.isoformat()
                if snapshot.recorded_at
                else snapshot.created_at.isoformat()
            ),
            "cached": cached,
            "snapshot_id": str(snapshot.id),
        }

    async def get_farm_weather(
        self,
        farm_id: uuid.UUID,
        user_dict: Dict[str, Any],
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Retrieve weather for a farm.
        Enforces tenant security: farm must be owned by the user.
        """
        user_uuid = uuid.UUID(user_dict["id"])

        # 1. Fetch farm and enforce tenant ownership
        farm = await self.farm_repo.get_user_farm_by_id(farm_id, user_uuid)
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found or not owned by the authenticated user",
            )

        # 2. Check if farm has GPS coordinates
        if farm.latitude is None or farm.longitude is None:
            return {
                "status": "success",
                "farm_id": str(farm.id),
                "farm_name": farm.name,
                "has_location": False,
                "message": (
                    "Farm coordinates (latitude and longitude) are not configured. "
                    "Please edit your farm profile with GPS coordinates to view live weather."
                ),
                "temperature_c": None,
                "humidity_pct": None,
                "rainfall_mm": None,
                "wind_speed_kmh": None,
                "weather_condition": None,
                "data_source": None,
                "recorded_at": None,
                "cached": False,
                "snapshot_id": None,
            }

        # 3. Check cache / freshness policy
        latest_snapshot = await self.weather_repo.get_latest_farm_snapshot(farm.id)
        cache_minutes = getattr(config, "WEATHER_CACHE_MINUTES", 30)

        if latest_snapshot and not force_refresh:
            now = datetime.now(timezone.utc)
            snapshot_time = latest_snapshot.created_at
            if snapshot_time.tzinfo is None:
                snapshot_time = snapshot_time.replace(tzinfo=timezone.utc)
            age = now - snapshot_time
            if age < timedelta(minutes=cache_minutes):
                logger.info(
                    f"Returning cached weather for farm {farm.id} (age: {int(age.total_seconds() / 60)} mins)"
                )
                return self._format_snapshot(farm, latest_snapshot, cached=True)

        # 4. Fetch live data from Open-Meteo
        lat = float(farm.latitude)
        lon = float(farm.longitude)
        url = "https://api.open-meteo.com/v1/forecast"
        params: Dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m",
            "timezone": "auto",
        }
        if config.WEATHER_API_KEY:
            params["apikey"] = config.WEATHER_API_KEY

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning(
                f"Failed to fetch live weather from Open-Meteo for farm {farm.id}: {exc}"
            )
            # If an older snapshot exists, fall back to it
            if latest_snapshot:
                logger.info("Serving stale cached snapshot due to external API error")
                fallback_resp = self._format_snapshot(farm, latest_snapshot, cached=True)
                fallback_resp["message"] = "Live weather update unavailable; displaying latest recorded snapshot."
                return fallback_resp
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Unable to reach weather service: {str(exc)}",
            )

        # 5. Parse Open-Meteo payload
        current = data.get("current", {})
        temp_c = current.get("temperature_2m")
        hum_pct = current.get("relative_humidity_2m")
        precip = current.get("precipitation")
        if precip is None:
            precip = current.get("rain", 0.0)
        wind_kmh = current.get("wind_speed_10m")
        wmo_code = current.get("weather_code")
        condition_str = self._interpret_wmo_code(wmo_code)

        recorded_time_str = current.get("time")
        recorded_at: Optional[datetime] = None
        if recorded_time_str:
            try:
                recorded_at = datetime.fromisoformat(recorded_time_str)
                if recorded_at.tzinfo is None:
                    recorded_at = recorded_at.replace(tzinfo=timezone.utc)
            except Exception:
                recorded_at = datetime.now(timezone.utc)
        else:
            recorded_at = datetime.now(timezone.utc)

        # 6. Save snapshot to PostgreSQL
        new_snapshot = await self.weather_repo.create_weather_snapshot(
            farm_id=farm.id,
            temperature_c=temp_c,
            humidity_pct=hum_pct,
            rainfall_mm=precip,
            wind_speed_kmh=wind_kmh,
            weather_condition=condition_str,
            data_source="Open-Meteo",
            recorded_at=recorded_at,
        )

        logger.info(
            f"Saved new weather snapshot for farm {farm.id}: {temp_c}°C, {hum_pct}%, {condition_str}"
        )
        return self._format_snapshot(farm, new_snapshot, cached=False)
