"""
backend/services/farm_service.py
================================
Business logic and operations for farm management in Module 12.
Ensures strict tenant ownership: operations are restricted exclusively
to farms owned by the authenticated PostgreSQL user.
"""

from typing import Any, Dict, List
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models import Farm
from repositories.farm_repository import FarmRepository
from schemas import FarmCreateRequest, FarmUpdateRequest


class FarmService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.farm_repo = FarmRepository(session)

    @staticmethod
    def _format_farm(farm: Farm) -> Dict[str, Any]:
        """Transform SQLAlchemy Farm entity to serializable response dictionary."""
        loc_parts = [p for p in [farm.village, farm.district, farm.state] if p]
        location_text = ", ".join(loc_parts) if loc_parts else "Location not specified"
        has_location = farm.latitude is not None and farm.longitude is not None

        return {
            "id": str(farm.id),
            "name": farm.name,
            "village": farm.village,
            "district": farm.district,
            "state": farm.state,
            "area_hectares": (
                float(farm.area_hectares) if farm.area_hectares is not None else None
            ),
            "latitude": float(farm.latitude) if farm.latitude is not None else None,
            "longitude": float(farm.longitude) if farm.longitude is not None else None,
            "location_text": location_text,
            "has_location": has_location,
            "is_active": farm.is_active,
            "created_at": farm.created_at.isoformat() if farm.created_at else None,
            "updated_at": farm.updated_at.isoformat() if farm.updated_at else None,
        }

    async def create_farm(
        self, user_dict: Dict[str, Any], payload: FarmCreateRequest
    ) -> Dict[str, Any]:
        """
        Create a new farm profile owned by the authenticated user.
        Ignores any client-supplied user_id in favor of the verified session user.
        """
        user_uuid = uuid.UUID(user_dict["id"])

        farm = await self.farm_repo.create_farm(
            user_id=user_uuid,
            name=payload.name,
            village=payload.village,
            district=payload.district,
            state=payload.state,
            area_hectares=payload.area_hectares,
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        await self.session.commit()
        await self.session.refresh(farm)
        return self._format_farm(farm)

    async def get_user_farms(
        self, user_dict: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fetch all active farms owned by the authenticated user."""
        user_uuid = uuid.UUID(user_dict["id"])
        farms = await self.farm_repo.get_active_user_farms(user_uuid)
        return [self._format_farm(f) for f in farms]

    async def get_farm_by_id(
        self, user_dict: Dict[str, Any], farm_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Fetch a single farm owned by the authenticated user.
        Returns HTTP 404 if the farm does not exist or belongs to another user.
        """
        user_uuid = uuid.UUID(user_dict["id"])
        farm = await self.farm_repo.get_user_farm_by_id(farm_id, user_uuid)
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found",
            )
        return self._format_farm(farm)

    async def update_farm(
        self,
        user_dict: Dict[str, Any],
        farm_id: uuid.UUID,
        payload: FarmUpdateRequest,
    ) -> Dict[str, Any]:
        """
        Update fields on an existing farm owned by the authenticated user.
        Returns HTTP 404 if the farm is not found or not owned by the user.
        """
        user_uuid = uuid.UUID(user_dict["id"])
        farm = await self.farm_repo.get_user_farm_by_id(farm_id, user_uuid)
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found",
            )

        if payload.name is not None:
            farm.name = payload.name
        if payload.village is not None:
            farm.village = payload.village
        if payload.district is not None:
            farm.district = payload.district
        if payload.state is not None:
            farm.state = payload.state
        if payload.area_hectares is not None:
            farm.area_hectares = payload.area_hectares
        if payload.latitude is not None:
            farm.latitude = payload.latitude
        if payload.longitude is not None:
            farm.longitude = payload.longitude

        await self.session.commit()
        await self.session.refresh(farm)
        return self._format_farm(farm)

    async def deactivate_farm(
        self, user_dict: Dict[str, Any], farm_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Soft-delete / deactivate a farm owned by the authenticated user.
        Sets is_active=False. Returns HTTP 404 if not found or unauthorized.
        """
        user_uuid = uuid.UUID(user_dict["id"])
        farm = await self.farm_repo.get_user_farm_by_id(farm_id, user_uuid)
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found",
            )

        farm.is_active = False
        await self.session.commit()
        return {
            "status": "success",
            "message": "Farm deactivated successfully",
            "id": str(farm.id),
        }
