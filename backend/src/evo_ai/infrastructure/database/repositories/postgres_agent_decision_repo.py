"""PostgreSQL implementation of AgentDecision repository."""

from typing import List, Optional
from uuid import UUID

from opentelemetry import trace
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.domain.models.agent_decision import AgentDecision
from evo_ai.infrastructure.database.models import AgentDecisionDB


def _get_span_id() -> str:
    """Return current span ID as 16-char hex string."""
    span = trace.get_current_span()
    span_context = span.get_span_context() if span else None
    if span_context and span_context.span_id:
        return f"{span_context.span_id:016x}"
    return "0000000000000000"


class PostgresAgentDecisionRepository:
    """PostgreSQL implementation of AgentDecisionRepository."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, entity: AgentDecision) -> AgentDecision:
        """Create a new agent decision record."""
        decision_payload = {
            "decision_type": entity.decision_type,
            "confidence_score": entity.confidence_score,
            "metadata": entity.metadata,
        }
        if entity.policy_id:
            decision_payload["policy_id"] = str(entity.policy_id)

        db_decision = AgentDecisionDB(
            id=entity.id,
            trace_id=entity.trace_id,
            span_id=entity.span_id or _get_span_id(),
            agent_type=entity.agent_type,
            campaign_id=entity.campaign_id,
            round_id=entity.round_id,
            variant_id=entity.variant_id,
            decision=decision_payload,
            rationale=entity.reasoning or "No reasoning provided.",
            input_context=entity.input_data,
            output_data=entity.output_data,
            llm_config=entity.llm_config,
            token_usage=entity.token_usage,
            duration_ms=entity.duration_ms,
            created_at=entity.created_at,
        )
        self.session.add(db_decision)
        await self.session.flush()
        return self._to_domain(db_decision)

    async def get_by_id(self, entity_id: UUID) -> Optional[AgentDecision]:
        """Retrieve decision by ID."""
        result = await self.session.execute(
            select(AgentDecisionDB).where(AgentDecisionDB.id == entity_id)
        )
        db_decision = result.scalar_one_or_none()
        return self._to_domain(db_decision) if db_decision else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[AgentDecision]:
        """Retrieve all decisions with pagination."""
        result = await self.session.execute(
            select(AgentDecisionDB)
            .order_by(desc(AgentDecisionDB.created_at))
            .offset(skip)
            .limit(limit)
        )
        db_decisions = result.scalars().all()
        return [self._to_domain(db_d) for db_d in db_decisions]

    async def get_by_trace_id(self, trace_id: UUID) -> List[AgentDecision]:
        """Retrieve all decisions for a given trace ID."""
        result = await self.session.execute(
            select(AgentDecisionDB)
            .where(AgentDecisionDB.trace_id == trace_id)
            .order_by(desc(AgentDecisionDB.created_at))
        )
        db_decisions = result.scalars().all()
        return [self._to_domain(db_d) for db_d in db_decisions]

    async def update(self, entity: AgentDecision) -> AgentDecision:
        """Update an existing decision."""
        result = await self.session.execute(
            select(AgentDecisionDB).where(AgentDecisionDB.id == entity.id)
        )
        db_decision = result.scalar_one_or_none()

        if not db_decision:
            raise ValueError(f"AgentDecision {entity.id} not found")

        db_decision.agent_type = entity.agent_type
        db_decision.decision = {
            "decision_type": entity.decision_type,
            "confidence_score": entity.confidence_score,
            "metadata": entity.metadata,
            "policy_id": str(entity.policy_id) if entity.policy_id else None,
        }
        db_decision.rationale = entity.reasoning or db_decision.rationale
        db_decision.input_context = entity.input_data
        db_decision.output_data = entity.output_data
        db_decision.llm_config = entity.llm_config
        db_decision.token_usage = entity.token_usage
        db_decision.duration_ms = entity.duration_ms

        await self.session.flush()
        return self._to_domain(db_decision)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a decision record."""
        result = await self.session.execute(
            select(AgentDecisionDB).where(AgentDecisionDB.id == entity_id)
        )
        db_decision = result.scalar_one_or_none()
        if not db_decision:
            return False
        await self.session.delete(db_decision)
        return True

    async def count(self) -> int:
        """Count total decisions."""
        result = await self.session.execute(select(AgentDecisionDB))
        return len(result.scalars().all())

    @staticmethod
    def _to_domain(db_decision: AgentDecisionDB) -> AgentDecision:
        """Convert database model to domain model."""
        decision_payload = db_decision.decision or {}
        policy_id = decision_payload.get("policy_id")
        policy_uuid = UUID(policy_id) if policy_id else None

        return AgentDecision(
            id=db_decision.id,
            trace_id=db_decision.trace_id,
            agent_type=db_decision.agent_type,
            decision_type=decision_payload.get("decision_type", "unknown"),
            input_data=db_decision.input_context,
            output_data=db_decision.output_data,
            reasoning=db_decision.rationale,
            confidence_score=decision_payload.get("confidence_score"),
            metadata=decision_payload.get("metadata", {}),
            campaign_id=db_decision.campaign_id,
            round_id=db_decision.round_id,
            variant_id=db_decision.variant_id,
            policy_id=policy_uuid,
            span_id=db_decision.span_id,
            llm_config=db_decision.llm_config,
            token_usage=db_decision.token_usage,
            duration_ms=db_decision.duration_ms,
            created_at=db_decision.created_at,
        )
