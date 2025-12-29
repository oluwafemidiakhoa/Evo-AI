"""Campaign management endpoints."""

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

import structlog

from evo_ai.agents.implementations.orchestrator import AgentOrchestrator
from evo_ai.api.dependencies import get_db, get_orchestrator
from evo_ai.api.schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignList,
    CampaignStats,
    RoundExecutionResponse,
)
from evo_ai.domain.models.campaign import Campaign, CampaignStatus
from evo_ai.infrastructure.database.repositories.postgres_campaign_repo import (
    PostgresCampaignRepository
)
from evo_ai.infrastructure.database.repositories.postgres_round_repo import (
    PostgresRoundRepository
)
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    campaign_data: CampaignCreate,
    db: AsyncSession = Depends(get_db)
) -> CampaignResponse:
    """
    Create a new campaign.

    Args:
        campaign_data: Campaign creation data
        db: Database session

    Returns:
        Created campaign

    Example:
        POST /api/campaigns
        {
            "name": "My Experiment",
            "description": "Testing code evolution",
            "config": {
                "max_rounds": 20,
                "variants_per_round": 10,
                "evaluators": ["llm_judge"]
            }
        }
    """
    logger.info("creating_campaign", name=campaign_data.name)

    campaign = Campaign(
        name=campaign_data.name,
        description=campaign_data.description,
        status=CampaignStatus.DRAFT,
        config=campaign_data.config,
    )

    repo = PostgresCampaignRepository(db)
    saved_campaign = await repo.create(campaign)

    logger.info("campaign_created", campaign_id=str(saved_campaign.id))

    return CampaignResponse.model_validate(saved_campaign)


@router.get("", response_model=CampaignList)
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> CampaignList:
    """
    List campaigns with pagination.

    Args:
        page: Page number (starts at 1)
        page_size: Number of items per page
        status: Optional status filter
        db: Database session

    Returns:
        Paginated list of campaigns
    """
    repo = PostgresCampaignRepository(db)
    campaigns = await repo.get_all()

    # Filter by status if provided
    if status:
        campaigns = [c for c in campaigns if c.status.value == status]

    # Pagination
    total = len(campaigns)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = campaigns[start:end]

    return CampaignList(
        campaigns=[CampaignResponse.model_validate(c) for c in paginated],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> CampaignResponse:
    """
    Get campaign by ID.

    Args:
        campaign_id: Campaign UUID
        db: Database session

    Returns:
        Campaign details
    """
    repo = PostgresCampaignRepository(db)
    campaign = await repo.get_by_id(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    return CampaignResponse.model_validate(campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    update_data: CampaignUpdate,
    db: AsyncSession = Depends(get_db)
) -> CampaignResponse:
    """
    Update campaign.

    Args:
        campaign_id: Campaign UUID
        update_data: Fields to update
        db: Database session

    Returns:
        Updated campaign
    """
    repo = PostgresCampaignRepository(db)
    campaign = await repo.get_by_id(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Update fields
    if update_data.name is not None:
        campaign.name = update_data.name
    if update_data.description is not None:
        campaign.description = update_data.description
    if update_data.config is not None:
        campaign.config = update_data.config

    updated = await repo.update(campaign)

    logger.info("campaign_updated", campaign_id=str(campaign_id))

    return CampaignResponse.model_validate(updated)


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete campaign.

    Args:
        campaign_id: Campaign UUID
        db: Database session
    """
    repo = PostgresCampaignRepository(db)
    campaign = await repo.get_by_id(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    await repo.delete(campaign_id)

    logger.info("campaign_deleted", campaign_id=str(campaign_id))


@router.post("/{campaign_id}/start", response_model=CampaignResponse)
async def start_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> CampaignResponse:
    """
    Start campaign execution.

    Args:
        campaign_id: Campaign UUID
        db: Database session

    Returns:
        Updated campaign with IN_PROGRESS status
    """
    repo = PostgresCampaignRepository(db)
    campaign = await repo.get_by_id(campaign_id)

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if campaign.status != CampaignStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail=f"Campaign must be in DRAFT status to start (current: {campaign.status.value})"
        )

    campaign.status = CampaignStatus.ACTIVE
    updated = await repo.update(campaign)

    logger.info("campaign_started", campaign_id=str(campaign_id))

    return CampaignResponse.model_validate(updated)


@router.post("/{campaign_id}/execute")
async def execute_campaign(
    campaign_id: UUID,
    max_rounds: Optional[int] = None,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator),
    db: AsyncSession = Depends(get_db)
) -> EventSourceResponse:
    """
    Execute campaign with Server-Sent Events for progress.

    Args:
        campaign_id: Campaign UUID
        max_rounds: Maximum rounds to execute
        orchestrator: Agent orchestrator
        db: Database session

    Returns:
        SSE stream with execution progress

    Example:
        POST /api/campaigns/{campaign_id}/execute?max_rounds=10

        # Streams events:
        event: round_started
        data: {"round_number": 1, "status": "in_progress"}

        event: round_completed
        data: {"round_number": 1, "variants_generated": 10, "average_score": 0.75}

        event: campaign_completed
        data: {"status": "completed", "rounds_completed": 10}
    """
    async def event_generator():
        """Generate SSE events during campaign execution."""
        try:
            # Verify campaign exists
            repo = PostgresCampaignRepository(db)
            campaign = await repo.get_by_id(campaign_id)

            if not campaign:
                yield {
                    "event": "error",
                    "data": {"error": "Campaign not found"}
                }
                return

            # Send start event
            yield {
                "event": "campaign_started",
                "data": {
                    "campaign_id": str(campaign_id),
                    "max_rounds": max_rounds or campaign.config.get("max_rounds", 10)
                }
            }

            # Execute campaign (simplified - would use background task in production)
            trace_id = uuid4()
            rounds_to_execute = max_rounds or campaign.config.get("max_rounds", 10)

            for round_num in range(1, rounds_to_execute + 1):
                # Send round start event
                yield {
                    "event": "round_started",
                    "data": {
                        "round_number": round_num,
                        "status": "in_progress"
                    }
                }

                # Execute round
                try:
                    result = await orchestrator.execute_round(
                        campaign_id=campaign_id,
                        round_number=round_num,
                        trace_id=trace_id
                    )

                    # Send round completed event
                    yield {
                        "event": "round_completed",
                        "data": result
                    }

                except Exception as e:
                    yield {
                        "event": "round_failed",
                        "data": {
                            "round_number": round_num,
                            "error": str(e)
                        }
                    }
                    break

            # Send completion event
            yield {
                "event": "campaign_completed",
                "data": {
                    "campaign_id": str(campaign_id),
                    "status": "completed"
                }
            }

        except Exception as e:
            logger.error("campaign_execution_failed", error=str(e))
            yield {
                "event": "error",
                "data": {"error": str(e)}
            }

    return EventSourceResponse(event_generator())


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> CampaignStats:
    """
    Get campaign statistics.

    Args:
        campaign_id: Campaign UUID
        db: Database session

    Returns:
        Campaign statistics
    """
    round_repo = PostgresRoundRepository(db)
    variant_repo = PostgresVariantRepository(db)

    # Get all rounds
    rounds = await round_repo.get_by_campaign(campaign_id)

    # Count variants
    total_variants = 0
    total_selected = 0
    max_generation = 0

    for round_obj in rounds:
        variants = await variant_repo.get_by_round_id(round_obj.id)
        total_variants += len(variants)
        total_selected += sum(1 for v in variants if v.is_selected)
        max_generation = max(max_generation, max((v.generation for v in variants), default=0))

    return CampaignStats(
        campaign_id=campaign_id,
        total_rounds=len(rounds),
        completed_rounds=sum(1 for r in rounds if r.status.value == "completed"),
        total_variants=total_variants,
        total_selected=total_selected,
        max_generation=max_generation,
        selection_rate=total_selected / total_variants if total_variants > 0 else 0.0
    )
