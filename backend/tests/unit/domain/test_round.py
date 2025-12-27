"""Unit tests for Round domain model."""

from uuid import uuid4

import pytest

from evo_ai.domain.models.round import Round, RoundStatus


class TestRound:
    """Test cases for Round entity."""

    def test_create_round(self):
        """Test creating a round."""
        campaign_id = uuid4()
        round_obj = Round(
            campaign_id=campaign_id,
            round_number=1
        )

        assert round_obj.campaign_id == campaign_id
        assert round_obj.round_number == 1
        assert round_obj.status == RoundStatus.PENDING
        assert round_obj.plan is None

    def test_round_execution_flow(self):
        """Test the complete round execution flow."""
        campaign_id = uuid4()
        round_obj = Round(campaign_id=campaign_id, round_number=1)

        # Start planning
        round_obj.start_planning()
        assert round_obj.status == RoundStatus.PLANNING
        assert round_obj.started_at is not None

        # Move to generating
        plan = {"population_size": 10, "mutation_rate": 0.3}
        round_obj.start_generating(plan)
        assert round_obj.status == RoundStatus.GENERATING
        assert round_obj.plan == plan

        # Move to evaluating
        round_obj.start_evaluating()
        assert round_obj.status == RoundStatus.EVALUATING

        # Move to selecting
        round_obj.start_selecting()
        assert round_obj.status == RoundStatus.SELECTING

        # Move to reporting
        round_obj.start_reporting()
        assert round_obj.status == RoundStatus.REPORTING

        # Complete
        metrics = {"duration_seconds": 120, "avg_score": 0.75}
        round_obj.complete(metrics)
        assert round_obj.status == RoundStatus.COMPLETED
        assert round_obj.completed_at is not None
        assert round_obj.metrics["avg_score"] == 0.75

    def test_invalid_state_transition(self):
        """Test that invalid state transitions raise errors."""
        campaign_id = uuid4()
        round_obj = Round(campaign_id=campaign_id, round_number=1)

        # Cannot start generating before planning
        with pytest.raises(ValueError, match="Cannot start generating"):
            round_obj.start_generating({"test": "plan"})

    def test_fail_round(self):
        """Test marking round as failed."""
        campaign_id = uuid4()
        round_obj = Round(campaign_id=campaign_id, round_number=1)
        round_obj.start_planning()

        error_info = {"error": "Test error", "traceback": "..."}
        round_obj.fail(error_info)

        assert round_obj.status == RoundStatus.FAILED
        assert round_obj.metrics["error"] == error_info

    def test_soft_delete(self):
        """Test soft deletion of round."""
        campaign_id = uuid4()
        round_obj = Round(campaign_id=campaign_id, round_number=1)

        assert round_obj.deleted_at is None

        round_obj.soft_delete()

        assert round_obj.deleted_at is not None
