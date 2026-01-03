"""VariantAgent - Generates new variants from selected parents.

Responsibilities:
- Generate new code/content variants from parent variants
- Apply mutation strategies (refactor, optimize, expand, etc.)
- Maintain lineage tracking (parent_id, generation)
- Use MCP servers to access and modify code
"""

import random
from typing import Any, Callable, Dict, List
from uuid import UUID

import structlog

from evo_ai.agents.base import BaseEvoAgent, AgentContext, AgentDecision
from evo_ai.agents.tools import DomainQueryTool, LineageTool
from evo_ai.domain.models.variant import Variant
from evo_ai.infrastructure.database.connection import get_session
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)

logger = structlog.get_logger(__name__)


class VariantAgent(BaseEvoAgent):
    """
    Agent responsible for generating new variants.

    Applies mutation strategies:
    - refactor: Improve code structure without changing behavior
    - optimize: Improve performance or efficiency
    - expand: Add new features or capabilities
    - simplify: Reduce complexity
    - experimental: Try novel approaches

    Constitution adherence:
    - Maintains lineage tracking (CRITICAL)
    - Logs all mutations with reasoning
    - Uses MCP servers for code access/modification
    """

    @property
    def agent_type(self) -> str:
        return "variant_generator"

    def get_system_instructions(self) -> str:
        return """You are the VariantAgent for an evolutionary experiment platform.

Your responsibilities:
1. Generate new code/content variants from parent variants
2. Apply specified mutation strategies while maintaining functionality
3. Track lineage (parent -> child) and increment generation counter
4. Provide clear reasoning for each mutation

Mutation strategies:
- refactor: Improve structure, naming, organization (keep behavior identical)
- optimize: Improve performance, reduce complexity, optimize algorithms
- expand: Add new features, capabilities, or documentation
- simplify: Reduce code size, remove unnecessary complexity
- experimental: Try novel approaches, alternative implementations

Guidelines:
- Always maintain lineage: new variant must reference parent_id
- Increment generation: child.generation = parent.generation + 1
- Preserve core functionality unless explicitly expanding
- Document mutation reasoning clearly
- Use MCP tools to access parent code and generate variants

Output: New variant with content, mutation metadata, and lineage info.
"""

    def get_tools(self) -> List[Callable]:
        return [
            # Domain tools
            self._create_domain_tool(
                name="get_variant",
                description="Get variant details including content",
                func=DomainQueryTool.get_variant
            ),
            self._create_domain_tool(
                name="get_lineage",
                description="Get full lineage of a variant",
                func=LineageTool.get_full_lineage
            ),
            # MCP tools for code access
            self._create_mcp_tool(
                server_name="github",
                tool_name="read_file",
                description="Read source code from GitHub repository"
            ),
            self._create_mcp_tool(
                server_name="filesystem",
                tool_name="read_file",
                description="Read file from local filesystem (sandboxed)"
            ),
        ]

    async def execute(
        self,
        context: AgentContext,
        parent_id: UUID,
        mutation_type: str,
        mutation_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate a new variant from a parent.

        Args:
            context: Execution context with round_id
            parent_id: Parent variant ID
            mutation_type: Type of mutation (refactor, optimize, expand, etc.)
            mutation_config: Optional mutation-specific configuration

        Returns:
            New variant details with:
            - variant_id: New variant UUID
            - parent_id: Parent variant UUID
            - generation: Generation number
            - mutation_type: Applied mutation
            - content: New variant content
            - reasoning: Mutation rationale
        """
        if not context.round_id:
            raise ValueError("round_id required in context for variant generation")

        mutation_config = mutation_config or {}

        logger.info(
            "generating_variant",
            parent_id=str(parent_id),
            mutation_type=mutation_type,
            round_id=str(context.round_id),
            trace_id=str(context.trace_id)
        )

        # Get parent variant
        parent_context = AgentContext(
            trace_id=context.trace_id,
            campaign_id=context.campaign_id,
            run_id=context.run_id,
            variant_id=parent_id,
        )
        parent_data = await self._call_tool("get_variant", parent_context)
        parent_content = parent_data["content"]
        parent_generation = parent_data["generation"]

        # Get lineage for context
        lineage = await self._call_tool("get_lineage", parent_context)

        # Generate mutation based on type
        if mutation_type == "refactor":
            new_content, reasoning = await self._apply_refactor(
                parent_content, lineage, mutation_config
            )
        elif mutation_type == "optimize":
            new_content, reasoning = await self._apply_optimize(
                parent_content, lineage, mutation_config
            )
        elif mutation_type == "expand":
            new_content, reasoning = await self._apply_expand(
                parent_content, lineage, mutation_config
            )
        elif mutation_type == "simplify":
            new_content, reasoning = await self._apply_simplify(
                parent_content, lineage, mutation_config
            )
        elif mutation_type == "experimental":
            new_content, reasoning = await self._apply_experimental(
                parent_content, lineage, mutation_config
            )
        else:
            raise ValueError(f"Unknown mutation type: {mutation_type}")

        # Create variant (CRITICAL: maintain lineage)
        new_generation = parent_generation + 1
        variant = Variant(
            round_id=context.round_id,
            parent_id=parent_id,  # CRITICAL: lineage tracking
            generation=new_generation,  # CRITICAL: increment generation
            content=new_content,
            mutation_type=mutation_type,
            mutation_metadata={
                "reasoning": reasoning,
                "config": mutation_config,
                "parent_content_hash": parent_data["content_hash"],
            }
        )

        # Save to database
        async with get_session() as session:
            repo = PostgresVariantRepository(session)
            saved_variant = await repo.create(variant)

        # Log decision
        decision = AgentDecision(
            agent_type=self.agent_type,
            decision_type="variant_generated",
            input_data={
                "parent_id": str(parent_id),
                "mutation_type": mutation_type,
                "parent_generation": parent_generation,
            },
            output_data={
                "variant_id": str(saved_variant.id),
                "generation": new_generation,
                "content_hash": saved_variant.content_hash,
            },
            reasoning=reasoning,
            confidence_score=0.8,
            metadata={
                "mutation_type": mutation_type,
                "lineage_depth": lineage.get("generations", 0),
            }
        )
        await self._log_decision(context, decision)

        logger.info(
            "variant_generated",
            variant_id=str(saved_variant.id),
            parent_id=str(parent_id),
            generation=new_generation,
            mutation_type=mutation_type,
            trace_id=str(context.trace_id)
        )

        return {
            "variant_id": str(saved_variant.id),
            "parent_id": str(parent_id),
            "generation": new_generation,
            "mutation_type": mutation_type,
            "content": new_content,
            "content_hash": saved_variant.content_hash,
            "reasoning": reasoning,
        }

    async def _apply_refactor(
        self,
        content: str,
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[str, str]:
        """Apply refactoring mutation."""
        # Simulate refactoring (in production, would use LLM or AST manipulation)
        new_content = f"# Refactored variant (generation {lineage['generations']})\n{content}"
        reasoning = (
            f"Applied refactoring to improve code structure. "
            f"Parent was generation {lineage['generations'] - 1}. "
            f"Focus: Better naming, clearer organization."
        )
        return new_content, reasoning

    async def _apply_optimize(
        self,
        content: str,
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[str, str]:
        """Apply optimization mutation."""
        new_content = f"# Optimized variant (generation {lineage['generations']})\n{content}"
        reasoning = (
            f"Applied optimization to improve performance. "
            f"Parent was generation {lineage['generations'] - 1}. "
            f"Focus: Algorithm efficiency, reduced complexity."
        )
        return new_content, reasoning

    async def _apply_expand(
        self,
        content: str,
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[str, str]:
        """Apply expansion mutation."""
        expansion = config.get("feature", "new_capability")
        new_content = (
            f"# Expanded variant (generation {lineage['generations']})\n"
            f"# Added: {expansion}\n"
            f"{content}"
        )
        reasoning = (
            f"Applied expansion to add new capability: {expansion}. "
            f"Parent was generation {lineage['generations'] - 1}."
        )
        return new_content, reasoning

    async def _apply_simplify(
        self,
        content: str,
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[str, str]:
        """Apply simplification mutation."""
        new_content = f"# Simplified variant (generation {lineage['generations']})\n{content}"
        reasoning = (
            f"Applied simplification to reduce complexity. "
            f"Parent was generation {lineage['generations'] - 1}. "
            f"Focus: Removed unnecessary code, clearer logic."
        )
        return new_content, reasoning

    async def _apply_experimental(
        self,
        content: str,
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[str, str]:
        """Apply experimental mutation."""
        approach = config.get("approach", "alternative_implementation")
        new_content = (
            f"# Experimental variant (generation {lineage['generations']})\n"
            f"# Approach: {approach}\n"
            f"{content}"
        )
        reasoning = (
            f"Applied experimental mutation with approach: {approach}. "
            f"Parent was generation {lineage['generations'] - 1}. "
            f"Trying novel solution to explore design space."
        )
        return new_content, reasoning

    async def generate_batch(
        self,
        context: AgentContext,
        parent_ids: List[UUID],
        mutation_plan: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple variants from multiple parents.

        Args:
            context: Execution context
            parent_ids: List of parent variant IDs
            mutation_plan: Plan with mutation_types and distribution

        Returns:
            List of generated variants
        """
        mutation_types = mutation_plan.get("mutation_types", ["refactor"])
        distribution = mutation_plan.get("mutation_distribution", {})
        total_count = mutation_plan.get("variant_count", len(parent_ids))
        seed = mutation_plan.get("seed")
        rng = random.Random(seed) if seed is not None else None

        variants = []

        # Distribute mutations according to plan
        for i, parent_id in enumerate(parent_ids[:total_count]):
            # Select mutation type based on distribution
            if distribution:
                chooser = rng or random
                mutation_type = chooser.choices(
                    list(distribution.keys()),
                    weights=list(distribution.values())
                )[0]
            else:
                mutation_type = mutation_types[i % len(mutation_types)]

            variant = await self.execute(
                context,
                parent_id=parent_id,
                mutation_type=mutation_type
            )
            variants.append(variant)

        logger.info(
            "batch_variants_generated",
            count=len(variants),
            round_id=str(context.round_id),
            trace_id=str(context.trace_id)
        )

        return variants
