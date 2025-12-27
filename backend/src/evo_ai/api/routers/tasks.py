"""Task execution and job management endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import structlog

from evo_ai.tasks import (
    execute_round_task,
    execute_campaign_task,
    job_tracker,
    JobStatus,
)
from evo_ai.tasks.campaign_tasks import get_task_status, cancel_task

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])


class AsyncRoundRequest(BaseModel):
    """Request schema for async round execution."""
    round_number: int
    trace_id: Optional[UUID] = None


class AsyncCampaignRequest(BaseModel):
    """Request schema for async campaign execution."""
    max_rounds: Optional[int] = None
    trace_id: Optional[UUID] = None


class JobResponse(BaseModel):
    """Response schema for job status."""
    job_id: str
    task_type: str
    status: str
    campaign_id: Optional[str]
    round_number: Optional[int]
    progress: float
    result: Optional[dict]
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[float]


@router.post("/rounds/execute", response_model=dict)
async def execute_round_async(
    campaign_id: UUID,
    request: AsyncRoundRequest
) -> dict:
    """
    Execute a round asynchronously using Ray.

    Args:
        campaign_id: Campaign UUID
        request: Round execution request

    Returns:
        Job information with job_id for status tracking

    Example:
        POST /api/tasks/rounds/execute?campaign_id={uuid}
        {
            "round_number": 5,
            "trace_id": "optional-uuid"
        }

        Response:
        {
            "job_id": "uuid",
            "status": "pending",
            "task_type": "execute_round",
            "campaign_id": "uuid",
            "round_number": 5,
            "trace_id": "uuid"
        }

        Then poll: GET /api/tasks/{job_id}
    """
    logger.info(
        "submitting_round_task",
        campaign_id=str(campaign_id),
        round_number=request.round_number
    )

    try:
        result = execute_round_task(
            campaign_id=campaign_id,
            round_number=request.round_number,
            trace_id=request.trace_id,
            async_execution=True
        )

        return result

    except Exception as e:
        logger.error(
            "round_task_submission_failed",
            campaign_id=str(campaign_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaigns/execute", response_model=dict)
async def execute_campaign_async(
    campaign_id: UUID,
    request: AsyncCampaignRequest
) -> dict:
    """
    Execute entire campaign asynchronously using Ray.

    Args:
        campaign_id: Campaign UUID
        request: Campaign execution request

    Returns:
        Job information with job_id for status tracking

    Example:
        POST /api/tasks/campaigns/execute?campaign_id={uuid}
        {
            "max_rounds": 20,
            "trace_id": "optional-uuid"
        }

        Response:
        {
            "job_id": "uuid",
            "status": "pending",
            "task_type": "execute_campaign",
            "campaign_id": "uuid",
            "max_rounds": 20,
            "trace_id": "uuid"
        }
    """
    logger.info(
        "submitting_campaign_task",
        campaign_id=str(campaign_id),
        max_rounds=request.max_rounds
    )

    try:
        result = execute_campaign_task(
            campaign_id=campaign_id,
            max_rounds=request.max_rounds,
            trace_id=request.trace_id,
            async_execution=True
        )

        return result

    except Exception as e:
        logger.error(
            "campaign_task_submission_failed",
            campaign_id=str(campaign_id),
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: UUID) -> JobResponse:
    """
    Get job status by ID.

    Args:
        job_id: Job UUID

    Returns:
        Job status and results

    Example:
        GET /api/tasks/{job_id}

        Response:
        {
            "job_id": "uuid",
            "task_type": "execute_round",
            "status": "completed",
            "campaign_id": "uuid",
            "round_number": 5,
            "progress": 1.0,
            "result": {
                "round_id": "uuid",
                "variants_generated": 10,
                "average_score": 0.85
            },
            "error": null,
            "created_at": "2025-01-15T10:00:00Z",
            "started_at": "2025-01-15T10:00:05Z",
            "completed_at": "2025-01-15T10:05:00Z",
            "duration_seconds": 295.0
        }
    """
    status = get_task_status(job_id)

    if not status:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(**status)


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    campaign_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
) -> List[JobResponse]:
    """
    List jobs with optional filters.

    Args:
        campaign_id: Filter by campaign
        status: Filter by status (pending, running, completed, failed, cancelled)
        limit: Maximum number of jobs to return

    Returns:
        List of jobs
    """
    job_status = JobStatus(status) if status else None

    jobs = job_tracker.list_jobs(
        campaign_id=campaign_id,
        status=job_status
    )

    # Limit results
    jobs = jobs[:limit]

    return [
        JobResponse(
            job_id=str(job.job_id),
            task_type=job.task_type,
            status=job.status.value,
            campaign_id=str(job.campaign_id) if job.campaign_id else None,
            round_number=job.round_number,
            progress=job.progress,
            result=job.result,
            error=job.error,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            duration_seconds=job.duration_seconds
        )
        for job in jobs
    ]


@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_job(job_id: UUID) -> dict:
    """
    Cancel a running job.

    Args:
        job_id: Job UUID

    Returns:
        Cancellation status

    Example:
        POST /api/tasks/{job_id}/cancel

        Response:
        {
            "job_id": "uuid",
            "cancelled": true
        }
    """
    cancelled = cancel_task(job_id)

    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Job not found or already completed"
        )

    logger.info("job_cancelled_via_api", job_id=str(job_id))

    return {
        "job_id": str(job_id),
        "cancelled": True
    }


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: UUID) -> None:
    """
    Delete a job from the tracker.

    Args:
        job_id: Job UUID
    """
    deleted = job_tracker.delete_job(job_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info("job_deleted_via_api", job_id=str(job_id))
