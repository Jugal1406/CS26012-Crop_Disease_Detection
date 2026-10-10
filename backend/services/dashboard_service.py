"""
backend/services/dashboard_service.py
====================================
Service aggregating authenticated farmer profile, farm details,
scan statistics, active crop catalog, and recent activities.
"""

from typing import Any, Dict, List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.crop_repository import CropRepository
from repositories.farm_repository import FarmRepository
from repositories.scan_repository import ScanRepository
from repositories.user_repository import UserRepository
from repositories.weather_repository import WeatherRepository


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.farm_repo = FarmRepository(session)
        self.scan_repo = ScanRepository(session)
        self.crop_repo = CropRepository(session)
        self.weather_repo = WeatherRepository(session)

    async def get_dashboard_overview(self, user_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Builds the personalized dashboard payload for the authenticated user.
        Ensures strict tenant isolation (only the authenticated user's data is returned).
        """
        user_uuid = uuid.UUID(user_dict["id"])

        # 1. User profile summary
        user = await self.user_repo.get_by_id(user_uuid)
        user_profile = {
            "id": str(user.id) if user else user_dict["id"],
            "display_name": user.display_name if user and user.display_name else "Farmer",
            "email": user.email if user else None,
            "phone_number": user.phone_number if user else None,
            "preferred_language": user.preferred_language if user else "en",
            "is_active": user.is_active if user else True,
            "created_at": user.created_at.isoformat() if user and user.created_at else None,
        }

        # 2. Farm and Location details
        primary_farm = await self.farm_repo.get_user_primary_farm(user_uuid)
        farm_info = None
        current_location = "Location Not Configured"

        if primary_farm:
            loc_parts = [p for p in [primary_farm.village, primary_farm.district, primary_farm.state] if p]
            if loc_parts:
                current_location = ", ".join(loc_parts)

            farm_info = {
                "id": str(primary_farm.id),
                "name": primary_farm.name,
                "village": primary_farm.village,
                "district": primary_farm.district,
                "state": primary_farm.state,
                "area_hectares": float(primary_farm.area_hectares) if primary_farm.area_hectares else None,
                "location_text": current_location,
                "is_active": primary_farm.is_active,
            }

        # 3. Scan & Diagnosis Statistics
        stats = await self.scan_repo.get_user_scan_stats(user_uuid)
        active_farms = await self.farm_repo.get_active_user_farms(user_uuid)
        stats["active_farms_count"] = len(active_farms)

        # 4. Active & Supported Crops
        all_crops = await self.crop_repo.get_all_crops()
        crops_catalog: List[Dict[str, Any]] = [
            {
                "id": c.id,
                "name": c.name,
                "display_name": c.display_name,
                "is_supported": c.is_supported,
                "status": "Active (AI Ready)" if c.is_supported else "Training In Progress",
            }
            for c in all_crops
        ]

        # 5. Recent Diagnoses (isolated to user_id)
        recent_scans_entities = await self.scan_repo.get_user_scans(user_uuid, limit=5)
        
        # Populate quick statistics for last scan and recent crop
        if recent_scans_entities:
            latest_scan = recent_scans_entities[0]
            stats["last_scan_date"] = (
                latest_scan.created_at.strftime("%d %b %Y")
                if latest_scan.created_at
                else None
            )
            stats["most_recent_crop"] = (
                latest_scan.crop.display_name
                if (latest_scan and latest_scan.crop)
                else None
            )
        else:
            stats["last_scan_date"] = None
            stats["most_recent_crop"] = None

        recent_scans = []
        for s in recent_scans_entities:
            pred = s.prediction
            disease_name = "Undetermined"
            confidence_pct = None
            is_healthy = False

            if pred:
                confidence_pct = round(float(pred.confidence) * 100, 1)
                if pred.disease:
                    disease_name = pred.disease.display_name
                    is_healthy = "healthy" in pred.disease.label.lower()
                elif not pred.is_confident:
                    disease_name = "Low Confidence (Retake Recommended)"

            formatted_date = (
                s.created_at.strftime("%d %b %Y") if s.created_at else None
            )

            recent_scans.append({
                "id": str(s.id),
                "crop": s.crop.display_name if s.crop else "Unknown",
                "condition": disease_name,
                "disease": disease_name,
                "is_healthy": is_healthy,
                "confidence": confidence_pct,
                "is_confident": pred.is_confident if pred else False,
                "status": s.status,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "date": formatted_date,
            })

        # 6. Recent Advisory Reports (isolated to user_id)
        recent_reports_entities = await self.scan_repo.get_user_recent_reports(user_uuid, limit=5)
        recent_reports = [
            {
                "id": str(r.id),
                "scan_id": str(r.scan_id),
                "disease_name": r.disease_name,
                "summary": r.summary,
                "language_code": r.language_code,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent_reports_entities
        ]

        # 7. Weather Context for Primary Farm (Module 13)
        weather_info = None
        if primary_farm and primary_farm.latitude is not None and primary_farm.longitude is not None:
            latest_weather = await self.weather_repo.get_latest_farm_snapshot(primary_farm.id)
            if latest_weather:
                weather_info = {
                    "temperature_c": (
                        float(latest_weather.temperature_c)
                        if latest_weather.temperature_c is not None
                        else None
                    ),
                    "humidity_pct": (
                        float(latest_weather.humidity_pct)
                        if latest_weather.humidity_pct is not None
                        else None
                    ),
                    "rainfall_mm": (
                        float(latest_weather.rainfall_mm)
                        if latest_weather.rainfall_mm is not None
                        else None
                    ),
                    "wind_speed_kmh": (
                        float(latest_weather.wind_speed_kmh)
                        if latest_weather.wind_speed_kmh is not None
                        else None
                    ),
                    "weather_condition": latest_weather.weather_condition,
                    "data_source": latest_weather.data_source or "Open-Meteo",
                    "recorded_at": (
                        latest_weather.recorded_at.isoformat()
                        if latest_weather.recorded_at
                        else latest_weather.created_at.isoformat()
                    ),
                    "farm_id": str(primary_farm.id),
                    "farm_name": primary_farm.name,
                }

        return {
            "user": user_profile,
            "farm": farm_info,
            "current_location": current_location,
            "weather": weather_info,
            "weather_placeholder": {
                "status": "ready" if weather_info else "pending_module_integration",
                "message": (
                    "Live meteorological context active."
                    if weather_info
                    else "Configure farm GPS coordinates to view live weather."
                ),
                "regional_station": (
                    primary_farm.district
                    if (primary_farm and primary_farm.district)
                    else "Regional Agro Station"
                ),
            },
            "stats": stats,
            "active_crops": crops_catalog,
            "recent_scans": recent_scans,
            "recent_reports": recent_reports,
        }
