"""Variant query endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from evo_ai.agents.tools import LineageTool
from evo_ai.agents.base import AgentContext
from evo_ai.api.dependencies import get_db
from evo_ai.api.schemas import VariantResponse, VariantList, LineageResponse
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/variants", tags=["variants"])


@router.get("", response_model=VariantList)
async def list_variants(
    round_id: Optional[UUID] = None,
    campaign_id: Optional[UUID] = None,
    selected_only: bool = False,
    generation: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> VariantList:
    """
    List variants with filters.

    Args:
        round_id: Filter by round
        campaign_id: Filter by campaign (requires joining rounds)
        selected_only: Only show selected variants
        generation: Filter by generation number
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        Paginated list of variants
    """
    repo = PostgresVariantRepository(db)

    if round_id:
        if selected_only:
            variants = await repo.get_selected_by_round(round_id)
        else:
            variants = await repo.get_by_round_id(round_id)
    else:
        # Get all variants (in production, would optimize this)
        variants = []
        logger.warning("listing_all_variants_not_optimized")

    # Apply filters
    if generation is not None:
        variants = [v for v in variants if v.generation == generation]

    # Pagination
    total = len(variants)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = variants[start:end]

    return VariantList(
        variants=[VariantResponse.model_validate(v) for v in paginated],
        total=total
    )


@router.get("/{variant_id}", response_model=VariantResponse)
async def get_variant(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> VariantResponse:
    """
    Get variant by ID.

    Args:
        variant_id: Variant UUID
        db: Database session

    Returns:
        Variant details
    """
    repo = PostgresVariantRepository(db)
    variant = await repo.get_by_id(variant_id)

    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    return VariantResponse.model_validate(variant)


@router.get("/{variant_id}/lineage", response_model=LineageResponse)
async def get_variant_lineage(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> LineageResponse:
    """
    Get variant's full lineage (ancestry chain).

    Args:
        variant_id: Variant UUID
        db: Database session

    Returns:
        Lineage information with all ancestors

    Example:
        GET /api/variants/{variant_id}/lineage

        Response:
        {
            "variant_id": "...",
            "lineage": [
                {"id": "...", "generation": 5, "mutation_type": "refactor"},
                {"id": "...", "generation": 4, "mutation_type": "optimize"},
                {"id": "...", "generation": 3, "mutation_type": "expand"},
                {"id": "...", "generation": 0, "mutation_type": null}
            ],
            "generations": 6,
            "founder": {"id": "...", "generation": 0}
        }
    """
    # Verify variant exists
    repo = PostgresVariantRepository(db)
    variant = await repo.get_by_id(variant_id)

    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    # Get lineage using LineageTool
    context = AgentContext(
        trace_id=UUID("00000000-0000-0000-0000-000000000000"),  # Dummy trace for API
        campaign_id=UUID("00000000-0000-0000-0000-000000000000"),  # Would get from variant
        variant_id=variant_id
    )

    lineage = await LineageTool.get_full_lineage(context, variant_id)

    return LineageResponse(
        variant_id=variant_id,
        lineage=lineage.get("lineage", []),
        generations=lineage.get("generations", 0),
        founder=lineage.get("founder")
    )


@router.get("/{variant_id}/descendants", response_model=VariantList)
async def get_variant_descendants(
    variant_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> VariantList:
    """
    Get all descendants of a variant.

    Args:
        variant_id: Parent variant UUID
        db: Database session

    Returns:
        List of descendant variants
    """
    repo = PostgresVariantRepository(db)
    variant = await repo.get_by_id(variant_id)

    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")

    descendants = await repo.get_descendants(variant_id)

    return VariantList(
        variants=[VariantResponse.model_validate(v) for v in descendants],
        total=len(descendants)
    )
