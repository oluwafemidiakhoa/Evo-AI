"""PlannerAgent - Plans experiment rounds and evolution strategies.

Responsibilities:
- Determine number of variants to generate per round
- Select mutation strategies based on campaign progress
- Adapt exploration/exploitation balance
- Plan evaluation strategies
"""

import hashlib
import json
from typing import Any, Callable, Dict, List
from uuid import UUID

import structlog

from evo_ai.agents.base import BaseEvoAgent, AgentContext, AgentDecision
from evo_ai.agents.tools import DomainQueryTool, LineageTool, EvaluationTool
from evo_ai.domain.models.round import Round, RoundStatus
from evo_ai.infrastructure.database.connection import get_session
from evo_ai.infrastructure.database.repositories.postgres_evaluation_repo import (
    PostgresEvaluationRepository
)
from evo_ai.infrastructure.database.repositories.postgres_round_repo import (
    PostgresRoundRepository
)
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)

logger = structlog.get_logger(__name__)


class PlannerAgent(BaseEvoAgent):
    """
    Agent responsible for planning experiment rounds.

    Plans include:
    - Number of variants to generate
    - Mutation types and rates
    - Evaluation strategy
    - Selection pressure
    - Exploration vs exploitation balance

    Constitution adherence:
    - Logs all planning decisions with reasoning
    - Uses historical data for informed planning
    - Adapts strategies based on campaign progress
    """

    @property
    def agent_type(self) -> str:
        return "planner"

    def get_system_instructions(self) -> str:
        return """You are the PlannerAgent for an evolutionary experiment platform.

Your responsibilities:
1. Plan experiment rounds based on campaign configuration and historical data
2. Determine optimal number of variants to generate
3. Select appropriate mutation strategies (refactor, optimize, expand, etc.)
4. Balance exploration (trying new approaches) vs exploitation (refining good solutions)
5. Adapt selection pressure based on evolution progress

Guidelines:
- Early rounds: High exploration, more variants, diverse mutations
- Middle rounds: Balanced approach, focus on promising lineages
- Late rounds: High exploitation, fewer variants, refinement mutations
- Always provide clear reasoning for your decisions
- Use historical evaluation data to inform planning
- Consider diversity to avoid premature convergence

Output: A detailed round plan with mutation strategy, variant counts, and reasoning.
"""

    def get_tools(self) -> List[Callable]:
        return [
            # Domain queries
            self._create_domain_tool(
                name="get_campaign",
                description="Get campaign details and configuration",
                func=DomainQueryTool.get_campaign
            ),
            self._create_domain_tool(
                name="get_campaign_rounds",
                description="Get all rounds for the campaign",
                func=DomainQueryTool.get_campaign_rounds
            ),
            self._create_domain_tool(
                name="get_campaign_statistics",
                description="Get campaign statistics (total variants, generations, etc.)",
                func=DomainQueryTool.get_campaign_statistics
            ),
            self._create_domain_tool(
                name="get_round_evaluations",
                description="Get evaluation results for a round",
                func=EvaluationTool.get_round_evaluations
            ),
        ]

    async def execute(
        self,
        context: AgentContext,
        round_number: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Plan an experiment round.

        Args:
            context: Execution context with campaign_id
            round_number: Round number to plan
            **kwargs: Additional planning parameters

        Returns:
            Round plan with:
            - variant_count: Number of variants to generate
            - mutation_types: List of mutation strategies
            - mutation_distribution: Proportion for each mutation type
            - evaluation_strategy: How to evaluate variants
            - selection_pressure: Selection intensity (0.0-1.0)
            - reasoning: Detailed planning rationale
        """
        logger.info(
            "planning_round",
            round_number=round_number,
            campaign_id=str(context.campaign_id),
            trace_id=str(context.trace_id)
        )

        # Gather context
        campaign = await self._call_tool("get_campaign", context)
        rounds = await self._call_tool("get_campaign_rounds", context)
        stats = await self._call_tool("get_campaign_statistics", context)

        # Get campaign configuration
        config = campaign.get("config", {})
        base_variant_count = config.get("variants_per_round", 10)
        max_rounds = config.get("max_rounds", 20)

        # Analyze historical performance
        historical_scores = []
        if rounds:
            for round_data in rounds[-3:]:  # Last 3 rounds
                round_id = UUID(round_data["id"])
                round_context = AgentContext(
                    trace_id=context.trace_id,
                    campaign_id=context.campaign_id,
                    round_id=round_id
                )
                evals = await self._call_tool("get_round_evaluations", round_context)
                if evals.get("average_score"):
                    historical_scores.append(evals["average_score"])

        # Determine evolution phase
        progress = round_number / max_rounds
        if progress < 0.3:
            phase = "exploration"
        elif progress < 0.7:
            phase = "balanced"
        else:
            phase = "exploitation"

        # Plan based on phase
        if phase == "exploration":
            # Early rounds: high diversity
            variant_count = int(base_variant_count * 1.5)
            mutation_types = ["refactor", "optimize", "expand", "simplify", "experimental"]
            mutation_distribution = {
                "refactor": 0.3,
                "optimize": 0.2,
                "expand": 0.2,
                "simplify": 0.15,
                "experimental": 0.15,
            }
            selection_pressure = 0.3  # Low pressure, keep more variants
            reasoning = (
                f"Exploration phase (round {round_number}/{max_rounds}). "
                f"Using high diversity with {variant_count} variants across "
                f"5 mutation types to explore the solution space broadly."
            )

        elif phase == "balanced":
            # Middle rounds: focus on promising directions
            variant_count = base_variant_count

            # Adapt based on historical performance
            if historical_scores and len(historical_scores) >= 2:
                trend = historical_scores[-1] - historical_scores[0]
                if trend > 0:
                    # Improving: continue current strategy
                    mutation_types = ["refactor", "optimize", "expand"]
                    mutation_distribution = {"refactor": 0.4, "optimize": 0.4, "expand": 0.2}
                else:
                    # Stagnating: try different approaches
                    mutation_types = ["refactor", "experimental", "simplify"]
                    mutation_distribution = {"refactor": 0.4, "experimental": 0.3, "simplify": 0.3}
            else:
                mutation_types = ["refactor", "optimize", "expand"]
                mutation_distribution = {"refactor": 0.4, "optimize": 0.4, "expand": 0.2}

            selection_pressure = 0.5  # Moderate pressure
            reasoning = (
                f"Balanced phase (round {round_number}/{max_rounds}). "
                f"Generating {variant_count} variants with focus on refactoring and optimization. "
                f"Historical trend: {historical_scores[-2:] if len(historical_scores) >= 2 else 'insufficient data'}."
            )

        else:  # exploitation
            # Late rounds: refine best solutions
            variant_count = int(base_variant_count * 0.7)
            mutation_types = ["optimize", "refactor"]
            mutation_distribution = {"optimize": 0.6, "refactor": 0.4}
            selection_pressure = 0.7  # High pressure, only keep best
            reasoning = (
                f"Exploitation phase (round {round_number}/{max_rounds}). "
                f"Focusing on refinement with {variant_count} variants using "
                f"optimization and refactoring. High selection pressure to converge "
                f"on best solutions."
            )

        # Evaluation strategy (supports ensemble evaluators)
        evaluators = config.get("evaluators", ["llm_judge"])
        ensemble = config.get("ensemble")
        if ensemble is None and len(evaluators) > 1:
            weight = 1.0 / len(evaluators)
            ensemble = [{"type": evaluator, "weight": weight} for evaluator in evaluators]

        evaluation_strategy = {
            "evaluators": evaluators,
            "primary_evaluator": evaluators[0] if evaluators else "llm_judge",
            "ensemble": ensemble,
            "criteria_weights": config.get("criteria_weights"),
            "parallel_execution": True,
            "timeout_seconds": 300,
        }

        seed = config.get("seed", context.campaign_id.int % (2 ** 32))

        # Build round plan
        round_plan = {
            "round_number": round_number,
            "variant_count": variant_count,
            "mutation_types": mutation_types,
            "mutation_distribution": mutation_distribution,
            "evaluation_strategy": evaluation_strategy,
            "selection_pressure": selection_pressure,
            "seed": seed,
            "phase": phase,
            "reasoning": reasoning,
            "historical_context": {
                "completed_rounds": stats.get("completed_rounds", 0),
                "total_variants": stats.get("total_variants", 0),
                "max_generation": stats.get("max_generation", 0),
                "recent_scores": historical_scores,
            }
        }
        plan_hash = hashlib.sha256(
            json.dumps(round_plan, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        round_plan["plan_hash"] = plan_hash

        # Log planning decision
        decision = AgentDecision(
            agent_type=self.agent_type,
            decision_type="round_plan",
            input_data={
                "round_number": round_number,
                "campaign_id": str(context.campaign_id),
                "phase": phase,
                "progress": progress,
            },
            output_data=round_plan,
            reasoning=reasoning,
            confidence_score=0.85 if historical_scores else 0.7,
            metadata={
                "phase": phase,
                "historical_scores": historical_scores,
            }
        )
        await self._log_decision(context, decision)

        logger.info(
            "round_plan_created",
            round_number=round_number,
            variant_count=variant_count,
            phase=phase,
            trace_id=str(context.trace_id)
        )

        return round_plan

    async def create_round(
        self,
        context: AgentContext,
        round_number: int
    ) -> Dict[str, Any]:
        """
        Create a new round with planning.

        Args:
            context: Execution context
            round_number: Round number to create

        Returns:
            Created round details with plan
        """
        # Generate plan
        plan = await self.execute(context, round_number)

        # Create round entity
        round_obj = Round(
            campaign_id=context.campaign_id,
            round_number=round_number,
            status=RoundStatus.PENDING,
            plan=plan,
        )

        async with get_session() as session:
            repo = PostgresRoundRepository(session)
            existing_rounds = await repo.get_by_campaign_id(context.campaign_id)
            existing_round = next(
                (r for r in existing_rounds if r.round_number == round_number),
                None
            )

            if existing_round:
                logger.info(
                    "round_reuse_existing",
                    round_id=str(existing_round.id),
                    round_number=round_number,
                    trace_id=str(context.trace_id)
                )

                variant_repo = PostgresVariantRepository(session)
                eval_repo = PostgresEvaluationRepository(session)

                existing_variants = await variant_repo.get_by_round_id(existing_round.id)
                for variant in existing_variants:
                    await variant_repo.delete(variant.id, soft=True)

                await eval_repo.delete_by_round_id(existing_round.id)

                existing_round.status = RoundStatus.PENDING
                existing_round.plan = plan
                existing_round.metrics = {}
                existing_round.started_at = None
                existing_round.completed_at = None
                saved_round = await repo.update(existing_round)
            else:
                saved_round = await repo.create(round_obj)

        logger.info(
            "round_created",
            round_id=str(saved_round.id),
            round_number=round_number,
            trace_id=str(context.trace_id)
        )

        return {
            "round_id": str(saved_round.id),
            "round_number": round_number,
            "status": saved_round.status.value,
            "plan": plan,
        }
