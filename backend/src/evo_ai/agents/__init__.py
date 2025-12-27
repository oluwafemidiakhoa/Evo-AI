"""Evo-AI Agent Framework.

Base classes and tools for building evolution experiment agents.
All agents log decisions with trace IDs and use MCP servers for external access.
"""

from evo_ai.agents.base import BaseEvoAgent, AgentContext, AgentDecision
from evo_ai.agents.tools import LineageTool, EvaluationTool, DomainQueryTool
from evo_ai.agents.implementations import (
    PlannerAgent,
    VariantAgent,
    ScorerAgent,
    PolicyAgent,
    ReporterAgent,
    AgentOrchestrator,
)

__all__ = [
    "BaseEvoAgent",
    "AgentContext",
    "AgentDecision",
    "LineageTool",
    "EvaluationTool",
    "DomainQueryTool",
    "PlannerAgent",
    "VariantAgent",
    "ScorerAgent",
    "PolicyAgent",
    "ReporterAgent",
    "AgentOrchestrator",
]
