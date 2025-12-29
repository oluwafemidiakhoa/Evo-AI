"""API request/response schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Campaign Schemas


class CampaignCreate(BaseModel):
    """Request schema for creating a campaign."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    """Request schema for updating a campaign."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class CampaignResponse(BaseModel):
    """Response schema for campaign."""
    id: UUID
    name: str
    description: Optional[str]
    status: str
    config: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CampaignList(BaseModel):
    """Response schema for campaign list."""
    campaigns: List[CampaignResponse]
    total: int
    page: int
    page_size: int


# Round Schemas


class RoundCreate(BaseModel):
    """Request schema for creating a round."""
    campaign_id: UUID
    round_number: int = Field(..., ge=1)


class RoundResponse(BaseModel):
    """Response schema for round."""
    id: UUID
    campaign_id: UUID
    round_number: int
    status: str
    config: Dict[str, Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class RoundExecutionRequest(BaseModel):
    """Request schema for executing a round."""
    round_number: int = Field(..., ge=1)


class RoundExecutionResponse(BaseModel):
    """Response schema for round execution."""
    round_id: UUID
    round_number: int
    status: str
    variants_generated: int
    variants_evaluated: int
    variants_selected: int
    average_score: Optional[float]
    report_id: UUID
    trace_id: UUID


# Variant Schemas


class VariantResponse(BaseModel):
    """Response schema for variant."""
    id: UUID
    round_id: UUID
    parent_id: Optional[UUID]
    generation: int
    content: str
    content_hash: str
    mutation_type: Optional[str]
    is_selected: bool
    created_at: datetime

    class Config:
        from_attributes = True


class VariantList(BaseModel):
    """Response schema for variant list."""
    variants: List[VariantResponse]
    total: int


class LineageResponse(BaseModel):
    """Response schema for variant lineage."""
    variant_id: UUID
    lineage: List[Dict[str, Any]]
    generations: int
    founder: Optional[Dict[str, Any]]


# Evaluation Schemas


class EvaluationResponse(BaseModel):
    """Response schema for evaluation."""
    id: UUID
    variant_id: UUID
    evaluator_type: str
    score: Optional[float]
    status: str
    result_data: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class EvaluationList(BaseModel):
    """Response schema for evaluation list."""
    evaluations: List[EvaluationResponse]
    total: int


# Policy Schemas


class PolicyResponse(BaseModel):
    """Response schema for policy."""
    id: UUID
    campaign_id: UUID
    round_number: int
    policy_type: str
    rules: Dict[str, Any]
    parameters: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Report Schemas


class ReportResponse(BaseModel):
    """Response schema for report."""
    id: UUID
    campaign_id: UUID
    round_id: Optional[UUID]
    report_type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportList(BaseModel):
    """Response schema for report list."""
    reports: List[ReportResponse]
    total: int


# Statistics Schemas


class CampaignStats(BaseModel):
    """Response schema for campaign statistics."""
    campaign_id: UUID
    total_rounds: int
    completed_rounds: int
    total_variants: int
    total_selected: int
    max_generation: int
    selection_rate: float


class RoundStats(BaseModel):
    """Response schema for round statistics."""
    round_id: UUID
    round_number: int
    total_variants: int
    selected_variants: int
    average_score: Optional[float]
    min_score: Optional[float]
    max_score: Optional[float]


# SSE Event Schemas


class SSEEvent(BaseModel):
    """Server-Sent Event schema."""
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None


# Error Schemas


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    trace_id: Optional[str] = None


# Health Check Schema


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]
