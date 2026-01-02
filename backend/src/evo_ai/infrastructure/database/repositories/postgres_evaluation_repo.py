"""PostgreSQL implementation of Evaluation repository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.domain.models.evaluation import Evaluation, EvaluationStatus
from evo_ai.infrastructure.database.models import EvaluationDB


def _build_execution_metadata(evaluation: Evaluation) -> dict:
    metadata = {
        "status": evaluation.status.value,
        "evaluator_type": evaluation.evaluator_type,
    }
    if evaluation.completed_at:
        metadata["completed_at"] = evaluation.completed_at.isoformat()
    return metadata


class PostgresEvaluationRepository:
    """PostgreSQL implementation of EvaluationRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, entity: Evaluation) -> Evaluation:
        """Create a new evaluation."""
        score = entity.score if entity.score is not None else 0.0
        db_evaluation = EvaluationDB(
            id=entity.id,
            variant_id=entity.variant_id,
            round_id=entity.round_id,
            score=score,
            metrics=entity.result_data,
            evaluator_config=entity.evaluation_config,
            execution_metadata=_build_execution_metadata(entity),
            meta_data=entity.metadata,
            created_at=entity.created_at,
        )
        self.session.add(db_evaluation)
        await self.session.flush()
        return self._to_domain(db_evaluation)

    async def get_by_id(self, entity_id: UUID) -> Optional[Evaluation]:
        """Retrieve evaluation by ID."""
        result = await self.session.execute(
            select(EvaluationDB).where(EvaluationDB.id == entity_id)
        )
        db_evaluation = result.scalar_one_or_none()
        return self._to_domain(db_evaluation) if db_evaluation else None

    async def get_by_variant_id(self, variant_id: UUID) -> List[Evaluation]:
        """Retrieve all evaluations for a variant."""
        result = await self.session.execute(
            select(EvaluationDB)
            .where(EvaluationDB.variant_id == variant_id)
            .order_by(desc(EvaluationDB.created_at))
        )
        db_evaluations = result.scalars().all()
        return [self._to_domain(db_e) for db_e in db_evaluations]

    async def get_by_round_id(self, round_id: UUID) -> List[Evaluation]:
        """Retrieve all evaluations for a round."""
        result = await self.session.execute(
            select(EvaluationDB)
            .where(EvaluationDB.round_id == round_id)
            .order_by(desc(EvaluationDB.score))
        )
        db_evaluations = result.scalars().all()
        return [self._to_domain(db_e) for db_e in db_evaluations]

    async def update(self, entity: Evaluation) -> Evaluation:
        """Update an existing evaluation."""
        result = await self.session.execute(
            select(EvaluationDB).where(EvaluationDB.id == entity.id)
        )
        db_evaluation = result.scalar_one_or_none()

        if not db_evaluation:
            raise ValueError(f"Evaluation {entity.id} not found")

        # Update fields
        db_evaluation.score = entity.score if entity.score is not None else db_evaluation.score
        db_evaluation.metrics = entity.result_data
        db_evaluation.evaluator_config = entity.evaluation_config
        db_evaluation.execution_metadata = _build_execution_metadata(entity)
        db_evaluation.meta_data = entity.metadata

        await self.session.flush()
        return self._to_domain(db_evaluation)

    @staticmethod
    def _to_domain(db_evaluation: EvaluationDB) -> Evaluation:
        """Convert database model to domain model."""
        exec_meta = db_evaluation.execution_metadata or {}
        status_value = exec_meta.get("status", "completed")
        try:
            status = EvaluationStatus(status_value)
        except ValueError:
            status = EvaluationStatus.COMPLETED

        evaluator_type = exec_meta.get("evaluator_type", "unknown")
        completed_at = None
        completed_raw = exec_meta.get("completed_at")
        if completed_raw:
            try:
                completed_at = datetime.fromisoformat(completed_raw)
            except ValueError:
                completed_at = None

        score = db_evaluation.score
        if status in (EvaluationStatus.PENDING, EvaluationStatus.RUNNING) and score == 0.0:
            score = None

        return Evaluation(
            id=db_evaluation.id,
            variant_id=db_evaluation.variant_id,
            round_id=db_evaluation.round_id,
            evaluator_type=evaluator_type,
            status=status,
            score=score,
            result_data=db_evaluation.metrics,
            evaluation_config=db_evaluation.evaluator_config,
            metadata=db_evaluation.meta_data or {},
            created_at=db_evaluation.created_at,
            completed_at=completed_at,
        )
