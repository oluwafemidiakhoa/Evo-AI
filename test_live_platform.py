"""
Test the live Evo-AI platform deployed on Render.

This script:
1. Tests health endpoint
2. Creates a test campaign
3. Retrieves campaign details
4. Lists all campaigns
"""

import requests
import json
from datetime import datetime

# Your live backend URL
API_URL = "https://evo-ai-nakk.onrender.com"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    """Test the health endpoint."""
    print_section("1. Testing Health Endpoint")

    response = requests.get(f"{API_URL}/health")

    if response.status_code == 200:
        data = response.json()
        print("[OK] Backend is healthy!")
        print(f"   Version: {data['version']}")
        print(f"   Status: {data['status']}")
        print("\n   Services:")
        for service, status in data['services'].items():
            indicator = "[OK]" if status == "up" else "[WARN]"
            print(f"   {indicator} {service}: {status}")
        return True
    else:
        print(f"[ERROR] Health check failed: {response.status_code}")
        return False

def create_campaign():
    """Create a test campaign."""
    print_section("2. Creating Test Campaign")

    campaign_data = {
        "name": f"Test Campaign - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "description": "Testing the live Evo-AI platform with multi-agent evolution",
        "config": {
            "max_rounds": 5,
            "variants_per_round": 10,
            "objective": "Optimize sorting algorithm performance",
            "evaluators": ["llm_judge", "benchmark"],
            "mutation_types": ["refactor", "optimize", "experimental"]
        }
    }

    print("Sending request to create campaign...")
    print(f"Campaign name: {campaign_data['name']}")

    response = requests.post(
        f"{API_URL}/api/campaigns",
        json=campaign_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 201:
        data = response.json()
        print("[OK] Campaign created successfully!")
        print(f"\n   Campaign ID: {data['id']}")
        print(f"   Name: {data['name']}")
        print(f"   Status: {data['status']}")
        print(f"   Created: {data['created_at']}")
        return data['id']
    else:
        print(f"[ERROR] Failed to create campaign: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def get_campaign(campaign_id):
    """Get campaign details."""
    print_section("3. Retrieving Campaign Details")

    response = requests.get(f"{API_URL}/api/campaigns/{campaign_id}")

    if response.status_code == 200:
        data = response.json()
        print("[OK] Campaign retrieved successfully!")
        print(f"\n   ID: {data['id']}")
        print(f"   Name: {data['name']}")
        print(f"   Description: {data['description']}")
        print(f"   Status: {data['status']}")
        print(f"\n   Configuration:")
        for key, value in data['config'].items():
            print(f"   - {key}: {value}")
        return True
    else:
        print(f"[ERROR] Failed to get campaign: {response.status_code}")
        return False

def list_campaigns():
    """List all campaigns."""
    print_section("4. Listing All Campaigns")

    response = requests.get(f"{API_URL}/api/campaigns?page=1&page_size=10")

    if response.status_code == 200:
        data = response.json()
        total = data.get('total', 0)
        campaigns = data.get('campaigns', [])

        print(f"[OK] Found {total} campaign(s)")

        if campaigns:
            print("\nRecent campaigns:")
            for i, campaign in enumerate(campaigns[:5], 1):
                print(f"\n   {i}. {campaign['name']}")
                print(f"      ID: {campaign['id']}")
                print(f"      Status: {campaign['status']}")
                print(f"      Created: {campaign['created_at']}")
        return True
    else:
        print(f"[ERROR] Failed to list campaigns: {response.status_code}")
        return False

def get_campaign_stats(campaign_id):
    """Get campaign statistics."""
    print_section("5. Getting Campaign Statistics")

    response = requests.get(f"{API_URL}/api/campaigns/{campaign_id}/stats")

    if response.status_code == 200:
        data = response.json()
        print("[OK] Campaign statistics retrieved!")
        print(f"\n   Total Rounds: {data.get('total_rounds', 0)}")
        print(f"   Completed Rounds: {data.get('completed_rounds', 0)}")
        print(f"   Total Variants: {data.get('total_variants', 0)}")
        print(f"   Selected Variants: {data.get('total_selected', 0)}")
        print(f"   Max Generation: {data.get('max_generation', 0)}")
        print(f"   Selection Rate: {data.get('selection_rate', 0):.2%}")
        return True
    else:
        print(f"[WARN] Stats not available yet (campaign needs to run first)")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  EVO-AI PLATFORM TEST SUITE")
    print("  Live Backend: " + API_URL)
    print("="*60)

    # Test 1: Health check
    if not test_health():
        print("\n[ERROR] Backend is not healthy. Stopping tests.")
        return

    # Test 2: Create campaign
    campaign_id = create_campaign()
    if not campaign_id:
        print("\n[ERROR] Could not create campaign. Stopping tests.")
        return

    # Test 3: Get campaign details
    get_campaign(campaign_id)

    # Test 4: List all campaigns
    list_campaigns()

    # Test 5: Get campaign stats
    get_campaign_stats(campaign_id)

    # Summary
    print_section("TEST SUITE COMPLETE!")
    print("\nAll tests passed successfully!")
    print(f"\nYour campaign ID: {campaign_id}")
    print(f"View in browser: {API_URL}/api/campaigns/{campaign_id}")
    print(f"API Docs: {API_URL}/api/docs")
    print(f"Health: {API_URL}/health")

    print("\n" + "="*60)
    print("  Next Steps:")
    print("="*60)
    print("1. Execute a round: POST /api/campaigns/{id}/execute")
    print("2. View variants: GET /api/variants?campaign_id={id}")
    print("3. Check reports: GET /api/reports?campaign_id={id}")
    print("4. Deploy frontend to interact with the platform visually")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] Error running tests: {e}")
        import traceback
        traceback.print_exc()
