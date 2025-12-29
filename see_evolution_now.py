"""
SEE EVOLUTION HAPPEN NOW!

This will actually generate variants and show you AI in action.
"""

import requests
import json
import time

API = "http://localhost:8002"

print("=" * 80)
print("  WATCH AI EVOLVE CODE IN REAL-TIME")
print("=" * 80)
print()

# Step 1: Create simple campaign
print("Step 1: Creating campaign...")
campaign = requests.post(f"{API}/api/campaigns", json={
    "name": "LIVE EVOLUTION DEMO",
    "description": "Watch AI improve this code right now",
    "config": {
        "max_rounds": 2,
        "variants_per_round": 3,  # Small number for quick demo
        "evaluators": ["llm_judge"]
    }
}).json()

campaign_id = campaign["id"]
print(f"[OK] Campaign created: {campaign_id[:8]}...")
print()

# Step 2: Start it
print("Step 2: Starting campaign...")
requests.post(f"{API}/api/campaigns/{campaign_id}/start")
print("[OK] Campaign started")
print()

# Step 3: Execute Round 1 - THIS IS WHERE EVOLUTION HAPPENS
print("Step 3: Executing Round 1 - AI AGENTS WORKING NOW...")
print("(This takes 30-90 seconds as LLMs generate and evaluate code)")
print()
print("What's happening:")
print("  [*] PlannerAgent - Analyzing and creating strategy...")
print("  [*] VariantAgent - Generating 3 code variants...")
print("  [*] ScorerAgent - Evaluating each variant...")
print("  [*] PolicyAgent - Selecting winners...")
print("  [*] ReporterAgent - Creating insights...")
print()

try:
    result = requests.post(
        f"{API}/api/campaigns/{campaign_id}/rounds/1/execute",
        timeout=120  # 2 minutes
    ).json()

    print("=" * 80)
    print("  [SUCCESS] ROUND 1 COMPLETE - EVOLUTION HAPPENED!")
    print("=" * 80)
    print()
    print(f"Variants Generated: {result.get('variants_generated', 'N/A')}")
    print(f"Variants Evaluated: {result.get('variants_evaluated', 'N/A')}")
    print(f"Variants Selected: {result.get('variants_selected', 'N/A')}")
    print()

    # Get the actual variants
    print("Generated Variants:")
    print("-" * 80)

    variants = requests.get(f"{API}/api/campaigns/{campaign_id}/rounds/1/variants").json()

    for i, variant in enumerate(variants[:3], 1):
        print(f"\nVariant {i}:")
        print(f"  Score: {variant.get('score', 'N/A')}")
        print(f"  Selected: {'[YES]' if variant.get('is_selected') else '[No]'}")
        if 'code' in variant:
            code_preview = variant['code'][:200]
            print(f"  Code: {code_preview}...")

    print()
    print("=" * 80)
    print("  THIS IS WHAT EVO-AI DOES!")
    print("=" * 80)
    print()
    print("Instead of you manually writing 3 implementations,")
    print("AI agents generated, tested, and ranked them automatically.")
    print()
    print(f"View full results:")
    print(f"  http://localhost:3000/campaigns/{campaign_id}")
    print()

except requests.exceptions.Timeout:
    print("⏰ Request timed out - evolution takes time!")
    print("   Check the UI to see progress:")
    print(f"   http://localhost:3000/campaigns/{campaign_id}")

except Exception as e:
    print(f"Error: {e}")
    print()
    print("Check backend logs for details:")
    print("The agents might be working but taking longer than expected.")
    print(f"View campaign: http://localhost:3000/campaigns/{campaign_id}")
