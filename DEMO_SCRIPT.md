# 2-Minute Demo Script for Evo-AI Platform

## What You'll Show (WOW Moments)

### Scene 1: The Problem (15 seconds)
"Ever wished AI could automatically optimize your code? Watch this."

### Scene 2: Create a Campaign (20 seconds)
**Show:** Creating a campaign via API or frontend
**Say:** "I'm asking the AI to optimize a sorting algorithm. It'll generate 10 variants per round over 3 generations."

**Visual:**
```json
{
  "name": "Optimize Bubble Sort",
  "objective": "Find fastest sorting algorithm",
  "max_rounds": 3,
  "variants_per_round": 10
}
```

### Scene 3: Execute Evolution (30 seconds)
**Show:** Executing a round, watching agents work
**Say:** "5 AI agents are now collaborating:
- Planner designs the strategy
- Variant Generator creates mutations
- Scorer evaluates each one
- Policy Maker selects winners
- Reporter analyzes results"

**Visual:** Show the API response or frontend showing progress

### Scene 4: Results (30 seconds)
**Show:** The evolved variants, lineage tree, performance improvements
**Say:** "After 3 rounds, the AI discovered a hybrid algorithm that's 10x faster than the original. All tracked with full lineage for reproducibility."

**Visual:** Show the variant lineage, scores, selected variants

### Scene 5: Architecture (25 seconds)
**Show:** Quick architecture diagram or code
**Say:** "Built with FastAPI, PostgreSQL, Next.js. Full observability with OpenTelemetry. Production-ready with distributed tracing."

**Visual:** Show the clean architecture, agent code, or monitoring

### Ending (10 seconds)
**Say:** "Check out the live API and GitHub repo - links in description!"
**Visual:** Show URLs on screen

## How to Record

**Tools:**
- OBS Studio (free): https://obsproject.com/
- Loom (easiest): https://loom.com/
- QuickTime (Mac)
- Windows Game Bar (Win + G)

**Steps:**
1. Start `docker-compose up` locally
2. Open frontend at localhost:3000
3. Open API docs at localhost:8000/api/docs
4. Record your screen following the script above
5. Upload to YouTube/Twitter
6. Share!

## What to Capture

1. **Frontend Dashboard** - Show campaigns list, stats
2. **Create Campaign Form** - Fill it out live
3. **Execute Round** - Click button, show progress
4. **Variant Results** - Show lineage tree, scores
5. **Code View** - Show one of the generated variants
6. **Architecture** - Quick code walkthrough

## Make It Visual

Add text overlays:
- "5 AI Agents Collaborating" when showing execution
- "10x Performance Improvement" when showing results
- "Production-Ready Architecture" when showing code
- URLs at the end

## Background Music (Optional)

Use royalty-free music from:
- YouTube Audio Library
- Epidemic Sound
- Uppbeat

Keep it upbeat and tech-focused!
