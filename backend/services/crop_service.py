"""
backend/services/crop_service.py
================================
Domain service managing crop and disease catalog operations.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.crop_repository import CropRepository


class CropService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.crop_repo = CropRepository(session)

    async def list_supported_crops(self) -> List[Dict[str, Any]]:
        """Return list of crops that have trained models active."""
        crops = await self.crop_repo.get_supported_crops()
        return [
            {
                "id": c.id,
                "name": c.name,
                "display_name": c.display_name,
                "is_supported": c.is_supported,
            }
            for c in crops
        ]

    async def list_all_crops(self) -> List[Dict[str, Any]]:
        """Return all crops registered in the platform."""
        crops = await self.crop_repo.get_all_crops()
        return [
            {
                "id": c.id,
                "name": c.name,
                "display_name": c.display_name,
                "is_supported": c.is_supported,
            }
            for c in crops
        ]

    async def get_crop_diseases(self, crop_name: str) -> Optional[List[Dict[str, Any]]]:
        """Return recognized disease classes for a given crop name."""
        crop = await self.crop_repo.get_by_name(crop_name)
        if not crop:
            return None
        diseases = await self.crop_repo.get_diseases_by_crop_id(crop.id)
        return [
            {
                "id": d.id,
                "label": d.label,
                "display_name": d.display_name,
                "severity_category": d.severity_category,
            }
            for d in diseases
        ]
