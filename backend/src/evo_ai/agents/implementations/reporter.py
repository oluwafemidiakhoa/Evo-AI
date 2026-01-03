"""ReporterAgent - Generates comprehensive experiment reports.

Responsibilities:
- Generate round summaries
- Create campaign reports with evolution metrics
- Visualize lineage trees and progress
- Export results in multiple formats
"""

import json
from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import UUID

import structlog

from evo_ai.agents.base import BaseEvoAgent, AgentContext, AgentDecision
from evo_ai.agents.tools import DomainQueryTool, EvaluationTool, LineageTool
from evo_ai.domain.models.report import Report, ReportType
from evo_ai.infrastructure.database.connection import get_session
from evo_ai.infrastructure.database.repositories.postgres_report_repo import (
    PostgresReportRepository
)
from evo_ai.infrastructure.database.repositories.postgres_round_repo import (
    PostgresRoundRepository
)
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)

logger = structlog.get_logger(__name__)


class ReporterAgent(BaseEvoAgent):
    """
    Agent responsible for generating experiment reports.

    Report types:
    - round_summary: Summary of a single round
    - campaign_progress: Overall campaign progress
    - lineage_analysis: Detailed lineage evolution
    - final_report: Complete experiment results

    Constitution adherence:
    - Transparent reporting of all metrics
    - Reproducible report generation
    - Logs report generation decisions
    """

    @property
    def agent_type(self) -> str:
        return "reporter"

    def get_system_instructions(self) -> str:
        return """You are the ReporterAgent for an evolutionary experiment platform.

Your responsibilities:
1. Generate comprehensive experiment reports
2. Analyze evolution metrics and trends
3. Visualize lineage trees and progress
4. Provide actionable insights and recommendations

Report types:
- round_summary: What happened in this round?
- campaign_progress: How is the experiment progressing?
- lineage_analysis: How have lineages evolved?
- final_report: Complete results and conclusions

Guidelines:
- Be comprehensive but concise
- Highlight key findings and anomalies
- Include quantitative metrics and qualitative insights
- Provide visualizations where appropriate
- Offer recommendations for future rounds
- Make reports accessible to both technical and non-technical audiences

Output: Structured report with metrics, visualizations, and insights.
"""

    def get_tools(self) -> List[Callable]:
        return [
            # Domain tools
            self._create_domain_tool(
                name="get_campaign",
                description="Get campaign details",
                func=DomainQueryTool.get_campaign
            ),
            self._create_domain_tool(
                name="get_campaign_rounds",
                description="Get all campaign rounds",
                func=DomainQueryTool.get_campaign_rounds
            ),
            self._create_domain_tool(
                name="get_campaign_statistics",
                description="Get campaign statistics",
                func=DomainQueryTool.get_campaign_statistics
            ),
            self._create_domain_tool(
                name="get_round_variants",
                description="Get round variants",
                func=DomainQueryTool.get_round_variants
            ),
            self._create_domain_tool(
                name="get_round_evaluations",
                description="Get round evaluations",
                func=EvaluationTool.get_round_evaluations
            ),
            self._create_domain_tool(
                name="get_lineage",
                description="Get variant lineage",
                func=LineageTool.get_full_lineage
            ),
            # MCP tools for export
            self._create_mcp_tool(
                server_name="filesystem",
                tool_name="list_directory",
                description="List report directory"
            ),
        ]

    async def execute(
        self,
        context: AgentContext,
        report_type: ReportType = ReportType.ROUND_SUMMARY,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a report.

        Args:
            context: Execution context
            report_type: Type of report to generate
            **kwargs: Report-specific parameters

        Returns:
            Report content and metadata
        """
        logger.info(
            "generating_report",
            report_type=report_type.value,
            campaign_id=str(context.campaign_id),
            trace_id=str(context.trace_id)
        )

        # Generate report based on type
        report_round_id = context.round_id

        if report_type == ReportType.ROUND_SUMMARY:
            if not context.round_id:
                raise ValueError("round_id required for round summary")
            content = await self._generate_round_summary(context)

        elif report_type == ReportType.CAMPAIGN_PROGRESS:
            content = await self._generate_campaign_progress(context)

        elif report_type == ReportType.LINEAGE_ANALYSIS:
            variant_id = kwargs.get("variant_id")
            if not variant_id:
                raise ValueError("variant_id required for lineage analysis")
            content = await self._generate_lineage_analysis(context, variant_id)
            report_round_id = await self._get_round_id_for_variant(variant_id)

        elif report_type == ReportType.FINAL_REPORT:
            content = await self._generate_final_report(context)

        else:
            raise ValueError(f"Unknown report type: {report_type}")

        if not report_round_id:
            report_round_id = await self._get_latest_round_id(context.campaign_id)

        serialized_content = json.dumps(content, ensure_ascii=True)

        # Create report entity
        report_meta = {
            "generated_at": datetime.utcnow().isoformat(),
            "report_version": "1.0",
        }
        if context.run_id or context.metadata.get("run_id"):
            report_meta["run_id"] = str(context.run_id or context.metadata.get("run_id"))

        report = Report(
            round_id=report_round_id,
            report_type=report_type.value,
            format="json",
            content=serialized_content,
            meta_data=report_meta,
        )

        async with get_session() as session:
            repo = PostgresReportRepository(session)
            saved_report = await repo.create(report)

        # Log decision
        decision = AgentDecision(
            agent_type=self.agent_type,
            decision_type="report_generated",
            input_data={
                "report_type": report_type.value,
                "campaign_id": str(context.campaign_id),
            },
            output_data={
                "report_id": str(saved_report.id),
                "content_size": len(serialized_content),
            },
            reasoning=f"Generated {report_type.value} report",
            confidence_score=0.9,
            metadata={"report_type": report_type.value}
        )
        await self._log_decision(context, decision)

        logger.info(
            "report_generated",
            report_id=str(saved_report.id),
            report_type=report_type.value,
            trace_id=str(context.trace_id)
        )

        return {
            "report_id": str(saved_report.id),
            "report_type": report_type.value,
            "content": content,
            "generated_at": saved_report.created_at.isoformat(),
        }

    async def _get_latest_round_id(self, campaign_id: UUID) -> UUID:
        """Fetch latest round ID for a campaign."""
        async with get_session() as session:
            round_repo = PostgresRoundRepository(session)
            latest_round = await round_repo.get_latest_round(campaign_id)
            if not latest_round:
                raise ValueError("No rounds found for campaign report")
            return latest_round.id

    async def _get_round_id_for_variant(self, variant_id: UUID) -> UUID:
        """Fetch round ID for a variant."""
        async with get_session() as session:
            variant_repo = PostgresVariantRepository(session)
            variant = await variant_repo.get_by_id(variant_id)
            if not variant:
                raise ValueError(f"Variant {variant_id} not found for report")
            return variant.round_id

    async def _generate_round_summary(self, context: AgentContext) -> Dict[str, Any]:
        """Generate round summary report."""
        variants = await self._call_tool("get_round_variants", context)
        evaluations = await self._call_tool("get_round_evaluations", context)

        total_variants = len(variants)
        selected_variants = [v for v in variants if v.get("is_selected")]

        # Get evaluation summary
        eval_summary = evaluations.get("evaluations", [])
        avg_score = evaluations.get("average_score", 0)
        min_score = evaluations.get("min_score", 0)
        max_score = evaluations.get("max_score", 0)

        # Analyze generations
        generations = [v.get("generation", 0) for v in variants]
        max_gen = max(generations) if generations else 0
        avg_gen = sum(generations) / len(generations) if generations else 0

        # Mutation type distribution
        mutation_types = {}
        for v in variants:
            mt = v.get("mutation_type")
            if mt:
                mutation_types[mt] = mutation_types.get(mt, 0) + 1

        return {
            "summary": {
                "round_id": str(context.round_id),
                "total_variants": total_variants,
                "selected_variants": len(selected_variants),
                "selection_rate": len(selected_variants) / total_variants if total_variants else 0,
            },
            "evaluations": {
                "total_evaluations": len(eval_summary),
                "completed": evaluations.get("completed", 0),
                "average_score": avg_score,
                "min_score": min_score,
                "max_score": max_score,
                "score_range": max_score - min_score if max_score and min_score else 0,
            },
            "evolution": {
                "max_generation": max_gen,
                "average_generation": avg_gen,
                "mutation_distribution": mutation_types,
            },
            "insights": [
                f"Generated {total_variants} variants with {len(selected_variants)} selected",
                f"Average score: {avg_score:.2f}, range: {min_score:.2f}-{max_score:.2f}",
                f"Evolution reached generation {max_gen}",
                f"Most common mutation: {max(mutation_types, key=mutation_types.get) if mutation_types else 'N/A'}",
            ]
        }

    async def _generate_campaign_progress(self, context: AgentContext) -> Dict[str, Any]:
        """Generate campaign progress report."""
        campaign = await self._call_tool("get_campaign", context)
        rounds = await self._call_tool("get_campaign_rounds", context)
        stats = await self._call_tool("get_campaign_statistics", context)

        # Analyze round progression
        round_scores = []
        for round_data in rounds:
            if round_data.get("status") == "completed":
                round_id = UUID(round_data["id"])
                round_context = AgentContext(
                    trace_id=context.trace_id,
                    campaign_id=context.campaign_id,
                    run_id=context.run_id,
                    round_id=round_id,
                )
                evals = await self._call_tool("get_round_evaluations", round_context)
                if evals.get("average_score"):
                    round_scores.append({
                        "round_number": round_data.get("round_number"),
                        "average_score": evals.get("average_score"),
                    })

        # Calculate trends
        if len(round_scores) >= 2:
            trend = round_scores[-1]["average_score"] - round_scores[0]["average_score"]
            trend_direction = "improving" if trend > 0 else "declining" if trend < 0 else "stable"
        else:
            trend = 0
            trend_direction = "insufficient_data"

        return {
            "campaign": {
                "id": str(context.campaign_id),
                "name": campaign.get("name"),
                "status": campaign.get("status"),
                "started_at": campaign.get("started_at"),
            },
            "progress": {
                "total_rounds": len(rounds),
                "completed_rounds": stats.get("completed_rounds", 0),
                "total_variants": stats.get("total_variants", 0),
                "max_generation": stats.get("max_generation", 0),
            },
            "performance": {
                "round_scores": round_scores,
                "trend": trend,
                "trend_direction": trend_direction,
                "current_score": round_scores[-1]["average_score"] if round_scores else None,
            },
            "insights": [
                f"Campaign '{campaign.get('name')}' has completed {stats.get('completed_rounds', 0)} rounds",
                f"Generated {stats.get('total_variants', 0)} total variants across {stats.get('max_generation', 0)} generations",
                f"Performance trend: {trend_direction} ({trend:+.2f})" if trend else "Trend: insufficient data",
            ]
        }

    async def _generate_lineage_analysis(
        self,
        context: AgentContext,
        variant_id: UUID
    ) -> Dict[str, Any]:
        """Generate lineage analysis report."""
        variant_context = AgentContext(
            trace_id=context.trace_id,
            campaign_id=context.campaign_id,
            run_id=context.run_id,
            variant_id=variant_id,
        )

        lineage = await self._call_tool("get_lineage", variant_context)
        lineage_variants = lineage.get("lineage", [])

        # Analyze lineage evolution
        mutations = []
        scores = []

        for v in lineage_variants:
            if v.get("mutation_type"):
                mutations.append(v.get("mutation_type"))

        mutation_path = " -> ".join(mutations) if mutations else "No mutations"

        return {
            "variant": {
                "id": str(variant_id),
                "generation": lineage_variants[0].get("generation") if lineage_variants else 0,
            },
            "lineage": {
                "total_ancestors": len(lineage_variants),
                "founder": lineage.get("founder"),
                "mutation_path": mutation_path,
                "mutations": mutations,
            },
            "evolution": {
                "generations": lineage.get("generations", 0),
                "mutation_diversity": len(set(mutations)),
            },
            "insights": [
                f"Variant has {len(lineage_variants)} ancestors across {lineage.get('generations', 0)} generations",
                f"Mutation path: {mutation_path}",
                f"Mutation diversity: {len(set(mutations))} unique mutation types",
            ]
        }

    async def _generate_final_report(self, context: AgentContext) -> Dict[str, Any]:
        """Generate final experiment report."""
        campaign = await self._call_tool("get_campaign", context)
        stats = await self._call_tool("get_campaign_statistics", context)
        rounds = await self._call_tool("get_campaign_rounds", context)

        # Get best performing variants across all rounds
        best_variants = []
        # Would query top variants by score across all rounds

        return {
            "campaign": {
                "id": str(context.campaign_id),
                "name": campaign.get("name"),
                "status": campaign.get("status"),
                "duration": "TBD",  # Would calculate from timestamps
            },
            "results": {
                "total_rounds": len(rounds),
                "total_variants": stats.get("total_variants", 0),
                "max_generation": stats.get("max_generation", 0),
                "selection_rate": stats.get("selection_rate", 0),
            },
            "best_variants": best_variants[:10],  # Top 10
            "conclusions": [
                f"Experiment completed {len(rounds)} rounds",
                f"Evolved {stats.get('total_variants', 0)} variants over {stats.get('max_generation', 0)} generations",
                f"Overall selection rate: {stats.get('selection_rate', 0):.1%}",
            ],
            "recommendations": [
                "Consider running additional rounds if convergence not achieved",
                "Analyze top-performing lineages for common patterns",
                "Review mutation strategies for future experiments",
            ]
        }
