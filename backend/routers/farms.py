"""
backend/routers/farms.py
========================
FastAPI route handlers for Farm Profile & Location (Module 12).
All endpoints require Firebase authentication and operate strictly
within the scope of the authenticated PostgreSQL user.
"""

from typing import Any, Dict
import uuid
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from schemas import (
    FarmCreateRequest,
    FarmListResponse,
    FarmResponse,
    FarmUpdateRequest,
    WeatherResponse,
)
from services.farm_service import FarmService
from services.weather_service import WeatherService

router = APIRouter(prefix="/api/v1/farms", tags=["Farms"])


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new farm profile",
    description="Registers a new farm plot owned by the authenticated user.",
)
@router.post(
    "/",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_farm(
    payload: FarmCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FarmService(db)
    return await service.create_farm(current_user, payload)


@router.get(
    "",
    response_model=FarmListResponse,
    summary="List authenticated user's active farms",
    description="Returns all active farm profiles belonging to the authenticated user.",
)
@router.get(
    "/",
    response_model=FarmListResponse,
    include_in_schema=False,
)
async def list_farms(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FarmService(db)
    farms = await service.get_user_farms(current_user)
    return FarmListResponse(status="success", count=len(farms), farms=farms)


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Get single farm details",
    description="Fetches details for a specific active farm owned by the authenticated user.",
)
async def get_farm(
    farm_id: uuid.UUID = Path(..., description="UUID identifier of the farm"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FarmService(db)
    return await service.get_farm_by_id(current_user, farm_id)


@router.put(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Update farm profile",
    description="Updates metadata or location on a farm owned by the authenticated user.",
)
async def update_farm(
    payload: FarmUpdateRequest,
    farm_id: uuid.UUID = Path(..., description="UUID identifier of the farm"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FarmService(db)
    return await service.update_farm(current_user, farm_id, payload)


@router.delete(
    "/{farm_id}",
    summary="Deactivate farm profile",
    description="Soft-deactivates a farm profile. Inactive farms do not appear in active listings.",
)
async def deactivate_farm(
    farm_id: uuid.UUID = Path(..., description="UUID identifier of the farm"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FarmService(db)
    return await service.deactivate_farm(current_user, farm_id)


@router.get(
    "/{farm_id}/weather",
    response_model=WeatherResponse,
    summary="Get current weather for a farm",
    description="Fetches live or cached agro-meteorological snapshot for the specified farm.",
)
async def get_farm_weather(
    farm_id: uuid.UUID = Path(..., description="UUID identifier of the farm"),
    force_refresh: bool = Query(
        False, description="If True, bypasses cache and queries live weather provider"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = WeatherService(db)
    return await service.get_farm_weather(
        farm_id=farm_id, user_dict=current_user, force_refresh=force_refresh
    )
