"""
Evaluation domain model - represents scoring results for variants.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any
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
    2. Score must be recorded along with detailed metrics
    3. Evaluator configuration must be tracked for reproducibility
    """

    id: UUID = Field(default_factory=uuid4)
    variant_id: UUID
    round_id: UUID
    score: float
    metrics: Dict[str, Any] = Field(default_factory=dict)
    evaluator_config: Dict[str, Any] = Field(default_factory=dict)
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
