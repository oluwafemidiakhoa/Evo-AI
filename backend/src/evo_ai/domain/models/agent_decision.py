"""Agent decision domain model - records an agent's decision metadata."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AgentDecision(BaseModel):
    """
    AgentDecision entity - represents a single agent decision.

    Stored for traceability and auditability across all agent actions.
    """

    id: UUID = Field(default_factory=uuid4)
    trace_id: UUID
    agent_type: str = Field(min_length=1, max_length=50)
    decision_type: str = Field(min_length=1, max_length=100)
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    reasoning: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    campaign_id: Optional[UUID] = None
    round_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    policy_id: Optional[UUID] = None
    span_id: Optional[str] = None
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    token_usage: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
