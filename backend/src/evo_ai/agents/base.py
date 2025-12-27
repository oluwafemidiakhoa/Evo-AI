"""Base agent class for Evo-AI agents.

All agents inherit from BaseEvoAgent which provides:
- Automatic OpenTelemetry tracing
- Decision logging to database with trace_id
- Tool registration and execution
- MCP server access via registry
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from opentelemetry import trace
from swarm import Agent as SwarmAgent

from evo_ai.infrastructure.observability.metrics import agent_calls, agent_duration
from evo_ai.mcp.registry import MCPRegistry

logger = structlog.get_logger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class AgentContext:
    """
    Execution context for an agent run.

    Attributes:
        trace_id: OpenTelemetry trace ID for correlation
        campaign_id: Campaign being processed
        round_id: Current round (optional)
        variant_id: Current variant (optional)
        policy_id: Current policy (optional)
        metadata: Additional context-specific data
    """
    trace_id: UUID
    campaign_id: UUID
    round_id: Optional[UUID] = None
    variant_id: Optional[UUID] = None
    policy_id: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentDecision:
    """
    Represents an agent's decision before persistence.

    Used by BaseEvoAgent to log all decisions to the agent_decisions table.
    """
    agent_type: str
    decision_type: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    reasoning: Optional[str] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseEvoAgent(ABC):
    """
    Abstract base class for all Evo-AI agents.

    Provides:
    - Tool registration and execution
    - Automatic decision logging with trace context
    - OpenTelemetry span creation
    - MCP server access
    - Integration with OpenAI Swarm

    Constitution adherence:
    - All decisions logged with trace_id (non-negotiable)
    - All MCP access via registry (versioned and logged)
    - Correctness > Speed: Decisions validated before logging
    - Traceability > Black-box: Full reasoning captured

    Usage:
        class MyAgent(BaseEvoAgent):
            @property
            def agent_type(self) -> str:
                return "my_agent"

            def get_system_instructions(self) -> str:
                return "You are MyAgent..."

            def get_tools(self) -> List[Callable]:
                return [self.my_custom_tool]

            async def execute(self, context: AgentContext, **kwargs) -> Dict[str, Any]:
                result = await self._call_tool("my_custom_tool", {...})
                await self._log_decision(context, AgentDecision(...))
                return result
    """

    def __init__(self, mcp_registry: MCPRegistry):
        """
        Initialize base agent.

        Args:
            mcp_registry: MCP registry for external system access
        """
        self.mcp_registry = mcp_registry
        self._tools: Dict[str, Callable] = {}
        self._register_tools()

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """
        Return unique agent type identifier.

        Examples: "planner", "variant_generator", "scorer", "policy_maker", "reporter"
        """
        pass

    @abstractmethod
    def get_system_instructions(self) -> str:
        """
        Return system instructions for the agent.

        Used by OpenAI Swarm to set agent behavior.
        """
        pass

    @abstractmethod
    def get_tools(self) -> List[Callable]:
        """
        Return list of tools available to this agent.

        Tools can be:
        - Custom agent-specific functions
        - MCP access tools (via self._create_mcp_tool)
        - Domain tools (via self._create_domain_tool)
        """
        pass

    @abstractmethod
    async def execute(self, context: AgentContext, **kwargs) -> Dict[str, Any]:
        """
        Execute agent's main logic.

        Args:
            context: Execution context with trace_id and entity IDs
            **kwargs: Agent-specific parameters

        Returns:
            Dictionary with execution results

        Raises:
            Exception: If execution fails
        """
        pass

    def _register_tools(self) -> None:
        """Register all tools provided by get_tools()."""
        for tool in self.get_tools():
            self._tools[tool.__name__] = tool

    async def _call_tool(
        self,
        tool_name: str,
        context: AgentContext,
        **kwargs
    ) -> Any:
        """
        Call a registered tool with tracing.

        Args:
            tool_name: Name of the tool to call
            context: Execution context
            **kwargs: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not registered for {self.agent_type}")

        with tracer.start_as_current_span(f"{self.agent_type}.tool.{tool_name}") as span:
            span.set_attribute("agent.type", self.agent_type)
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("trace_id", str(context.trace_id))

            logger.info(
                f"calling_tool",
                agent_type=self.agent_type,
                tool_name=tool_name,
                trace_id=str(context.trace_id)
            )

            try:
                tool = self._tools[tool_name]
                result = await tool(context=context, **kwargs)
                span.set_attribute("tool.status", "success")
                return result
            except Exception as e:
                span.set_attribute("tool.status", "error")
                span.set_attribute("tool.error", str(e))
                logger.error(
                    "tool_execution_failed",
                    agent_type=self.agent_type,
                    tool_name=tool_name,
                    error=str(e),
                    trace_id=str(context.trace_id)
                )
                raise

    async def _log_decision(
        self,
        context: AgentContext,
        decision: AgentDecision,
        repository=None
    ) -> None:
        """
        Log agent decision to database (NON-NEGOTIABLE).

        Args:
            context: Execution context with trace_id
            decision: Decision to log
            repository: Optional AgentDecisionRepository (injected for testing)

        Constitution: All decisions MUST be logged with trace_id for full traceability.
        """
        from evo_ai.infrastructure.database.connection import get_session
        from evo_ai.infrastructure.database.repositories.postgres_agent_decision_repo import (
            PostgresAgentDecisionRepository
        )
        from evo_ai.domain.models.agent_decision import AgentDecision as AgentDecisionModel

        # Create domain model
        decision_model = AgentDecisionModel(
            trace_id=context.trace_id,
            campaign_id=context.campaign_id,
            round_id=context.round_id,
            variant_id=context.variant_id,
            policy_id=context.policy_id,
            agent_type=decision.agent_type,
            decision_type=decision.decision_type,
            input_data=decision.input_data,
            output_data=decision.output_data,
            reasoning=decision.reasoning,
            confidence_score=decision.confidence_score,
            metadata=decision.metadata,
        )

        # Persist to database
        if repository is None:
            async with get_session() as session:
                repository = PostgresAgentDecisionRepository(session)
                saved_decision = await repository.create(decision_model)
        else:
            saved_decision = await repository.create(decision_model)

        logger.info(
            "decision_logged",
            agent_type=decision.agent_type,
            decision_type=decision.decision_type,
            decision_id=str(saved_decision.id),
            trace_id=str(context.trace_id),
            campaign_id=str(context.campaign_id)
        )

    async def run_with_tracing(
        self,
        context: AgentContext,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute agent with full OpenTelemetry tracing.

        Args:
            context: Execution context
            **kwargs: Agent-specific parameters

        Returns:
            Execution results from execute()

        Constitution: All agent executions traced for observability.
        """
        with tracer.start_as_current_span(f"agent.{self.agent_type}.execute") as span:
            span.set_attribute("agent.type", self.agent_type)
            span.set_attribute("trace_id", str(context.trace_id))
            span.set_attribute("campaign_id", str(context.campaign_id))

            if context.round_id:
                span.set_attribute("round_id", str(context.round_id))
            if context.variant_id:
                span.set_attribute("variant_id", str(context.variant_id))

            start_time = time.time()
            status = "success"

            try:
                logger.info(
                    "agent_execution_started",
                    agent_type=self.agent_type,
                    trace_id=str(context.trace_id),
                    campaign_id=str(context.campaign_id)
                )

                result = await self.execute(context, **kwargs)

                logger.info(
                    "agent_execution_completed",
                    agent_type=self.agent_type,
                    trace_id=str(context.trace_id),
                    duration_seconds=time.time() - start_time
                )

                agent_calls.labels(agent_type=self.agent_type, status="success").inc()
                return result

            except Exception as e:
                status = "error"
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))

                logger.error(
                    "agent_execution_failed",
                    agent_type=self.agent_type,
                    error=str(e),
                    trace_id=str(context.trace_id)
                )

                agent_calls.labels(agent_type=self.agent_type, status="error").inc()
                raise

            finally:
                duration_seconds = time.time() - start_time
                agent_duration.labels(agent_type=self.agent_type).observe(duration_seconds)

    def to_swarm_agent(self) -> SwarmAgent:
        """
        Convert to OpenAI Swarm Agent for orchestration.

        Returns:
            SwarmAgent instance configured with this agent's instructions and tools
        """
        return SwarmAgent(
            name=self.agent_type,
            instructions=self.get_system_instructions(),
            functions=list(self._tools.values())
        )

    def _create_mcp_tool(
        self,
        server_name: str,
        tool_name: str,
        description: str,
        version: Optional[str] = None
    ) -> Callable:
        """
        Create a tool that calls an MCP server.

        Args:
            server_name: MCP server name (e.g., "github", "filesystem")
            tool_name: Tool name on the server (e.g., "read_file")
            description: Tool description for agent
            version: Optional server version (defaults to latest)

        Returns:
            Async callable that wraps MCP server call

        Example:
            read_github_file = self._create_mcp_tool(
                server_name="github",
                tool_name="read_file",
                description="Read a file from a GitHub repository"
            )
        """
        async def mcp_tool_wrapper(context: AgentContext, **params) -> Any:
            """Tool wrapper that calls MCP server."""
            return await self.mcp_registry.call_tool(
                server_name=server_name,
                tool_name=tool_name,
                params=params,
                version=version,
                trace_id=context.trace_id
            )

        # Set function metadata for Swarm
        mcp_tool_wrapper.__name__ = f"{server_name}_{tool_name}"
        mcp_tool_wrapper.__doc__ = description

        return mcp_tool_wrapper

    def _create_domain_tool(
        self,
        name: str,
        description: str,
        func: Callable
    ) -> Callable:
        """
        Create a domain-specific tool.

        Args:
            name: Tool name
            description: Tool description
            func: Async function that implements the tool

        Returns:
            Async callable with proper metadata
        """
        async def domain_tool_wrapper(context: AgentContext, **kwargs) -> Any:
            """Domain tool wrapper."""
            return await func(context=context, **kwargs)

        domain_tool_wrapper.__name__ = name
        domain_tool_wrapper.__doc__ = description

        return domain_tool_wrapper
