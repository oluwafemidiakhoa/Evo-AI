"""Test campaign execution - no emojis for Windows console."""

import httpx
import sys
import json

BACKEND_URL = "https://evo-ai-nakk.onrender.com"
CAMPAIGN_ID = "2a44ae66-8df8-4c01-8fe9-6b3fe77eb369"  # LeetCode Two Sum Evolution


async def start_campaign(campaign_id: str):
    """Start a campaign."""
    print(f"\n[1/3] Starting campaign {campaign_id}...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/campaigns/{campaign_id}/start",
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS! Campaign status: {data['status']}")
            return data
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            return None


async def execute_campaign(campaign_id: str):
    """Execute campaign."""
    print(f"\n[2/3] Executing campaign (running 2 evolution rounds)...")
    print("This will run all 5 AI agents:")
    print("  - PlannerAgent: Creates round strategy")
    print("  - VariantAgent: Generates code variants")
    print("  - ScorerAgent: Evaluates variants")
    print("  - PolicyAgent: Selects best variants")
    print("  - ReporterAgent: Creates summary\n")

    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{BACKEND_URL}/api/campaigns/{campaign_id}/execute",
            params={"max_rounds": 2},
            timeout=300.0
        ) as response:
            print(f"Streaming execution (HTTP {response.status_code})...\n")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    print(f"  {line[6:]}")
                elif line.startswith("event: "):
                    print(f"\n[EVENT] {line[7:]}")


async def get_stats(campaign_id: str):
    """Get final stats."""
    print(f"\n[3/3] Getting campaign statistics...")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/campaigns/{campaign_id}/stats",
            timeout=30.0
        )

        if response.status_code == 200:
            stats = response.json()
            print("\n" + "="*50)
            print("CAMPAIGN RESULTS:")
            print("="*50)
            print(f"Total Rounds: {stats['total_rounds']}")
            print(f"Completed Rounds: {stats['completed_rounds']}")
            print(f"Total Variants: {stats['total_variants']}")
            print(f"Selected Variants: {stats['total_selected']}")
            print(f"Max Generation: {stats['max_generation']}")
            print(f"Selection Rate: {stats['selection_rate']:.1%}")
            print("="*50)
        else:
            print(f"FAILED: {response.status_code}")


async def main():
    campaign_id = sys.argv[1] if len(sys.argv) > 1 else CAMPAIGN_ID

    print("="*50)
    print("EVO-AI PLATFORM TEST")
    print("="*50)
    print(f"Campaign: {campaign_id}")
    print(f"Backend: {BACKEND_URL}")

    # Execute full flow
    campaign = await start_campaign(campaign_id)
    if campaign:
        await execute_campaign(campaign_id)
        await get_stats(campaign_id)

    print(f"\nView results: https://evo-ai-oluwafemi-scufield-oluwafemi-s-projects.vercel.app/campaigns/{campaign_id}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
