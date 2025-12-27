"""Tests for BaseEvoAgent."""

import pytest
from uuid import uuid4, UUID
from typing import Any, Callable, Dict, List

from evo_ai.agents.base import (
    BaseEvoAgent,
    AgentContext,
    AgentDecision,
)
from evo_ai.mcp.registry import MCPRegistry


class MockAgent(BaseEvoAgent):
    """Mock agent for testing."""

    @property
    def agent_type(self) -> str:
        return "mock_agent"

    def get_system_instructions(self) -> str:
        return "You are a mock agent for testing."

    def get_tools(self) -> List[Callable]:
        return [self.mock_tool]

    async def execute(self, context: AgentContext, **kwargs) -> Dict[str, Any]:
        """Execute mock agent logic."""
        result = await self._call_tool("mock_tool", context, value=kwargs.get("value", 42))

        # Log a decision
        decision = AgentDecision(
            agent_type=self.agent_type,
            decision_type="test_decision",
            input_data=kwargs,
            output_data=result,
            reasoning="This is a test decision",
            confidence_score=0.95,
        )
        await self._log_decision(context, decision, repository=kwargs.get("decision_repo"))

        return result

    async def mock_tool(self, context: AgentContext, value: int = 0) -> Dict[str, Any]:
        """Mock tool for testing."""
        return {
            "value": value,
            "doubled": value * 2,
            "trace_id": str(context.trace_id)
        }


@pytest.fixture
def mcp_registry():
    """Create MCP registry."""
    return MCPRegistry()


@pytest.fixture
def agent(mcp_registry):
    """Create mock agent."""
    return MockAgent(mcp_registry)


@pytest.fixture
def context():
    """Create agent context."""
    return AgentContext(
        trace_id=uuid4(),
        campaign_id=uuid4(),
        round_id=uuid4(),
        variant_id=uuid4(),
    )


def test_agent_type(agent):
    """Test agent type property."""
    assert agent.agent_type == "mock_agent"


def test_system_instructions(agent):
    """Test system instructions."""
    instructions = agent.get_system_instructions()
    assert "mock agent" in instructions.lower()


def test_tool_registration(agent):
    """Test tools are registered correctly."""
    assert "mock_tool" in agent._tools
    assert callable(agent._tools["mock_tool"])


@pytest.mark.asyncio
async def test_call_tool(agent, context):
    """Test calling a registered tool."""
    result = await agent._call_tool("mock_tool", context, value=10)

    assert result["value"] == 10
    assert result["doubled"] == 20
    assert result["trace_id"] == str(context.trace_id)


@pytest.mark.asyncio
async def test_call_nonexistent_tool(agent, context):
    """Test calling a non-existent tool raises error."""
    with pytest.raises(ValueError, match="Tool 'nonexistent' not registered"):
        await agent._call_tool("nonexistent", context)


@pytest.mark.asyncio
async def test_execute(agent, context):
    """Test agent execution."""
    result = await agent.execute(context, value=100)

    assert result["value"] == 100
    assert result["doubled"] == 200


@pytest.mark.asyncio
async def test_run_with_tracing(agent, context):
    """Test agent execution with tracing."""
    result = await agent.run_with_tracing(context, value=50)

    assert result["value"] == 50
    assert result["doubled"] == 100


def test_to_swarm_agent(agent):
    """Test conversion to Swarm agent."""
    swarm_agent = agent.to_swarm_agent()

    assert swarm_agent.name == "mock_agent"
    assert "mock agent" in swarm_agent.instructions.lower()
    assert len(swarm_agent.functions) > 0


def test_create_mcp_tool(agent):
    """Test MCP tool creation."""
    mcp_tool = agent._create_mcp_tool(
        server_name="github",
        tool_name="read_file",
        description="Read a file from GitHub"
    )

    assert callable(mcp_tool)
    assert mcp_tool.__name__ == "github_read_file"
    assert "GitHub" in mcp_tool.__doc__


def test_create_domain_tool(agent):
    """Test domain tool creation."""
    async def my_func(context: AgentContext, x: int) -> int:
        return x * 2

    domain_tool = agent._create_domain_tool(
        name="my_domain_tool",
        description="My test tool",
        func=my_func
    )

    assert callable(domain_tool)
    assert domain_tool.__name__ == "my_domain_tool"
    assert domain_tool.__doc__ == "My test tool"


def test_agent_context_creation():
    """Test AgentContext creation."""
    trace_id = uuid4()
    campaign_id = uuid4()

    context = AgentContext(
        trace_id=trace_id,
        campaign_id=campaign_id,
        metadata={"key": "value"}
    )

    assert context.trace_id == trace_id
    assert context.campaign_id == campaign_id
    assert context.round_id is None
    assert context.metadata["key"] == "value"


def test_agent_decision_creation():
    """Test AgentDecision creation."""
    decision = AgentDecision(
        agent_type="test_agent",
        decision_type="test_decision",
        input_data={"input": "data"},
        output_data={"output": "data"},
        reasoning="Test reasoning",
        confidence_score=0.9,
        metadata={"meta": "data"}
    )

    assert decision.agent_type == "test_agent"
    assert decision.decision_type == "test_decision"
    assert decision.confidence_score == 0.9
    assert decision.metadata["meta"] == "data"


@pytest.mark.asyncio
async def test_decision_logging_creates_record(agent, context):
    """Test that decision logging creates a database record."""
    from unittest.mock import AsyncMock, MagicMock
    from evo_ai.domain.models.agent_decision import AgentDecision as AgentDecisionModel

    # Create mock repository
    mock_repo = AsyncMock()
    mock_saved_decision = AgentDecisionModel(
        trace_id=context.trace_id,
        campaign_id=context.campaign_id,
        round_id=context.round_id,
        agent_type="mock_agent",
        decision_type="test_decision",
        input_data={"test": "input"},
        output_data={"test": "output"},
    )
    mock_saved_decision.id = uuid4()
    mock_repo.create.return_value = mock_saved_decision

    # Create decision
    decision = AgentDecision(
        agent_type="mock_agent",
        decision_type="test_decision",
        input_data={"test": "input"},
        output_data={"test": "output"},
        reasoning="Test reasoning",
    )

    # Log decision with mock repository
    await agent._log_decision(context, decision, repository=mock_repo)

    # Verify repository.create was called
    mock_repo.create.assert_called_once()
    call_args = mock_repo.create.call_args[0][0]

    assert call_args.trace_id == context.trace_id
    assert call_args.campaign_id == context.campaign_id
    assert call_args.agent_type == "mock_agent"
    assert call_args.decision_type == "test_decision"


@pytest.mark.asyncio
async def test_run_with_tracing_handles_errors(agent, context):
    """Test that run_with_tracing properly handles errors."""
    class FailingAgent(BaseEvoAgent):
        @property
        def agent_type(self) -> str:
            return "failing_agent"

        def get_system_instructions(self) -> str:
            return "I fail"

        def get_tools(self) -> List[Callable]:
            return []

        async def execute(self, context: AgentContext, **kwargs) -> Dict[str, Any]:
            raise ValueError("Intentional failure")

    failing_agent = FailingAgent(agent.mcp_registry)

    with pytest.raises(ValueError, match="Intentional failure"):
        await failing_agent.run_with_tracing(context)
