# Getting Started with Evo-AI

## What You Just Got

Evo-AI is now fully set up with:

✅ **Docker Compose** - Run entire stack with one command
✅ **Backend API** - FastAPI with 5 AI agents
✅ **Frontend Dashboard** - Next.js UI for monitoring evolution
✅ **Database** - PostgreSQL for data persistence
✅ **Redis** - Job queue and caching
✅ **Examples** - Ready-to-run evolution demos
✅ **Deployment Guides** - Deploy to Vercel + Railway

---

## What Evo-AI Actually Does

**Instead of manually optimizing code:**

1. Start with any code (function, algorithm, prompt, etc.)
2. Evo-AI generates 10+ variants using LLM agents
3. Each variant is tested and benchmarked
4. Best performers are selected
5. Winners become parents for next generation
6. Repeat for multiple generations

**Result:** Discover optimized code automatically - faster algorithms, better performance, novel approaches.

---

## Quick Start (5 Minutes)

### Option 1: Docker (Recommended)

```bash
# 1. Add your API keys
cp .env.example .env
# Edit .env and add: ANTHROPIC_API_KEY or OPENAI_API_KEY

# 2. Start everything
docker-compose up -d

# 3. Run migrations
docker-compose exec backend alembic upgrade head

# 4. Open browser
# Frontend: http://localhost:3000
# API Docs: http://localhost:8002/docs
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
poetry install
cp .env.example .env
# Add your API keys to .env
poetry run alembic upgrade head
poetry run uvicorn evo_ai.api.app:app --reload --port 8002
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8002
npm run dev
```

---

## See Evolution in Action

### Demo 1: Sorting Algorithm Evolution

```bash
# Install dependencies
pip install httpx

# Run demo
python examples/sorting_evolution.py
```

**What happens:**
1. Creates campaign to optimize bubble sort
2. Generates 10 variants per round (quick sort, merge sort, etc.)
3. Evaluates each with benchmarks
4. Selects best performers
5. Evolves for 3 generations

### Demo 2: Via UI

1. Go to http://localhost:3000
2. Click "New Campaign"
3. Fill in:
   - Name: "Test Evolution"
   - Max Rounds: 3
   - Variants per Round: 5
4. Click "Create"
5. Click "Start Campaign"
6. Click "Execute Round 1"
7. Watch variants being generated and evaluated!

### Demo 3: Via API

```bash
# Create campaign
curl -X POST http://localhost:8002/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Test",
    "description": "Testing via API",
    "config": {
      "max_rounds": 3,
      "variants_per_round": 5,
      "evaluators": ["llm_judge"]
    }
  }'

# Start campaign (use ID from response)
curl -X POST http://localhost:8002/api/campaigns/{id}/start

# Execute round
curl -X POST http://localhost:8002/api/campaigns/{id}/rounds/1/execute
```

---

## Real-World Examples

### 1. Optimize a Slow Function

```python
# Your slow code
def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result

# Let Evo-AI evolve it
curl -X POST http://localhost:8002/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Optimize process_data",
    "config": {
      "base_code": "def process_data(items):\n    result = []\n    for item in items:\n        if item > 0:\n            result.append(item * 2)\n    return result",
      "optimization_goal": "speed",
      "evaluators": ["benchmark", "unit_test"]
    }
  }'

# Result: Evo-AI discovers list comprehension, filter(), or numpy approaches
```

### 2. Improve API Endpoint

```python
# Current slow endpoint
@app.get("/users")
def get_users():
    users = db.query(User).all()
    return [user.to_dict() for user in users]

# Evo-AI variants might discover:
# - Pagination
# - Select only needed fields
# - Caching
# - Async queries
# - Database indexing
```

### 3. Evolve LLM Prompts

```bash
# Original prompt
"Classify this review as positive or negative"

# Evo-AI tests variations:
# - Different phrasings
# - Few-shot examples
# - Chain-of-thought
# - Structured output
```

---

## Understanding the UI

### Campaign Dashboard (`/campaigns`)
- View all evolution experiments
- See campaign status (draft, active, completed)
- Create new campaigns
- Quick stats overview

### Campaign Detail (`/campaigns/{id}`)
- Full campaign configuration
- Real-time statistics
- Round-by-round results
- Generated reports
- Start/pause controls

### Round Details (`/campaigns/{id}/rounds/{round}`)
- All variants for this round
- Performance scores
- Evaluation results
- Selection decisions

### Lineage View (`/campaigns/{id}/lineage`)
- Evolution tree visualization
- Parent-child relationships
- Performance trends across generations
- Identify successful patterns

---

## Key Concepts

### Campaign
An evolution experiment with specific goal and configuration.

### Round
One generation in the evolution. Each round:
1. Generates variants
2. Evaluates them
3. Selects winners

### Variant
A single code implementation. Has:
- Unique code
- Parent lineage
- Performance scores
- Selection status

### Evaluators
How variants are scored:
- **unit_test**: Correctness
- **benchmark**: Speed/performance
- **llm_judge**: Code quality
- **memory_profiler**: Memory usage
- **custom**: Your own criteria

### Selection Policy
How winners are chosen:
- **top_k**: Best N performers
- **tournament**: Bracket-style competition
- **diversity**: Maintain variety

---

## Configuration Options

### Campaign Config

```json
{
  "max_rounds": 5,              // How many generations
  "variants_per_round": 10,     // Variants per generation
  "evaluators": ["benchmark", "unit_test", "llm_judge"],
  "optimization_goal": "speed", // What to optimize for
  "selection_strategy": "top_k",
  "selection_count": 5,         // Winners per round
  "base_code": "...",           // Starting point
  "constraints": ["pure_python", "no_external_libs"],
  "test_cases": [...]           // Test data
}
```

---

## Deployment

### Deploy to Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete guide.

**Quick version:**

1. **Frontend to Vercel** (free)
   ```bash
   cd frontend
   vercel --prod
   ```

2. **Backend to Railway** ($5/month)
   ```bash
   railway init
   railway up
   ```

3. **Database on Neon** (free tier)
   - Create database at neon.tech
   - Copy connection string

4. **Redis on Upstash** (free tier)
   - Create database at upstash.com
   - Copy connection URL

**Total cost:** ~$5-10/month

---

## Next Steps

### 1. Run Your First Evolution

Try the sorting example:
```bash
python examples/sorting_evolution.py
```

### 2. Create Custom Campaign

Use the UI to create a campaign for your own code:
1. Go to http://localhost:3000
2. Create new campaign
3. Add your code
4. Configure evaluators
5. Start evolving!

### 3. View Evolution Results

Watch the evolution happen:
1. Click on campaign
2. Execute rounds
3. View variants
4. Check lineage tree
5. Read AI reports

### 4. Deploy to Production

When ready:
1. Follow [DEPLOYMENT.md](DEPLOYMENT.md)
2. Deploy to Vercel + Railway
3. Share with team
4. Start evolving code in production!

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common fixes:
# 1. Add API keys to .env
# 2. Run migrations
docker-compose exec backend alembic upgrade head
```

### Frontend Can't Connect

```bash
# Check backend is running
curl http://localhost:8002/health

# Check .env.local has correct API URL
cat frontend/.env.local
# Should show: NEXT_PUBLIC_API_URL=http://localhost:8002
```

### No Variants Generated

- Check you have API keys (ANTHROPIC_API_KEY or OPENAI_API_KEY)
- Check API key has credits
- View backend logs for errors

### Evolution Takes Long

This is normal! Generating and evaluating code takes time:
- 10 variants × 3 evaluators = 30 LLM calls
- Each call: 5-30 seconds
- Total: 2-10 minutes per round

---

## Learn More

- **Evolution Demo**: [EVOLUTION_DEMO.md](EVOLUTION_DEMO.md)
- **Platform Guide**: [DEMO_GUIDE.md](DEMO_GUIDE.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Docs**: http://localhost:8002/docs
- **README**: [README.md](README.md)

---

## Support

Questions? Issues?

1. Check logs: `docker-compose logs -f`
2. Review documentation above
3. Check GitHub issues
4. Contact: Oluwafemi Idiakhoa

---

## Quick Reference

**Start Everything:**
```bash
docker-compose up -d
```

**Stop Everything:**
```bash
docker-compose down
```

**View Logs:**
```bash
docker-compose logs -f
```

**Run Demo:**
```bash
python examples/sorting_evolution.py
```

**Access UI:**
- http://localhost:3000

**API Docs:**
- http://localhost:8002/docs

---

**You're ready to start evolving code with AI!** 🚀
