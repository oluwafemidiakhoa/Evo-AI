"""PostgreSQL implementation of Evaluation repository."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.domain.models.evaluation import Evaluation
from evo_ai.infrastructure.database.models import EvaluationDB


class PostgresEvaluationRepository:
    """PostgreSQL implementation of EvaluationRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, entity: Evaluation) -> Evaluation:
        """Create a new evaluation."""
        db_evaluation = EvaluationDB(
            id=entity.id,
            variant_id=entity.variant_id,
            round_id=entity.round_id,
            score=entity.score,
            metrics=entity.metrics,
            evaluator_config=entity.evaluator_config,
            execution_metadata=entity.execution_metadata,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
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
        db_evaluation.score = entity.score
        db_evaluation.metrics = entity.metrics
        db_evaluation.evaluator_config = entity.evaluator_config
        db_evaluation.execution_metadata = entity.execution_metadata
        db_evaluation.updated_at = datetime.utcnow()

        await self.session.flush()
        return self._to_domain(db_evaluation)

    @staticmethod
    def _to_domain(db_evaluation: EvaluationDB) -> Evaluation:
        """Convert database model to domain model."""
        return Evaluation(
            id=db_evaluation.id,
            variant_id=db_evaluation.variant_id,
            round_id=db_evaluation.round_id,
            score=db_evaluation.score,
            metrics=db_evaluation.metrics,
            evaluator_config=db_evaluation.evaluator_config,
            execution_metadata=db_evaluation.execution_metadata,
            created_at=db_evaluation.created_at,
            updated_at=db_evaluation.updated_at,
        )
