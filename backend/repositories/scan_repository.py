"""
backend/repositories/scan_repository.py
=======================================
Repository for managing Scan and Prediction entities.
"""

from typing import Optional, Sequence, Tuple
import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Crop, Disease, Farm, Prediction, Report, Scan, WeatherSnapshot
from .base import BaseRepository


class ScanRepository(BaseRepository[Scan]):
    def __init__(self, session: AsyncSession):
        super().__init__(Scan, session)

    async def get_scan_with_details(self, scan_id: uuid.UUID) -> Optional[Scan]:
        """Fetch a scan by ID with prediction, crop, and farm relationships loaded."""
        stmt = (
            select(Scan)
            .where(Scan.id == scan_id)
            .options(
                selectinload(Scan.prediction).selectinload(Prediction.disease),
                selectinload(Scan.crop),
                selectinload(Scan.farm),
                selectinload(Scan.reports),
                selectinload(Scan.weather_snapshot),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_user_scans_paginated(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
        crop: Optional[str] = None,
        status: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Tuple[Sequence[Scan], int]:
        """
        Fetch paginated scan records for an authenticated user with optional filtering and sorting.
        Applies a stable secondary sort key (Scan.id) when created_at values match.
        """
        base_filters = [Scan.user_id == user_id]

        if status and status.strip():
            base_filters.append(Scan.status == status.strip().lower())

        # Count total matching records
        count_stmt = select(func.count(Scan.id)).where(*base_filters)
        if crop and crop.strip():
            count_stmt = count_stmt.join(Crop, Scan.crop_id == Crop.id).where(
                Crop.name == crop.strip().lower()
            )
        total_res = await self.session.execute(count_stmt)
        total_count = total_res.scalar() or 0

        # Paginated items query
        query_stmt = select(Scan).where(*base_filters)
        if crop and crop.strip():
            query_stmt = query_stmt.join(Crop, Scan.crop_id == Crop.id).where(
                Crop.name == crop.strip().lower()
            )

        # Stable ordering: primary created_at, secondary id
        if sort_order and sort_order.strip().lower() == "asc":
            query_stmt = query_stmt.order_by(Scan.created_at.asc(), Scan.id.asc())
        else:
            query_stmt = query_stmt.order_by(Scan.created_at.desc(), Scan.id.desc())

        offset = max(0, (page - 1) * page_size)
        query_stmt = query_stmt.limit(page_size).offset(offset).options(
            selectinload(Scan.crop),
            selectinload(Scan.farm),
            selectinload(Scan.prediction).selectinload(Prediction.disease),
            selectinload(Scan.reports),
        )

        records_res = await self.session.execute(query_stmt)
        scans = records_res.scalars().all()
        return scans, total_count

    async def get_user_scan_detail(
        self, scan_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Scan]:
        """
        Fetch a single scan by ID scoped strictly to the authenticated user with all diagnostic details loaded.
        """
        stmt = (
            select(Scan)
            .where(Scan.id == scan_id, Scan.user_id == user_id)
            .options(
                selectinload(Scan.crop),
                selectinload(Scan.farm),
                selectinload(Scan.prediction).selectinload(Prediction.disease),
                selectinload(Scan.reports),
                selectinload(Scan.weather_snapshot),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_user_scans(
        self, user_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> Sequence[Scan]:
        """Fetch scan history for a specific user (legacy overview helper)."""
        stmt = (
            select(Scan)
            .where(Scan.user_id == user_id)
            .order_by(Scan.created_at.desc(), Scan.id.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Scan.prediction).selectinload(Prediction.disease),
                selectinload(Scan.crop),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_scan_stats(self, user_id: uuid.UUID) -> dict:
        """Calculate summary scan counts and breakdown for the authenticated user."""
        from sqlalchemy import func
        from models import Disease

        total_stmt = select(func.count(Scan.id)).where(Scan.user_id == user_id)
        total_res = await self.session.execute(total_stmt)
        total_scans = total_res.scalar() or 0

        # Healthy scans
        healthy_stmt = (
            select(func.count(Scan.id))
            .join(Prediction, Scan.id == Prediction.scan_id)
            .join(Disease, Prediction.disease_id == Disease.id)
            .where(Scan.user_id == user_id, Disease.label.ilike("%healthy%"))
        )
        healthy_res = await self.session.execute(healthy_stmt)
        healthy_scans = healthy_res.scalar() or 0

        # Issues detected (total confident non-healthy scans)
        issues_detected = max(0, total_scans - healthy_scans)

        return {
            "total_scans": total_scans,
            "healthy_scans": healthy_scans,
            "issues_detected": issues_detected,
        }

    async def get_user_recent_reports(
        self, user_id: uuid.UUID, limit: int = 5
    ) -> Sequence:
        """Fetch recent LLM advisory reports generated for the user's scans."""
        from models import Report
        stmt = (
            select(Report)
            .join(Scan, Report.scan_id == Scan.id)
            .where(Scan.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def create_scan_record(
        self,
        crop_id: int,
        image_path: str,
        user_id: Optional[uuid.UUID] = None,
        farm_id: Optional[uuid.UUID] = None,
        status: str = "completed",
    ) -> Scan:
        """Create and persist a new Scan record."""
        scan = Scan(
            crop_id=crop_id,
            image_path=image_path,
            user_id=user_id,
            farm_id=farm_id,
            status=status,
        )
        self.session.add(scan)
        await self.session.flush()
        return scan

    async def create_prediction_record(
        self,
        scan_id: uuid.UUID,
        disease_id: Optional[int],
        confidence: float,
        is_confident: bool,
        raw_scores: Optional[dict] = None,
        threshold_used: Optional[float] = None,
        model_version_id: int = 1,
    ) -> Prediction:
        """Create and persist a Prediction record associated with a Scan."""
        import config
        prediction = Prediction(
            scan_id=scan_id,
            disease_id=disease_id,
            model_version_id=model_version_id,
            confidence=confidence,
            threshold_used=(
                threshold_used if threshold_used is not None else config.CONFIDENCE_THRESHOLD
            ),
            is_confident=is_confident,
            raw_scores=raw_scores or {},
        )
        self.session.add(prediction)
        await self.session.flush()
        return prediction
