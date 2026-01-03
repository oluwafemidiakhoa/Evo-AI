"""Ray tasks for campaign and round execution."""

from typing import Any, Dict, Optional
from uuid import UUID, uuid4
import asyncio
import os
import threading

import ray
import structlog

from evo_ai.agents.implementations.orchestrator import AgentOrchestrator
from evo_ai.mcp.registry import mcp_registry
from evo_ai.tasks.job_tracker import job_tracker, JobStatus

logger = structlog.get_logger(__name__)


def _use_ray() -> bool:
    """Return True when Ray should be used for execution."""
    flag = os.getenv("EVO_AI_USE_RAY", "").strip().lower()
    return flag in ("1", "true", "yes")


def _run_round_local(
    job_id: UUID,
    campaign_id: UUID,
    round_number: int,
    trace_id: UUID
) -> None:
    """Run a round without Ray and update job status."""
    job_tracker.update_status(job_id, JobStatus.RUNNING, progress=0.0)
    try:
        orchestrator = AgentOrchestrator(mcp_registry)
        result = asyncio.run(
            orchestrator.execute_round(
                campaign_id=campaign_id,
                round_number=round_number,
                trace_id=trace_id
            )
        )
        job_tracker.update_status(job_id, JobStatus.COMPLETED, progress=1.0, result=result)
    except Exception as exc:
        logger.error(
            "local_round_execution_failed",
            campaign_id=str(campaign_id),
            round_number=round_number,
            error=str(exc)
        )
        job_tracker.update_status(job_id, JobStatus.FAILED, error=str(exc))


def _run_campaign_local(
    job_id: UUID,
    campaign_id: UUID,
    max_rounds: Optional[int],
    trace_id: UUID
) -> None:
    """Run a campaign without Ray and update job status."""
    job_tracker.update_status(job_id, JobStatus.RUNNING, progress=0.0)
    try:
        orchestrator = AgentOrchestrator(mcp_registry)
        result = asyncio.run(
            orchestrator.execute_campaign(
                campaign_id=campaign_id,
                max_rounds=max_rounds
            )
        )
        job_tracker.update_status(job_id, JobStatus.COMPLETED, progress=1.0, result=result)
    except Exception as exc:
        logger.error(
            "local_campaign_execution_failed",
            campaign_id=str(campaign_id),
            error=str(exc)
        )
        job_tracker.update_status(job_id, JobStatus.FAILED, error=str(exc))


@ray.remote
def execute_round_remote(
    campaign_id: str,
    round_number: int,
    trace_id: Optional[str] = None,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ray remote function for executing a single round.

    Args:
        campaign_id: Campaign UUID as string
        round_number: Round number to execute
        trace_id: Optional trace ID
        job_id: Optional job ID for tracking

    Returns:
        Round execution results
    """
    campaign_uuid = UUID(campaign_id)
    trace_uuid = UUID(trace_id) if trace_id else uuid4()
    job_uuid = UUID(job_id) if job_id else None

    logger.info(
        "ray_round_execution_started",
        campaign_id=campaign_id,
        round_number=round_number,
        trace_id=str(trace_uuid),
        job_id=job_id
    )

    # Update job status
    if job_uuid:
        job_tracker.update_status(job_uuid, JobStatus.RUNNING, progress=0.0)

    try:
        # Create orchestrator
        orchestrator = AgentOrchestrator(mcp_registry)

        # Execute round
        result = ray.get(
            orchestrator.execute_round(
                campaign_id=campaign_uuid,
                round_number=round_number,
                trace_id=trace_uuid
            )
        )

        # Update job status
        if job_uuid:
            job_tracker.update_status(
                job_uuid,
                JobStatus.COMPLETED,
                progress=1.0,
                result=result
            )

        logger.info(
            "ray_round_execution_completed",
            campaign_id=campaign_id,
            round_number=round_number,
            job_id=job_id
        )

        return result

    except Exception as e:
        logger.error(
            "ray_round_execution_failed",
            campaign_id=campaign_id,
            round_number=round_number,
            error=str(e),
            job_id=job_id
        )

        # Update job status
        if job_uuid:
            job_tracker.update_status(
                job_uuid,
                JobStatus.FAILED,
                error=str(e)
            )

        raise


@ray.remote
def execute_campaign_remote(
    campaign_id: str,
    max_rounds: Optional[int] = None,
    trace_id: Optional[str] = None,
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Ray remote function for executing entire campaign.

    Args:
        campaign_id: Campaign UUID as string
        max_rounds: Maximum rounds to execute
        trace_id: Optional trace ID
        job_id: Optional job ID for tracking

    Returns:
        Campaign execution results
    """
    campaign_uuid = UUID(campaign_id)
    trace_uuid = UUID(trace_id) if trace_id else uuid4()
    job_uuid = UUID(job_id) if job_id else None

    logger.info(
        "ray_campaign_execution_started",
        campaign_id=campaign_id,
        max_rounds=max_rounds,
        trace_id=str(trace_uuid),
        job_id=job_id
    )

    # Update job status
    if job_uuid:
        job_tracker.update_status(job_uuid, JobStatus.RUNNING, progress=0.0)

    try:
        # Create orchestrator
        orchestrator = AgentOrchestrator(mcp_registry)

        # Execute campaign
        result = ray.get(
            orchestrator.execute_campaign(
                campaign_id=campaign_uuid,
                max_rounds=max_rounds
            )
        )

        # Update job status
        if job_uuid:
            job_tracker.update_status(
                job_uuid,
                JobStatus.COMPLETED,
                progress=1.0,
                result=result
            )

        logger.info(
            "ray_campaign_execution_completed",
            campaign_id=campaign_id,
            job_id=job_id
        )

        return result

    except Exception as e:
        logger.error(
            "ray_campaign_execution_failed",
            campaign_id=campaign_id,
            error=str(e),
            job_id=job_id
        )

        # Update job status
        if job_uuid:
            job_tracker.update_status(
                job_uuid,
                JobStatus.FAILED,
                error=str(e)
            )

        raise


def execute_round_task(
    campaign_id: UUID,
    round_number: int,
    trace_id: Optional[UUID] = None,
    async_execution: bool = True
) -> Dict[str, Any]:
    """
    Submit round execution task to Ray.

    Args:
        campaign_id: Campaign UUID
        round_number: Round number to execute
        trace_id: Optional trace ID
        async_execution: If True, return immediately with job_id. If False, wait for completion.

    Returns:
        If async: {"job_id": UUID, "status": "pending"}
        If sync: Round execution results
    """
    trace_uuid = trace_id or uuid4()

    # Create job
    job = job_tracker.create_job(
        task_type="execute_round",
        campaign_id=campaign_id,
        round_number=round_number,
        trace_id=trace_uuid
    )

    if _use_ray():
        try:
            task_ref = execute_round_remote.remote(
                campaign_id=str(campaign_id),
                round_number=round_number,
                trace_id=str(trace_uuid),
                job_id=str(job.job_id)
            )

            if async_execution:
                return {
                    "job_id": str(job.job_id),
                    "status": job.status.value,
                    "task_type": "execute_round",
                    "campaign_id": str(campaign_id),
                    "round_number": round_number,
                    "trace_id": str(trace_uuid)
                }
            result = ray.get(task_ref)
            return result
        except Exception as exc:
            logger.warning("ray_unavailable_fallback", error=str(exc))

    if async_execution:
        thread = threading.Thread(
            target=_run_round_local,
            args=(job.job_id, campaign_id, round_number, trace_uuid),
            daemon=True
        )
        thread.start()
        return {
            "job_id": str(job.job_id),
            "status": job.status.value,
            "task_type": "execute_round",
            "campaign_id": str(campaign_id),
            "round_number": round_number,
            "trace_id": str(trace_uuid)
        }

    _run_round_local(job.job_id, campaign_id, round_number, trace_uuid)
    status = job_tracker.get_job(job.job_id)
    return status.result if status and status.result else {}


def execute_campaign_task(
    campaign_id: UUID,
    max_rounds: Optional[int] = None,
    trace_id: Optional[UUID] = None,
    async_execution: bool = True
) -> Dict[str, Any]:
    """
    Submit campaign execution task to Ray.

    Args:
        campaign_id: Campaign UUID
        max_rounds: Maximum rounds to execute
        trace_id: Optional trace ID
        async_execution: If True, return immediately with job_id. If False, wait for completion.

    Returns:
        If async: {"job_id": UUID, "status": "pending"}
        If sync: Campaign execution results
    """
    trace_uuid = trace_id or uuid4()

    # Create job
    job = job_tracker.create_job(
        task_type="execute_campaign",
        campaign_id=campaign_id,
        trace_id=trace_uuid
    )

    if _use_ray():
        try:
            task_ref = execute_campaign_remote.remote(
                campaign_id=str(campaign_id),
                max_rounds=max_rounds,
                trace_id=str(trace_uuid),
                job_id=str(job.job_id)
            )

            if async_execution:
                return {
                    "job_id": str(job.job_id),
                    "status": job.status.value,
                    "task_type": "execute_campaign",
                    "campaign_id": str(campaign_id),
                    "max_rounds": max_rounds,
                    "trace_id": str(trace_uuid)
                }
            result = ray.get(task_ref)
            return result
        except Exception as exc:
            logger.warning("ray_unavailable_fallback", error=str(exc))

    if async_execution:
        thread = threading.Thread(
            target=_run_campaign_local,
            args=(job.job_id, campaign_id, max_rounds, trace_uuid),
            daemon=True
        )
        thread.start()
        return {
            "job_id": str(job.job_id),
            "status": job.status.value,
            "task_type": "execute_campaign",
            "campaign_id": str(campaign_id),
            "max_rounds": max_rounds,
            "trace_id": str(trace_uuid)
        }

    _run_campaign_local(job.job_id, campaign_id, max_rounds, trace_uuid)
    status = job_tracker.get_job(job.job_id)
    return status.result if status and status.result else {}


def get_task_status(job_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get task status by job ID.

    Args:
        job_id: Job UUID

    Returns:
        Job status dictionary or None if not found
    """
    job = job_tracker.get_job(job_id)

    if not job:
        return None

    return {
        "job_id": str(job.job_id),
        "task_type": job.task_type,
        "status": job.status.value,
        "campaign_id": str(job.campaign_id) if job.campaign_id else None,
        "round_number": job.round_number,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_seconds": job.duration_seconds,
    }


def cancel_task(job_id: UUID) -> bool:
    """
    Cancel a running task.

    Args:
        job_id: Job UUID

    Returns:
        True if cancelled, False if not found or already completed
    """
    job = job_tracker.get_job(job_id)

    if not job:
        return False

    if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
        return False

    # Update status to cancelled
    job_tracker.update_status(job_id, JobStatus.CANCELLED)

    logger.info("task_cancelled", job_id=str(job_id))

    return True
