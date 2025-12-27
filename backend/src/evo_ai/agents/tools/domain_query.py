"""Domain query tool for agents.

Provides access to domain entities (campaigns, rounds, variants, policies).
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from evo_ai.agents.base import AgentContext
from evo_ai.infrastructure.database.connection import get_session
from evo_ai.infrastructure.database.repositories.postgres_campaign_repo import (
    PostgresCampaignRepository
)
from evo_ai.infrastructure.database.repositories.postgres_round_repo import (
    PostgresRoundRepository
)
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)
from evo_ai.infrastructure.database.repositories.postgres_policy_repo import (
    PostgresPolicyRepository
)

logger = structlog.get_logger(__name__)


class DomainQueryTool:
    """
    Tool for querying domain entities.

    Provides agents with read access to:
    - Campaigns
    - Rounds
    - Variants
    - Policies
    """

    @staticmethod
    async def get_campaign(
        context: AgentContext,
        campaign_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get campaign details.

        Args:
            context: Agent execution context
            campaign_id: Campaign ID (defaults to context.campaign_id)

        Returns:
            Campaign details dictionary
        """
        cid = campaign_id or context.campaign_id

        async with get_session() as session:
            repo = PostgresCampaignRepository(session)
            campaign = await repo.get_by_id(cid)

            if not campaign:
                raise ValueError(f"Campaign {cid} not found")

            return {
                "id": str(campaign.id),
                "name": campaign.name,
                "description": campaign.description,
                "status": campaign.status.value,
                "config": campaign.config,
                "created_at": campaign.created_at.isoformat(),
                "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
                "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
            }

    @staticmethod
    async def get_round(
        context: AgentContext,
        round_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get round details.

        Args:
            context: Agent execution context
            round_id: Round ID (defaults to context.round_id)

        Returns:
            Round details dictionary
        """
        rid = round_id or context.round_id

        if not rid:
            raise ValueError("round_id not provided and not in context")

        async with get_session() as session:
            repo = PostgresRoundRepository(session)
            round_obj = await repo.get_by_id(rid)

            if not round_obj:
                raise ValueError(f"Round {rid} not found")

            return {
                "id": str(round_obj.id),
                "campaign_id": str(round_obj.campaign_id),
                "round_number": round_obj.round_number,
                "status": round_obj.status.value,
                "config": round_obj.config,
                "started_at": round_obj.started_at.isoformat() if round_obj.started_at else None,
                "completed_at": round_obj.completed_at.isoformat() if round_obj.completed_at else None,
            }

    @staticmethod
    async def get_variant(
        context: AgentContext,
        variant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get variant details.

        Args:
            context: Agent execution context
            variant_id: Variant ID (defaults to context.variant_id)

        Returns:
            Variant details dictionary
        """
        vid = variant_id or context.variant_id

        if not vid:
            raise ValueError("variant_id not provided and not in context")

        async with get_session() as session:
            repo = PostgresVariantRepository(session)
            variant = await repo.get_by_id(vid)

            if not variant:
                raise ValueError(f"Variant {vid} not found")

            return {
                "id": str(variant.id),
                "round_id": str(variant.round_id),
                "parent_id": str(variant.parent_id) if variant.parent_id else None,
                "generation": variant.generation,
                "content": variant.content,
                "content_hash": variant.content_hash,
                "mutation_type": variant.mutation_type,
                "mutation_metadata": variant.mutation_metadata,
                "is_selected": variant.is_selected,
                "created_at": variant.created_at.isoformat(),
            }

    @staticmethod
    async def get_policy(
        context: AgentContext,
        policy_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get policy details.

        Args:
            context: Agent execution context
            policy_id: Policy ID (defaults to context.policy_id)

        Returns:
            Policy details dictionary
        """
        pid = policy_id or context.policy_id

        if not pid:
            raise ValueError("policy_id not provided and not in context")

        async with get_session() as session:
            repo = PostgresPolicyRepository(session)
            policy = await repo.get_by_id(pid)

            if not policy:
                raise ValueError(f"Policy {pid} not found")

            return {
                "id": str(policy.id),
                "campaign_id": str(policy.campaign_id),
                "round_number": policy.round_number,
                "policy_type": policy.policy_type,
                "rules": policy.rules,
                "parameters": policy.parameters,
                "is_active": policy.is_active,
                "created_at": policy.created_at.isoformat(),
            }

    @staticmethod
    async def get_campaign_rounds(
        context: AgentContext,
        campaign_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all rounds for a campaign.

        Args:
            context: Agent execution context
            campaign_id: Campaign ID (defaults to context.campaign_id)

        Returns:
            List of round dictionaries
        """
        cid = campaign_id or context.campaign_id

        async with get_session() as session:
            repo = PostgresRoundRepository(session)
            rounds = await repo.get_by_campaign_id(cid)

            return [
                {
                    "id": str(r.id),
                    "round_number": r.round_number,
                    "status": r.status.value,
                    "started_at": r.started_at.isoformat() if r.started_at else None,
                    "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                }
                for r in rounds
            ]

    @staticmethod
    async def get_round_variants(
        context: AgentContext,
        round_id: Optional[UUID] = None,
        selected_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all variants for a round.

        Args:
            context: Agent execution context
            round_id: Round ID (defaults to context.round_id)
            selected_only: If True, return only selected variants

        Returns:
            List of variant dictionaries
        """
        rid = round_id or context.round_id

        if not rid:
            raise ValueError("round_id not provided and not in context")

        async with get_session() as session:
            repo = PostgresVariantRepository(session)

            if selected_only:
                variants = await repo.get_selected_by_round(rid)
            else:
                variants = await repo.get_by_round_id(rid)

            return [
                {
                    "id": str(v.id),
                    "parent_id": str(v.parent_id) if v.parent_id else None,
                    "generation": v.generation,
                    "content_hash": v.content_hash,
                    "mutation_type": v.mutation_type,
                    "is_selected": v.is_selected,
                }
                for v in variants
            ]

    @staticmethod
    async def get_active_policies(
        context: AgentContext,
        campaign_id: Optional[UUID] = None,
        round_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active policies for a campaign/round.

        Args:
            context: Agent execution context
            campaign_id: Campaign ID (defaults to context.campaign_id)
            round_number: Optional round number filter

        Returns:
            List of active policy dictionaries
        """
        cid = campaign_id or context.campaign_id

        async with get_session() as session:
            repo = PostgresPolicyRepository(session)
            policies = await repo.get_by_campaign_id(cid)

            # Filter active only
            policies = [p for p in policies if p.is_active]

            # Filter by round number if specified
            if round_number is not None:
                policies = [p for p in policies if p.round_number == round_number]

            return [
                {
                    "id": str(p.id),
                    "policy_type": p.policy_type,
                    "round_number": p.round_number,
                    "rules": p.rules,
                    "parameters": p.parameters,
                }
                for p in policies
            ]

    @staticmethod
    async def get_campaign_statistics(
        context: AgentContext,
        campaign_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics for a campaign.

        Args:
            context: Agent execution context
            campaign_id: Campaign ID (defaults to context.campaign_id)

        Returns:
            Dictionary with campaign statistics
        """
        cid = campaign_id or context.campaign_id

        async with get_session() as session:
            round_repo = PostgresRoundRepository(session)
            variant_repo = PostgresVariantRepository(session)

            # Get all rounds
            rounds = await round_repo.get_by_campaign_id(cid)

            # Count variants across all rounds
            total_variants = 0
            total_selected = 0
            max_generation = 0

            for round_obj in rounds:
                variants = await variant_repo.get_by_round_id(round_obj.id)
                total_variants += len(variants)
                total_selected += sum(1 for v in variants if v.is_selected)
                max_generation = max(max_generation, max((v.generation for v in variants), default=0))

            return {
                "campaign_id": str(cid),
                "total_rounds": len(rounds),
                "completed_rounds": sum(1 for r in rounds if r.status.value == "completed"),
                "total_variants": total_variants,
                "total_selected": total_selected,
                "max_generation": max_generation,
                "selection_rate": total_selected / total_variants if total_variants > 0 else 0,
            }
