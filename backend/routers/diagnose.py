"""
backend/routers/diagnose.py
===========================
FastAPI route handlers for Leaf Disease Diagnosis & LLM Advisory Reports (Module 14).
Provides authenticated diagnosis pipeline with MobileNetV2 classification,
farm location resolution, Open-Meteo weather snapshotting, and Groq LLM advisory.
"""

from typing import Any, Dict, Optional
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from repositories.report_repository import ReportRepository
from repositories.scan_repository import ScanRepository
from schemas import DiagnosisResponse, ReportResponse
from services.diagnosis_service import DiagnosisService

router = APIRouter(prefix="/api/v1/diagnose", tags=["Diagnosis & Advisory"])


@router.post(
    "",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_200_OK,
    summary="Diagnose crop leaf disease & generate localized LLM advisory",
    description=(
        "Upload a leaf photograph for MobileNetV2 classification. If confident, "
        "fetches farm location and live weather to generate a structured, localized agricultural advisory report via Groq LLM."
    ),
)
@router.post(
    "/",
    response_model=DiagnosisResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def diagnose_leaf(
    crop: str = Form(
        ...,
        description="Crop identifier e.g. 'chili'",
        examples=["chili"],
    ),
    image: UploadFile = File(
        ...,
        description="Leaf image file (JPEG, PNG, WEBP). Max 10MB.",
    ),
    farm_id: Optional[uuid.UUID] = Form(
        None,
        description="Optional farm UUID to associate diagnostic event and local weather context.",
    ),
    language: Optional[str] = Form(
        None,
        description="Advisory report target language code (e.g. 'en', 'hi', 'gu').",
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiagnosisResponse:
    if not image.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No leaf image file uploaded.",
        )

    image_bytes = await image.read()
    service = DiagnosisService(db)
    result = await service.diagnose_leaf(
        user_dict=current_user,
        crop_name=crop,
        image_bytes=image_bytes,
        farm_id=farm_id,
        language_code=language,
    )
    return DiagnosisResponse(**result)


# Endpoint to fetch previously generated report for a scan
reports_router = APIRouter(prefix="/api/v1/scans", tags=["Scans & Reports"])


@reports_router.get(
    "/{scan_id}/report",
    response_model=ReportResponse,
    summary="Retrieve advisory report for a scan",
    description=(
        "Fetches the structured agricultural advisory report for a confident scan in the requested language (en, hi, gu). "
        "Returns cached report if already generated; dynamically generates and caches on demand if missing."
    ),
)
async def get_scan_report(
    scan_id: uuid.UUID = Path(..., description="UUID identifier of the scan"),
    lang: str = Query("en", description="Report language code ('en', 'hi', 'gu')"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    service = DiagnosisService(db)
    report_dict = await service.get_or_generate_report_for_scan(
        scan_id=scan_id,
        language_code=lang,
        user_dict=current_user,
    )
    return ReportResponse(**report_dict)
