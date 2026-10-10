"""
backend/repositories/report_repository.py
=========================================
Repository for storing and querying LLM Advisory Report entities in PostgreSQL.
"""

from datetime import datetime, timezone
from typing import List, Optional, Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Report
from .base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session: AsyncSession):
        super().__init__(Report, session)

    async def get_report_by_scan_and_lang(
        self, scan_id: uuid.UUID, language_code: str = "en"
    ) -> Optional[Report]:
        """Fetch the advisory report for a scan matching the requested language code."""
        stmt = select(Report).where(
            Report.scan_id == scan_id, Report.language_code == language_code
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_reports_for_scan(self, scan_id: uuid.UUID) -> Sequence[Report]:
        """Fetch all reports generated across languages for a given scan."""
        stmt = (
            select(Report)
            .where(Report.scan_id == scan_id)
            .order_by(Report.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_report(
        self,
        scan_id: uuid.UUID,
        language_code: str,
        disease_name: str,
        summary: str,
        confidence_interpretation: Optional[str] = None,
        symptoms: Optional[List[str]] = None,
        possible_causes: Optional[List[str]] = None,
        local_context: Optional[str] = None,
        management_steps: Optional[List[str]] = None,
        prevention_steps: Optional[List[str]] = None,
        warning_signs: Optional[List[str]] = None,
        expert_verification_recommended: bool = False,
        disclaimer: Optional[str] = None,
        generated_at: Optional[datetime] = None,
    ) -> Report:
        """Create and persist a new Report record in PostgreSQL."""
        report = Report(
            scan_id=scan_id,
            language_code=language_code,
            disease_name=disease_name,
            confidence_interpretation=confidence_interpretation,
            summary=summary,
            symptoms=symptoms or [],
            possible_causes=possible_causes or [],
            local_context=local_context,
            management_steps=management_steps or [],
            prevention_steps=prevention_steps or [],
            warning_signs=warning_signs or [],
            expert_verification_recommended=expert_verification_recommended,
            disclaimer=disclaimer,
            generated_at=generated_at or datetime.now(timezone.utc),
        )
        self.session.add(report)
        await self.session.flush()
        return report
