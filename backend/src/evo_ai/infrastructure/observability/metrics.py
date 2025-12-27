"""Prometheus metrics definitions."""

from prometheus_client import Counter, Gauge, Histogram

# Campaign metrics
campaigns_created = Counter(
    'evo_ai_campaigns_created_total',
    'Total campaigns created',
)

campaigns_active = Gauge(
    'evo_ai_campaigns_active',
    'Number of active campaigns',
)

# Round metrics
rounds_executed = Counter(
    'evo_ai_rounds_executed_total',
    'Total rounds executed',
    ['campaign_id', 'status'],
)

round_duration = Histogram(
    'evo_ai_round_duration_seconds',
    'Round execution duration in seconds',
    ['campaign_id'],
    buckets=[60, 300, 900, 1800, 3600, 7200],  # 1m, 5m, 15m, 30m, 1h, 2h
)

# Agent metrics
agent_calls = Counter(
    'evo_ai_agent_calls_total',
    'Total agent calls',
    ['agent_type', 'status'],
)

agent_duration = Histogram(
    'evo_ai_agent_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300],  # 1s, 5s, 10s, 30s, 1m, 2m, 5m
)

agent_tokens = Counter(
    'evo_ai_agent_tokens_total',
    'Total tokens used by agents',
    ['agent_type', 'model'],
)

# Variant metrics
variants_generated = Counter(
    'evo_ai_variants_generated_total',
    'Total variants generated',
    ['campaign_id', 'mutation_type'],
)

variants_evaluated = Counter(
    'evo_ai_variants_evaluated_total',
    'Total variants evaluated',
    ['campaign_id'],
)

evaluation_score = Histogram(
    'evo_ai_evaluation_score',
    'Variant evaluation scores',
    ['campaign_id', 'round_id'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# MCP metrics
mcp_calls = Counter(
    'evo_ai_mcp_calls_total',
    'Total MCP server calls',
    ['server_name', 'tool_name', 'status'],
)

mcp_duration = Histogram(
    'evo_ai_mcp_duration_seconds',
    'MCP call duration in seconds',
    ['server_name', 'tool_name'],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],  # 100ms to 30s
)
