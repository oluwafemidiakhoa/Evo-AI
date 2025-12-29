# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Full Stack (Docker)
```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f [backend|frontend|postgres|redis]

# Stop all services
docker-compose down

# Rebuild after dependency changes
docker-compose up -d --build
```

### Backend (FastAPI + Python)
```bash
cd backend

# Install dependencies
poetry install

# Run development server
poetry run uvicorn evo_ai.api.app:app --reload --port 8002

# Run tests
poetry run pytest                    # All tests with coverage
poetry run pytest tests/unit         # Unit tests only
poetry run pytest -k test_name       # Specific test
poetry run pytest -v                 # Verbose output

# Linting and type checking
poetry run ruff check .              # Lint
poetry run ruff format .             # Format code
poetry run mypy src                  # Type check

# Database migrations
poetry run alembic upgrade head      # Apply migrations
poetry run alembic revision --autogenerate -m "description"  # Create migration
poetry run alembic downgrade -1      # Rollback one migration
```

### Frontend (Next.js + TypeScript)
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev                          # Starts on port 3000

# Build and type check
npm run build                        # Production build
npm run type-check                   # TypeScript validation
npm run lint                         # ESLint

# Production server
npm run start                        # After build
```

## Architecture Overview

### Backend Structure (Clean Architecture + DDD)

The backend follows **Domain-Driven Design** with clear separation of concerns:

```
backend/src/evo_ai/
├── domain/              # Core business logic (entities, repositories interfaces)
├── agents/              # 5 AI agents + orchestration layer
├── infrastructure/      # External integrations (DB, cache, storage, MCP)
└── api/                 # REST API (FastAPI routers)
```

**Key Architectural Patterns:**
- **Repository Pattern**: All data access through abstract repository interfaces with PostgreSQL implementations
- **Dependency Injection**: FastAPI `Depends()` for sessions, services, and orchestrators
- **Async Throughout**: All I/O operations use `async/await` (AsyncSession, httpx, etc.)
- **Observability**: OpenTelemetry spans, structlog, Prometheus metrics on every operation

### The 5 AI Agents (Multi-Agent System)

All agents inherit from `BaseEvoAgent` and are orchestrated via `AgentOrchestrator` using OpenAI Swarm:

1. **PlannerAgent** ([planner.py](backend/src/evo_ai/agents/implementations/planner.py))
   - Plans evolution strategy for each round
   - Adapts based on round progress (exploration → exploitation)
   - Outputs: variant count, mutation distribution, selection pressure

2. **VariantAgent** ([variant_generator.py](backend/src/evo_ai/agents/implementations/variant_generator.py))
   - Generates new code/prompt variants via mutations
   - Mutation types: `refactor`, `optimize`, `expand`, `simplify`, `experimental`
   - **CRITICAL**: Maintains lineage (parent_id, generation increment)

3. **ScorerAgent** ([scorer.py](backend/src/evo_ai/agents/implementations/scorer.py))
   - Evaluates variant quality via LLM judge, tests, benchmarks
   - Weighted criteria: correctness (30%), quality (25%), performance (20%), innovation (15%), simplicity (10%)

4. **PolicyAgent** ([policy_maker.py](backend/src/evo_ai/agents/implementations/policy_maker.py))
   - Applies selection strategies (top_k, tournament, diversity, adaptive)
   - Marks variants with `is_selected=True` for next generation

5. **ReporterAgent** ([reporter.py](backend/src/evo_ai/agents/implementations/reporter.py))
   - Generates round summaries, progress reports, lineage analysis

**Agent Execution Flow (per round):**
```
PlannerAgent → VariantAgent → ScorerAgent → PolicyAgent → ReporterAgent
```

### Domain Model (Core Entities)

**Campaign** → **Round** → **Variant** → **Evaluation**

- **Campaign**: Top-level experiment container
  - Status: DRAFT → ACTIVE → PAUSED/COMPLETED/FAILED
  - Contains: population_size, max_rounds, objectives

- **Round**: Single evolution iteration
  - Status: PENDING → PLANNING → GENERATING → EVALUATING → SELECTING → REPORTING → COMPLETED
  - Contains plan from PlannerAgent

- **Variant**: Candidate solution (code, prompt, etc.)
  - **Non-negotiable invariant**: Lineage tracking
    - `parent_id`: Reference to parent (null for generation 0)
    - `generation`: Incremental counter
    - `content_hash`: SHA-256 for deduplication
  - `is_selected`: Flag for next generation

- **Policy**: Selection/mutation strategies with versioning
- **Evaluation**: Scoring results for variants
- **AgentDecision**: Logs all agent reasoning with trace_id (required for observability)
- **Report**: Generated summaries

### Frontend Structure (Next.js 14 App Router)

```
frontend/src/
├── app/                 # App Router pages
│   ├── campaigns/       # Campaign list, detail, new
│   ├── variants/        # Variant details, lineage visualization
│   ├── reports/         # Report viewing
│   └── analytics/       # Analytics dashboard
├── components/          # React components (shadcn/ui based)
└── lib/
    └── api/             # Type-safe API client
```

**Data Fetching**: SWR for client-side caching and real-time updates

## Critical Conventions & Invariants

### 1. Lineage Tracking (Non-Negotiable)
Every variant MUST track ancestry for reproducibility:
```python
# When creating variants
variant = Variant.create_from_parent(
    parent=parent_variant,  # Sets parent_id and increments generation
    content=new_content,
    mutation_metadata={"type": "optimize", ...}
)
```

### 2. Trace ID Propagation
All operations must include `trace_id` for distributed tracing:
```python
# Agents receive context with trace_id
context = AgentContext(
    trace_id=trace_id,
    campaign_id=campaign_id,
    round_id=round_id
)
# All agent decisions automatically logged with trace_id
```

### 3. Agent Decision Logging
All agent choices must be logged via `AgentDecision`:
```python
# Automatically handled by BaseEvoAgent._log_decision()
# Called after every agent tool execution
```

### 4. Soft Deletes for Audit Trail
Never hard delete operational data:
```python
campaign.soft_delete()  # Sets deleted_at timestamp
# Queries exclude soft-deleted by default
```

### 5. Repository Pattern Usage
Always access data through repository interfaces:
```python
# CORRECT
campaign = await campaign_repo.get(campaign_id)

# INCORRECT - don't query database directly in agents/API
session.execute(select(Campaign).where(...))
```

### 6. MCP Tool Integration
Agents use MCP (Model Context Protocol) for external access:
```python
# Register MCP tool in agent
self._create_mcp_tool(
    server_name="github",
    tool_name="read_file",
    description="Read from GitHub",
    version="1.0.0"  # Versioning required
)
```

## Database Migrations (Alembic)

**Important**: Always import ALL models in [backend/alembic/env.py](backend/alembic/env.py#L14-L23) before generating migrations.

```bash
# Workflow for schema changes:
1. Modify models in backend/src/evo_ai/infrastructure/database/models.py
2. Import new model in backend/alembic/env.py (line 14-23)
3. poetry run alembic revision --autogenerate -m "Add new field"
4. Review generated migration in backend/alembic/versions/
5. poetry run alembic upgrade head
```

Alembic uses async migrations and auto-loads database URL from settings.

## Testing Patterns

Tests use **pytest** with async support:

```python
# Fixture usage (from conftest.py)
async def test_campaign_creation(session: AsyncSession):
    # session fixture provides fresh in-memory SQLite DB
    campaign = Campaign(name="Test", ...)
    session.add(campaign)
    await session.commit()

    assert campaign.id is not None
```

**Test structure:**
- `tests/unit/domain/` - Domain model tests
- `tests/unit/agents/` - Agent behavior tests
- `tests/unit/api/` - API endpoint tests

**Key fixtures** ([backend/tests/conftest.py](backend/tests/conftest.py)):
- `engine`: Async SQLAlchemy engine (in-memory SQLite)
- `session`: Fresh database session per test
- `test_settings`: Settings with test configuration

## Environment Configuration

### Required Environment Variables

**Backend (.env):**
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/evo_ai
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...      # For Claude models
OPENAI_API_KEY=sk-...              # For GPT models
S3_ACCESS_KEY=minioadmin           # MinIO/S3 for report storage
S3_SECRET_KEY=minioadmin
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=evo-ai-reports
```

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8002
```

## Common Workflows

### Adding a New Agent Tool
1. Create tool function in `backend/src/evo_ai/agents/tools/`
2. Register in agent's `_setup_tools()` method via `_create_domain_tool()` or `_create_mcp_tool()`
3. Tool automatically logged and traced via `BaseEvoAgent`

### Adding a New API Endpoint
1. Add route in appropriate router (`backend/src/evo_ai/api/routers/`)
2. Define request/response schemas in `backend/src/evo_ai/api/schemas.py`
3. Use dependency injection for database session: `session: AsyncSession = Depends(get_db)`
4. Add corresponding method in `frontend/src/lib/api/client.ts`

### Modifying Domain Model
1. Update domain entity in `backend/src/evo_ai/domain/models/`
2. Update database model in `backend/src/evo_ai/infrastructure/database/models.py`
3. Update repository if needed (interface + PostgreSQL implementation)
4. Generate migration: `poetry run alembic revision --autogenerate -m "description"`
5. Update tests

## API Access

- **Backend API docs**: http://localhost:8002/docs (Swagger UI)
- **Frontend**: http://localhost:3000
- **Health check**: http://localhost:8002/health

## Key Files to Understand

- [backend/src/evo_ai/agents/base.py](backend/src/evo_ai/agents/base.py) - Base agent with tool management and decision logging
- [backend/src/evo_ai/agents/orchestrator.py](backend/src/evo_ai/agents/orchestrator.py) - Coordinates all 5 agents
- [backend/src/evo_ai/domain/models/](backend/src/evo_ai/domain/models/) - Core business entities
- [backend/src/evo_ai/infrastructure/database/repositories/](backend/src/evo_ai/infrastructure/database/repositories/) - Data access layer
- [backend/src/evo_ai/config.py](backend/src/evo_ai/config.py) - Settings management (Pydantic)
- [frontend/src/lib/api/client.ts](frontend/src/lib/api/client.ts) - Type-safe API client

## Philosophy & Principles

1. **Correctness > Speed** - Variants must work correctly first
2. **Reproducibility** - Every experiment must be deterministic
3. **Traceability** - All decisions logged with trace_id (non-negotiable)
4. **Transparency** - No black-box magic, all agent reasoning captured
5. **Type Safety** - Type hints everywhere (Python), strict mode (TypeScript)
6. **Clean Architecture** - Domain logic independent of infrastructure

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment to Vercel (frontend) and Railway/Render (backend).
