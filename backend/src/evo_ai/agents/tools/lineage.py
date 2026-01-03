"""Lineage query tool for agents.

Allows agents to trace variant ancestry and analyze evolutionary paths.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from evo_ai.agents.base import AgentContext
from evo_ai.infrastructure.database.connection import get_session
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)

logger = structlog.get_logger(__name__)


class LineageTool:
    """
    Tool for querying variant lineage and evolutionary history.

    Provides agents with:
    - Full ancestry chain (variant -> parent -> grandparent -> ...)
    - Descendants of a variant
    - Generation analysis
    - Lineage statistics
    """

    @staticmethod
    async def get_full_lineage(
        context: AgentContext,
        variant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get complete ancestry chain for a variant.

        Args:
            context: Agent execution context
            variant_id: Variant to trace lineage for

        Returns:
            Dictionary with:
            - lineage: List of variants from current to generation 0
            - generations: Number of generations
            - lineage_depth: Same as generations (alias)
            - founder: The generation 0 variant

        Example:
            result = await LineageTool.get_full_lineage(context, variant_id)
            # result = {
            #     "lineage": [gen2_variant, gen1_variant, gen0_variant],
            #     "generations": 3,
            #     "founder": gen0_variant
            # }
        """
        vid = variant_id or context.variant_id
        if not vid:
            raise ValueError("variant_id not provided and not in context")

        async with get_session() as session:
            repo = PostgresVariantRepository(session)
            lineage = await repo.get_lineage(vid)

            if not lineage:
                return {
                    "lineage": [],
                    "generations": 0,
                    "lineage_depth": 0,
                    "founder": None,
                    "error": "Variant not found"
                }

            # Convert to dict representation
            lineage_dicts = [
                {
                    "id": str(v.id),
                    "round_id": str(v.round_id),
                    "parent_id": str(v.parent_id) if v.parent_id else None,
                    "generation": v.generation,
                    "content": v.content,
                    "content_hash": v.content_hash,
                    "mutation_type": v.mutation_type,
                    "is_selected": v.is_selected,
                }
                for v in lineage
            ]

            return {
                "lineage": lineage_dicts,
                "generations": len(lineage),
                "lineage_depth": len(lineage),
                "founder": lineage_dicts[-1] if lineage_dicts else None,
            }

    @staticmethod
    async def get_descendants(
        context: AgentContext,
        variant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get all descendants of a variant.

        Args:
            context: Agent execution context
            variant_id: Parent variant ID

        Returns:
            Dictionary with descendants list and count
        """
        vid = variant_id or context.variant_id
        if not vid:
            raise ValueError("variant_id not provided and not in context")

        async with get_session() as session:
            repo = PostgresVariantRepository(session)
            descendants = await repo.get_descendants(vid)

            return {
                "descendants": [
                    {
                        "id": str(v.id),
                        "round_id": str(v.round_id),
                        "generation": v.generation,
                        "mutation_type": v.mutation_type,
                        "is_selected": v.is_selected,
                    }
                    for v in descendants
                ],
                "count": len(descendants),
            }

    @staticmethod
    async def get_lineage_statistics(
        context: AgentContext,
        variant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get statistical analysis of a variant's lineage.

        Args:
            context: Agent execution context
            variant_id: Variant to analyze

        Returns:
            Dictionary with lineage statistics
        """
        vid = variant_id or context.variant_id
        if not vid:
            raise ValueError("variant_id not provided and not in context")

        lineage_result = await LineageTool.get_full_lineage(context, vid)
        descendants_result = await LineageTool.get_descendants(context, vid)

        lineage = lineage_result.get("lineage", [])

        # Analyze mutations along lineage
        mutation_types = [v.get("mutation_type") for v in lineage if v.get("mutation_type")]
        mutation_counts = {}
        for mt in mutation_types:
            mutation_counts[mt] = mutation_counts.get(mt, 0) + 1

        # Count selected variants in lineage
        selected_count = sum(1 for v in lineage if v.get("is_selected"))

        return {
            "total_ancestors": len(lineage),
            "total_descendants": descendants_result.get("count", 0),
            "generation": lineage[0].get("generation") if lineage else 0,
            "mutation_types": mutation_counts,
            "selected_in_lineage": selected_count,
            "selection_rate": selected_count / len(lineage) if lineage else 0,
        }

    @staticmethod
    async def compare_variants(
        context: AgentContext,
        variant_id_1: UUID,
        variant_id_2: UUID
    ) -> Dict[str, Any]:
        """
        Compare two variants and find their relationship.

        Args:
            context: Agent execution context
            variant_id_1: First variant
            variant_id_2: Second variant

        Returns:
            Dictionary with:
            - relationship: "ancestor", "descendant", "sibling", "cousins", or "unrelated"
            - common_ancestor: Closest common ancestor if exists
            - generation_distance: Generations between variants
        """
        lineage_1 = await LineageTool.get_full_lineage(context, variant_id_1)
        lineage_2 = await LineageTool.get_full_lineage(context, variant_id_2)

        variants_1 = lineage_1.get("lineage", [])
        variants_2 = lineage_2.get("lineage", [])

        if not variants_1 or not variants_2:
            return {
                "relationship": "unknown",
                "error": "One or both variants not found"
            }

        # Check if one is ancestor of other
        ids_1 = {v["id"] for v in variants_1}
        ids_2 = {v["id"] for v in variants_2}

        if str(variant_id_2) in ids_1:
            return {
                "relationship": "ancestor",
                "detail": f"{variant_id_2} is ancestor of {variant_id_1}",
                "generation_distance": variants_1[0]["generation"] - next(
                    v["generation"] for v in variants_1 if v["id"] == str(variant_id_2)
                )
            }

        if str(variant_id_1) in ids_2:
            return {
                "relationship": "descendant",
                "detail": f"{variant_id_1} is ancestor of {variant_id_2}",
                "generation_distance": variants_2[0]["generation"] - next(
                    v["generation"] for v in variants_2 if v["id"] == str(variant_id_1)
                )
            }

        # Check for siblings (same parent)
        parent_1 = variants_1[0].get("parent_id") if len(variants_1) > 1 else None
        parent_2 = variants_2[0].get("parent_id") if len(variants_2) > 1 else None

        if parent_1 and parent_2 and parent_1 == parent_2:
            return {
                "relationship": "sibling",
                "common_parent": parent_1,
                "generation_distance": 0
            }

        # Find common ancestor
        for v1 in variants_1:
            if v1["id"] in ids_2:
                return {
                    "relationship": "cousins",
                    "common_ancestor": v1,
                    "generation_distance": abs(variants_1[0]["generation"] - variants_2[0]["generation"])
                }

        return {
            "relationship": "unrelated",
            "detail": "No common ancestor found"
        }
