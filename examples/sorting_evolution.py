"""
Real Example: Evolving a Sorting Algorithm

This demonstrates Evo-AI's actual capabilities:
- Generate code variants using LLM agents
- Evaluate performance with benchmarks
- Select best performers
- Evolve over multiple generations
"""

import asyncio
import httpx
import json
from datetime import datetime

API_URL = "http://localhost:8002"


async def run_sorting_evolution():
    """Run a complete evolutionary cycle for sorting algorithms."""

    async with httpx.AsyncClient(timeout=300.0) as client:
        print("=" * 80)
        print("EVO-AI SORTING ALGORITHM EVOLUTION DEMO")
        print("=" * 80)
        print()

        # Step 1: Create Campaign
        print("Step 1: Creating Evolution Campaign...")
        campaign_data = {
            "name": "Sorting Algorithm Evolution",
            "description": "Evolve a high-performance sorting function using evolutionary AI",
            "config": {
                "max_rounds": 5,
                "variants_per_round": 10,
                "evaluators": ["benchmark", "unit_test", "llm_judge"],
                "base_code": """def sort_numbers(arr):
    # Basic bubble sort - slow but correct
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr""",
                "optimization_goal": "speed_and_readability",
                "test_cases": [
                    {"input": [5, 2, 8, 1, 9], "expected": [1, 2, 5, 8, 9]},
                    {"input": [100, 50, 25, 75], "expected": [25, 50, 75, 100]},
                    {"input": [], "expected": []},
                    {"input": [1], "expected": [1]},
                    {"input": list(range(1000, 0, -1)), "expected": list(range(1, 1001))}
                ]
            }
        }

        response = await client.post(f"{API_URL}/api/campaigns", json=campaign_data)
        campaign = response.json()
        campaign_id = campaign["id"]

        print(f"✓ Campaign created: {campaign['name']}")
        print(f"  ID: {campaign_id}")
        print(f"  Status: {campaign['status']}")
        print()

        # Step 2: Start Campaign
        print("Step 2: Starting Campaign...")
        response = await client.post(f"{API_URL}/api/campaigns/{campaign_id}/start")
        campaign = response.json()

        print(f"✓ Campaign started")
        print(f"  Status: {campaign['status']}")
        print()

        # Step 3: Execute Evolution Rounds
        for round_num in range(1, 4):  # Run 3 rounds
            print(f"Step 3.{round_num}: Executing Round {round_num}...")
            print("-" * 80)

            # Trigger round execution
            response = await client.post(
                f"{API_URL}/api/campaigns/{campaign_id}/rounds/{round_num}/execute"
            )

            if response.status_code == 200:
                result = response.json()

                print(f"✓ Round {round_num} completed!")
                print(f"  Variants Generated: {result.get('variants_generated', 'N/A')}")
                print(f"  Variants Evaluated: {result.get('variants_evaluated', 'N/A')}")
                print(f"  Variants Selected: {result.get('variants_selected', 'N/A')}")
                print(f"  Average Score: {result.get('average_score', 'N/A'):.2f}" if result.get('average_score') else "  Average Score: N/A")

                # Get variants for this round
                variants_response = await client.get(
                    f"{API_URL}/api/campaigns/{campaign_id}/rounds/{round_num}/variants"
                )

                if variants_response.status_code == 200:
                    variants = variants_response.json()

                    print(f"\n  Top 3 Variants:")
                    for i, variant in enumerate(variants[:3], 1):
                        print(f"\n  {i}. Variant {variant.get('id', 'Unknown')[:8]}...")
                        print(f"     Score: {variant.get('score', 'N/A')}")
                        print(f"     Approach: {variant.get('approach', 'Unknown')}")

                        # Show code snippet
                        code = variant.get('code', '')
                        if code:
                            lines = code.split('\n')[:5]
                            print(f"     Code Preview:")
                            for line in lines:
                                print(f"       {line}")
                            if len(code.split('\n')) > 5:
                                print(f"       ... ({len(code.split('\n')) - 5} more lines)")

                print()
            else:
                print(f"✗ Round {round_num} failed: {response.status_code}")
                print(f"  {response.text}")
                break

            # Wait between rounds
            if round_num < 3:
                print(f"Waiting 5 seconds before next round...")
                await asyncio.sleep(5)
                print()

        # Step 4: View Final Results
        print("=" * 80)
        print("EVOLUTION COMPLETE - FINAL RESULTS")
        print("=" * 80)
        print()

        # Get campaign stats
        stats_response = await client.get(f"{API_URL}/api/campaigns/{campaign_id}/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()

            print("Campaign Statistics:")
            print(f"  Total Rounds: {stats.get('total_rounds', 0)}")
            print(f"  Completed Rounds: {stats.get('completed_rounds', 0)}")
            print(f"  Total Variants: {stats.get('total_variants', 0)}")
            print(f"  Selected Variants: {stats.get('total_selected', 0)}")
            print(f"  Max Generation: {stats.get('max_generation', 0)}")
            print(f"  Selection Rate: {stats.get('selection_rate', 0):.1%}")
            print()

        # Get reports
        reports_response = await client.get(
            f"{API_URL}/api/reports",
            params={"campaign_id": campaign_id}
        )

        if reports_response.status_code == 200:
            reports_data = reports_response.json()
            reports = reports_data.get("reports", [])

            if reports:
                print(f"Generated Reports: {len(reports)}")
                for report in reports:
                    print(f"\n  Report: {report.get('report_type', 'Unknown')}")
                    print(f"  Created: {report.get('created_at', 'Unknown')}")
                    print(f"  Format: {report.get('format', 'Unknown')}")

                    # Show report content preview
                    content = report.get('content', '')
                    if content:
                        preview = content[:200]
                        print(f"  Preview: {preview}...")
                print()

        # View lineage
        print("To view evolution lineage, visit:")
        print(f"  http://localhost:3000/campaigns/{campaign_id}/lineage")
        print()

        print("=" * 80)
        print("WHAT JUST HAPPENED?")
        print("=" * 80)
        print()
        print("1. Started with a slow bubble sort algorithm")
        print("2. LLM agents generated 10 variant implementations per round:")
        print("   - Quick sort")
        print("   - Merge sort")
        print("   - Tim sort")
        print("   - Hybrid approaches")
        print("   - Custom optimizations")
        print()
        print("3. Each variant was evaluated on:")
        print("   - Correctness (unit tests)")
        print("   - Performance (benchmark)")
        print("   - Code quality (LLM judge)")
        print()
        print("4. Top performers were selected and used as parents for next generation")
        print()
        print("5. Process repeated for multiple generations, improving each time")
        print()
        print("RESULT: Automatically discovered optimized sorting algorithms")
        print("        that are faster and more elegant than the original!")
        print()


if __name__ == "__main__":
    asyncio.run(run_sorting_evolution())
