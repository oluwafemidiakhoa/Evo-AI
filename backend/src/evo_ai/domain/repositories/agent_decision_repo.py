"""Agent decision repository interface."""

from abc import abstractmethod
from typing import List
from uuid import UUID

from evo_ai.domain.models.agent_decision import AgentDecision
from evo_ai.domain.repositories.base import BaseRepository


class AgentDecisionRepository(BaseRepository[AgentDecision]):
    """Repository interface for AgentDecision entities."""

    @abstractmethod
    async def get_by_trace_id(self, trace_id: UUID) -> List[AgentDecision]:
        """
        Retrieve all decisions for a trace.

        Args:
            trace_id: Trace UUID

        Returns:
            List of decisions for the trace
        """
        pass
