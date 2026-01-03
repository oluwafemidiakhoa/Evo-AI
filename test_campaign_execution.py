"""
Test script to execute a campaign and see full platform functionality.

Usage:
    python test_campaign_execution.py <campaign_id>

Example:
    python test_campaign_execution.py 2a44ae66-8df8-4c01-8fe9-6b3fe77eb369
"""

import httpx
import sys
import json
from uuid import UUID

# Your deployment URLs
BACKEND_URL = "https://evo-ai-nakk.onrender.com"
CAMPAIGN_ID = "2a44ae66-8df8-4c01-8fe9-6b3fe77eb369"  # LeetCode Two Sum Evolution


async def start_campaign(campaign_id: str):
    """Start a campaign (change status to ACTIVE)."""
    print(f">> Starting campaign {campaign_id}...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/campaigns/{campaign_id}/start",
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Campaign started! Status: {data['status']}")
            return data
        else:
            print(f"❌ Failed to start campaign: {response.status_code}")
            print(response.text)
            return None


async def execute_campaign(campaign_id: str, max_rounds: int = 2):
    """
    Execute a campaign and stream results.

    This triggers the full AI agent pipeline:
    1. PlannerAgent - Plans the round strategy
    2. VariantAgent - Generates code variants
    3. ScorerAgent - Evaluates each variant
    4. PolicyAgent - Selects best variants
    5. ReporterAgent - Creates summary
    """
    print(f"\n🎯 Executing campaign with {max_rounds} rounds...")
    print("This will:")
    print("  1. Run PlannerAgent to create strategy")
    print("  2. Generate code variants with VariantAgent")
    print("  3. Score variants with ScorerAgent")
    print("  4. Select best with PolicyAgent")
    print("  5. Create reports with ReporterAgent\n")

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{BACKEND_URL}/api/campaigns/{campaign_id}/execute",
            params={"max_rounds": max_rounds},
            timeout=300.0  # 5 minutes
        ) as response:
            print(f"📡 Streaming execution (status {response.status_code})...\n")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    try:
                        event_data = json.loads(data)
                        print(f"📊 {json.dumps(event_data, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"📝 {data}")
                elif line.startswith("event: "):
                    event_type = line[7:]
                    print(f"\n🎬 Event: {event_type}")


async def get_campaign_stats(campaign_id: str):
    """Get campaign statistics after execution."""
    print(f"\n📈 Getting campaign stats...")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/campaigns/{campaign_id}/stats",
            timeout=30.0
        )

        if response.status_code == 200:
            stats = response.json()
            print("\n✨ Campaign Statistics:")
            print(f"  Total Rounds: {stats['total_rounds']}")
            print(f"  Completed Rounds: {stats['completed_rounds']}")
            print(f"  Total Variants: {stats['total_variants']}")
            print(f"  Selected Variants: {stats['total_selected']}")
            print(f"  Max Generation: {stats['max_generation']}")
            print(f"  Selection Rate: {stats['selection_rate']:.2%}")
            return stats
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            return None


async def main():
    """Main execution flow."""
    # Get campaign ID from command line or use default
    campaign_id = sys.argv[1] if len(sys.argv) > 1 else CAMPAIGN_ID

    print("="*60)
    print("🤖 EVO-AI PLATFORM TEST")
    print("="*60)
    print(f"Campaign ID: {campaign_id}")
    print(f"Backend: {BACKEND_URL}\n")

    # Step 1: Start campaign
    campaign = await start_campaign(campaign_id)
    if not campaign:
        return

    # Step 2: Execute campaign (run evolution)
    await execute_campaign(campaign_id, max_rounds=2)

    # Step 3: Get final stats
    await get_campaign_stats(campaign_id)

    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)
    print(f"\n🌐 View results at:")
    print(f"   Frontend: https://evo-ai-oluwafemi-scufield-oluwafemi-s-projects.vercel.app/campaigns/{campaign_id}")
    print(f"   API Docs: {BACKEND_URL}/docs")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
