"""Policy domain model - represents selection and mutation strategies."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class PolicyType(str, Enum):
    """Types of policies in the system."""

    SELECTION = "selection"  # How to select variants for next round
    MUTATION = "mutation"    # How to mutate/generate new variants
    TERMINATION = "termination"  # When to stop the campaign


class Policy(BaseModel):
    """
    Policy entity - represents a strategy for selection, mutation, or termination.

    Policies can be versioned and evolved over time as the system learns
    better strategies.
    """

    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID = Field(description="Parent campaign")
    name: str = Field(min_length=1, max_length=255)
    policy_type: PolicyType
    version: int = Field(default=1, ge=1, description="Policy version number")
    config: dict = Field(description="Policy configuration and parameters")
    is_active: bool = Field(default=True, description="Whether this policy is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None

    def activate(self) -> None:
        """Activate this policy."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """Deactivate this policy."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def create_new_version(self, new_config: dict) -> "Policy":
        """
        Create a new version of this policy with updated config.

        Returns:
            New Policy instance with incremented version
        """
        return Policy(
            campaign_id=self.campaign_id,
            name=self.name,
            policy_type=self.policy_type,
            version=self.version + 1,
            config=new_config,
            is_active=True,
        )

    def soft_delete(self) -> None:
        """Soft delete this policy (for audit trail)."""
        self.deleted_at = datetime.utcnow()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "770e8400-e29b-41d4-a716-446655440002",
                    "campaign_id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Top-K Selection",
                    "policy_type": "selection",
                    "version": 1,
                    "config": {
                        "strategy": "top_k",
                        "k": 5,
                        "diversity_weight": 0.2,
                    },
                    "is_active": True,
                }
            ]
        }
    }
