"""Concrete repository implementations using SQLModel and PostgreSQL."""

from evo_ai.infrastructure.database.repositories.postgres_campaign_repo import (
    PostgresCampaignRepository,
)

__all__ = [
    "PostgresCampaignRepository",
]
