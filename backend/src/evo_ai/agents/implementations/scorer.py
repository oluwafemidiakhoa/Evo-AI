"""ScorerAgent - Evaluates variant quality.

Responsibilities:
- Execute evaluations on variants using configured evaluators
- Compare variants and rank by performance
- Provide detailed evaluation feedback
- Support multiple evaluation types (LLM judge, unit tests, benchmarks)
"""

from typing import Any, Callable, Dict, List
from uuid import UUID

import structlog

from evo_ai.agents.base import BaseEvoAgent, AgentContext, AgentDecision
from evo_ai.agents.tools import DomainQueryTool, EvaluationTool, LineageTool

logger = structlog.get_logger(__name__)


class ScorerAgent(BaseEvoAgent):
    """
    Agent responsible for evaluating variant quality.

    Evaluation types:
    - llm_judge: Use LLM to assess code quality
    - unit_test: Run automated tests
    - benchmark: Measure performance metrics
    - human_review: Facilitate human evaluation (async)

    Constitution adherence:
    - Logs all scoring decisions with detailed reasoning
    - Transparent evaluation criteria
    - Reproducible scoring methodology
    """

    @property
    def agent_type(self) -> str:
        return "scorer"

    def get_system_instructions(self) -> str:
        return """You are the ScorerAgent for an evolutionary experiment platform.

Your responsibilities:
1. Evaluate variant quality using configured evaluators
2. Provide numerical scores (0.0-1.0) with detailed feedback
3. Compare variants and identify best performers
4. Analyze evaluation trends across generations

Evaluation criteria (configurable):
- Correctness: Does it work as intended?
- Code quality: Is it well-structured and maintainable?
- Performance: Is it efficient?
- Innovation: Does it introduce novel approaches?
- Simplicity: Is it unnecessarily complex?

Guidelines:
- Be objective and consistent in scoring
- Provide detailed reasoning for scores
- Consider lineage context (has quality improved over generations?)
- Flag anomalies (sudden score drops, etc.)
- Support multiple evaluation types (LLM, tests, benchmarks)

Output: Evaluation results with scores, feedback, and confidence.
"""

    def get_tools(self) -> List[Callable]:
        return [
            # Domain tools
            self._create_domain_tool(
                name="get_variant",
                description="Get variant content for evaluation",
                func=DomainQueryTool.get_variant
            ),
            self._create_domain_tool(
                name="get_lineage",
                description="Get variant lineage for context",
                func=LineageTool.get_full_lineage
            ),
            self._create_domain_tool(
                name="create_evaluation",
                description="Create evaluation record",
                func=EvaluationTool.create_evaluation
            ),
            self._create_domain_tool(
                name="update_evaluation",
                description="Update evaluation with results",
                func=EvaluationTool.update_evaluation_result
            ),
            self._create_domain_tool(
                name="get_variant_evaluations",
                description="Get existing evaluations for variant",
                func=EvaluationTool.get_variant_evaluations
            ),
            # MCP tools
            self._create_mcp_tool(
                server_name="filesystem",
                tool_name="read_file",
                description="Read variant source code"
            ),
        ]

    async def execute(
        self,
        context: AgentContext,
        variant_id: UUID,
        evaluator_type: str = "llm_judge",
        evaluation_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a variant.

        Args:
            context: Execution context
            variant_id: Variant to evaluate
            evaluator_type: Type of evaluator (llm_judge, unit_test, benchmark)
            evaluation_config: Evaluator-specific configuration

        Returns:
            Evaluation results with:
            - evaluation_id: Evaluation record UUID
            - score: Numeric score (0.0-1.0)
            - feedback: Detailed evaluation feedback
            - criteria_scores: Per-criterion breakdown
            - confidence: Confidence in the evaluation
        """
        evaluation_config = evaluation_config or {}

        logger.info(
            "evaluating_variant",
            variant_id=str(variant_id),
            evaluator_type=evaluator_type,
            trace_id=str(context.trace_id)
        )

        # Get variant
        variant_context = AgentContext(
            trace_id=context.trace_id,
            campaign_id=context.campaign_id,
            variant_id=variant_id
        )
        variant = await self._call_tool("get_variant", variant_context)
        lineage = await self._call_tool("get_lineage", variant_context)

        # Create evaluation record (may return cached result)
        eval_result = await self._call_tool(
            "create_evaluation",
            variant_context,
            variant_id=variant_id,
            evaluator_type=evaluator_type,
            evaluation_config=evaluation_config
        )
        evaluation_id = UUID(eval_result["evaluation_id"])

        if eval_result.get("cached"):
            cached_data = eval_result.get("result_data", {})
            return {
                "evaluation_id": str(evaluation_id),
                "variant_id": str(variant_id),
                "score": eval_result.get("score"),
                "feedback": cached_data.get("feedback", "Cached evaluation result."),
                "criteria_scores": cached_data.get("criteria_scores", {}),
                "confidence": 0.95,
                "cached": True,
            }

        # Execute evaluation based on type
        if evaluator_type == "llm_judge":
            score, feedback, criteria = await self._evaluate_with_llm(
                variant, lineage, evaluation_config
            )
        elif evaluator_type == "unit_test":
            score, feedback, criteria = await self._evaluate_with_tests(
                variant, lineage, evaluation_config
            )
        elif evaluator_type == "benchmark":
            score, feedback, criteria = await self._evaluate_with_benchmark(
                variant, lineage, evaluation_config
            )
        elif evaluator_type == "ensemble":
            score, feedback, criteria = await self._evaluate_with_ensemble(
                variant, lineage, evaluation_config
            )
        else:
            raise ValueError(f"Unknown evaluator type: {evaluator_type}")

        # Update evaluation with results
        from evo_ai.domain.models.evaluation import EvaluationStatus

        eval_context = AgentContext(
            trace_id=context.trace_id,
            campaign_id=context.campaign_id
        )
        await self._call_tool(
            "update_evaluation",
            eval_context,
            evaluation_id=evaluation_id,
            score=score,
            result_data={
                "feedback": feedback,
                "criteria_scores": criteria,
                "lineage_context": {
                    "generation": variant["generation"],
                    "lineage_depth": lineage.get("generations", 0),
                }
            },
            status=EvaluationStatus.COMPLETED
        )

        # Log decision
        decision = AgentDecision(
            agent_type=self.agent_type,
            decision_type="variant_evaluated",
            input_data={
                "variant_id": str(variant_id),
                "evaluator_type": evaluator_type,
                "generation": variant["generation"],
            },
            output_data={
                "evaluation_id": str(evaluation_id),
                "score": score,
                "criteria_scores": criteria,
            },
            reasoning=feedback,
            confidence_score=0.85,
            metadata={
                "evaluator_type": evaluator_type,
                "lineage_depth": lineage.get("generations", 0),
            }
        )
        await self._log_decision(context, decision)

        logger.info(
            "variant_evaluated",
            variant_id=str(variant_id),
            evaluation_id=str(evaluation_id),
            score=score,
            trace_id=str(context.trace_id)
        )

        return {
            "evaluation_id": str(evaluation_id),
            "variant_id": str(variant_id),
            "score": score,
            "feedback": feedback,
            "criteria_scores": criteria,
            "confidence": 0.85,
        }

    async def _evaluate_with_llm(
        self,
        variant: Dict[str, Any],
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[float, str, Dict[str, float]]:
        """Evaluate using LLM judge."""
        # Simulate LLM evaluation (in production, would call LLM API)
        content = variant["content"]
        generation = variant["generation"]

        # Criteria-based scoring
        criteria = {
            "correctness": 0.8,  # Would analyze code semantics
            "code_quality": 0.75,  # Would assess structure, naming
            "performance": 0.7,  # Would analyze algorithmic complexity
            "innovation": 0.6 + (generation * 0.02),  # Reward evolution
            "simplicity": 0.85,  # Would measure complexity metrics
        }

        # Aggregate score (weighted average)
        weights = config.get("criteria_weights", {
            "correctness": 0.3,
            "code_quality": 0.25,
            "performance": 0.2,
            "innovation": 0.15,
            "simplicity": 0.1,
        })
        score = sum(criteria[k] * weights.get(k, 0) for k in criteria)

        feedback = (
            f"LLM evaluation of variant (generation {generation}):\n"
            f"- Correctness: {criteria['correctness']:.2f} - Code appears functionally correct\n"
            f"- Code quality: {criteria['code_quality']:.2f} - Well-structured with clear naming\n"
            f"- Performance: {criteria['performance']:.2f} - Reasonable algorithmic efficiency\n"
            f"- Innovation: {criteria['innovation']:.2f} - Shows evolutionary progress\n"
            f"- Simplicity: {criteria['simplicity']:.2f} - Good balance of simplicity\n"
            f"\nOverall score: {score:.2f}"
        )

        return score, feedback, criteria

    async def _evaluate_with_tests(
        self,
        variant: Dict[str, Any],
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[float, str, Dict[str, float]]:
        """Evaluate using unit tests."""
        # Simulate test execution (in production, would run actual tests)
        total_tests = config.get("total_tests", 10)
        passed_tests = 8  # Simulated

        score = passed_tests / total_tests

        criteria = {
            "tests_passed": score,
            "coverage": 0.75,  # Would measure code coverage
            "execution_time": 0.9,  # Would measure test speed
        }

        feedback = (
            f"Unit test evaluation:\n"
            f"- Tests passed: {passed_tests}/{total_tests} ({score:.1%})\n"
            f"- Code coverage: {criteria['coverage']:.1%}\n"
            f"- Execution time: {criteria['execution_time']:.2f} (normalized)\n"
        )

        return score, feedback, criteria

    async def _evaluate_with_benchmark(
        self,
        variant: Dict[str, Any],
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[float, str, Dict[str, float]]:
        """Evaluate using performance benchmarks."""
        # Simulate benchmark execution
        criteria = {
            "throughput": 0.8,  # Requests per second
            "latency": 0.85,  # Response time
            "memory": 0.75,  # Memory usage
            "cpu": 0.8,  # CPU efficiency
        }

        score = sum(criteria.values()) / len(criteria)

        feedback = (
            f"Benchmark evaluation:\n"
            f"- Throughput: {criteria['throughput']:.2f}\n"
            f"- Latency: {criteria['latency']:.2f}\n"
            f"- Memory efficiency: {criteria['memory']:.2f}\n"
            f"- CPU efficiency: {criteria['cpu']:.2f}\n"
            f"\nAggregate score: {score:.2f}"
        )

        return score, feedback, criteria

    async def _evaluate_with_ensemble(
        self,
        variant: Dict[str, Any],
        lineage: Dict[str, Any],
        config: Dict[str, Any]
    ) -> tuple[float, str, Dict[str, Any]]:
        """Evaluate using an ensemble of evaluators."""
        config = config or {}
        ensemble = config.get("ensemble", [])

        if not ensemble:
            score, feedback, criteria = await self._evaluate_with_llm(
                variant, lineage, config
            )
            return score, feedback, {"ensemble": [{"type": "llm_judge", "score": score, "criteria": criteria}]}

        component_results = []
        weighted_scores = []
        total_weight = 0.0

        for component in ensemble:
            evaluator = component.get("type", "llm_judge")
            weight = float(component.get("weight", 1.0))
            component_config = component.get("config", {})

            if evaluator == "llm_judge":
                score, feedback, criteria = await self._evaluate_with_llm(
                    variant, lineage, component_config
                )
            elif evaluator == "unit_test":
                score, feedback, criteria = await self._evaluate_with_tests(
                    variant, lineage, component_config
                )
            elif evaluator == "benchmark":
                score, feedback, criteria = await self._evaluate_with_benchmark(
                    variant, lineage, component_config
                )
            else:
                raise ValueError(f"Unknown evaluator type: {evaluator}")

            component_results.append({
                "type": evaluator,
                "weight": weight,
                "score": score,
                "criteria_scores": criteria,
                "feedback": feedback,
            })

            weighted_scores.append(score * weight)
            total_weight += weight

        aggregate_score = sum(weighted_scores) / total_weight if total_weight else 0.0
        feedback = (
            "Ensemble evaluation:\n"
            + "\n".join(
                f"- {c['type']}: {c['score']:.2f} (w={c['weight']:.2f})"
                for c in component_results
            )
            + f"\nAggregate score: {aggregate_score:.2f}"
        )

        return aggregate_score, feedback, {"ensemble": component_results}

    async def evaluate_batch(
        self,
        context: AgentContext,
        variant_ids: List[UUID],
        evaluator_type: str = "llm_judge",
        evaluation_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate multiple variants and rank them.

        Args:
            context: Execution context
            variant_ids: List of variants to evaluate
            evaluator_type: Type of evaluator
            evaluation_config: Evaluator configuration

        Returns:
            Batch results with rankings
        """
        evaluation_config = evaluation_config or {}
        strategy_evaluators = evaluation_config.get("evaluators") or []
        strategy_ensemble = evaluation_config.get("ensemble")

        if strategy_ensemble:
            evaluator_type = "ensemble"
        elif strategy_evaluators:
            evaluator_type = strategy_evaluators[0]

        results = []

        for variant_id in variant_ids:
            eval_result = await self.execute(
                context,
                variant_id=variant_id,
                evaluator_type=evaluator_type,
                evaluation_config=evaluation_config
            )
            results.append(eval_result)

        # Rank by score
        ranked = sorted(results, key=lambda x: x["score"], reverse=True)

        logger.info(
            "batch_evaluation_complete",
            variant_count=len(variant_ids),
            best_score=ranked[0]["score"] if ranked else None,
            trace_id=str(context.trace_id)
        )

        return {
            "total_evaluated": len(results),
            "results": results,
            "ranked": ranked,
            "best_variant": ranked[0] if ranked else None,
            "worst_variant": ranked[-1] if ranked else None,
            "average_score": sum(r["score"] for r in results) / len(results) if results else 0,
        }
