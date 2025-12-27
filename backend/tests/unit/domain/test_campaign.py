"""Unit tests for Campaign domain model."""

import pytest

from evo_ai.domain.models.campaign import Campaign, CampaignStatus


class TestCampaign:
    """Test cases for Campaign entity."""

    def test_create_campaign(self):
        """Test creating a campaign."""
        campaign = Campaign(
            name="Test Campaign",
            description="Test description",
            config={"population_size": 10, "max_rounds": 5}
        )

        assert campaign.name == "Test Campaign"
        assert campaign.status == CampaignStatus.DRAFT
        assert campaign.config["population_size"] == 10
        assert campaign.deleted_at is None

    def test_activate_campaign(self):
        """Test activating a draft campaign."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )

        assert campaign.status == CampaignStatus.DRAFT

        campaign.activate()

        assert campaign.status == CampaignStatus.ACTIVE

    def test_cannot_activate_non_draft_campaign(self):
        """Test that non-draft campaigns cannot be activated."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )
        campaign.activate()

        with pytest.raises(ValueError, match="Cannot activate"):
            campaign.activate()

    def test_pause_active_campaign(self):
        """Test pausing an active campaign."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )
        campaign.activate()

        campaign.pause()

        assert campaign.status == CampaignStatus.PAUSED

    def test_cannot_pause_non_active_campaign(self):
        """Test that only active campaigns can be paused."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )

        with pytest.raises(ValueError, match="Cannot pause"):
            campaign.pause()

    def test_resume_paused_campaign(self):
        """Test resuming a paused campaign."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )
        campaign.activate()
        campaign.pause()

        campaign.resume()

        assert campaign.status == CampaignStatus.ACTIVE

    def test_cannot_resume_non_paused_campaign(self):
        """Test that only paused campaigns can be resumed."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )

        with pytest.raises(ValueError, match="Cannot resume"):
            campaign.resume()

    def test_complete_campaign(self):
        """Test completing a campaign."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )
        campaign.activate()

        campaign.complete()

        assert campaign.status == CampaignStatus.COMPLETED

    def test_fail_campaign(self):
        """Test marking campaign as failed."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )
        campaign.activate()

        campaign.fail()

        assert campaign.status == CampaignStatus.FAILED

    def test_soft_delete(self):
        """Test soft deletion of campaign."""
        campaign = Campaign(
            name="Test Campaign",
            config={"population_size": 10}
        )

        assert campaign.deleted_at is None

        campaign.soft_delete()

        assert campaign.deleted_at is not None
