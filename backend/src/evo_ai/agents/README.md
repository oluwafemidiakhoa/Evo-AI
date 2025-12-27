# Agent Framework

Production-grade agent framework for Evo-AI with full observability and traceability.

## Overview

The agent framework provides a base class (`BaseEvoAgent`) that all agents inherit from, ensuring:

- **Automatic OpenTelemetry tracing** - Every agent execution creates spans
- **Decision logging with trace_id** - All decisions stored in `agent_decisions` table (NON-NEGOTIABLE)
- **MCP server access** - Versioned, logged access to external systems
- **Tool registration** - Consistent tool management pattern
- **OpenAI Swarm integration** - Multi-agent orchestration support

## Constitution Adherence

1. **Correctness > Speed** - Decisions validated before logging
2. **Reproducibility > Cleverness** - All inputs/outputs/reasoning captured
3. **Traceability > Black-box** - Full trace context in logs and database

## Architecture

```
BaseEvoAgent (abstract)
├── Tool Registration
├── Decision Logging (to database with trace_id)
├── OpenTelemetry Integration
├── MCP Registry Access
└── Swarm Conversion

Concrete Agents:
├── PlannerAgent (plans experiment rounds)
├── VariantAgent (generates new variants)
├── ScorerAgent (evaluates variants)
├── PolicyAgent (adapts selection policies)
└── ReporterAgent (generates reports)
```

## Core Components

### AgentContext

Execution context passed to all agent operations:

```python
from evo_ai.agents import AgentContext

context = AgentContext(
    trace_id=uuid4(),          # OpenTelemetry trace ID
    campaign_id=uuid4(),       # Campaign being processed
    round_id=uuid4(),          # Current round (optional)
    variant_id=uuid4(),        # Current variant (optional)
    metadata={"key": "value"}  # Additional context
)
```

### AgentDecision

Represents a decision before persistence:

```python
from evo_ai.agents import AgentDecision

decision = AgentDecision(
    agent_type="planner",
    decision_type="round_plan",
    input_data={"campaign_id": str(campaign_id)},
    output_data={"num_variants": 10, "mutation_types": ["refactor"]},
    reasoning="Planning 10 variants based on campaign config",
    confidence_score=0.95,
    metadata={"planner_version": "1.0"}
)
```

### BaseEvoAgent

Abstract base class for all agents:

```python
from evo_ai.agents import BaseEvoAgent

class MyAgent(BaseEvoAgent):
    @property
    def agent_type(self) -> str:
        return "my_agent"

    def get_system_instructions(self) -> str:
        return "You are MyAgent, responsible for..."

    def get_tools(self) -> List[Callable]:
        return [
            self.custom_tool,
            self._create_mcp_tool(
                server_name="github",
                tool_name="read_file",
                description="Read file from GitHub"
            )
        ]

    async def execute(self, context: AgentContext, **kwargs) -> Dict[str, Any]:
        # Your agent logic here
        result = await self._call_tool("custom_tool", context, param=value)

        # Log decision (NON-NEGOTIABLE)
        await self._log_decision(context, AgentDecision(...))

        return result

    async def custom_tool(self, context: AgentContext, param: str) -> Dict[str, Any]:
        # Tool implementation
        return {"result": param}
```

## Built-in Tools

### LineageTool

Query variant lineage and evolutionary history:

```python
from evo_ai.agents.tools import LineageTool

# Get full ancestry
lineage = await LineageTool.get_full_lineage(context, variant_id)
# Returns: {lineage: [...], generations: 5, founder: {...}}

# Get descendants
descendants = await LineageTool.get_descendants(context, variant_id)

# Get statistics
stats = await LineageTool.get_lineage_statistics(context, variant_id)
# Returns: {total_ancestors: 5, mutation_types: {...}, selection_rate: 0.6}

# Compare variants
comparison = await LineageTool.compare_variants(context, variant_id_1, variant_id_2)
# Returns: {relationship: "sibling", common_parent: {...}}
```

### EvaluationTool

Execute and query evaluations:

```python
from evo_ai.agents.tools import EvaluationTool

# Create evaluation
eval_result = await EvaluationTool.create_evaluation(
    context,
    variant_id=variant_id,
    evaluator_type="llm_judge",
    evaluation_config={"model": "gpt-4", "criteria": ["correctness"]}
)

# Update with results
await EvaluationTool.update_evaluation_result(
    context,
    evaluation_id=eval_id,
    score=0.85,
    result_data={"details": "..."}
)

# Get variant evaluations
evals = await EvaluationTool.get_variant_evaluations(context, variant_id)

# Compare scores
comparison = await EvaluationTool.compare_variant_scores(
    context,
    variant_ids=[id1, id2, id3],
    evaluator_type="llm_judge"
)
```

### DomainQueryTool

Query domain entities:

```python
from evo_ai.agents.tools import DomainQueryTool

# Get campaign
campaign = await DomainQueryTool.get_campaign(context)

# Get round variants
variants = await DomainQueryTool.get_round_variants(
    context,
    selected_only=True
)

# Get active policies
policies = await DomainQueryTool.get_active_policies(context, round_number=5)

# Get statistics
stats = await DomainQueryTool.get_campaign_statistics(context)
# Returns: {total_rounds: 10, total_variants: 100, max_generation: 15}
```

## MCP Tool Creation

Access external systems via MCP servers:

```python
class MyAgent(BaseEvoAgent):
    def get_tools(self) -> List[Callable]:
        return [
            # GitHub access
            self._create_mcp_tool(
                server_name="github",
                tool_name="read_file",
                description="Read file from GitHub repo"
            ),

            # Filesystem access (sandboxed)
            self._create_mcp_tool(
                server_name="filesystem",
                tool_name="read_file",
                description="Read local file (sandboxed)"
            ),

            # Web scraping
            self._create_mcp_tool(
                server_name="web",
                tool_name="scrape_page",
                description="Scrape web page content"
            ),

            # Database queries
            self._create_mcp_tool(
                server_name="database",
                tool_name="query",
                description="Execute read-only SQL query"
            ),
        ]
```

## Agent Execution

### Direct Execution

```python
agent = MyAgent(mcp_registry)
result = await agent.execute(context, param1="value1")
```

### With Tracing

```python
# Automatic OpenTelemetry tracing
result = await agent.run_with_tracing(context, param1="value1")
```

### Swarm Integration

```python
from swarm import Swarm

swarm = Swarm()

# Convert agents to Swarm format
planner_swarm = planner_agent.to_swarm_agent()
variant_swarm = variant_agent.to_swarm_agent()

# Run with Swarm
response = swarm.run(
    agent=planner_swarm,
    messages=[{"role": "user", "content": "Plan next round"}]
)
```

## Observability

### Decision Logging

Every agent decision is automatically logged to the `agent_decisions` table:

```sql
SELECT
    trace_id,
    agent_type,
    decision_type,
    reasoning,
    confidence_score,
    created_at
FROM agent_decisions
WHERE campaign_id = '...'
ORDER BY created_at DESC;
```

### Tracing

OpenTelemetry spans created for:
- Agent execution (`agent.{agent_type}.execute`)
- Tool calls (`{agent_type}.tool.{tool_name}`)
- MCP access (in MCP registry)

View in Jaeger: http://localhost:16686

### Metrics

Prometheus metrics tracked:
- `evo_ai_agent_calls_total{agent_type, status}` - Total agent calls
- `evo_ai_agent_duration_seconds{agent_type}` - Agent execution duration

View in Grafana: http://localhost:3001

### Structured Logging

All logs include trace context:

```json
{
  "event": "agent_execution_started",
  "agent_type": "planner",
  "trace_id": "abc123...",
  "campaign_id": "def456...",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## Testing

### Unit Tests

```python
import pytest
from evo_ai.agents import BaseEvoAgent, AgentContext

@pytest.mark.asyncio
async def test_my_agent():
    agent = MyAgent(mcp_registry)
    context = AgentContext(trace_id=uuid4(), campaign_id=uuid4())

    result = await agent.execute(context, param="test")

    assert result["status"] == "success"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_agent_with_database(db_session):
    """Test agent with real database."""
    agent = MyAgent(mcp_registry)
    context = AgentContext(trace_id=uuid4(), campaign_id=campaign.id)

    result = await agent.run_with_tracing(context)

    # Verify decision logged
    decisions = await decision_repo.get_by_trace_id(context.trace_id)
    assert len(decisions) > 0
```

## Best Practices

1. **Always log decisions** - Use `_log_decision()` for every meaningful decision
2. **Use context correctly** - Pass `AgentContext` to all tool calls
3. **Provide reasoning** - Include human-readable reasoning in decisions
4. **Set confidence scores** - Help downstream analysis understand decision quality
5. **Use MCP for external access** - Never bypass MCP registry (ensures versioning/logging)
6. **Test with real traces** - Verify OpenTelemetry integration in tests
7. **Document tools** - Clear docstrings for agent instructions

## Example: Complete Agent

```python
from typing import Any, Callable, Dict, List
from evo_ai.agents import BaseEvoAgent, AgentContext, AgentDecision
from evo_ai.agents.tools import LineageTool, EvaluationTool

class ScorerAgent(BaseEvoAgent):
    """Agent that evaluates variant quality."""

    @property
    def agent_type(self) -> str:
        return "scorer"

    def get_system_instructions(self) -> str:
        return """You are the ScorerAgent. Your job is to:
        1. Evaluate variant quality using configured evaluators
        2. Log evaluation results with reasoning
        3. Provide confidence scores
        """

    def get_tools(self) -> List[Callable]:
        return [
            # Domain tools
            self._create_domain_tool(
                name="get_variant_lineage",
                description="Get variant's full ancestry",
                func=LineageTool.get_full_lineage
            ),
            # MCP tools
            self._create_mcp_tool(
                server_name="github",
                tool_name="read_file",
                description="Read variant source code from GitHub"
            ),
        ]

    async def execute(
        self,
        context: AgentContext,
        variant_id: UUID,
        evaluator_type: str = "llm_judge"
    ) -> Dict[str, Any]:
        """Evaluate a variant."""

        # Get lineage for context
        lineage = await LineageTool.get_full_lineage(context, variant_id)

        # Create evaluation
        eval_result = await EvaluationTool.create_evaluation(
            context,
            variant_id=variant_id,
            evaluator_type=evaluator_type,
            evaluation_config={"model": "gpt-4"}
        )

        # TODO: Actually run evaluation (would use MCP tools to access variant)
        score = 0.85  # Placeholder

        # Update evaluation
        await EvaluationTool.update_evaluation_result(
            context,
            evaluation_id=UUID(eval_result["evaluation_id"]),
            score=score,
            result_data={"lineage_depth": lineage["generations"]}
        )

        # Log decision (NON-NEGOTIABLE)
        decision = AgentDecision(
            agent_type=self.agent_type,
            decision_type="variant_scored",
            input_data={
                "variant_id": str(variant_id),
                "evaluator_type": evaluator_type
            },
            output_data={
                "score": score,
                "evaluation_id": eval_result["evaluation_id"]
            },
            reasoning=f"Scored variant using {evaluator_type}. "
                     f"Lineage depth: {lineage['generations']} generations.",
            confidence_score=0.9,
            metadata={"evaluator_type": evaluator_type}
        )
        await self._log_decision(context, decision)

        return {
            "variant_id": str(variant_id),
            "score": score,
            "evaluation_id": eval_result["evaluation_id"]
        }
```

## Next Steps

See [Module 5: Agent Implementations](../../../docs/module-05-agents.md) for the 5 concrete agent implementations.
