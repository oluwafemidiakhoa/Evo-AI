"""Policy repository interface."""

from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from evo_ai.domain.models.policy import Policy, PolicyType
from evo_ai.domain.repositories.base import BaseRepository


class PolicyRepository(BaseRepository[Policy]):
    """Repository interface for Policy entities."""

    @abstractmethod
    async def get_by_campaign(
        self,
        campaign_id: UUID,
        policy_type: Optional[PolicyType] = None,
        active_only: bool = True
    ) -> List[Policy]:
        """
        Retrieve policies for a campaign.

        Args:
            campaign_id: Campaign UUID
            policy_type: Optional filter by policy type
            active_only: If True, only return active policies

        Returns:
            List of policies
        """
        pass

    @abstractmethod
    async def get_active_policy(
        self,
        campaign_id: UUID,
        policy_type: PolicyType
    ) -> Optional[Policy]:
        """
        Get the active policy of a specific type for a campaign.

        Args:
            campaign_id: Campaign UUID
            policy_type: Policy type

        Returns:
            Active policy if exists, None otherwise
        """
        pass

    @abstractmethod
    async def get_latest_version(
        self,
        campaign_id: UUID,
        policy_name: str,
        policy_type: PolicyType
    ) -> Optional[Policy]:
        """
        Get the latest version of a policy.

        Args:
            campaign_id: Campaign UUID
            policy_name: Policy name
            policy_type: Policy type

        Returns:
            Latest version of the policy if exists, None otherwise
        """
        pass
