"""Report query endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.api.dependencies import get_db
from evo_ai.api.schemas import ReportResponse, ReportList
from evo_ai.infrastructure.database.repositories.postgres_report_repo import (
    PostgresReportRepository
)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=ReportList)
async def list_reports(
    campaign_id: Optional[UUID] = None,
    round_id: Optional[UUID] = None,
    report_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> ReportList:
    """
    List reports with filters.

    Args:
        campaign_id: Filter by campaign
        round_id: Filter by round
        report_type: Filter by report type
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        Paginated list of reports
    """
    repo = PostgresReportRepository(db)

    if campaign_id:
        reports = await repo.get_by_campaign_id(campaign_id)
    else:
        # Would implement get_all in production
        reports = []

    # Apply filters
    if round_id:
        reports = [r for r in reports if r.round_id == round_id]
    if report_type:
        reports = [r for r in reports if r.report_type.value == report_type]

    # Pagination
    total = len(reports)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = reports[start:end]

    return ReportList(
        reports=[ReportResponse.model_validate(r) for r in paginated],
        total=total
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """
    Get report by ID.

    Args:
        report_id: Report UUID
        db: Database session

    Returns:
        Report details with full content
    """
    repo = PostgresReportRepository(db)
    report = await repo.get_by_id(report_id)

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse.model_validate(report)
