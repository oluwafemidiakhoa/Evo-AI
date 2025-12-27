"""Tests for concrete agent implementations."""

import pytest
from uuid import uuid4

from evo_ai.agents import (
    AgentContext,
    PlannerAgent,
    VariantAgent,
    ScorerAgent,
    PolicyAgent,
    ReporterAgent,
)
from evo_ai.domain.models.report import ReportType
from evo_ai.mcp.registry import MCPRegistry


@pytest.fixture
def mcp_registry():
    """Create MCP registry."""
    return MCPRegistry()


@pytest.fixture
def context():
    """Create agent context."""
    return AgentContext(
        trace_id=uuid4(),
        campaign_id=uuid4(),
        round_id=uuid4(),
    )


# PlannerAgent Tests


def test_planner_agent_type(mcp_registry):
    """Test PlannerAgent type."""
    agent = PlannerAgent(mcp_registry)
    assert agent.agent_type == "planner"


def test_planner_system_instructions(mcp_registry):
    """Test PlannerAgent system instructions."""
    agent = PlannerAgent(mcp_registry)
    instructions = agent.get_system_instructions()
    assert "PlannerAgent" in instructions
    assert "experiment rounds" in instructions.lower()


def test_planner_tools(mcp_registry):
    """Test PlannerAgent tools."""
    agent = PlannerAgent(mcp_registry)
    tools = agent.get_tools()
    assert len(tools) > 0
    # Tools should include campaign queries
    tool_names = [t.__name__ for t in tools]
    assert "get_campaign" in tool_names


# VariantAgent Tests


def test_variant_agent_type(mcp_registry):
    """Test VariantAgent type."""
    agent = VariantAgent(mcp_registry)
    assert agent.agent_type == "variant_generator"


def test_variant_system_instructions(mcp_registry):
    """Test VariantAgent system instructions."""
    agent = VariantAgent(mcp_registry)
    instructions = agent.get_system_instructions()
    assert "VariantAgent" in instructions
    assert "mutation" in instructions.lower()
    assert "lineage" in instructions.lower()


def test_variant_tools(mcp_registry):
    """Test VariantAgent tools."""
    agent = VariantAgent(mcp_registry)
    tools = agent.get_tools()
    assert len(tools) > 0
    tool_names = [t.__name__ for t in tools]
    assert "get_variant" in tool_names
    assert "get_lineage" in tool_names


@pytest.mark.asyncio
async def test_variant_mutation_types(mcp_registry):
    """Test that VariantAgent supports all mutation types."""
    agent = VariantAgent(mcp_registry)

    mutation_types = ["refactor", "optimize", "expand", "simplify", "experimental"]

    for mutation_type in mutation_types:
        # Test each mutation method exists
        method_name = f"_apply_{mutation_type}"
        assert hasattr(agent, method_name)
        method = getattr(agent, method_name)

        # Test method signature
        result = await method("test content", {"generations": 1}, {})
        assert isinstance(result, tuple)
        assert len(result) == 2  # (new_content, reasoning)
        assert isinstance(result[0], str)  # new_content
        assert isinstance(result[1], str)  # reasoning


# ScorerAgent Tests


def test_scorer_agent_type(mcp_registry):
    """Test ScorerAgent type."""
    agent = ScorerAgent(mcp_registry)
    assert agent.agent_type == "scorer"


def test_scorer_system_instructions(mcp_registry):
    """Test ScorerAgent system instructions."""
    agent = ScorerAgent(mcp_registry)
    instructions = agent.get_system_instructions()
    assert "ScorerAgent" in instructions
    assert "evaluate" in instructions.lower()


def test_scorer_tools(mcp_registry):
    """Test ScorerAgent tools."""
    agent = ScorerAgent(mcp_registry)
    tools = agent.get_tools()
    assert len(tools) > 0
    tool_names = [t.__name__ for t in tools]
    assert "get_variant" in tool_names
    assert "create_evaluation" in tool_names


@pytest.mark.asyncio
async def test_scorer_evaluation_methods(mcp_registry):
    """Test ScorerAgent evaluation methods."""
    agent = ScorerAgent(mcp_registry)

    variant = {"content": "test", "generation": 1}
    lineage = {"generations": 1}
    config = {}

    # Test LLM evaluation
    score, feedback, criteria = await agent._evaluate_with_llm(variant, lineage, config)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert isinstance(feedback, str)
    assert isinstance(criteria, dict)
    assert "correctness" in criteria

    # Test unit test evaluation
    score, feedback, criteria = await agent._evaluate_with_tests(variant, lineage, config)
    assert isinstance(score, float)
    assert isinstance(feedback, str)
    assert "tests_passed" in criteria

    # Test benchmark evaluation
    score, feedback, criteria = await agent._evaluate_with_benchmark(variant, lineage, config)
    assert isinstance(score, float)
    assert isinstance(feedback, str)
    assert "throughput" in criteria


# PolicyAgent Tests


def test_policy_agent_type(mcp_registry):
    """Test PolicyAgent type."""
    agent = PolicyAgent(mcp_registry)
    assert agent.agent_type == "policy_maker"


def test_policy_system_instructions(mcp_registry):
    """Test PolicyAgent system instructions."""
    agent = PolicyAgent(mcp_registry)
    instructions = agent.get_system_instructions()
    assert "PolicyAgent" in instructions
    assert "selection" in instructions.lower()


def test_policy_tools(mcp_registry):
    """Test PolicyAgent tools."""
    agent = PolicyAgent(mcp_registry)
    tools = agent.get_tools()
    assert len(tools) > 0
    tool_names = [t.__name__ for t in tools]
    assert "get_round_variants" in tool_names


def test_policy_creation_methods(mcp_registry):
    """Test PolicyAgent policy creation methods."""
    agent = PolicyAgent(mcp_registry)

    # Test top-K policy
    rules, params = agent._create_top_k_policy(k=5)
    assert rules["strategy"] == "top_k"
    assert params["k"] == 5

    # Test tournament policy
    rules, params = agent._create_tournament_policy(winners=3, tournament_size=2)
    assert rules["strategy"] == "tournament"
    assert params["winners"] == 3
    assert params["tournament_size"] == 2

    # Test diversity policy
    rules, params = agent._create_diversity_policy(count=10)
    assert rules["strategy"] == "diversity"
    assert params["count"] == 10


# ReporterAgent Tests


def test_reporter_agent_type(mcp_registry):
    """Test ReporterAgent type."""
    agent = ReporterAgent(mcp_registry)
    assert agent.agent_type == "reporter"


def test_reporter_system_instructions(mcp_registry):
    """Test ReporterAgent system instructions."""
    agent = ReporterAgent(mcp_registry)
    instructions = agent.get_system_instructions()
    assert "ReporterAgent" in instructions
    assert "report" in instructions.lower()


def test_reporter_tools(mcp_registry):
    """Test ReporterAgent tools."""
    agent = ReporterAgent(mcp_registry)
    tools = agent.get_tools()
    assert len(tools) > 0
    tool_names = [t.__name__ for t in tools]
    assert "get_campaign" in tool_names
    assert "get_campaign_rounds" in tool_names


# Integration Tests


@pytest.mark.asyncio
async def test_agent_swarm_conversion(mcp_registry):
    """Test that all agents can be converted to Swarm agents."""
    agents = [
        PlannerAgent(mcp_registry),
        VariantAgent(mcp_registry),
        ScorerAgent(mcp_registry),
        PolicyAgent(mcp_registry),
        ReporterAgent(mcp_registry),
    ]

    for agent in agents:
        swarm_agent = agent.to_swarm_agent()
        assert swarm_agent.name == agent.agent_type
        assert swarm_agent.instructions == agent.get_system_instructions()
        assert len(swarm_agent.functions) > 0


def test_all_agents_have_unique_types(mcp_registry):
    """Test that all agents have unique type identifiers."""
    agents = [
        PlannerAgent(mcp_registry),
        VariantAgent(mcp_registry),
        ScorerAgent(mcp_registry),
        PolicyAgent(mcp_registry),
        ReporterAgent(mcp_registry),
    ]

    agent_types = [agent.agent_type for agent in agents]
    assert len(agent_types) == len(set(agent_types))  # All unique


def test_all_agents_inherit_from_base(mcp_registry):
    """Test that all agents inherit from BaseEvoAgent."""
    from evo_ai.agents.base import BaseEvoAgent

    agents = [
        PlannerAgent(mcp_registry),
        VariantAgent(mcp_registry),
        ScorerAgent(mcp_registry),
        PolicyAgent(mcp_registry),
        ReporterAgent(mcp_registry),
    ]

    for agent in agents:
        assert isinstance(agent, BaseEvoAgent)
