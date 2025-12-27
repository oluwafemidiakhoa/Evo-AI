# Evo-AI Platform

**Production-Ready LTEE-Inspired Experimental Evolution Platform**

A comprehensive platform for designing, simulating, and learning from evolutionary and selection loops, inspired by Lenski's Long-Term Evolution Experiment (LTEE).

## Project Status

✅ **All 12 Modules Completed** ✅

The Evo-AI platform is now production-ready with complete backend, frontend, testing, and documentation!

## Architecture

This platform follows a **Domain-Driven Design** with **Hexagonal Architecture**:

```
evo-ai/
├── backend/              # Python FastAPI backend
│   ├── src/evo_ai/
│   │   ├── domain/       # Pure business logic
│   │   ├── infrastructure/ # DB, storage, observability
│   │   ├── agents/       # 5 AI agents
│   │   ├── mcp/          # MCP server framework
│   │   ├── api/          # FastAPI routes
│   │   └── tasks/        # Ray async tasks
│   ├── tests/            # Unit, integration, E2E
│   └── alembic/          # Database migrations
│
├── frontend/             # Next.js 14+ TypeScript frontend
│   └── src/
│       ├── app/          # App Router pages
│       ├── components/   # React components
│       └── lib/          # API client, hooks
│
├── infrastructure/       # Docker Compose & config
│   ├── docker/
│   ├── observability/    # Grafana, Prometheus
│   └── scripts/
│
└── docs/                 # Architecture docs
    ├── architecture/     # ADRs
    ├── api/              # OpenAPI specs
    └── guides/           # User guides
```

## Core Domain Model

```
Campaign
├─> Round (N)
    ├─> Variant (N) [with lineage tracking]
    └─> Evaluation (N)

Policy (versioned selection strategies)
AgentDecisions (all decisions logged with trace_id)
MCPAccessLogs (all external access versioned)
```

## Tech Stack

### Backend
- **FastAPI** - Async web framework
- **SQLModel** - Pydantic + SQLAlchemy ORM
- **PostgreSQL 15+** - Primary database (JSONB for flexibility)
- **Ray** - Distributed task execution
- **OpenAI Agents SDK** - Multi-agent orchestration
- **OpenTelemetry** - Distributed tracing
- **Structlog** - Structured JSON logging
- **Prometheus** - Metrics

### Frontend
- **Next.js 14+** - React framework (App Router)
- **TypeScript** - Strict mode
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **TanStack Query** - Data fetching

### Infrastructure
- **Docker Compose** - Local development
- **PostgreSQL** - Database
- **Redis** - Caching & pub/sub
- **MinIO** - S3-compatible storage
- **Jaeger** - Tracing UI
- **Grafana** - Dashboards

## Non-Negotiables

Following [AGENTS.md](AGENTS.md):

- ✅ Correctness > Speed
- ✅ Reproducibility > Cleverness
- ✅ Traceability > Black-box magic
- ✅ All agent decisions logged with trace_id
- ✅ Every variant has lineage tracking
- ✅ All MCP access versioned and logged
- ✅ Type hints (Python) / strict mode (TypeScript)
- ✅ No secrets in repository

## Implementation Modules

1. **Core Domain & Database** - ✅ Complete
2. **Infrastructure & Observability** - ✅ Complete
3. **MCP Server Framework** - ✅ Complete
4. **Agent Framework** - ✅ Complete
5. **Agent Implementations** - ✅ Complete
6. **API Layer** - ✅ Complete
7. **Task Orchestration** - ✅ Complete
8. **Frontend Foundation** - ✅ Complete
9. **Campaign Management UI** - ✅ Complete
10. **Variant Visualization** - ✅ Complete
11. **Reporting & Analytics** - ✅ Complete
12. **Testing & Documentation** - ✅ Complete

## Agent Roles

The platform implements 5 specialized AI agents:

1. **PlannerAgent** - Analyzes state and plans rounds
2. **VariantAgent** - Generates new variants via mutation/crossover
3. **ScorerAgent** - Evaluates variants against test cases
4. **PolicyAgent** - Selects variants for next generation
5. **ReporterAgent** - Generates human-readable reports

All agents orchestrated via **OpenAI Swarm** pattern with proper handoffs and traceability.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis

### Quick Start

```bash
# Backend setup
cd backend
poetry install
cp .env.example .env
# Edit .env with your config
poetry run alembic upgrade head
poetry run uvicorn evo_ai.main:app --reload

# Frontend setup (when ready)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

### With Docker Compose

```bash
cd infrastructure/docker
docker-compose up -d
```

## Testing

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests (when ready)
cd frontend
npm test
```

## Documentation

- **Plan**: [.claude/plans/squishy-dreaming-gray.md](.claude/plans/squishy-dreaming-gray.md)
- **Architecture**: docs/architecture/
- **API Docs**: http://localhost:8000/docs (when running)

## License

Proprietary

**Owner**: Oluwafemi Idiakhoa

---

**Philosophy**: *This code will matter in 5 years.*
