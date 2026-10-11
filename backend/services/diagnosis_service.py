"""
backend/services/diagnosis_service.py
=====================================
Core diagnostic orchestration service for Module 14.

Pipeline Execution:
  1. Image validation & MobileNetV2 classification.
  2. Strict ML Confidence Gate:
     - IF confidence < CONFIDENCE_THRESHOLD:
       -> Persists Scan (status: low_confidence) and Prediction (disease_id: NULL)
       -> Halts; returns advisory rejection guidance without invoking the LLM.
     - IF confidence >= CONFIDENCE_THRESHOLD:
       -> Resolves Disease entity and Farm profile.
       -> Retrieves localized Open-Meteo agro-weather context.
       -> Persists authoritative Scan, Prediction, and WeatherSnapshot records.
       -> Invokes Groq LLM (openai/gpt-oss-120b) to generate a structured,
          location- & weather-aware advisory report (zero chemical hallucinations).
       -> Stores structured report in PostgreSQL reports table.
       -> Returns unified diagnosis & advisory contract.
"""

from datetime import datetime, timezone
import logging
import os
from typing import Any, Dict, Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import config
import inference
from models import Crop, Disease, Farm, ModelVersion, Prediction, Report, Scan, WeatherSnapshot
from repositories.crop_repository import CropRepository
from repositories.farm_repository import FarmRepository
from repositories.report_repository import ReportRepository
from repositories.scan_repository import ScanRepository
from repositories.weather_repository import WeatherRepository
from services.llm_service import LLMService
from services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class DiagnosisService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.crop_repo = CropRepository(session)
        self.farm_repo = FarmRepository(session)
        self.scan_repo = ScanRepository(session)
        self.weather_repo = WeatherRepository(session)
        self.report_repo = ReportRepository(session)
        self.llm_service = LLMService()
        self.weather_service = WeatherService(session)

    async def diagnose_leaf(
        self,
        user_dict: Dict[str, Any],
        crop_name: str,
        image_bytes: bytes,
        farm_id: Optional[uuid.UUID] = None,
        language_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute end-to-end diagnosis and localized LLM advisory generation."""
        # 1. Normalize and validate crop
        normalized_crop = crop_name.strip().lower()
        crop_entity = await self.crop_repo.get_by_name(normalized_crop)
        if not crop_entity or not crop_entity.is_supported:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported crop '{crop_name}'. Supported crops: chili, groundnut, potato.",
            )

        # 2. Run MobileNetV2 Inference (authoritative)
        result = inference.predict(normalized_crop, image_bytes)
        confidence = float(result["confidence"])
        top_disease_label = result["disease"]
        threshold = config.CONFIDENCE_THRESHOLD
        is_confident = confidence >= threshold

        user_uuid = uuid.UUID(user_dict["id"])

        # 3. Resolve Farm profile (if provided, verify ownership; otherwise use primary active farm)
        farm: Optional[Farm] = None
        if farm_id:
            farm = await self.farm_repo.get_user_farm_by_id(farm_id, user_uuid)
            if not farm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Specified farm was not found or is not owned by the authenticated user.",
                )
        else:
            farm = await self.farm_repo.get_user_primary_farm(user_uuid)

        farm_info: Optional[Dict[str, Any]] = None
        if farm:
            parts = [farm.village, farm.district, farm.state]
            loc_summary = ", ".join([p for p in parts if p]) if any(parts) else "Registered Plot"
            farm_info = {
                "id": str(farm.id),
                "name": farm.name,
                "village": farm.village,
                "district": farm.district,
                "state": farm.state,
                "location_text": loc_summary,
                "latitude": float(farm.latitude) if farm.latitude is not None else None,
                "longitude": float(farm.longitude) if farm.longitude is not None else None,
                "has_location": farm.latitude is not None and farm.longitude is not None,
            }

        # 4. Resolve Weather context
        weather_info: Optional[Dict[str, Any]] = None
        if farm and farm.latitude is not None and farm.longitude is not None:
            try:
                weather_info = await self.weather_service.get_farm_weather(
                    farm_id=farm.id, user_dict=user_dict, force_refresh=False
                )
            except Exception as exc:
                logger.warning(f"Could not retrieve weather for farm {farm.id}: {exc}")

        # 5. Look up active ModelVersion
        mv_stmt = select(ModelVersion).where(
            ModelVersion.crop_id == crop_entity.id, ModelVersion.is_active.is_(True)
        )
        model_version = (await self.session.execute(mv_stmt)).scalars().first()
        model_version_id = model_version.id if model_version else 1

        raw_scores_dict = {
            item["class"]: item["confidence"] for item in result.get("all_probs", [])
        }

        # Persist uploaded image to disk
        scan_rel_path = f"scans/{uuid.uuid4().hex}.jpg"
        abs_img_path = os.path.join(config.UPLOAD_DIR, scan_rel_path)
        try:
            os.makedirs(os.path.dirname(abs_img_path), exist_ok=True)
            with open(abs_img_path, "wb") as f:
                f.write(image_bytes)
        except Exception as exc:
            logger.warning(f"Failed to persist image bytes: {exc}")

        # 6. Branch on Confidence Gate
        if not is_confident:
            logger.info(
                f"Scan rejected by confidence gate: {confidence * 100:.1f}% < {threshold * 100:.1f}%"
            )
            # Persist unconfident scan & prediction
            scan = await self.scan_repo.create_scan_record(
                crop_id=crop_entity.id,
                image_path=scan_rel_path,
                user_id=user_uuid,
                farm_id=farm.id if farm else None,
                status="low_confidence",
            )
            await self.scan_repo.create_prediction_record(
                scan_id=scan.id,
                disease_id=None,
                confidence=confidence,
                is_confident=False,
                raw_scores=raw_scores_dict,
                threshold_used=threshold,
                model_version_id=model_version_id,
            )
            await self.session.commit()

            return {
                "status": "low_confidence",
                "crop": normalized_crop,
                "is_confident": False,
                "confidence": confidence,
                "threshold": threshold,
                "disease": None,
                "disease_display_name": None,
                "scan_id": str(scan.id),
                "message": (
                    f"Prediction confidence ({confidence * 100:.1f}%) is below the acceptable certainty "
                    f"threshold ({threshold * 100:.1f}%). The leaf image may be blurry, uncentered, "
                    "or showing ambiguous symptoms. Please upload a clearer, well-lit photo focusing directly "
                    "on the leaf or consult an agricultural extension officer."
                ),
                "farm": farm_info,
                "weather": weather_info,
                "report": None,
            }

        # 7. Accepted Prediction Workflow
        # Look up Disease entity
        raw_disease_label = result.get("raw_disease", top_disease_label)
        dis_stmt = select(Disease).where(
            Disease.crop_id == crop_entity.id,
            (Disease.label == top_disease_label) | (Disease.label == raw_disease_label),
        )
        disease_entity = (await self.session.execute(dis_stmt)).scalars().first()
        disease_display_name = (
            disease_entity.display_name if disease_entity else top_disease_label
        )

        # Create Scan record
        scan = await self.scan_repo.create_scan_record(
            crop_id=crop_entity.id,
            image_path=scan_rel_path,
            user_id=user_uuid,
            farm_id=farm.id if farm else None,
            status="success",
        )

        # Create Prediction record
        await self.scan_repo.create_prediction_record(
            scan_id=scan.id,
            disease_id=disease_entity.id if disease_entity else None,
            confidence=confidence,
            is_confident=True,
            raw_scores=raw_scores_dict,
            threshold_used=threshold,
            model_version_id=model_version_id,
        )

        # Create WeatherSnapshot record linked to this scan if weather available
        if weather_info and weather_info.get("temperature_c") is not None:
            try:
                rec_at = None
                if weather_info.get("recorded_at"):
                    try:
                        rec_at = datetime.fromisoformat(weather_info["recorded_at"])
                    except Exception:
                        rec_at = datetime.now(timezone.utc)
                await self.weather_repo.create_weather_snapshot(
                    farm_id=farm.id if farm else None,
                    scan_id=scan.id,
                    temperature_c=weather_info.get("temperature_c"),
                    humidity_pct=weather_info.get("humidity_pct"),
                    rainfall_mm=weather_info.get("rainfall_mm"),
                    wind_speed_kmh=weather_info.get("wind_speed_kmh"),
                    weather_condition=weather_info.get("weather_condition"),
                    data_source=weather_info.get("data_source") or "Open-Meteo",
                    recorded_at=rec_at,
                )
            except Exception as exc:
                logger.warning(f"Could not link weather snapshot to scan {scan.id}: {exc}")

        # 8. Generate Localized LLM Advisory Report
        target_lang = (
            language_code
            or user_dict.get("preferred_language")
            or "en"
        )

        structured_advisory = await self.llm_service.generate_advisory_report(
            crop=normalized_crop,
            disease_name=disease_display_name,
            confidence=confidence,
            farm_info=farm_info,
            weather_info=weather_info,
            target_lang=target_lang,
        )

        # 9. Store Report in PostgreSQL
        report = await self.report_repo.create_report(
            scan_id=scan.id,
            language_code=target_lang,
            disease_name=structured_advisory.disease_name,
            summary=structured_advisory.summary,
            confidence_interpretation=structured_advisory.confidence_interpretation,
            symptoms=structured_advisory.symptoms,
            possible_causes=structured_advisory.possible_causes,
            local_context=structured_advisory.local_context,
            management_steps=structured_advisory.management_steps,
            prevention_steps=structured_advisory.prevention_steps,
            warning_signs=structured_advisory.warning_signs,
            expert_verification_recommended=structured_advisory.expert_verification_recommended,
            disclaimer=structured_advisory.disclaimer,
        )

        await self.session.commit()
        await self.session.refresh(report)

        report_response = self._format_report_dict(report)

        return {
            "status": "success",
            "crop": normalized_crop,
            "is_confident": True,
            "confidence": confidence,
            "threshold": threshold,
            "disease": top_disease_label,
            "disease_display_name": disease_display_name,
            "scan_id": str(scan.id),
            "message": "Diagnosis accepted with high confidence. Localized advisory report generated.",
            "farm": farm_info,
            "weather": weather_info,
            "report": report_response,
        }

    def _format_report_dict(self, report: Report) -> Dict[str, Any]:
        """Convert a Report SQLAlchemy instance to a standardized response dictionary."""
        return {
            "id": str(report.id),
            "scan_id": str(report.scan_id),
            "language_code": report.language_code,
            "disease_name": report.disease_name,
            "confidence_interpretation": report.confidence_interpretation,
            "summary": report.summary,
            "symptoms": report.symptoms or [],
            "possible_causes": report.possible_causes or [],
            "local_context": report.local_context,
            "management_steps": report.management_steps or [],
            "prevention_steps": report.prevention_steps or [],
            "warning_signs": report.warning_signs or [],
            "expert_verification_recommended": report.expert_verification_recommended,
            "disclaimer": report.disclaimer,
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "created_at": report.created_at.isoformat() if report.created_at else None,
        }

    async def get_or_generate_report_for_scan(
        self,
        scan_id: uuid.UUID,
        language_code: str,
        user_dict: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Retrieve existing cached report for (scan_id, language_code), or
        dynamically generate and persist it via LLM service if missing.

        Mandatory Guarantees:
          - Validates scan ownership (blocks unauthorized cross-tenant access).
          - Low-confidence or unconfirmed scans NEVER receive normal advisory reports.
          - Never alters the ML disease label or confidence.
          - Uses atomic caching: if report exists, Groq is NOT called again.
          - Handles race conditions gracefully.
        """
        user_uuid = (
            uuid.UUID(user_dict["id"])
            if isinstance(user_dict["id"], str)
            else user_dict["id"]
        )
        scan = await self.scan_repo.get_by_id(scan_id)
        if not scan or scan.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scan not found or access denied.",
            )

        if scan.status != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Advisory reports cannot be generated for low-confidence or rejected scans.",
            )

        # Normalize target language: only en, hi, gu supported
        target_lang = language_code.strip().lower() if language_code else "en"
        if target_lang not in ["en", "hi", "gu"]:
            target_lang = "en"

        # 1. Check cache first (atomic caching)
        existing_report = await self.report_repo.get_report_by_scan_and_lang(
            scan_id, target_lang
        )
        if existing_report:
            return self._format_report_dict(existing_report)

        # 2. Fetch ML Prediction for authoritative diagnosis
        pred_stmt = select(Prediction).where(Prediction.scan_id == scan_id)
        prediction = (await self.session.execute(pred_stmt)).scalars().first()
        if not prediction or not prediction.is_confident or not prediction.disease_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No confident ML prediction found for this scan.",
            )

        # 3. Retrieve Disease & Crop metadata
        disease = await self.session.get(Disease, prediction.disease_id)
        disease_display = disease.display_name if disease else "Crop Disease"

        crop = await self.crop_repo.get_by_id(scan.crop_id)
        crop_name = crop.name if crop else "chili"

        # 4. Retrieve Farm location context if linked
        farm_info: Optional[Dict[str, Any]] = None
        if scan.farm_id:
            farm = await self.farm_repo.get_by_id(scan.farm_id)
            if farm:
                parts = [farm.village, farm.district, farm.state]
                farm_info = {
                    "id": str(farm.id),
                    "name": farm.name,
                    "village": farm.village,
                    "district": farm.district,
                    "state": farm.state,
                    "location_text": (
                        ", ".join([p for p in parts if p]) if any(parts) else farm.name
                    ),
                    "latitude": (
                        float(farm.latitude) if farm.latitude is not None else None
                    ),
                    "longitude": (
                        float(farm.longitude) if farm.longitude is not None else None
                    ),
                }

        # 5. Retrieve Weather Snapshot if linked
        weather_info: Optional[Dict[str, Any]] = None
        wx_stmt = select(WeatherSnapshot).where(WeatherSnapshot.scan_id == scan_id)
        wx = (await self.session.execute(wx_stmt)).scalars().first()
        if wx:
            weather_info = {
                "temperature_c": (
                    float(wx.temperature_c) if wx.temperature_c is not None else None
                ),
                "humidity_pct": (
                    int(wx.humidity_pct) if wx.humidity_pct is not None else None
                ),
                "rainfall_mm": (
                    float(wx.rainfall_mm) if wx.rainfall_mm is not None else None
                ),
                "wind_speed_kmh": (
                    float(wx.wind_speed_kmh) if wx.wind_speed_kmh is not None else None
                ),
                "weather_condition": wx.weather_condition,
                "data_source": wx.data_source,
            }

        # 6. Generate localized advisory report for target language
        structured_advisory = await self.llm_service.generate_advisory_report(
            crop=crop_name,
            disease_name=disease_display,
            confidence=float(prediction.confidence),
            farm_info=farm_info,
            weather_info=weather_info,
            target_lang=target_lang,
        )

        # 7. Persist to PostgreSQL reports table safely
        try:
            report = await self.report_repo.create_report(
                scan_id=scan.id,
                language_code=target_lang,
                disease_name=structured_advisory.disease_name,
                summary=structured_advisory.summary,
                confidence_interpretation=structured_advisory.confidence_interpretation,
                symptoms=structured_advisory.symptoms,
                possible_causes=structured_advisory.possible_causes,
                local_context=structured_advisory.local_context,
                management_steps=structured_advisory.management_steps,
                prevention_steps=structured_advisory.prevention_steps,
                warning_signs=structured_advisory.warning_signs,
                expert_verification_recommended=structured_advisory.expert_verification_recommended,
                disclaimer=structured_advisory.disclaimer,
            )
            await self.session.commit()
            await self.session.refresh(report)
            return self._format_report_dict(report)
        except Exception:
            await self.session.rollback()
            # If concurrent request already inserted (scan_id, target_lang), fetch and return it
            existing = await self.report_repo.get_report_by_scan_and_lang(
                scan_id, target_lang
            )
            if existing:
                return self._format_report_dict(existing)
            raise
