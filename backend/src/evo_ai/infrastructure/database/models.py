"""
SQLModel database models - defines the actual PostgreSQL schema.

CRITICAL: This file implements all domain invariants via database constraints:
1. Every Round belongs to exactly one Campaign (FK + NOT NULL)
2. Every Variant has lineage tracking (parent_id FK, generation)
3. All decisions logged (agent_decisions table)
4. All MCP access logged (mcp_access_logs table)

All tables include:
- id (UUID, primary key)
- created_at, updated_at (timestamps)
- deleted_at (for soft deletes)
"""

import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON, TIMESTAMP, UUID as PG_UUID
from sqlmodel import Field, SQLModel


# Enums
class CampaignStatusEnum(str, Enum):
    """Campaign status enum."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class RoundStatusEnum(str, Enum):
    """Round status enum."""
    PENDING = "pending"
    PLANNING = "planning"
    GENERATING = "generating"
    EVALUATING = "evaluating"
    SELECTING = "selecting"
    REPORTING = "reporting"
    COMPLETED = "completed"
    FAILED = "failed"


class PolicyTypeEnum(str, Enum):
    """Policy type enum."""
    SELECTION = "selection"
    MUTATION = "mutation"
    TERMINATION = "termination"


# Database Models

class CampaignDB(SQLModel, table=True):
    """Campaign table - represents experimental evolution campaigns."""

    __tablename__ = "campaigns"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = None
    status: CampaignStatusEnum = Field(default=CampaignStatusEnum.DRAFT)
    config: dict = Field(sa_column=Column(JSON, nullable=False))
    meta_data: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )

    __table_args__ = (
        Index("idx_campaigns_status", "status", "deleted_at"),
        Index("idx_campaigns_name", "name"),
    )


class RoundDB(SQLModel, table=True):
    """Round table - represents evolution iterations."""

    __tablename__ = "rounds"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    campaign_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    )
    round_number: int = Field(ge=1)
    status: RoundStatusEnum = Field(default=RoundStatusEnum.PENDING)
    plan: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    metrics: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    started_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )

    __table_args__ = (
        UniqueConstraint("campaign_id", "round_number", name="uq_campaign_round_number"),
        Index("idx_rounds_campaign_status", "campaign_id", "status", "deleted_at"),
        Index("idx_rounds_status", "status"),
    )


class VariantDB(SQLModel, table=True):
    """
    Variant table - represents candidate solutions.

    CRITICAL: Implements lineage tracking invariant via parent_id FK and generation.
    """

    __tablename__ = "variants"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    round_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=False, index=True)
    )
    parent_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("variants.id"), nullable=True, index=True)
    )
    generation: int = Field(ge=0)
    content: str = Field(min_length=1)
    content_hash: str = Field(max_length=64)  # SHA-256 hash
    mutation_type: Optional[str] = Field(default=None, max_length=50)
    mutation_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False)
    )
    is_selected: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )

    def __init__(self, **data):  # type: ignore[no-untyped-def]
        """Override __init__ to auto-generate content_hash."""
        if "content" in data and "content_hash" not in data:
            data["content_hash"] = hashlib.sha256(
                data["content"].encode('utf-8')
            ).hexdigest()
        super().__init__(**data)

    __table_args__ = (
        Index("idx_variants_round", "round_id", "deleted_at"),
        Index("idx_variants_parent", "parent_id", "deleted_at"),
        Index("idx_variants_lineage", "generation", "is_selected"),
        Index("idx_variants_content_hash", "content_hash"),
        Index("idx_variants_selected", "round_id", "is_selected"),
    )


class EvaluationDB(SQLModel, table=True):
    """Evaluation table - stores variant scores and metrics."""

    __tablename__ = "evaluations"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    variant_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("variants.id"), nullable=False, index=True)
    )
    round_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=False, index=True)
    )
    score: float = Field()
    metrics: dict = Field(sa_column=Column(JSON, nullable=False))
    evaluator_config: dict = Field(sa_column=Column(JSON, nullable=False))
    execution_metadata: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )

    __table_args__ = (
        Index("idx_evaluations_variant", "variant_id"),
        Index("idx_evaluations_round", "round_id"),
        Index("idx_evaluations_score", "round_id", "score"),
    )


class PolicyDB(SQLModel, table=True):
    """Policy table - stores selection and mutation strategies."""

    __tablename__ = "policies"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    campaign_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=False, index=True)
    )
    name: str = Field(max_length=255)
    policy_type: PolicyTypeEnum = Field()
    version: int = Field(default=1, ge=1)
    config: dict = Field(sa_column=Column(JSON, nullable=False))
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True)
    )

    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "policy_type", "version",
            name="uq_campaign_policy_type_version"
        ),
        Index("idx_policies_campaign_active", "campaign_id", "is_active", "deleted_at"),
        Index("idx_policies_type", "policy_type"),
    )


class AgentDecisionDB(SQLModel, table=True):
    """
    Agent decisions table - logs all AI agent decisions.

    NON-NEGOTIABLE: Every agent decision must be logged with trace_id.
    """

    __tablename__ = "agent_decisions"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    trace_id: UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False, index=True))
    span_id: str = Field(max_length=16)  # OpenTelemetry span ID
    agent_type: str = Field(max_length=50)  # 'planner', 'variant', 'scorer', 'policy', 'reporter'
    campaign_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True)
    )
    round_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=True)
    )
    variant_id: Optional[UUID] = Field(
        default=None,
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("variants.id"), nullable=True)
    )
    decision: dict = Field(sa_column=Column(JSON, nullable=False))
    rationale: str = Field(min_length=1)  # Agent's reasoning (REQUIRED)
    input_context: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    output_data: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    llm_config: dict = Field(sa_column=Column(JSON, nullable=False))
    token_usage: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    duration_ms: Optional[int] = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )

    __table_args__ = (
        Index("idx_agent_decisions_trace", "trace_id"),
        Index("idx_agent_decisions_agent", "agent_type", "created_at"),
        Index("idx_agent_decisions_round", "round_id", "agent_type"),
        Index("idx_agent_decisions_campaign", "campaign_id", "created_at"),
    )


class MCPAccessLogDB(SQLModel, table=True):
    """
    MCP access logs table - logs all MCP server calls.

    NON-NEGOTIABLE: All MCP access must be versioned and logged.
    """

    __tablename__ = "mcp_access_logs"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    trace_id: UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False, index=True))
    mcp_server_name: str = Field(max_length=100)
    mcp_server_version: str = Field(max_length=20)  # Semantic versioning
    tool_name: str = Field(max_length=100)
    input_params: dict = Field(sa_column=Column(JSON, nullable=False))
    output_data: Optional[dict] = Field(default=None, sa_column=Column(JSON, nullable=True))
    status: str = Field(max_length=20)  # 'success' or 'error'
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )

    __table_args__ = (
        Index("idx_mcp_logs_trace", "trace_id"),
        Index("idx_mcp_logs_server", "mcp_server_name", "created_at"),
        Index("idx_mcp_logs_status", "status", "created_at"),
    )


class ReportDB(SQLModel, table=True):
    """Report table - stores generated reports."""

    __tablename__ = "reports"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
    )
    round_id: UUID = Field(
        sa_column=Column(PG_UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=False, index=True)
    )
    report_type: str = Field(max_length=50)  # 'round_summary', 'lineage_analysis', etc.
    format: str = Field(max_length=20)  # 'markdown', 'json', 'html'
    content: Optional[str] = None  # Small reports stored inline
    storage_path: Optional[str] = Field(default=None, max_length=500)  # S3 path for large reports
    meta_data: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )

    __table_args__ = (
        Index("idx_reports_round", "round_id", "report_type"),
        Index("idx_reports_created", "created_at"),
    )
