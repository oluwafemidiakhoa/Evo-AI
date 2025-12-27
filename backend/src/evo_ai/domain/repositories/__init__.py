"""Repository interfaces - define data access contracts."""

from evo_ai.domain.repositories.base import BaseRepository
from evo_ai.domain.repositories.campaign_repo import CampaignRepository
from evo_ai.domain.repositories.policy_repo import PolicyRepository
from evo_ai.domain.repositories.round_repo import RoundRepository
from evo_ai.domain.repositories.variant_repo import VariantRepository

__all__ = [
    "BaseRepository",
    "CampaignRepository",
    "RoundRepository",
    "VariantRepository",
    "PolicyRepository",
]
