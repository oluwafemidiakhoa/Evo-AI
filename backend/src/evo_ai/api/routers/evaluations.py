"""Evaluation query endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.api.dependencies import get_db
from evo_ai.api.schemas import EvaluationResponse, EvaluationList
from evo_ai.infrastructure.database.repositories.postgres_evaluation_repo import (
    PostgresEvaluationRepository
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("", response_model=EvaluationList)
async def list_evaluations(
    variant_id: Optional[UUID] = None,
    evaluator_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> EvaluationList:
    """
    List evaluations with filters.

    Args:
        variant_id: Filter by variant
        evaluator_type: Filter by evaluator type
        status: Filter by status
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        Paginated list of evaluations
    """
    repo = PostgresEvaluationRepository(db)

    if variant_id:
        evaluations = await repo.get_by_variant_id(variant_id)
    else:
        # Would implement get_all in production
        evaluations = []

    # Apply filters
    if evaluator_type:
        evaluations = [e for e in evaluations if e.evaluator_type == evaluator_type]
    if status:
        evaluations = [e for e in evaluations if e.status.value == status]

    # Pagination
    total = len(evaluations)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = evaluations[start:end]

    return EvaluationList(
        evaluations=[EvaluationResponse.model_validate(e) for e in paginated],
        total=total
    )


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
async def get_evaluation(
    evaluation_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> EvaluationResponse:
    """
    Get evaluation by ID.

    Args:
        evaluation_id: Evaluation UUID
        db: Database session

    Returns:
        Evaluation details
    """
    repo = PostgresEvaluationRepository(db)
    evaluation = await repo.get_by_id(evaluation_id)

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return EvaluationResponse.model_validate(evaluation)
