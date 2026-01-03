"""AgentOrchestrator - Coordinates multi-agent workflow using OpenAI Swarm.

Responsibilities:
- Coordinate all 5 agents (Planner, Variant, Scorer, Policy, Reporter)
- Manage round execution workflow
- Handle agent handoffs and communication
- Ensure proper sequencing and error handling
"""

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from swarm import Swarm

from evo_ai.agents.base import AgentContext
from evo_ai.agents.implementations.planner import PlannerAgent
from evo_ai.agents.implementations.variant_generator import VariantAgent
from evo_ai.agents.implementations.scorer import ScorerAgent
from evo_ai.agents.implementations.policy_maker import PolicyAgent
from evo_ai.agents.implementations.reporter import ReporterAgent
from evo_ai.domain.models.campaign import CampaignStatus
from evo_ai.domain.models.round import RoundStatus
from evo_ai.domain.models.report import ReportType
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
from evo_ai.mcp.registry import MCPRegistry

logger = structlog.get_logger(__name__)


class AgentOrchestrator:
    """
    Orchestrates multi-agent evolutionary experiments.

    Workflow for each round:
    1. PlannerAgent: Plan round (variant count, mutations, etc.)
    2. VariantAgent: Generate variants from selected parents
    3. ScorerAgent: Evaluate all variants
    4. PolicyAgent: Apply selection policy
    5. ReporterAgent: Generate round summary

    Constitution adherence:
    - All agent operations traced and logged
    - Clear sequencing and handoffs
    - Error handling and recovery
    - Full observability
    """

    def __init__(self, mcp_registry: MCPRegistry):
        """
        Initialize orchestrator with all agents.

        Args:
            mcp_registry: MCP registry for agent access to external systems
        """
        self.mcp_registry = mcp_registry

        # Initialize all agents
        self.planner = PlannerAgent(mcp_registry)
        self.variant_generator = VariantAgent(mcp_registry)
        self.scorer = ScorerAgent(mcp_registry)
        self.policy_maker = PolicyAgent(mcp_registry)
        self.reporter = ReporterAgent(mcp_registry)

        # Initialize Swarm
        self.swarm = Swarm()

        logger.info("orchestrator_initialized", agents=5)

    async def execute_round(
        self,
        campaign_id: UUID,
        round_number: int,
        trace_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete experiment round.

        Args:
            campaign_id: Campaign ID
            round_number: Round number to execute
            trace_id: Optional trace ID (generated if not provided)

        Returns:
            Round execution results

        Workflow:
        1. Create context with trace_id
        2. Plan round (PlannerAgent)
        3. Get parent variants (from previous round if not round 1)
        4. Generate new variants (VariantAgent)
        5. Evaluate variants (ScorerAgent)
        6. Apply selection policy (PolicyAgent)
        7. Generate report (ReporterAgent)
        8. Update round status
        """
        trace_id = trace_id or uuid4()

        logger.info(
            "round_execution_started",
            campaign_id=str(campaign_id),
            round_number=round_number,
            trace_id=str(trace_id)
        )

        # Create base context
        context = AgentContext(
            trace_id=trace_id,
            campaign_id=campaign_id,
        )

        try:
            # Step 1: Plan round
            logger.info("step_1_planning", round_number=round_number, trace_id=str(trace_id))
            round_result = await self.planner.create_round(context, round_number)
            round_id = UUID(round_result["round_id"])
            plan = round_result["plan"]

            # Update context with round_id
            context.round_id = round_id

            # Update round status to GENERATING (planning already completed)
            async with get_session() as session:
                round_repo = PostgresRoundRepository(session)
                round_obj = await round_repo.get_by_id(round_id)
                round_obj.status = RoundStatus.GENERATING
                await round_repo.update(round_obj)

            # Step 2: Get parent variants
            logger.info("step_2_get_parents", round_number=round_number, trace_id=str(trace_id))
            if round_number == 1:
                # First round: create initial variant(s)
                parent_ids = await self._create_initial_variants(context)
            else:
                # Get selected variants from previous round
                parent_ids = await self._get_selected_parents(context, round_number - 1)

            if not parent_ids:
                raise ValueError(f"No parent variants found for round {round_number}")

            # Step 3: Generate variants
            logger.info(
                "step_3_generate_variants",
                round_number=round_number,
                parent_count=len(parent_ids),
                trace_id=str(trace_id)
            )
            variants = await self.variant_generator.generate_batch(
                context,
                parent_ids=parent_ids,
                mutation_plan=plan
            )
            variant_ids = [UUID(v["variant_id"]) for v in variants]

            # Step 4: Evaluate variants
            logger.info(
                "step_4_evaluate_variants",
                round_number=round_number,
                variant_count=len(variant_ids),
                trace_id=str(trace_id)
            )
            evaluation_strategy = plan.get("evaluation_strategy", {})

            eval_results = await self.scorer.evaluate_batch(
                context,
                variant_ids=variant_ids,
                evaluator_type=evaluation_strategy.get("primary_evaluator", "llm_judge"),
                evaluation_config=evaluation_strategy
            )

            # Step 5: Apply selection policy
            logger.info("step_5_apply_policy", round_number=round_number, trace_id=str(trace_id))
            policy_result = await self.policy_maker.execute(
                context,
                round_number=round_number,
                selection_pressure=plan.get("selection_pressure", 0.5),
                policy_type="adaptive"
            )
            policy_id = UUID(policy_result["policy_id"])

            selection_result = await self.policy_maker.apply_policy(
                context,
                policy_id=policy_id
            )

            # Step 6: Generate report
            logger.info("step_6_generate_report", round_number=round_number, trace_id=str(trace_id))
            report_result = await self.reporter.execute(
                context,
                report_type=ReportType.ROUND_SUMMARY
            )

            # Step 7: Update round status
            async with get_session() as session:
                round_repo = PostgresRoundRepository(session)
                round_obj = await round_repo.get_by_id(round_id)
                round_obj.status = RoundStatus.COMPLETED
                await round_repo.update(round_obj)

            logger.info(
                "round_execution_completed",
                campaign_id=str(campaign_id),
                round_number=round_number,
                round_id=str(round_id),
                variants_generated=len(variants),
                variants_selected=selection_result["selected_count"],
                trace_id=str(trace_id)
            )

            return {
                "round_id": str(round_id),
                "round_number": round_number,
                "status": "completed",
                "plan": plan,
                "variants_generated": len(variants),
                "variants_evaluated": eval_results["total_evaluated"],
                "variants_selected": selection_result["selected_count"],
                "average_score": eval_results.get("average_score"),
                "report_id": report_result["report_id"],
                "trace_id": str(trace_id),
            }

        except Exception as e:
            logger.error(
                "round_execution_failed",
                campaign_id=str(campaign_id),
                round_number=round_number,
                error=str(e),
                trace_id=str(trace_id)
            )

            # Update round status to FAILED
            if context.round_id:
                async with get_session() as session:
                    round_repo = PostgresRoundRepository(session)
                    round_obj = await round_repo.get_by_id(context.round_id)
                    if round_obj:
                        round_obj.status = RoundStatus.FAILED
                        await round_repo.update(round_obj)

            raise

    async def execute_campaign(
        self,
        campaign_id: UUID,
        max_rounds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute complete campaign (multiple rounds).

        Args:
            campaign_id: Campaign ID
            max_rounds: Maximum rounds to execute (defaults to campaign config)

        Returns:
            Campaign execution results
        """
        trace_id = uuid4()

        logger.info(
            "campaign_execution_started",
            campaign_id=str(campaign_id),
            trace_id=str(trace_id)
        )

        # Get campaign
        async with get_session() as session:
            campaign_repo = PostgresCampaignRepository(session)
            campaign = await campaign_repo.get_by_id(campaign_id)

            if not campaign:
                raise ValueError(f"Campaign {campaign_id} not found")

            # Update status to ACTIVE while executing rounds
            campaign.status = CampaignStatus.ACTIVE
            await campaign_repo.update(campaign)

            # Get max_rounds from config if not provided
            if max_rounds is None:
                max_rounds = campaign.config.get("max_rounds", 10)

        round_results = []

        try:
            # Execute rounds sequentially
            for round_number in range(1, max_rounds + 1):
                logger.info(
                    "executing_round",
                    campaign_id=str(campaign_id),
                    round_number=round_number,
                    trace_id=str(trace_id)
                )

                round_result = await self.execute_round(
                    campaign_id=campaign_id,
                    round_number=round_number,
                    trace_id=trace_id
                )
                round_results.append(round_result)

                # Check early stopping conditions
                if round_result.get("average_score", 0) >= 0.95:
                    logger.info(
                        "early_stopping",
                        reason="high_score",
                        score=round_result["average_score"],
                        round_number=round_number
                    )
                    break

            # Generate final report
            context = AgentContext(
                trace_id=trace_id,
                campaign_id=campaign_id
            )
            final_report = await self.reporter.execute(
                context,
                report_type=ReportType.FINAL_REPORT
            )

            # Update campaign status
            async with get_session() as session:
                campaign_repo = PostgresCampaignRepository(session)
                campaign = await campaign_repo.get_by_id(campaign_id)
                campaign.status = CampaignStatus.COMPLETED
                await campaign_repo.update(campaign)

            logger.info(
                "campaign_execution_completed",
                campaign_id=str(campaign_id),
                rounds_completed=len(round_results),
                trace_id=str(trace_id)
            )

            return {
                "campaign_id": str(campaign_id),
                "status": "completed",
                "rounds_completed": len(round_results),
                "round_results": round_results,
                "final_report_id": final_report["report_id"],
                "trace_id": str(trace_id),
            }

        except Exception as e:
            logger.error(
                "campaign_execution_failed",
                campaign_id=str(campaign_id),
                error=str(e),
                trace_id=str(trace_id)
            )

            # Update campaign status
            async with get_session() as session:
                campaign_repo = PostgresCampaignRepository(session)
                campaign = await campaign_repo.get_by_id(campaign_id)
                if campaign:
                    campaign.status = CampaignStatus.FAILED
                    await campaign_repo.update(campaign)

            raise

    async def _create_initial_variants(self, context: AgentContext) -> List[UUID]:
        """Create initial variant(s) for round 1."""
        from evo_ai.domain.models.variant import Variant

        initial_content = """# Initial variant (Generation 0)
def hello_world():
    return "Hello, World!"
"""

        variant = Variant(
            round_id=context.round_id,
            parent_id=None,  # No parent for generation 0
            generation=0,  # Initial generation
            content=initial_content,
            mutation_type=None,
            mutation_metadata={"is_initial": True}
        )

        async with get_session() as session:
            repo = PostgresVariantRepository(session)
            saved = await repo.create(variant)

        logger.info(
            "initial_variant_created",
            variant_id=str(saved.id),
            round_id=str(context.round_id)
        )

        return [saved.id]

    async def _get_selected_parents(
        self,
        context: AgentContext,
        previous_round_number: int
    ) -> List[UUID]:
        """Get selected variants from previous round."""
        async with get_session() as session:
            round_repo = PostgresRoundRepository(session)
            variant_repo = PostgresVariantRepository(session)

            # Get previous round
            rounds = await round_repo.get_by_campaign_id(context.campaign_id)
            previous_round = next(
                (r for r in rounds if r.round_number == previous_round_number),
                None
            )

            if not previous_round:
                raise ValueError(f"Previous round {previous_round_number} not found")

            # Get selected variants
            selected = await variant_repo.get_selected_by_round(previous_round.id)

            return [v.id for v in selected]
