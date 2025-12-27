"""Tests for job tracker."""

import pytest
from uuid import uuid4

from evo_ai.tasks.job_tracker import JobTracker, JobStatus


@pytest.fixture
def tracker():
    """Create job tracker."""
    return JobTracker()


def test_create_job(tracker):
    """Test job creation."""
    campaign_id = uuid4()
    trace_id = uuid4()

    job = tracker.create_job(
        task_type="execute_round",
        campaign_id=campaign_id,
        round_number=5,
        trace_id=trace_id
    )

    assert job.task_type == "execute_round"
    assert job.campaign_id == campaign_id
    assert job.round_number == 5
    assert job.trace_id == trace_id
    assert job.status == JobStatus.PENDING
    assert job.progress == 0.0


def test_get_job(tracker):
    """Test getting job by ID."""
    job = tracker.create_job(task_type="test")

    retrieved = tracker.get_job(job.job_id)

    assert retrieved is not None
    assert retrieved.job_id == job.job_id
    assert retrieved.task_type == "test"


def test_get_nonexistent_job(tracker):
    """Test getting non-existent job."""
    job = tracker.get_job(uuid4())
    assert job is None


def test_update_status_to_running(tracker):
    """Test updating job status to running."""
    job = tracker.create_job(task_type="test")

    updated = tracker.update_status(job.job_id, JobStatus.RUNNING, progress=0.5)

    assert updated is not None
    assert updated.status == JobStatus.RUNNING
    assert updated.progress == 0.5
    assert updated.started_at is not None
    assert updated.completed_at is None


def test_update_status_to_completed(tracker):
    """Test updating job status to completed."""
    job = tracker.create_job(task_type="test")
    tracker.update_status(job.job_id, JobStatus.RUNNING)

    result = {"success": True}
    updated = tracker.update_status(
        job.job_id,
        JobStatus.COMPLETED,
        progress=1.0,
        result=result
    )

    assert updated is not None
    assert updated.status == JobStatus.COMPLETED
    assert updated.progress == 1.0
    assert updated.result == result
    assert updated.completed_at is not None


def test_update_status_to_failed(tracker):
    """Test updating job status to failed."""
    job = tracker.create_job(task_type="test")

    error = "Something went wrong"
    updated = tracker.update_status(
        job.job_id,
        JobStatus.FAILED,
        error=error
    )

    assert updated is not None
    assert updated.status == JobStatus.FAILED
    assert updated.error == error
    assert updated.completed_at is not None


def test_list_jobs(tracker):
    """Test listing jobs."""
    campaign_id = uuid4()

    # Create jobs
    job1 = tracker.create_job(task_type="test1", campaign_id=campaign_id)
    job2 = tracker.create_job(task_type="test2", campaign_id=campaign_id)
    job3 = tracker.create_job(task_type="test3", campaign_id=uuid4())

    # List all
    all_jobs = tracker.list_jobs()
    assert len(all_jobs) == 3

    # List by campaign
    campaign_jobs = tracker.list_jobs(campaign_id=campaign_id)
    assert len(campaign_jobs) == 2

    # Update status and list by status
    tracker.update_status(job1.job_id, JobStatus.COMPLETED)
    completed = tracker.list_jobs(status=JobStatus.COMPLETED)
    assert len(completed) == 1


def test_delete_job(tracker):
    """Test deleting job."""
    job = tracker.create_job(task_type="test")

    deleted = tracker.delete_job(job.job_id)
    assert deleted is True

    retrieved = tracker.get_job(job.job_id)
    assert retrieved is None


def test_delete_nonexistent_job(tracker):
    """Test deleting non-existent job."""
    deleted = tracker.delete_job(uuid4())
    assert deleted is False


def test_duration_calculation(tracker):
    """Test job duration calculation."""
    job = tracker.create_job(task_type="test")

    # Not started yet
    assert job.duration_seconds is None

    # Start job
    tracker.update_status(job.job_id, JobStatus.RUNNING)
    updated = tracker.get_job(job.job_id)
    assert updated.duration_seconds is not None
    assert updated.duration_seconds >= 0

    # Complete job
    tracker.update_status(job.job_id, JobStatus.COMPLETED)
    completed = tracker.get_job(job.job_id)
    assert completed.duration_seconds is not None
    assert completed.duration_seconds >= 0


def test_progress_clamping(tracker):
    """Test that progress is clamped to 0.0-1.0."""
    job = tracker.create_job(task_type="test")

    # Test upper bound
    tracker.update_status(job.job_id, JobStatus.RUNNING, progress=2.0)
    updated = tracker.get_job(job.job_id)
    assert updated.progress == 1.0

    # Test lower bound
    tracker.update_status(job.job_id, JobStatus.RUNNING, progress=-0.5)
    updated = tracker.get_job(job.job_id)
    assert updated.progress == 0.0
