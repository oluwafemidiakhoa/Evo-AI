"""Evaluation execution tool for agents.

Allows agents to run evaluations on variants and retrieve results.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from evo_ai.agents.base import AgentContext
from evo_ai.domain.models.evaluation import Evaluation, EvaluationStatus
from evo_ai.infrastructure.database.connection import get_session
from evo_ai.infrastructure.database.repositories.postgres_evaluation_repo import (
    PostgresEvaluationRepository
)
from evo_ai.infrastructure.database.repositories.postgres_variant_repo import (
    PostgresVariantRepository
)

logger = structlog.get_logger(__name__)


class EvaluationTool:
    """
    Tool for executing and querying evaluations.

    Provides agents with:
    - Evaluation creation
    - Score retrieval
    - Evaluation status checking
    - Comparative analysis
    """

    @staticmethod
    async def create_evaluation(
        context: AgentContext,
        variant_id: UUID,
        evaluator_type: str,
        evaluation_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new evaluation for a variant.

        Args:
            context: Agent execution context
            variant_id: Variant to evaluate
            evaluator_type: Type of evaluator (e.g., "llm_judge", "unit_test", "benchmark")
            evaluation_config: Evaluator configuration
            metadata: Optional additional metadata

        Returns:
            Dictionary with created evaluation details

        Example:
            result = await EvaluationTool.create_evaluation(
                context,
                variant_id=variant_id,
                evaluator_type="llm_judge",
                evaluation_config={
                    "model": "gpt-4",
                    "criteria": ["correctness", "clarity"]
                }
            )
        """
        async with get_session() as session:
            repo = PostgresEvaluationRepository(session)

            # Create evaluation in pending state
            evaluation = Evaluation(
                variant_id=variant_id,
                evaluator_type=evaluator_type,
                evaluation_config=evaluation_config,
                status=EvaluationStatus.PENDING,
                metadata=metadata or {},
            )

            saved_eval = await repo.create(evaluation)

            logger.info(
                "evaluation_created",
                evaluation_id=str(saved_eval.id),
                variant_id=str(variant_id),
                evaluator_type=evaluator_type,
                trace_id=str(context.trace_id)
            )

            return {
                "evaluation_id": str(saved_eval.id),
                "variant_id": str(saved_eval.variant_id),
                "evaluator_type": saved_eval.evaluator_type,
                "status": saved_eval.status.value,
                "created_at": saved_eval.created_at.isoformat(),
            }

    @staticmethod
    async def update_evaluation_result(
        context: AgentContext,
        evaluation_id: UUID,
        score: float,
        result_data: Dict[str, Any],
        status: EvaluationStatus = EvaluationStatus.COMPLETED
    ) -> Dict[str, Any]:
        """
        Update evaluation with results.

        Args:
            context: Agent execution context
            evaluation_id: Evaluation to update
            score: Numeric score
            result_data: Detailed evaluation results
            status: Evaluation status (default: COMPLETED)

        Returns:
            Updated evaluation details
        """
        async with get_session() as session:
            repo = PostgresEvaluationRepository(session)

            evaluation = await repo.get_by_id(evaluation_id)
            if not evaluation:
                raise ValueError(f"Evaluation {evaluation_id} not found")

            evaluation.score = score
            evaluation.result_data = result_data
            evaluation.status = status

            updated = await repo.update(evaluation)

            logger.info(
                "evaluation_updated",
                evaluation_id=str(updated.id),
                score=score,
                status=status.value,
                trace_id=str(context.trace_id)
            )

            return {
                "evaluation_id": str(updated.id),
                "variant_id": str(updated.variant_id),
                "score": updated.score,
                "status": updated.status.value,
                "result_data": updated.result_data,
            }

    @staticmethod
    async def get_variant_evaluations(
        context: AgentContext,
        variant_id: UUID,
        evaluator_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all evaluations for a variant.

        Args:
            context: Agent execution context
            variant_id: Variant to query
            evaluator_type: Optional filter by evaluator type

        Returns:
            List of evaluations
        """
        async with get_session() as session:
            repo = PostgresEvaluationRepository(session)

            evaluations = await repo.get_by_variant_id(variant_id)

            # Filter by evaluator type if specified
            if evaluator_type:
                evaluations = [e for e in evaluations if e.evaluator_type == evaluator_type]

            return [
                {
                    "evaluation_id": str(e.id),
                    "variant_id": str(e.variant_id),
                    "evaluator_type": e.evaluator_type,
                    "score": e.score,
                    "status": e.status.value,
                    "result_data": e.result_data,
                    "created_at": e.created_at.isoformat(),
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                }
                for e in evaluations
            ]

    @staticmethod
    async def get_round_evaluations(
        context: AgentContext,
        round_id: UUID,
        evaluator_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all evaluations for variants in a round.

        Args:
            context: Agent execution context
            round_id: Round to query
            evaluator_type: Optional filter by evaluator type

        Returns:
            Dictionary with aggregated evaluation data
        """
        async with get_session() as session:
            variant_repo = PostgresVariantRepository(session)
            eval_repo = PostgresEvaluationRepository(session)

            # Get all variants in round
            variants = await variant_repo.get_by_round_id(round_id)

            # Get evaluations for each variant
            all_evaluations = []
            for variant in variants:
                evals = await eval_repo.get_by_variant_id(variant.id)
                if evaluator_type:
                    evals = [e for e in evals if e.evaluator_type == evaluator_type]
                all_evaluations.extend(evals)

            # Aggregate statistics
            completed = [e for e in all_evaluations if e.status == EvaluationStatus.COMPLETED]
            scores = [e.score for e in completed if e.score is not None]

            return {
                "round_id": str(round_id),
                "total_evaluations": len(all_evaluations),
                "completed": len(completed),
                "pending": len([e for e in all_evaluations if e.status == EvaluationStatus.PENDING]),
                "failed": len([e for e in all_evaluations if e.status == EvaluationStatus.FAILED]),
                "average_score": sum(scores) / len(scores) if scores else None,
                "min_score": min(scores) if scores else None,
                "max_score": max(scores) if scores else None,
                "evaluations": [
                    {
                        "evaluation_id": str(e.id),
                        "variant_id": str(e.variant_id),
                        "evaluator_type": e.evaluator_type,
                        "score": e.score,
                        "status": e.status.value,
                    }
                    for e in all_evaluations
                ]
            }

    @staticmethod
    async def compare_variant_scores(
        context: AgentContext,
        variant_ids: List[UUID],
        evaluator_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare evaluation scores across multiple variants.

        Args:
            context: Agent execution context
            variant_ids: Variants to compare
            evaluator_type: Optional filter by evaluator type

        Returns:
            Comparative analysis of scores
        """
        async with get_session() as session:
            eval_repo = PostgresEvaluationRepository(session)

            comparisons = []

            for variant_id in variant_ids:
                evals = await eval_repo.get_by_variant_id(variant_id)

                if evaluator_type:
                    evals = [e for e in evals if e.evaluator_type == evaluator_type]

                completed = [e for e in evals if e.status == EvaluationStatus.COMPLETED]
                scores = [e.score for e in completed if e.score is not None]

                comparisons.append({
                    "variant_id": str(variant_id),
                    "evaluation_count": len(completed),
                    "average_score": sum(scores) / len(scores) if scores else None,
                    "min_score": min(scores) if scores else None,
                    "max_score": max(scores) if scores else None,
                    "scores": scores,
                })

            # Rank by average score
            ranked = sorted(
                [c for c in comparisons if c["average_score"] is not None],
                key=lambda x: x["average_score"],
                reverse=True
            )

            return {
                "variant_count": len(variant_ids),
                "evaluator_type": evaluator_type,
                "comparisons": comparisons,
                "ranked": ranked,
                "best_variant": ranked[0] if ranked else None,
                "worst_variant": ranked[-1] if ranked else None,
            }
