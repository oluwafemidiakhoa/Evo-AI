"""PolicyAgent - Adapts selection policies based on evolution progress.

Responsibilities:
- Create and update selection policies
- Determine which variants advance to next generation
- Adapt selection pressure based on campaign progress
- Balance diversity vs convergence
"""

from collections import Counter
from typing import Any, Callable, Dict, List
from uuid import UUID

import structlog

from evo_ai.agents.base import BaseEvoAgent, AgentContext, AgentDecision
from evo_ai.agents.tools import DomainQueryTool, EvaluationTool
from evo_ai.domain.models.policy import Policy, PolicyType
from evo_ai.infrastructure.database.connection import get_session
from evo_ai.infrastructure.database.repositories.postgres_policy_repo import (
    PostgresPolicyRepository
)
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)

logger = structlog.get_logger(__name__)


class PolicyAgent(BaseEvoAgent):
    """
    Agent responsible for selection policy decisions.

    Policy types:
    - top_k: Select top K variants by score
    - tournament: Tournament-style selection
    - roulette: Fitness-proportionate selection
    - diversity: Maintain diversity across lineages
    - adaptive: Dynamically adjust based on progress

    Constitution adherence:
    - Logs all policy decisions with reasoning
    - Transparent selection criteria
    - Adapts to campaign progress
    """

    @property
    def agent_type(self) -> str:
        return "policy_maker"

    def get_system_instructions(self) -> str:
        return """You are the PolicyAgent for an evolutionary experiment platform.

Your responsibilities:
1. Create selection policies that determine which variants advance
2. Adapt selection pressure based on evolution progress
3. Balance convergence (exploit best) vs diversity (explore space)
4. Prevent premature convergence while ensuring progress

Policy strategies:
- top_k: Select top K performers (elitist)
- tournament: Run tournaments, select winners
- roulette: Probability proportional to fitness
- diversity: Ensure diverse lineages represented
- adaptive: Combine strategies based on context

Guidelines:
- Early rounds: Lower pressure, maintain diversity
- Middle rounds: Balanced approach
- Late rounds: Higher pressure, focus on best
- Monitor diversity: Prevent single lineage dominance
- Consider evaluation confidence: Don't over-trust uncertain scores

Output: Selection policy with clear rules and parameters.
"""

    def get_tools(self) -> List[Callable]:
        return [
            # Domain tools
            self._create_domain_tool(
                name="get_round_variants",
                description="Get all variants in a round",
                func=DomainQueryTool.get_round_variants
            ),
            self._create_domain_tool(
                name="get_campaign_statistics",
                description="Get campaign statistics",
                func=DomainQueryTool.get_campaign_statistics
            ),
            self._create_domain_tool(
                name="get_round_evaluations",
                description="Get evaluation results for round",
                func=EvaluationTool.get_round_evaluations
            ),
            self._create_domain_tool(
                name="compare_scores",
                description="Compare variant scores",
                func=EvaluationTool.compare_variant_scores
            ),
        ]

    async def execute(
        self,
        context: AgentContext,
        round_number: int,
        selection_pressure: float = 0.5,
        policy_type: str = "adaptive"
    ) -> Dict[str, Any]:
        """
        Create a selection policy for a round.

        Args:
            context: Execution context with round_id
            round_number: Current round number
            selection_pressure: Selection intensity (0.0=keep all, 1.0=keep only best)
            policy_type: Policy strategy type

        Returns:
            Policy details with:
            - policy_id: Policy UUID
            - policy_type: Strategy type
            - rules: Selection rules
            - parameters: Policy parameters
            - reasoning: Policy rationale
        """
        if not context.round_id:
            raise ValueError("round_id required in context")

        logger.info(
            "creating_policy",
            round_number=round_number,
            policy_type=policy_type,
            selection_pressure=selection_pressure,
            trace_id=str(context.trace_id)
        )

        # Get round context
        variants = await self._call_tool("get_round_variants", context)
        evaluations = await self._call_tool("get_round_evaluations", context)
        stats = await self._call_tool("get_campaign_statistics", context)

        total_variants = len(variants)
        completed_evals = evaluations.get("completed", 0)

        # Determine selection count based on pressure
        if selection_pressure < 0.3:
            # Low pressure: keep most variants
            select_count = int(total_variants * 0.7)
        elif selection_pressure < 0.7:
            # Medium pressure: keep half
            select_count = int(total_variants * 0.5)
        else:
            # High pressure: keep only best
            select_count = max(int(total_variants * 0.3), 1)

        # Create policy based on type
        if policy_type == "top_k":
            rules, params = self._create_top_k_policy(select_count)
            reasoning = f"Top-K policy: Select {select_count} highest-scoring variants"

        elif policy_type == "tournament":
            tournament_size = 3
            rules, params = self._create_tournament_policy(select_count, tournament_size)
            reasoning = (
                f"Tournament policy: Run tournaments of size {tournament_size}, "
                f"select {select_count} winners"
            )

        elif policy_type == "diversity":
            rules, params = self._create_diversity_policy(select_count)
            reasoning = (
                f"Diversity policy: Select {select_count} variants ensuring "
                f"diverse lineages represented"
            )

        elif policy_type == "adaptive":
            # Adapt based on progress
            if round_number < 5:
                rules, params = self._create_diversity_policy(select_count)
                reasoning = "Early rounds: Diversity policy to maintain exploration"
            elif evaluations.get("average_score", 0) < 0.5:
                rules, params = self._create_tournament_policy(select_count, 3)
                reasoning = "Low scores: Tournament policy to find better solutions"
            else:
                rules, params = self._create_top_k_policy(select_count)
                reasoning = "Good progress: Top-K policy to exploit best variants"

        else:
            raise ValueError(f"Unknown policy type: {policy_type}")

        objective_weights = self._build_objective_weights(selection_pressure)

        # Create policy entity
        policy = Policy(
            campaign_id=context.campaign_id,
            name=f"{policy_type} selection policy (round {round_number})",
            policy_type=PolicyType.SELECTION,
            config={
                "strategy": policy_type,
                "round_number": round_number,
                "rules": rules,
                "parameters": params,
                "selection_pressure": selection_pressure,
                "selection_count": select_count,
                "objective_weights": objective_weights,
            },
            is_active=True,
        )

        async with get_session() as session:
            repo = PostgresPolicyRepository(session)
            existing = await repo.get_by_campaign(
                context.campaign_id,
                policy_type=PolicyType.SELECTION,
                active_only=False
            )
            next_version = max((p.version for p in existing), default=0) + 1

            for existing_policy in existing:
                if existing_policy.is_active:
                    existing_policy.is_active = False
                    await repo.update(existing_policy)

            policy.version = next_version
            saved_policy = await repo.create(policy)

        # Log decision
        decision = AgentDecision(
            agent_type=self.agent_type,
            decision_type="policy_created",
            input_data={
                "round_number": round_number,
                "policy_type": policy_type,
                "selection_pressure": selection_pressure,
                "total_variants": total_variants,
            },
            output_data={
                "policy_id": str(saved_policy.id),
                "select_count": select_count,
                "rules": rules,
            },
            reasoning=reasoning,
            confidence_score=0.8,
            metadata={
                "policy_type": policy_type,
                "average_score": evaluations.get("average_score"),
            }
        )
        await self._log_decision(context, decision)

        logger.info(
            "policy_created",
            policy_id=str(saved_policy.id),
            round_number=round_number,
            select_count=select_count,
            trace_id=str(context.trace_id)
        )

        return {
            "policy_id": str(saved_policy.id),
            "policy_type": policy_type,
            "rules": rules,
            "parameters": params,
            "reasoning": reasoning,
            "select_count": select_count,
        }

    def _create_top_k_policy(self, k: int) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Create top-K selection policy."""
        rules = {
            "strategy": "top_k",
            "description": "Select top K variants by evaluation score",
        }
        params = {
            "k": k,
            "metric": "evaluation_score",
            "tie_breaker": "lineage_diversity",
        }
        return rules, params

    def _build_objective_weights(self, selection_pressure: float) -> Dict[str, float]:
        """Build multi-objective weights based on selection pressure."""
        if selection_pressure < 0.4:
            weights = {
                "evaluation_score": 0.5,
                "novelty": 0.25,
                "diversity": 0.2,
                "innovation": 0.05,
            }
        elif selection_pressure < 0.7:
            weights = {
                "evaluation_score": 0.65,
                "novelty": 0.15,
                "diversity": 0.15,
                "innovation": 0.05,
            }
        else:
            weights = {
                "evaluation_score": 0.8,
                "novelty": 0.1,
                "diversity": 0.07,
                "innovation": 0.03,
            }

        total = sum(weights.values()) or 1.0
        return {key: value / total for key, value in weights.items()}

    def _rank_variants(
        self,
        variants: List[Dict[str, Any]],
        evaluations: Dict[str, Any],
        policy_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank variants using multi-objective scoring."""
        evals = evaluations.get("evaluations", [])
        scores_by_variant: Dict[str, List[float]] = {}
        innovation_by_variant: Dict[str, List[float]] = {}

        for evaluation in evals:
            if evaluation.get("status") != "completed":
                continue
            variant_id = evaluation.get("variant_id")
            score = evaluation.get("score")
            if variant_id is None or score is None:
                continue
            scores_by_variant.setdefault(variant_id, []).append(score)

            criteria = (evaluation.get("result_data") or {}).get("criteria_scores", {})
            innovation = criteria.get("innovation")
            if innovation is not None:
                innovation_by_variant.setdefault(variant_id, []).append(innovation)

        content_counts = Counter(
            v.get("content_hash") for v in variants if v.get("content_hash")
        )
        parent_counts = Counter(
            v.get("parent_id") or "root" for v in variants
        )

        weights = policy_config.get("objective_weights", {})
        if not weights:
            weights = self._build_objective_weights(
                float(policy_config.get("selection_pressure", 0.5))
            )

        ranked = []
        for variant in variants:
            variant_id = variant.get("id")
            if not variant_id:
                continue

            eval_scores = scores_by_variant.get(variant_id, [])
            evaluation_score = sum(eval_scores) / len(eval_scores) if eval_scores else 0.0

            innovation_scores = innovation_by_variant.get(variant_id, [])
            innovation = sum(innovation_scores) / len(innovation_scores) if innovation_scores else evaluation_score

            content_hash = variant.get("content_hash")
            novelty = 1.0 / content_counts.get(content_hash, 1) if content_hash else 0.5

            parent_key = variant.get("parent_id") or "root"
            diversity = 1.0 / parent_counts.get(parent_key, 1)

            composite_score = (
                evaluation_score * weights.get("evaluation_score", 0.0)
                + novelty * weights.get("novelty", 0.0)
                + diversity * weights.get("diversity", 0.0)
                + innovation * weights.get("innovation", 0.0)
            )

            ranked.append({
                "variant_id": variant_id,
                "parent_id": variant.get("parent_id"),
                "evaluation_score": evaluation_score,
                "novelty": novelty,
                "diversity": diversity,
                "innovation": innovation,
                "composite_score": composite_score,
            })

        ranked.sort(key=lambda item: item["composite_score"], reverse=True)
        return ranked

    def _select_with_diversity(
        self,
        ranked: List[Dict[str, Any]],
        select_count: int,
        min_lineages: int
    ) -> List[UUID]:
        """Select top variants while preserving lineage diversity."""
        selected: List[UUID] = []
        selected_ids = set()
        selected_parents = set()

        for candidate in ranked:
            if len(selected) >= select_count:
                break
            parent_key = candidate.get("parent_id") or "root"
            if parent_key not in selected_parents:
                selected_parents.add(parent_key)
                variant_id = UUID(candidate["variant_id"])
                selected.append(variant_id)
                selected_ids.add(candidate["variant_id"])
                if len(selected_parents) >= min_lineages:
                    break

        for candidate in ranked:
            if len(selected) >= select_count:
                break
            if candidate["variant_id"] in selected_ids:
                continue
            variant_id = UUID(candidate["variant_id"])
            selected.append(variant_id)
            selected_ids.add(candidate["variant_id"])

        return selected

    def _create_tournament_policy(
        self,
        winners: int,
        tournament_size: int
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Create tournament selection policy."""
        rules = {
            "strategy": "tournament",
            "description": "Run tournaments, select winners",
        }
        params = {
            "winners": winners,
            "tournament_size": tournament_size,
            "replacement": False,  # No replacement sampling
        }
        return rules, params

    def _create_diversity_policy(self, count: int) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Create diversity-preserving policy."""
        rules = {
            "strategy": "diversity",
            "description": "Select variants ensuring lineage diversity",
        }
        params = {
            "count": count,
            "min_lineages": max(count // 3, 1),  # At least 1/3 different lineages
            "score_threshold": 0.3,  # Minimum acceptable score
        }
        return rules, params

    async def apply_policy(
        self,
        context: AgentContext,
        policy_id: UUID
    ) -> Dict[str, Any]:
        """
        Apply selection policy to mark selected variants.

        Args:
            context: Execution context with round_id
            policy_id: Policy to apply

        Returns:
            Selection results with selected variant IDs
        """
        if not context.round_id:
            raise ValueError("round_id required")

        logger.info(
            "applying_policy",
            policy_id=str(policy_id),
            round_id=str(context.round_id),
            trace_id=str(context.trace_id)
        )

        # Get policy
        async with get_session() as session:
            policy_repo = PostgresPolicyRepository(session)
            policy = await policy_repo.get_by_id(policy_id)
            if not policy:
                raise ValueError(f"Policy {policy_id} not found")

        # Get variants and evaluations
        variants = await self._call_tool("get_round_variants", context)
        evaluations = await self._call_tool("get_round_evaluations", context)

        ranked = self._rank_variants(variants, evaluations, policy.config)
        select_count = min(
            int(policy.config.get("selection_count", len(ranked))),
            len(ranked)
        )
        min_lineages = int(policy.config.get("parameters", {}).get("min_lineages", 1))
        selected_ids = self._select_with_diversity(ranked, select_count, min_lineages)

        # Mark variants as selected
        async with get_session() as session:
            repo = PostgresVariantRepository(session)

            for variant_id in selected_ids:
                variant = await repo.get_by_id(variant_id)
                if variant:
                    variant.is_selected = True
                    await repo.update(variant)

        # Log decision
        decision = AgentDecision(
            agent_type=self.agent_type,
            decision_type="selection_applied",
            input_data={
                "policy_id": str(policy_id),
                "total_variants": len(variants),
            },
            output_data={
                "selected_count": len(selected_ids),
                "selected_ids": [str(vid) for vid in selected_ids],
            },
            reasoning=f"Applied selection policy, selected {len(selected_ids)} variants",
            confidence_score=0.85,
        )
        await self._log_decision(context, decision)

        logger.info(
            "policy_applied",
            selected_count=len(selected_ids),
            total_variants=len(variants),
            trace_id=str(context.trace_id)
        )

        return {
            "policy_id": str(policy_id),
            "total_variants": len(variants),
            "selected_count": len(selected_ids),
            "selected_ids": [str(vid) for vid in selected_ids],
            "selection_rate": len(selected_ids) / len(variants) if variants else 0,
        }
