# Evo-AI Platform

**AI-Powered Code Evolution Through Multi-Agent Evolutionary Algorithms**

Evo-AI is a production-ready platform that uses LLM agents and evolutionary algorithms to automatically improve code. Think of it as "genetic algorithms meets GPT" for software optimization.

## 🌐 Live Demo

**🎨 Frontend**: https://evo-ai-seven.vercel.app

**⚙️ Backend API**: https://evo-ai-nakk.onrender.com

- 📚 **API Docs**: https://evo-ai-nakk.onrender.com/api/docs
- 💚 **Health Check**: https://evo-ai-nakk.onrender.com/health
- 📖 **API Reference**: https://evo-ai-nakk.onrender.com/api/redoc

**Try it yourself!** Create campaigns, execute evolution rounds, and watch AI agents optimize code in real-time.

## Advanced Engine (Phase 2)

Evo-AI now runs a research-grade evolution loop:

- **Multi-objective selection**: balances score, novelty, diversity, and innovation.
- **Ensemble evaluation**: combines LLM judge + tests/benchmarks with weighted scoring.
- **Budget-aware evals**: cost/latency limits with deterministic fallback evaluators.
- **Reproducible runs**: seeded plans, deterministic mutation distribution, plan hashing.
- **Structured reports**: JSON reports with lineage + metrics for downstream analysis.

## Advanced Configuration

Use the campaign config to control evaluation ensembles, budgets, and reproducibility:

```json
{
  "variants_per_round": 6,
  "max_rounds": 10,
  "seed": 1337,
  "evaluators": ["llm_judge", "unit_test"],
  "ensemble": [
    { "type": "llm_judge", "weight": 0.7 },
    { "type": "unit_test", "weight": 0.3 }
  ],
  "criteria_weights": {
    "correctness": 0.35,
    "code_quality": 0.25,
    "performance": 0.2,
    "innovation": 0.1,
    "simplicity": 0.1
  },
  "evaluation_budget": {
    "max_cost_usd": 0.05,
    "max_latency_ms": 1500,
    "fallback_evaluator": "unit_test",
    "allow_over_budget": false,
    "cost_per_1k_tokens": 0.002
  }
}
```

## What Does Evo-AI Actually Do?

Instead of manually optimizing code, Evo-AI:

1. **Generates** multiple code variants using LLM agents
2. **Evaluates** each variant with benchmarks and tests
3. **Selects** the best performers
4. **Evolves** winning variants over generations
5. **Discovers** optimal solutions automatically

**Result**: Faster algorithms, better performance, novel approaches - all discovered by AI.

---

## Real Example: Sorting Algorithm Evolution

```bash
# Start with a slow bubble sort
Original: O(n²) bubble sort

# Evo-AI generates 10 variants per round:
Round 1: Quick sort, merge sort, insertion sort variations
Round 2: Hybrid algorithms from Round 1 winners
Round 3: Optimized implementations

# After 3 generations:
Best Variant: Custom hybrid sort - 10x faster
```

**See it in action**: [EVOLUTION_DEMO.md](EVOLUTION_DEMO.md)

---

## Quick Start with Docker

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/evo-ai.git
cd evo-ai

# Create environment file
cp .env.example .env

# Add your API keys to .env
# You need: ANTHROPIC_API_KEY or OPENAI_API_KEY
```

### 2. Start All Services

```bash
# Start full stack (PostgreSQL + Redis + Backend + Frontend)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002/docs
- **Database**: localhost:5432

### 4. Run Evolution Demo

```bash
# Install Python client
pip install httpx

# Run sorting evolution example
python examples/sorting_evolution.py
```

---

## Use Cases

### 1. Algorithm Optimization
Evolve faster, more efficient algorithms automatically.

```bash
# Example: Path-finding optimization
Base: A* algorithm
Goal: Reduce memory + increase speed
Result: Novel hybrid approach 40% faster
```

### 2. API Performance
Improve endpoint latency and throughput.

```bash
# Example: User API endpoint
Base: Current implementation (200ms latency)
Goal: Sub-50ms latency
Result: Optimized queries + caching (35ms latency)
```

### 3. Prompt Engineering
Evolve better LLM prompts through experimentation.

```bash
# Example: Classification prompts
Base: Basic classification prompt
Goal: Higher accuracy + lower tokens
Result: Optimized prompt (15% better, 30% fewer tokens)
```

### 4. Data Pipeline Optimization
Speed up ETL and data processing.

```bash
# Example: CSV processing
Base: Pandas-based processor
Goal: Handle 10x more data
Result: Streaming approach with parallel processing
```

---

## Architecture

### Tech Stack

**Backend**
- FastAPI (async Python web framework)
- SQLModel + PostgreSQL (database)
- Anthropic Claude / OpenAI (LLM agents)
- Ray (distributed execution)
- OpenTelemetry (tracing)

**Frontend**
- Next.js 14 (React framework)
- TypeScript (type safety)
- Tailwind CSS + shadcn/ui (styling)
- SWR (data fetching)

**Infrastructure**
- Docker Compose (local dev)
- PostgreSQL (database)
- Redis (caching/queue)
- Grafana (monitoring)

### Domain Model

```
Campaign (evolution experiment)
 ├─> Rounds (generations)
 │    ├─> Variants (code implementations)
 │    └─> Evaluations (test results)
 └─> Reports (AI-generated insights)

Policies (selection strategies)
AgentDecisions (all AI choices logged)
```

### AI Agents

Five specialized agents work together:

1. **PlannerAgent** - Analyzes current state, plans evolution strategy
2. **VariantAgent** - Generates new code variants via mutation/crossover
3. **ScorerAgent** - Evaluates variants with tests and benchmarks
4. **PolicyAgent** - Selects best performers for next generation
5. **ReporterAgent** - Generates human-readable analysis

---

## Development

### Local Setup (Without Docker)

#### Backend

```bash
cd backend

# Install dependencies
poetry install

# Setup database
cp .env.example .env
# Edit .env with your database URL and API keys

# Run migrations
poetry run alembic upgrade head

# Start server
poetry run uvicorn evo_ai.api.app:app --reload --port 8002
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.local.example .env.local
# Edit .env.local with API URL

# Start dev server
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
npm test
```

---

## Deployment

### Deploy to Production

#### Frontend (Vercel)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

#### Backend (Railway / Render / Cloud Run)

```bash
# Build production image
docker build -t evoai-backend:latest -f backend/Dockerfile --target production .

# Deploy to your cloud provider
# Set environment variables:
# - DATABASE_URL
# - ANTHROPIC_API_KEY
# - OPENAI_API_KEY
# - CORS_ORIGINS=https://your-frontend.vercel.app
```

### Environment Variables

**Backend** (.env)
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/evo_ai
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
REDIS_URL=redis://host:6379/0
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend.vercel.app
```

**Frontend** (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NODE_ENV=production
```

---

## Documentation

- **Evolution Guide**: [EVOLUTION_DEMO.md](EVOLUTION_DEMO.md) - See AI evolution in action
- **Demo Guide**: [DEMO_GUIDE.md](DEMO_GUIDE.md) - Platform walkthrough
- **API Documentation**: http://localhost:8002/docs (when running)
- **Architecture**: `docs/architecture/` - Technical design docs

---

## Project Structure

```
evo-ai/
├── backend/                 # Python FastAPI backend
│   ├── src/evo_ai/
│   │   ├── domain/         # Core business logic
│   │   ├── infrastructure/ # Database, storage
│   │   ├── agents/         # 5 AI agents
│   │   ├── api/            # REST API endpoints
│   │   └── tasks/          # Background jobs
│   ├── tests/              # Comprehensive tests
│   └── alembic/            # Database migrations
│
├── frontend/               # Next.js 14 frontend
│   └── src/
│       ├── app/           # App Router pages
│       ├── components/    # React components
│       └── lib/           # API client
│
├── examples/              # Usage examples
│   └── sorting_evolution.py
│
├── docs/                  # Documentation
├── docker-compose.yml     # Full stack setup
└── .env.example          # Environment template
```

---

## Features

### Core Capabilities

- ✅ **Multi-Agent Evolution** - 5 specialized AI agents
- ✅ **Variant Generation** - LLM-powered code creation
- ✅ **Automated Evaluation** - Tests + benchmarks + quality checks
- ✅ **Selection Strategies** - Top-k, tournament, diversity-based
- ✅ **Lineage Tracking** - Full genealogy of all variants
- ✅ **Performance Metrics** - Speed, memory, quality scores
- ✅ **Evolution Reports** - AI-generated insights
- ✅ **Real-time Dashboard** - Watch evolution live
- ✅ **API-First Design** - Full REST API
- ✅ **Distributed Execution** - Scale with Ray

### Advanced Features

- Custom evaluators
- Multi-objective optimization
- Constraint-based evolution
- A/B testing integration
- Continuous evolution pipelines
- Integration with CI/CD

---

## Examples

### Example 1: Optimize Function

```python
from evo_ai import Campaign

campaign = Campaign.create(
    name="Optimize Data Processing",
    base_code="""
    def process_data(items):
        result = []
        for item in items:
            if item > 0:
                result.append(item * 2)
        return result
    """,
    goal="speed",
    evaluators=["benchmark", "unit_test"]
)

campaign.evolve(rounds=5)
best_variant = campaign.get_best()
print(f"Improvement: {best_variant.speedup}x faster")
```

### Example 2: Prompt Evolution

```python
campaign = Campaign.create(
    name="Optimize Classification Prompt",
    base_code="""Classify this text into categories...""",
    goal="accuracy_and_cost",
    evaluators=["llm_judge", "cost_analyzer"]
)

campaign.evolve(rounds=3)
best_prompt = campaign.get_best()
```

---

## Monitoring

### View Evolution Progress

```bash
# Watch backend logs
docker-compose logs -f backend

# Monitor database
docker-compose exec postgres psql -U evoai -d evo_ai

# Redis monitoring
docker-compose exec redis redis-cli MONITOR
```

### Metrics

Track in real-time:
- Variants generated per round
- Average performance scores
- Selection rates
- Evolution convergence
- Best variant improvements

---

## Philosophy

### Core Principles

1. **Correctness > Speed** - Variants must work correctly first
2. **Reproducibility** - All experiments are deterministic
3. **Traceability** - Every decision logged with trace_id
4. **Transparency** - No black-box magic

### Non-Negotiables

- All agent decisions logged
- Every variant has lineage tracking
- All external API calls versioned
- Type hints everywhere (Python)
- Strict mode (TypeScript)
- No secrets in repository

---

## Contributing

This is currently a proprietary project. For questions or collaboration:

**Owner**: Oluwafemi Idiakhoa

---

## License

Proprietary - All rights reserved

---

## Status

✅ **All 12 Modules Completed**

The Evo-AI platform is production-ready with:
- Complete backend API
- Full-featured frontend
- Comprehensive testing
- Docker deployment
- Complete documentation

---

## Quick Links

- [Evolution Demo](EVOLUTION_DEMO.md) - See AI evolution in action
- [Platform Guide](DEMO_GUIDE.md) - Full walkthrough
- [API Docs](http://localhost:8002/docs) - REST API reference
- [Architecture](docs/architecture/) - Technical design

---

**Start evolving your code today!**

```bash
docker-compose up -d
python examples/sorting_evolution.py
```

Watch as AI discovers better algorithms automatically.
