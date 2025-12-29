"""Round execution endpoints."""

from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from evo_ai.agents.implementations.orchestrator import AgentOrchestrator
from evo_ai.api.dependencies import get_db, get_orchestrator
from evo_ai.api.schemas import (
    RoundResponse,
    RoundExecutionRequest,
    RoundExecutionResponse,
    RoundStats,
)
from evo_ai.infrastructure.database.repositories.postgres_round_repo import (
    PostgresRoundRepository
)
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)
from evo_ai.infrastructure.database.repositories.postgres_evaluation_repo import (
    PostgresEvaluationRepository
)
from evo_ai.domain.models.evaluation import EvaluationStatus

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/campaigns/{campaign_id}/rounds", tags=["rounds"])


@router.get("", response_model=List[RoundResponse])
async def list_rounds(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> List[RoundResponse]:
    """
    List all rounds for a campaign.

    Args:
        campaign_id: Campaign UUID
        db: Database session

    Returns:
        List of rounds
    """
    repo = PostgresRoundRepository(db)
    rounds = await repo.get_by_campaign(campaign_id)

    return [RoundResponse.model_validate(r) for r in rounds]


@router.get("/{round_number}", response_model=RoundResponse)
async def get_round(
    campaign_id: UUID,
    round_number: int,
    db: AsyncSession = Depends(get_db)
) -> RoundResponse:
    """
    Get round by number.

    Args:
        campaign_id: Campaign UUID
        round_number: Round number
        db: Database session

    Returns:
        Round details
    """
    repo = PostgresRoundRepository(db)
    rounds = await repo.get_by_campaign(campaign_id)

    round_obj = next((r for r in rounds if r.round_number == round_number), None)

    if not round_obj:
        raise HTTPException(status_code=404, detail="Round not found")

    return RoundResponse.model_validate(round_obj)


@router.post("/{round_number}/execute", response_model=RoundExecutionResponse)
async def execute_round(
    campaign_id: UUID,
    round_number: int,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> RoundExecutionResponse:
    """
    Execute a specific round.

    Args:
        campaign_id: Campaign UUID
        round_number: Round number to execute
        orchestrator: Agent orchestrator

    Returns:
        Round execution results

    Example:
        POST /api/campaigns/{campaign_id}/rounds/5/execute

        Response:
        {
            "round_id": "...",
            "round_number": 5,
            "status": "completed",
            "variants_generated": 10,
            "variants_evaluated": 10,
            "variants_selected": 5,
            "average_score": 0.82,
            "report_id": "...",
            "trace_id": "..."
        }
    """
    logger.info(
        "executing_round",
        campaign_id=str(campaign_id),
        round_number=round_number
    )

    try:
        result = await orchestrator.execute_round(
            campaign_id=campaign_id,
            round_number=round_number
        )

        return RoundExecutionResponse(
            round_id=UUID(result["round_id"]),
            round_number=result["round_number"],
            status=result["status"],
            variants_generated=result["variants_generated"],
            variants_evaluated=result["variants_evaluated"],
            variants_selected=result["variants_selected"],
            average_score=result.get("average_score"),
            report_id=UUID(result["report_id"]),
            trace_id=UUID(result["trace_id"])
        )

    except Exception as e:
        logger.error(
            "round_execution_failed",
            campaign_id=str(campaign_id),
            round_number=round_number,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{round_number}/stats", response_model=RoundStats)
async def get_round_stats(
    campaign_id: UUID,
    round_number: int,
    db: AsyncSession = Depends(get_db)
) -> RoundStats:
    """
    Get round statistics.

    Args:
        campaign_id: Campaign UUID
        round_number: Round number
        db: Database session

    Returns:
        Round statistics
    """
    # Get round
    round_repo = PostgresRoundRepository(db)
    rounds = await round_repo.get_by_campaign(campaign_id)
    round_obj = next((r for r in rounds if r.round_number == round_number), None)

    if not round_obj:
        raise HTTPException(status_code=404, detail="Round not found")

    # Get variants
    variant_repo = PostgresVariantRepository(db)
    variants = await variant_repo.get_by_round_id(round_obj.id)
    selected = [v for v in variants if v.is_selected]

    # Get evaluations
    eval_repo = PostgresEvaluationRepository(db)
    all_evals = []
    for variant in variants:
        evals = await eval_repo.get_by_variant_id(variant.id)
        all_evals.extend(evals)

    completed = [e for e in all_evals if e.status == EvaluationStatus.COMPLETED]
    scores = [e.score for e in completed if e.score is not None]

    return RoundStats(
        round_id=round_obj.id,
        round_number=round_number,
        total_variants=len(variants),
        selected_variants=len(selected),
        average_score=sum(scores) / len(scores) if scores else None,
        min_score=min(scores) if scores else None,
        max_score=max(scores) if scores else None
    )
