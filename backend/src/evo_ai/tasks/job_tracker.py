"""Job tracking for Ray tasks."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(BaseModel):
    """Job tracking model."""
    job_id: UUID = Field(default_factory=uuid4)
    task_type: str  # "execute_round", "execute_campaign", etc.
    status: JobStatus = JobStatus.PENDING
    campaign_id: Optional[UUID] = None
    round_number: Optional[int] = None
    trace_id: Optional[UUID] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()


class JobTracker:
    """
    In-memory job tracker for Ray tasks.

    In production, this would persist to Redis or database.
    """

    def __init__(self):
        """Initialize job tracker."""
        self._jobs: Dict[UUID, Job] = {}
        logger.info("job_tracker_initialized")

    def create_job(
        self,
        task_type: str,
        campaign_id: Optional[UUID] = None,
        round_number: Optional[int] = None,
        trace_id: Optional[UUID] = None
    ) -> Job:
        """
        Create a new job.

        Args:
            task_type: Type of task
            campaign_id: Optional campaign ID
            round_number: Optional round number
            trace_id: Optional trace ID

        Returns:
            Created job
        """
        job = Job(
            task_type=task_type,
            campaign_id=campaign_id,
            round_number=round_number,
            trace_id=trace_id
        )

        self._jobs[job.job_id] = job

        logger.info(
            "job_created",
            job_id=str(job.job_id),
            task_type=task_type,
            campaign_id=str(campaign_id) if campaign_id else None
        )

        return job

    def get_job(self, job_id: UUID) -> Optional[Job]:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[Job]:
        """
        Update job status.

        Args:
            job_id: Job UUID
            status: New status
            progress: Optional progress update (0.0-1.0)
            result: Optional result data
            error: Optional error message

        Returns:
            Updated job or None if not found
        """
        job = self._jobs.get(job_id)
        if not job:
            logger.warning("job_not_found", job_id=str(job_id))
            return None

        job.status = status

        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.utcnow()

        if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = datetime.utcnow()

        if progress is not None:
            job.progress = min(max(progress, 0.0), 1.0)

        if result is not None:
            job.result = result

        if error is not None:
            job.error = error

        logger.info(
            "job_status_updated",
            job_id=str(job_id),
            status=status.value,
            progress=job.progress
        )

        return job

    def list_jobs(
        self,
        campaign_id: Optional[UUID] = None,
        status: Optional[JobStatus] = None
    ) -> list[Job]:
        """
        List jobs with optional filters.

        Args:
            campaign_id: Filter by campaign
            status: Filter by status

        Returns:
            List of matching jobs
        """
        jobs = list(self._jobs.values())

        if campaign_id:
            jobs = [j for j in jobs if j.campaign_id == campaign_id]

        if status:
            jobs = [j for j in jobs if j.status == status]

        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def delete_job(self, job_id: UUID) -> bool:
        """
        Delete job.

        Args:
            job_id: Job UUID

        Returns:
            True if deleted, False if not found
        """
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.info("job_deleted", job_id=str(job_id))
            return True
        return False

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Cleanup completed jobs older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of jobs deleted
        """
        cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        to_delete = []

        for job_id, job in self._jobs.items():
            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                if job.completed_at and job.completed_at.timestamp() < cutoff:
                    to_delete.append(job_id)

        for job_id in to_delete:
            del self._jobs[job_id]

        if to_delete:
            logger.info("jobs_cleaned_up", count=len(to_delete))

        return len(to_delete)


# Global job tracker instance
job_tracker = JobTracker()
