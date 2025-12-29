"""Test asyncpg connection directly"""
import asyncio
import asyncpg

async def test():
    print("Testing direct asyncpg connection...")

    try:
        # Try without SSL
        print("\n1. Trying with ssl='disable' (no SSL)...")
        conn = await asyncpg.connect(
            user='evo_user',
            password='evo_password',
            database='evo_ai',
            host='localhost',
            port=5432,
            ssl='disable'
        )
        result = await conn.fetchval('SELECT 1')
        print(f"   [SUCCESS] Result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"   [FAILED] {type(e).__name__}: {e}")

    try:
        # Try with ssl=False
        print("\n2. Trying with ssl=False...")
        conn = await asyncpg.connect(
            user='evo_user',
            password='evo_password',
            database='evo_ai',
            host='localhost',
            port=5432,
            ssl=False
        )
        result = await conn.fetchval('SELECT 1')
        print(f"   [SUCCESS] Result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"   [FAILED] {type(e).__name__}: {e}")

    try:
        # Try with no ssl parameter (default)
        print("\n3. Trying with NO SSL parameter (default behavior)...")
        conn = await asyncpg.connect(
            user='evo_user',
            password='evo_password',
            database='evo_ai',
            host='localhost',
            port=5432
        )
        result = await conn.fetchval('SELECT 1')
        print(f"   [SUCCESS] Result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"   [FAILED] {type(e).__name__}: {e}")

    print("\n[ERROR] All connection attempts failed!")
    return False

if __name__ == "__main__":
    asyncio.run(test())
