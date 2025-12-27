"""Campaign repository interface."""

from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from evo_ai.domain.models.campaign import Campaign, CampaignStatus
from evo_ai.domain.repositories.base import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    """Repository interface for Campaign entities."""

    @abstractmethod
    async def get_by_status(
        self,
        status: CampaignStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Campaign]:
        """
        Retrieve campaigns by status.

        Args:
            status: Campaign status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of campaigns with the specified status
        """
        pass

    @abstractmethod
    async def get_active_campaigns(self) -> List[Campaign]:
        """
        Retrieve all active campaigns.

        Returns:
            List of campaigns with status=ACTIVE
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Campaign]:
        """
        Retrieve campaign by name.

        Args:
            name: Campaign name

        Returns:
            Campaign if found, None otherwise
        """
        pass
