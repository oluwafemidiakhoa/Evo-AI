"""Initialize database tables."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from evo_ai.infrastructure.database.connection import init_db


async def main():
    """Create all database tables."""
    print("Creating database tables...")
    try:
        await init_db()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
