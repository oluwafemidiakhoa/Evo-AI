"""Campaign domain model - represents an experimental evolution campaign."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CampaignStatus(str, Enum):
    """Campaign lifecycle states."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Campaign(BaseModel):
    """
    Campaign entity - represents a complete evolution experiment.

    A campaign contains multiple rounds, each executing the evolution loop:
    planning → variant generation → evaluation → selection → reporting
    """

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT)
    config: dict = Field(
        description="Campaign configuration (population_size, max_rounds, etc.)"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Extensible metadata for custom fields"
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    def activate(self) -> None:
        """Transition campaign to active status."""
        if self.status != CampaignStatus.DRAFT:
            raise ValueError(f"Cannot activate campaign with status {self.status}")
        self.status = CampaignStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def pause(self) -> None:
        """Pause an active campaign."""
        if self.status != CampaignStatus.ACTIVE:
            raise ValueError(f"Cannot pause campaign with status {self.status}")
        self.status = CampaignStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume(self) -> None:
        """Resume a paused campaign."""
        if self.status != CampaignStatus.PAUSED:
            raise ValueError(f"Cannot resume campaign with status {self.status}")
        self.status = CampaignStatus.ACTIVE
        self.updated_at = datetime.utcnow()

    def complete(self) -> None:
        """Mark campaign as completed."""
        if self.status not in [CampaignStatus.ACTIVE, CampaignStatus.PAUSED]:
            raise ValueError(f"Cannot complete campaign with status {self.status}")
        self.status = CampaignStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def fail(self) -> None:
        """Mark campaign as failed."""
        self.status = CampaignStatus.FAILED
        self.updated_at = datetime.utcnow()

    def soft_delete(self) -> None:
        """Soft delete this campaign (for audit trail)."""
        self.deleted_at = datetime.utcnow()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Prompt Optimization Experiment",
                    "description": "Evolving prompts for customer support",
                    "status": "active",
                    "config": {
                        "population_size": 10,
                        "max_rounds": 20,
                        "objective": "Maximize customer satisfaction",
                    },
                    "metadata": {},
                }
            ]
        }
    }
