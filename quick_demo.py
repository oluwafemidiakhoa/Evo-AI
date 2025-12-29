"""
Quick Demo: See Evo-AI Evolution in 2 Minutes

This creates a simple campaign and shows you what evolution looks like.
"""

import httpx
import json
import time
from datetime import datetime

API_URL = "http://localhost:8002"


def print_header(title):
    """Print a nice header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_step(step, desc):
    """Print a step."""
    print(f"Step {step}: {desc}")
    print("-" * 80)


async def main():
    """Run the quick demo."""

    print_header("EVO-AI QUICK DEMO - SEE EVOLUTION IN ACTION")

    async with httpx.AsyncClient(timeout=60.0) as client:

        # Step 1: Create Campaign
        print_step(1, "Creating Evolution Campaign")

        campaign_data = {
            "name": f"Quick Demo - {datetime.now().strftime('%H:%M:%S')}",
            "description": "Simple function optimization demo",
            "config": {
                "max_rounds": 3,
                "variants_per_round": 5,
                "evaluators": ["llm_judge"],
                "base_code": """def calculate_sum(numbers):
    # Simple but could be better
    total = 0
    for num in numbers:
        total = total + num
    return total""",
                "optimization_goal": "Make this more pythonic and efficient"
            }
        }

        response = await client.post(f"{API_URL}/api/campaigns", json=campaign_data)
        campaign = response.json()
        campaign_id = campaign["id"]

        print(f"✓ Campaign created!")
        print(f"  Name: {campaign['name']}")
        print(f"  ID: {campaign_id}")
        print(f"  Status: {campaign['status']}")
        print()

        # Step 2: View in Browser
        print_step(2, "View in Browser")
        print(f"Open this URL to watch live:")
        print(f"  http://localhost:3000/campaigns/{campaign_id}")
        print()

        # Step 3: Start Campaign
        print_step(3, "Starting Campaign")
        response = await client.post(f"{API_URL}/api/campaigns/{campaign_id}/start")
        campaign = response.json()
        print(f"✓ Campaign started!")
        print(f"  Status: {campaign['status']}")
        print()

        # Step 4: Show what the platform does
        print_step(4, "What Happens During Evolution")
        print("""
When you execute a round, Evo-AI:

1. 🧠 PLANNING AGENT analyzes the code and creates evolution strategy
2. 🔨 VARIANT AGENT generates 5 different implementations:
   - Using list comprehension
   - Using sum() built-in
   - Using reduce()
   - Using numpy
   - Custom optimizations

3. 📊 SCORER AGENT evaluates each variant:
   - Code quality
   - Readability
   - Performance characteristics
   - Pythonic-ness

4. 🏆 POLICY AGENT selects top performers

5. 📝 REPORTER AGENT generates insights

This all happens automatically with AI agents!
        """)

        # Step 5: Next Steps
        print_step(5, "Try It Yourself!")
        print("""
NOW DO THIS:

1. Go to: http://localhost:3000/campaigns/{campaign_id}

2. Click "Execute Round 1" button

3. Watch as:
   - Variants are generated (takes 30-60 seconds)
   - Each is evaluated
   - Results appear in real-time

4. After Round 1 completes:
   - View the 5 variants generated
   - See their scores
   - Click "Execute Round 2" to evolve winners

5. Compare Round 1 vs Round 2 variants to see evolution!

        """.format(campaign_id=campaign_id))

        print_header("DEMO READY!")
        print(f"Campaign URL: http://localhost:3000/campaigns/{campaign_id}")
        print(f"Campaign ID: {campaign_id}")
        print()
        print("Go execute rounds and watch AI evolve your code!")
        print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
