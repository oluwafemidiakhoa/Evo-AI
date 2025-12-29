"""Test database connection"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test_connection():
    print("Testing database connection...")

    # Try without SSL
    url = "postgresql+asyncpg://evo_user:evo_password@localhost:5432/evo_ai?sslmode=disable"
    print(f"Connection string: {url}")

    try:
        engine = create_async_engine(url, echo=True)
        async with engine.connect() as conn:
            result = await conn.execute("SELECT 1")
            print("\n[SUCCESS] DATABASE CONNECTION WORKS!")
            return True
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")

        # Try with require
        print("\nTrying with ssl=require...")
        url2 = "postgresql+asyncpg://evo_user:evo_password@localhost:5432/evo_ai"
        try:
            engine2 = create_async_engine(url2, echo=False)
            async with engine2.connect() as conn:
                await conn.execute("SELECT 1")
                print("✓ Works without SSL parameter!")
                return True
        except Exception as e2:
            print(f"✗ Also failed: {e2}")
            return False

if __name__ == "__main__":
    asyncio.run(test_connection())
