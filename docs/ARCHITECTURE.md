# Architecture Documentation

Comprehensive guide to the Evo-AI platform architecture, design decisions, and implementation patterns.

## Table of Contents

- [System Overview](#system-overview)
- [Design Principles](#design-principles)
- [Domain Model](#domain-model)
- [Agent Architecture](#agent-architecture)
- [Data Flow](#data-flow)
- [Technology Choices](#technology-choices)
- [Observability](#observability)
- [Security](#security)

## System Overview

Evo-AI implements a **Domain-Driven Design** with **Hexagonal Architecture** (Ports & Adapters), ensuring clean separation of concerns and testability.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                        │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐ │
│  │  Next.js UI    │  │  REST API      │  │  SSE Streaming    │ │
│  └────────────────┘  └────────────────┘  └───────────────────┘ │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                     Application Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Agent Orchestration (Swarm)                 │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │  PlannerAgent  │  VariantAgent  │  ScorerAgent │    │   │
│  │  │  PolicyAgent   │  ReporterAgent                 │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Task Orchestration (Ray)                       │   │
│  │  - Async round execution                                 │   │
│  │  - Distributed variant generation                        │   │
│  │  - Parallel evaluation                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                       Domain Layer (Core)                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Campaign  →  Round  →  Variant  →  Evaluation          │   │
│  │                          ↑                                │   │
│  │                    Lineage Tracking                       │   │
│  │                    (parent_id + generation)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AgentDecision | MCPAccessLog | Policy | Report          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                   Infrastructure Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ PostgreSQL   │  │   Redis      │  │   MinIO (S3)          │ │
│  │ (SQLModel)   │  │ (Cache/Pub)  │  │ (File Storage)        │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ OpenTelemetry│  │  Prometheus  │  │   Grafana             │ │
│  │ (Tracing)    │  │  (Metrics)   │  │ (Dashboards)          │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Domain-Driven Design (DDD)

**Core Entities**:
- `Campaign`: Aggregate root for an evolution experiment
- `Round`: Represents one generation in the evolution
- `Variant`: A code solution with lineage tracking
- `Evaluation`: Assessment of a variant's quality
- `Policy`: Selection strategy (versioned)

**Value Objects**:
- `LineageInfo`: Parent ID + generation number
- `EvaluationScore`: Normalized score (0.0-1.0)
- `MutationType`: Enum of evolution strategies

### 2. Hexagonal Architecture (Ports & Adapters)

**Ports** (Interfaces):
```python
# Domain port
class VariantRepository(ABC):
    @abstractmethod
    async def save(self, variant: Variant) -> Variant:
        pass

    @abstractmethod
    async def get_lineage(self, variant_id: UUID) -> List[Variant]:
        pass
```

**Adapters** (Implementations):
```python
# PostgreSQL adapter
class PostgresVariantRepository(VariantRepository):
    async def save(self, variant: Variant) -> Variant:
        # SQLModel implementation
        pass

    async def get_lineage(self, variant_id: UUID) -> List[Variant]:
        # Recursive CTE query
        pass
```

### 3. CQRS (Command Query Responsibility Segregation)

**Commands** (Writes):
- `CreateCampaignCommand`
- `ExecuteRoundCommand`
- `SelectVariantsCommand`

**Queries** (Reads):
- `GetCampaignStatsQuery`
- `GetVariantLineageQuery`
- `ListReportsQuery`

## Domain Model

### Campaign Lifecycle

```
pending → in_progress → completed
            ↓
         failed
```

**State Transitions**:
1. **Created** (`pending`): Campaign configured, no rounds executed
2. **Started** (`in_progress`): At least one round executing
3. **Completed** (`completed`): All rounds successful
4. **Failed** (`failed`): Unrecoverable error occurred

### Round Execution Flow

```
1. Planning Phase
   └─> PlannerAgent determines:
       - Number of variants to generate
       - Mutation strategies to use
       - Parent variant selection

2. Generation Phase
   └─> VariantAgent creates variants:
       - Selects parents from previous round
       - Applies mutation strategy
       - Tracks lineage (parent_id + generation++)

3. Evaluation Phase
   └─> ScorerAgent evaluates each variant:
       - Runs unit tests
       - Performs benchmarks
       - Uses LLM judge
       - Aggregates scores

4. Selection Phase
   └─> PolicyAgent selects survivors:
       - Applies selection policy (top_k, tournament, etc.)
       - Marks selected variants (is_selected = true)
       - Prepares next round parents

5. Reporting Phase
   └─> ReporterAgent generates insights:
       - Round summary
       - Performance trends
       - Lineage analysis
```

### Lineage Tracking

**Critical Design**: Every variant MUST have lineage information.

```python
class Variant(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    parent_id: Optional[UUID] = Field(foreign_key="variant.id")  # CRITICAL
    generation: int  # CRITICAL: parent.generation + 1
    mutation_type: Optional[str]  # How it was created
    content: str  # The actual code
    content_hash: str  # SHA256 for deduplication
    is_selected: bool = False
```

**Lineage Query** (Recursive CTE):
```sql
WITH RECURSIVE lineage AS (
    -- Base case: the variant itself
    SELECT * FROM variant WHERE id = :variant_id
    UNION ALL
    -- Recursive case: parent variants
    SELECT v.*
    FROM variant v
    INNER JOIN lineage l ON v.id = l.parent_id
)
SELECT * FROM lineage ORDER BY generation;
```

## Agent Architecture

### BaseEvoAgent (Abstract)

All agents inherit from `BaseEvoAgent`:

```python
class BaseEvoAgent(ABC):
    def __init__(self, mcp_registry: MCPRegistry):
        self.mcp_registry = mcp_registry
        self._tools: Dict[str, Callable] = {}
        self._register_tools()

    @abstractmethod
    async def execute(self, context: AgentContext, **kwargs) -> Any:
        """Main execution logic - must be implemented by subclasses."""
        pass

    async def run_with_tracing(self, context: AgentContext, **kwargs) -> Any:
        """Wraps execution with OpenTelemetry tracing."""
        with tracer.start_as_current_span(f"agent.{self.agent_type}.execute"):
            # Auto-inject trace context
            # Record metrics
            # Log decision to database
            result = await self.execute(context, **kwargs)
            await self._log_decision(context, decision)
            return result
```

**Key Features**:
- Automatic tracing with OpenTelemetry
- Decision logging (NON-NEGOTIABLE)
- Tool registration and access
- Metrics collection (Prometheus)

### Agent Swarm Orchestration

Uses **OpenAI Swarm** pattern for agent coordination:

```python
class AgentOrchestrator:
    def __init__(self, mcp_registry: MCPRegistry):
        self.planner = PlannerAgent(mcp_registry)
        self.variant_generator = VariantAgent(mcp_registry)
        self.scorer = ScorerAgent(mcp_registry)
        self.policy_maker = PolicyAgent(mcp_registry)
        self.reporter = ReporterAgent(mcp_registry)

    async def execute_round(self, campaign_id: UUID, round_number: int):
        # 1. Plan
        plan = await self.planner.create_round(context, round_number)

        # 2. Generate (can be parallelized)
        variants = await self.variant_generator.generate_batch(context, plan)

        # 3. Evaluate (highly parallelizable with Ray)
        evaluations = await self.scorer.evaluate_batch(context, variant_ids)

        # 4. Select
        selection = await self.policy_maker.apply_policy(context, policy_id)

        # 5. Report
        report = await self.reporter.execute(context, ReportType.ROUND_SUMMARY)

        return RoundResult(...)
```

### MCP Integration

Agents access external tools via **Model Context Protocol**:

```python
# Example: Filesystem access
async with mcp_registry.get_server("filesystem") as fs_server:
    content = await fs_server.call_tool("read_file", path="/code/main.py")

# All MCP access automatically logged:
# - server_name
# - tool_name
# - input_params
# - output_result
# - trace_id
# - timestamp
```

## Data Flow

### Campaign Execution (Async)

```
User → POST /api/campaigns/{id}/execute
  ↓
FastAPI endpoint
  ↓
Ray remote task submission
  ↓
execute_campaign_remote@ray
  ↓
AgentOrchestrator.execute_round (loop)
  ↓
├─> PlannerAgent → DB write
├─> VariantAgent → DB write
├─> ScorerAgent → DB write
├─> PolicyAgent → DB update
└─> ReporterAgent → DB write
  ↓
SSE updates to frontend
```

### Variant Lineage Query

```
GET /api/variants/{id}/lineage
  ↓
VariantRepository.get_lineage()
  ↓
PostgreSQL recursive CTE
  ↓
[Variant Gen 0, Variant Gen 1, ..., Variant Gen N]
  ↓
Frontend LineageTree component (D3.js)
```

## Technology Choices

### Backend: FastAPI

**Why**:
- Async/await native support
- Automatic OpenAPI documentation
- Type hints with Pydantic
- Fast performance (comparable to Node.js/Go)

**Alternatives Considered**:
- Django: Too heavyweight, not async-first
- Flask: No native async support
- Node.js: Less robust typing, different ecosystem

### ORM: SQLModel

**Why**:
- Combines Pydantic (validation) + SQLAlchemy (ORM)
- Same models for API and database
- Full async support
- Type-safe queries

### Multi-Agent: OpenAI Swarm

**Why**:
- Lightweight, no framework lock-in
- Clear handoff patterns
- Easy tracing and debugging
- Native tool use support

**Alternatives Considered**:
- LangGraph: More complex, graph-based
- AutoGen: Different paradigm (conversational)

### Task Queue: Ray

**Why**:
- True distributed computing
- Python-native
- Built-in monitoring dashboard
- Handles both task queue + actor model

**Alternatives Considered**:
- Celery: Less modern, Redis-dependent
- RQ: Simple but limited scalability

### Frontend: Next.js 14

**Why**:
- App Router for modern React patterns
- Server Components for performance
- Built-in API routes
- Excellent TypeScript support
- Great developer experience

### Charts: Recharts

**Why**:
- React-native (not canvas-based like Chart.js)
- Composable components
- TypeScript support
- Responsive by default

### Visualization: D3.js

**Why**:
- Most powerful data visualization library
- Full control over SVG rendering
- Perfect for complex lineage trees
- Large community and examples

## Observability

### Three Pillars

1. **Logs** (Structlog)
   - JSON-formatted
   - Trace ID included
   - Configurable levels (DEBUG, INFO, WARN, ERROR)

2. **Metrics** (Prometheus)
   - Agent execution counts
   - API request durations
   - Variant generation rates
   - Selection success rates

3. **Traces** (OpenTelemetry + Jaeger)
   - Distributed tracing across services
   - Automatic context propagation
   - Agent decision correlation

### Key Metrics

```python
# Agent metrics
agent_calls = Counter('agent_calls_total', 'Total agent calls', ['agent_type', 'status'])
agent_duration = Histogram('agent_execution_seconds', 'Agent execution time', ['agent_type'])

# API metrics
http_requests = Counter('http_requests_total', 'HTTP requests', ['method', 'endpoint', 'status'])
http_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# Domain metrics
variants_generated = Counter('variants_generated_total', 'Variants generated', ['mutation_type'])
variants_selected = Counter('variants_selected_total', 'Variants selected', ['policy_type'])
```

## Security

### API Key Management

**Never** hardcode API keys:
```python
# ✅ GOOD
openai_key = os.getenv("OPENAI_API_KEY")

# ❌ BAD
openai_key = "sk-1234..."
```

### Input Validation

All inputs validated with Pydantic:
```python
class CreateCampaignRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    config: CampaignConfig

    @validator('config')
    def validate_config(cls, v):
        if v.max_rounds < 1 or v.max_rounds > 100:
            raise ValueError("max_rounds must be between 1 and 100")
        return v
```

### Database Security

- Parameterized queries (SQLModel prevents SQL injection)
- Row-level security for multi-tenancy (future)
- Encrypted connections (SSL/TLS)

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## Scaling Considerations

### Horizontal Scaling

- **Stateless API**: Multiple FastAPI instances behind load balancer
- **Database Connection Pooling**: SQLAlchemy pool (size=20, max_overflow=40)
- **Ray Cluster**: Distribute variant generation across workers

### Vertical Scaling

- **PostgreSQL**: Increase `shared_buffers`, `work_mem`
- **Redis**: Increase `maxmemory`
- **Ray**: More CPU cores for parallel task execution

### Caching Strategy

```python
# Cache campaign stats (1 minute TTL)
@cache(ttl=60)
async def get_campaign_stats(campaign_id: UUID) -> CampaignStats:
    # Expensive aggregation query
    pass

# Cache variant lineage (5 minutes TTL - rarely changes)
@cache(ttl=300)
async def get_variant_lineage(variant_id: UUID) -> List[Variant]:
    # Recursive CTE query
    pass
```

## Future Enhancements

- **Multi-language support**: Extend beyond Python to JS, Go, Rust
- **Collaborative evolution**: Multiple campaigns sharing variants
- **ML-based policies**: Learn optimal selection strategies
- **Real-time collaboration**: WebSocket support for multi-user
- **Advanced visualizations**: 3D lineage trees, animated evolution

## References

- [Domain-Driven Design by Eric Evans](https://www.domainlanguage.com/ddd/)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [LTEE Wikipedia](https://en.wikipedia.org/wiki/E._coli_long-term_evolution_experiment)
- [OpenAI Swarm](https://github.com/openai/swarm)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
