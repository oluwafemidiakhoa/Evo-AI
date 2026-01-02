"""Evaluation domain model - represents scoring results for variants."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EvaluationStatus(str, Enum):
    """Status of an evaluation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Evaluation(BaseModel):
    """
    Evaluation entity - represents a scored variant.

    Domain Invariants:
    1. Every evaluation must have a variant_id and round_id
    2. Evaluations track status, score, and result data
    3. Evaluator configuration and metadata are persisted for reproducibility
    """

    id: UUID = Field(default_factory=uuid4)
    variant_id: UUID
    round_id: UUID
    evaluator_type: str = Field(min_length=1, max_length=100)
    status: EvaluationStatus = EvaluationStatus.PENDING
    score: Optional[float] = None
    result_data: Dict[str, Any] = Field(default_factory=dict)
    evaluation_config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
