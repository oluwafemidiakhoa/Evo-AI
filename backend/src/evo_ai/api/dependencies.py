"""FastAPI dependencies for dependency injection."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from evo_ai.agents.implementations.orchestrator import AgentOrchestrator
from evo_ai.infrastructure.database.connection import get_session
from evo_ai.mcp.registry import mcp_registry


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.

    Usage:
        @app.get("/...")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with get_session() as session:
        yield session


def get_orchestrator() -> AgentOrchestrator:
    """
    Get agent orchestrator dependency.

    Usage:
        @app.post("/...")
        async def endpoint(orchestrator: AgentOrchestrator = Depends(get_orchestrator)):
            ...
    """
    return AgentOrchestrator(mcp_registry)
