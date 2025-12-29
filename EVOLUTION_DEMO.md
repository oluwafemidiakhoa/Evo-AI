# Evo-AI Evolution Demo: See AI-Driven Code Evolution in Action

This guide demonstrates the **real power** of Evo-AI: autonomous code evolution through multiple generations.

---

## What Evo-AI Actually Does

Evo-AI is a **multi-agent evolutionary platform** that:

1. **Generates Code Variants** - LLM agents create different implementations
2. **Evaluates Performance** - Tests and benchmarks each variant
3. **Selects Best Performers** - Chooses top variants based on scores
4. **Evolves Over Generations** - Best variants become parents for next round
5. **Analyzes Lineage** - Tracks evolutionary paths and insights

Think of it as **genetic algorithms meets LLM agents** for code optimization.

---

## Quick Start with Docker

### 1. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# You need at least one: ANTHROPIC_API_KEY or OPENAI_API_KEY
```

### 2. Start Full Stack

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 3. Access Platform

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs

---

## Real Evolution Example: Optimizing a Sorting Function

Let's evolve a sorting algorithm to be faster and more elegant.

### Step 1: Create Campaign

```bash
curl -X POST http://localhost:8002/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Optimize Sorting Algorithm",
    "description": "Evolve a high-performance sorting function",
    "config": {
      "max_rounds": 5,
      "variants_per_round": 10,
      "evaluators": ["unit_test", "benchmark", "llm_judge"],
      "base_code": "def sort_numbers(arr):\n    return sorted(arr)",
      "optimization_goal": "speed",
      "constraints": ["pure_python", "no_external_libs"]
    }
  }'
```

### Step 2: Start Campaign

```bash
# Get campaign ID from previous response
CAMPAIGN_ID="<campaign-id-here>"

# Start the evolution
curl -X POST http://localhost:8002/api/campaigns/$CAMPAIGN_ID/start
```

### Step 3: Execute First Round

```bash
# Trigger Round 1 execution
curl -X POST http://localhost:8002/api/campaigns/$CAMPAIGN_ID/rounds/1/execute
```

**What Happens:**

1. **Planning Agent** analyzes the base code and creates evolution strategy
2. **Variant Generator** creates 10 different sorting implementations:
   - Quick sort variations
   - Merge sort optimizations
   - Hybrid approaches
   - Tim sort implementations
   - Custom algorithms

3. **Evaluator Agents** test each variant:
   - **Unit Tests**: Correctness on various inputs
   - **Benchmarks**: Speed tests with different data sizes
   - **LLM Judge**: Code quality, readability, elegance

4. **Selection Policy** chooses top 5 performers based on combined scores

5. **Reporter** generates analysis:
   - Performance comparisons
   - Evolution insights
   - Improvement metrics

### Step 4: View Results

```bash
# Get round results
curl http://localhost:8002/api/campaigns/$CAMPAIGN_ID/rounds/1

# View generated variants
curl http://localhost:8002/api/campaigns/$CAMPAIGN_ID/rounds/1/variants

# Read evolution report
curl http://localhost:8002/api/reports?campaign_id=$CAMPAIGN_ID
```

### Step 5: Continue Evolution

```bash
# Execute Round 2 (uses Round 1 winners as parents)
curl -X POST http://localhost:8002/api/campaigns/$CAMPAIGN_ID/rounds/2/execute

# Round 2 variants are mutations/crossovers of Round 1 winners
```

---

## Real-World Use Cases

### 1. API Endpoint Optimization
```json
{
  "name": "Optimize User API",
  "config": {
    "base_code": "# Current slow API endpoint",
    "optimization_goal": "latency_and_throughput",
    "evaluators": ["load_test", "unit_test", "llm_judge"]
  }
}
```

### 2. Algorithm Discovery
```json
{
  "name": "Find Better Path Algorithm",
  "config": {
    "base_code": "# Basic A* pathfinding",
    "optimization_goal": "speed_and_memory",
    "evaluators": ["benchmark", "memory_profiler", "llm_judge"]
  }
}
```

### 3. Prompt Engineering Evolution
```json
{
  "name": "Optimize LLM Prompts",
  "config": {
    "base_code": "# Initial prompt template",
    "optimization_goal": "accuracy_and_tokens",
    "evaluators": ["llm_judge", "cost_analyzer", "quality_scorer"]
  }
}
```

### 4. Data Processing Pipeline
```json
{
  "name": "ETL Pipeline Optimization",
  "config": {
    "base_code": "# Current ETL code",
    "optimization_goal": "throughput",
    "evaluators": ["benchmark", "unit_test", "integration_test"]
  }
}
```

---

## Viewing Evolution in UI

### Campaign Dashboard
1. Go to http://localhost:3000/campaigns
2. See all active evolution experiments
3. Click on campaign to view details

### Round-by-Round Progress
1. View each generation's results
2. See variant scores and rankings
3. Track performance improvements

### Lineage Visualization
1. Navigate to `/campaigns/{id}/lineage`
2. See evolutionary tree
3. Identify successful mutation patterns
4. Track performance trends across generations

### Generated Reports
1. Access AI-generated insights
2. Read performance analysis
3. View code quality assessments
4. Get optimization recommendations

---

## Evolution Metrics

Each campaign tracks:

- **Generations Completed**: Number of evolution rounds
- **Total Variants Created**: All implementations generated
- **Average Score Improvement**: Performance gains over baseline
- **Best Variant**: Highest-scoring implementation
- **Success Rate**: Percentage of functional variants
- **Convergence**: Whether evolution is stabilizing

---

## Advanced Features

### Custom Evaluators

Create custom evaluation criteria:

```python
# backend/src/evo_ai/evaluators/custom_evaluator.py

class CustomSecurityEvaluator(BaseEvaluator):
    async def evaluate(self, variant: Variant) -> EvaluationResult:
        # Check for security vulnerabilities
        # SQL injection detection
        # XSS vulnerability scanning
        return EvaluationResult(
            score=security_score,
            metrics={"vulnerabilities": [], "safety_level": "high"}
        )
```

### Custom Selection Policies

Define how variants are selected:

```python
# backend/src/evo_ai/policies/custom_policy.py

class DiversitySelectionPolicy(SelectionPolicy):
    def select(self, variants: List[Variant]) -> List[Variant]:
        # Select top performers + diverse alternatives
        # Avoid local optima
        # Maintain genetic diversity
        return selected_variants
```

### Multi-Objective Optimization

Optimize for multiple goals:

```json
{
  "config": {
    "optimization_goals": {
      "speed": 0.5,      // 50% weight
      "memory": 0.3,     // 30% weight
      "readability": 0.2 // 20% weight
    }
  }
}
```

---

## Deployment Guide

### Deploy to Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy backend (any cloud provider)
# - Railway
# - Render
# - Google Cloud Run
# - AWS ECS

# Deploy frontend to Vercel
vercel --prod

# Set environment variables in Vercel:
# NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### Environment Variables for Production

```bash
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/evo_ai
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
ENVIRONMENT=production
CORS_ORIGINS=https://your-frontend.vercel.app

# Frontend
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NODE_ENV=production
```

---

## Git Workflow

### Initial Commit

```bash
git init
git add .
git commit -m "Initial commit: Evo-AI Platform - Multi-agent evolutionary experimentation system"
git branch -M main
git remote add origin https://github.com/yourusername/evo-ai.git
git push -u origin main
```

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel --prod

# Link to git repository for auto-deployments
vercel git connect
```

---

## Monitoring Evolution

### Watch Live Execution

```bash
# Terminal 1: Backend logs
docker-compose logs -f backend

# Terminal 2: Database queries
docker-compose exec postgres psql -U evoai -d evo_ai

# Terminal 3: Redis monitoring
docker-compose exec redis redis-cli MONITOR
```

### View Execution Traces

```bash
# Get execution trace
curl http://localhost:8002/api/traces/{trace_id}

# View agent decisions
curl http://localhost:8002/api/agent-decisions?campaign_id=$CAMPAIGN_ID
```

---

## The Real Value

**Traditional Approach:**
- Manual code optimization
- Human trial and error
- Limited exploration
- Slow iteration

**With Evo-AI:**
- Automated variant generation
- Parallel evaluation
- Systematic exploration
- Rapid evolution across generations
- AI-driven insights
- Continuous improvement

**Result:** Find optimal solutions faster than manual development, discover novel approaches humans might miss, and systematically improve code quality.

---

## Next Steps

1. **Run Demo**: Start Docker and execute first campaign
2. **Customize**: Adapt for your specific use case
3. **Scale**: Add more evaluators and optimization goals
4. **Deploy**: Move to production when ready
5. **Iterate**: Let AI evolve your code continuously

---

## Need Help?

- **Documentation**: Check `/docs` folder
- **API Reference**: http://localhost:8002/docs
- **Issues**: GitHub Issues
- **Examples**: `/examples` directory

**Start evolving your code today!**
