"""Variant repository interface."""

from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from evo_ai.domain.models.variant import Variant
from evo_ai.domain.repositories.base import BaseRepository


class VariantRepository(BaseRepository[Variant]):
    """Repository interface for Variant entities."""

    @abstractmethod
    async def get_by_round(
        self,
        round_id: UUID,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Variant]:
        """
        Retrieve all variants for a round.

        Args:
            round_id: Round UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of variants for the round
        """
        pass

    @abstractmethod
    async def get_selected_variants(self, round_id: UUID) -> List[Variant]:
        """
        Retrieve variants marked as selected for next round.

        Args:
            round_id: Round UUID

        Returns:
            List of selected variants
        """
        pass

    @abstractmethod
    async def get_by_parent(self, parent_id: UUID) -> List[Variant]:
        """
        Retrieve all child variants of a parent.

        Args:
            parent_id: Parent variant UUID

        Returns:
            List of child variants
        """
        pass

    @abstractmethod
    async def get_lineage(self, variant_id: UUID) -> List[Variant]:
        """
        Retrieve the full lineage (ancestry) of a variant.

        This should recursively follow parent_id links back to generation 0.

        Args:
            variant_id: Variant UUID

        Returns:
            List of variants from generation 0 to this variant
        """
        pass

    @abstractmethod
    async def get_by_content_hash(self, content_hash: str) -> Optional[Variant]:
        """
        Find variant by content hash (for deduplication).

        Args:
            content_hash: SHA-256 hash of variant content

        Returns:
            Variant if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_generation(
        self,
        campaign_id: UUID,
        generation: int
    ) -> List[Variant]:
        """
        Retrieve all variants at a specific generation across all rounds.

        Args:
            campaign_id: Campaign UUID
            generation: Generation number

        Returns:
            List of variants at the specified generation
        """
        pass
