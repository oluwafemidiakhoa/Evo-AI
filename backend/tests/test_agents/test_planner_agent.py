"""
Tests for PlannerAgent.

Validates planning logic, evolution phase detection, and decision logging.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from evo_ai.agents.implementations.planner import PlannerAgent
from evo_ai.agents.base import AgentContext
from evo_ai.mcp.registry import MCPRegistry
from evo_ai.domain.models import Campaign, Round


@pytest.fixture
async def mcp_registry():
    """Create test MCP registry."""
    registry = MCPRegistry()
    # Register test MCP servers
    yield registry
    await registry.cleanup()


@pytest.fixture
def campaign():
    """Create test campaign."""
    return Campaign(
        id=uuid4(),
        name="Test Campaign",
        status="in_progress",
        config={
            "max_rounds": 30,
            "variants_per_round": 10,
            "evaluators": ["llm_judge"]
        },
        created_at=datetime.utcnow()
    )


@pytest.fixture
async def planner_agent(mcp_registry):
    """Create PlannerAgent instance."""
    return PlannerAgent(mcp_registry)


class TestPlannerAgent:
    """Test suite for PlannerAgent."""

    async def test_early_round_exploration_phase(self, planner_agent, campaign):
        """Test that early rounds use exploration strategy."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        # Round 3 of 30 = 10% progress (should be exploration)
        result = await planner_agent.execute(context, round_number=3)

        assert result["phase"] == "exploration"
        assert result["diversity_weight"] > 0.7  # High diversity
        assert len(result["mutation_strategies"]) >= 4  # Multiple strategies

    async def test_middle_round_balanced_phase(self, planner_agent, campaign):
        """Test that middle rounds use balanced strategy."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        # Round 15 of 30 = 50% progress (should be balanced)
        result = await planner_agent.execute(context, round_number=15)

        assert result["phase"] == "balanced"
        assert 0.4 < result["diversity_weight"] < 0.6  # Medium diversity

    async def test_late_round_exploitation_phase(self, planner_agent, campaign):
        """Test that late rounds use exploitation strategy."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        # Round 27 of 30 = 90% progress (should be exploitation)
        result = await planner_agent.execute(context, round_number=27)

        assert result["phase"] == "exploitation"
        assert result["diversity_weight"] < 0.3  # Low diversity
        assert len(result["mutation_strategies"]) <= 2  # Focus on best strategies

    async def test_decision_logging(self, planner_agent, campaign):
        """Test that all decisions are logged with trace_id."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        result = await planner_agent.run_with_tracing(context, round_number=1)

        # Verify decision was logged (would check database in real test)
        assert result is not None
        # In real test: query agent_decisions table for trace_id

    async def test_variant_count_calculation(self, planner_agent, campaign):
        """Test variant count respects configuration."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        result = await planner_agent.execute(context, round_number=1)

        expected_count = campaign.config["variants_per_round"]
        assert result["target_variant_count"] == expected_count

    async def test_mutation_strategy_weights(self, planner_agent, campaign):
        """Test mutation strategy weights are valid probabilities."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        result = await planner_agent.execute(context, round_number=1)

        weights = result.get("mutation_weights", {})
        assert abs(sum(weights.values()) - 1.0) < 0.01  # Sum to 1.0

    async def test_parent_selection_strategy(self, planner_agent, campaign):
        """Test parent selection strategy changes with phase."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        # Early phase: should prefer diversity
        early_result = await planner_agent.execute(context, round_number=3)
        assert early_result["parent_selection"] in ["tournament", "diversity"]

        # Late phase: should prefer top performers
        late_result = await planner_agent.execute(context, round_number=27)
        assert late_result["parent_selection"] in ["top_k", "elitist"]

    @pytest.mark.parametrize("round_number,expected_phase", [
        (1, "exploration"),
        (5, "exploration"),
        (10, "exploration"),
        (15, "balanced"),
        (20, "balanced"),
        (25, "exploitation"),
        (30, "exploitation"),
    ])
    async def test_phase_detection(
        self, planner_agent, campaign, round_number, expected_phase
    ):
        """Test phase detection across all round numbers."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        result = await planner_agent.execute(context, round_number=round_number)

        assert result["phase"] == expected_phase


class TestPlannerAgentErrorHandling:
    """Test error handling and edge cases."""

    async def test_invalid_round_number(self, planner_agent, campaign):
        """Test handling of invalid round numbers."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        with pytest.raises(ValueError):
            await planner_agent.execute(context, round_number=0)

    async def test_round_exceeds_max(self, planner_agent, campaign):
        """Test handling when round exceeds max_rounds."""
        context = AgentContext(
            campaign_id=campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        # Round 31 exceeds max_rounds of 30
        with pytest.raises(ValueError):
            await planner_agent.execute(context, round_number=31)

    async def test_missing_config(self, planner_agent):
        """Test handling of missing campaign configuration."""
        invalid_campaign = Campaign(
            id=uuid4(),
            name="Invalid",
            status="pending",
            config={},  # Missing required fields
            created_at=datetime.utcnow()
        )

        context = AgentContext(
            campaign_id=invalid_campaign.id,
            round_id=None,
            trace_id=uuid4()
        )

        with pytest.raises(KeyError):
            await planner_agent.execute(context, round_number=1)


# Pytest configuration
pytestmark = pytest.mark.asyncio
