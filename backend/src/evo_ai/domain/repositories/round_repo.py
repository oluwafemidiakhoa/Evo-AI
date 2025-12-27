"""Round repository interface."""

from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from evo_ai.domain.models.round import Round, RoundStatus
from evo_ai.domain.repositories.base import BaseRepository


class RoundRepository(BaseRepository[Round]):
    """Repository interface for Round entities."""

    @abstractmethod
    async def get_by_campaign(
        self,
        campaign_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Round]:
        """
        Retrieve all rounds for a campaign.

        Args:
            campaign_id: Campaign UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of rounds for the campaign, ordered by round_number
        """
        pass

    @abstractmethod
    async def get_latest_round(self, campaign_id: UUID) -> Optional[Round]:
        """
        Get the most recent round for a campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Latest round if exists, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_status(
        self,
        status: RoundStatus,
        campaign_id: Optional[UUID] = None
    ) -> List[Round]:
        """
        Retrieve rounds by status, optionally filtered by campaign.

        Args:
            status: Round status to filter by
            campaign_id: Optional campaign UUID to filter by

        Returns:
            List of rounds with the specified status
        """
        pass

    @abstractmethod
    async def get_next_round_number(self, campaign_id: UUID) -> int:
        """
        Get the next round number for a campaign.

        Args:
            campaign_id: Campaign UUID

        Returns:
            Next round number (max(round_number) + 1, or 1 if no rounds exist)
        """
        pass
