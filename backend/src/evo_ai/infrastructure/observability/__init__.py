"""Observability infrastructure - tracing, logging, metrics."""

from evo_ai.infrastructure.observability.logging import setup_logging
from evo_ai.infrastructure.observability.metrics import (
    agent_calls,
    agent_duration,
    agent_tokens,
    campaigns_active,
    campaigns_created,
    evaluation_score,
    mcp_calls,
    mcp_duration,
    round_duration,
    rounds_executed,
    variants_evaluated,
    variants_generated,
)
from evo_ai.infrastructure.observability.tracing import setup_tracing

__all__ = [
    "setup_tracing",
    "setup_logging",
    # Metrics
    "campaigns_created",
    "campaigns_active",
    "rounds_executed",
    "round_duration",
    "agent_calls",
    "agent_duration",
    "agent_tokens",
    "variants_generated",
    "variants_evaluated",
    "evaluation_score",
    "mcp_calls",
    "mcp_duration",
]
