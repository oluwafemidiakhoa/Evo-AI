import asyncio
from sqlalchemy import text
from evo_ai.infrastructure.database.connection import get_async_session

async def check_enum():
    async with get_async_session() as session:
        result = await session.execute(text("SELECT unnest(enum_range(NULL::campaignstatusenum))"))
        print("Campaign status enum values:")
        for row in result:
            print(f"  - {row[0]}")

if __name__ == "__main__":
    asyncio.run(check_enum())
