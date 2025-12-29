# START SEEING EVOLUTION NOW!

## The Problem
Creating campaigns works, but you're not seeing **evolution** (variants being generated, evaluated, evolved).

## The Solution
Use **Docker** - it handles environment variables automatically.

---

## Quick Start (5 Minutes)

### Step 1: Stop Current Services

```cmd
# Kill backend/frontend if running
# Press Ctrl+C in their terminals
```

### Step 2: Start with Docker

```cmd
# Start full stack
docker-compose up -d

# Wait 30 seconds for startup
timeout /t 30

# Check status
docker-compose ps
```

### Step 3: Run Evolution Demo

```cmd
# This will ACTUALLY execute rounds and show AI agents working
python see_evolution_now.py
```

**OR** Open browser:
- http://localhost:3000
- Create campaign
- Click "Execute Round 1"
- **Watch AI agents generate and evaluate code!**

---

## What You'll See

When you click "Execute Round 1":

1. **PlannerAgent** analyzes the task (10-20 sec)
2. **VariantAgent** generates 3-5 code implementations (30-60 sec)
3. **ScorerAgent** evaluates each variant (20-40 sec)
4. **PolicyAgent** selects winners (5 sec)
5. **ReporterAgent** creates insights (10-20 sec)

**Total**: 1-2 minutes per round

You'll see:
- Different code implementations
- Performance scores
- Selection results
- AI-generated reports

---

## Alternative: Manual Setup (if Docker doesn't work)

If Docker isn't available:

1. **Set environment variables**:
   ```cmd
   # Windows PowerShell
   cd backend
   $env:ANTHROPIC_API_KEY="sk-ant-YOUR-KEY-HERE"
   $env:OPENAI_API_KEY="sk-YOUR-KEY-HERE"
   $env:DATABASE_URL="postgresql://evo_user:evo_password@localhost:5432/evo_ai"

   # Start backend
   venv\Scripts\python.exe -m uvicorn evo_ai.api.app:app --reload --port 8002
   ```

2. **In another terminal - Frontend**:
   ```cmd
   cd frontend
   npm run dev
   ```

3. **Run demo**:
   ```cmd
   python see_evolution_now.py
   ```

---

## Why Docker is Better

**Manual setup issues:**
- Environment variables not loaded ❌
- Services not connected ❌
- Complex configuration ❌

**Docker:**
- Everything configured ✅
- All services connected ✅
- One command to start ✅

---

## What Happens Next

After you run with Docker and execute a round:

```
Round 1 starts...
  [30 seconds] AI generates 5 code variants
  [40 seconds] Each variant is tested/evaluated
  [10 seconds] Best performers selected

Round 1 complete!
  View 5 different implementations
  See scores and rankings
  Read AI analysis

Execute Round 2...
  AI evolves the winners from Round 1
  Generates improved variants
  Selects even better solutions
```

**This is the evolution you want to see!**

---

## Ready?

```cmd
# 1. Start Docker
docker-compose up -d

# 2. Wait for startup (30 sec)

# 3. Run demo
python see_evolution_now.py

# OR open browser
http://localhost:3000
```

You'll see **REAL AI-POWERED CODE EVOLUTION**! 🚀
