"""PostgreSQL implementation of Report repository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.domain.models.report import Report
from evo_ai.infrastructure.database.models import ReportDB


class PostgresReportRepository:
    """PostgreSQL implementation of ReportRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, entity: Report) -> Report:
        """Create a new report."""
        db_report = ReportDB(
            id=entity.id,
            round_id=entity.round_id,
            report_type=entity.report_type,
            format=entity.format,
            content=entity.content,
            storage_path=entity.storage_path,
            meta_data=entity.meta_data,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(db_report)
        await self.session.flush()
        return self._to_domain(db_report)

    async def get_by_id(self, entity_id: UUID) -> Optional[Report]:
        """Retrieve report by ID."""
        result = await self.session.execute(
            select(ReportDB).where(ReportDB.id == entity_id)
        )
        db_report = result.scalar_one_or_none()
        return self._to_domain(db_report) if db_report else None

    async def get_by_round_id(self, round_id: UUID) -> List[Report]:
        """Retrieve all reports for a round."""
        result = await self.session.execute(
            select(ReportDB)
            .where(ReportDB.round_id == round_id)
            .order_by(desc(ReportDB.created_at))
        )
        db_reports = result.scalars().all()
        return [self._to_domain(db_r) for db_r in db_reports]

    async def update(self, entity: Report) -> Report:
        """Update an existing report."""
        result = await self.session.execute(
            select(ReportDB).where(ReportDB.id == entity.id)
        )
        db_report = result.scalar_one_or_none()

        if not db_report:
            raise ValueError(f"Report {entity.id} not found")

        # Update fields
        db_report.report_type = entity.report_type
        db_report.format = entity.format
        db_report.content = entity.content
        db_report.storage_path = entity.storage_path
        db_report.meta_data = entity.meta_data
        db_report.updated_at = datetime.utcnow()

        await self.session.flush()
        return self._to_domain(db_report)

    @staticmethod
    def _to_domain(db_report: ReportDB) -> Report:
        """Convert database model to domain model."""
        return Report(
            id=db_report.id,
            round_id=db_report.round_id,
            report_type=db_report.report_type,
            format=db_report.format,
            content=db_report.content,
            storage_path=db_report.storage_path,
            meta_data=db_report.meta_data,
            created_at=db_report.created_at,
            updated_at=db_report.updated_at,
        )
