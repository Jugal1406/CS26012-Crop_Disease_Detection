"""
backend/routers/dashboard.py
===========================
FastAPI routes for the authenticated farmer's personalized dashboard.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get(
    "",
    summary="Get authenticated farmer's personalized dashboard overview",
    description="Returns the authenticated farmer's profile, statistics, crops, and recent diagnoses.",
)
@router.get(
    "/",
    summary="Get authenticated farmer's personalized dashboard overview",
    description="Returns the authenticated farmer's profile, statistics, crops, and recent diagnoses.",
)
@router.get(
    "/overview",
    summary="Get authenticated farmer's personalized dashboard overview",
    description=(
        "Returns the authenticated farmer's profile, primary farm details, "
        "current location, scan & diagnosis statistics, supported crops, "
        "and recent personalized activity."
    ),
)
async def get_dashboard_overview(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    dashboard_service = DashboardService(db)
    return await dashboard_service.get_dashboard_overview(current_user)
