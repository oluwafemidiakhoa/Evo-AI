# Evo-AI Backend

Production-ready backend for the LTEE-inspired Experimental Evolution Platform.

## Overview

This backend implements a complete domain-driven architecture for evolutionary experiments:
- **Domain Layer**: Pure business logic (Campaign, Round, Variant, Policy models)
- **Infrastructure Layer**: Database, MCP servers, observability
- **API Layer**: FastAPI REST endpoints with OpenAPI docs
- **Agents**: 5 AI agents (Planner, Variant, Scorer, Policy, Reporter)

## Tech Stack

- **Framework**: FastAPI (async)
- **ORM**: SQLModel (Pydantic + SQLAlchemy)
- **Database**: PostgreSQL 15+ with JSONB
- **Task Queue**: Ray
- **AI**: OpenAI Agents SDK (Swarm)
- **Observability**: OpenTelemetry, Structlog, Prometheus

## Architecture

```
src/evo_ai/
├── domain/           # Pure domain logic (no deps)
│   ├── models/       # Campaign, Round, Variant, Policy
│   └── repositories/ # Repository interfaces
├── infrastructure/   # External adapters
│   ├── database/     # SQLModel + PostgreSQL
│   ├── observability/# Tracing, logging, metrics
│   ├── storage/      # S3/MinIO
│   └── cache/        # Redis
├── agents/           # AI agent implementations
├── mcp/              # MCP server framework
├── api/              # FastAPI routes
└── tasks/            # Ray async tasks
```

## Domain Model

```
Campaign (1) ──< (N) Round (1) ──< (N) Variant
                                         │
                                         └─ parent_id (lineage)

Round (1) ──< (N) Evaluation ──> (1) Variant
Campaign (1) ──< (N) Policy
```

**Invariants** (enforced):
1. Every Round belongs to exactly one Campaign
2. Every Variant has lineage (parent_id, generation)
3. Every agent decision logged with trace_id
4. All MCP access versioned and logged

## Setup

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL 15+
- Redis

### Installation

```bash
# Install dependencies
poetry install

# Copy environment template
cp .env.example .env
# Edit .env with your settings

# Run migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn evo_ai.main:app --reload
```

## Database Migrations

```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=evo_ai

# Run specific test file
poetry run pytest tests/unit/domain/test_variant.py

# Run integration tests
poetry run pytest tests/integration/
```

## Linting & Type Checking

```bash
# Run linter
poetry run ruff check .

# Auto-fix linting issues
poetry run ruff check --fix .

# Type checking
poetry run mypy src/

# Format code
poetry run black src/ tests/
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Environment Variables

See `.env.example` for all configuration options. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for agents
- `S3_ENDPOINT`: MinIO/S3 endpoint
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry collector

## Non-Negotiables

Following [AGENTS.md](/AGENTS.md):
- ✅ All agent decisions logged with trace_id
- ✅ All variants have lineage tracking
- ✅ All MCP access versioned and logged
- ✅ Type hints required on all functions
- ✅ No secrets in repository
- ✅ Reproducible builds

## Development Workflow

1. Create feature branch
2. Make changes (following domain-driven design)
3. Write tests (unit + integration)
4. Run linting and type checking
5. Create migration if DB schema changed
6. Commit with descriptive message
7. Open PR with tests passing

## License

Proprietary - Oluwafemi Idiakhoa
