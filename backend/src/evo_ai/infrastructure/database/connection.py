"""Database connection management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from evo_ai.config import settings


def prepare_database_url(url: str) -> tuple[str, dict]:
    """
    Prepare database URL for asyncpg connection.

    Removes ALL query parameters and handles SSL via connect_args instead.
    asyncpg doesn't support sslmode, channel_binding, or other PostgreSQL URL params.
    """
    # Convert postgresql:// to postgresql+asyncpg://
    url = url.replace("postgresql://", "postgresql+asyncpg://")

    # Parse URL
    parsed = urlparse(url)

    # Check if SSL is needed based on the original query params or hostname
    use_ssl = False

    # Check query params for SSL requirement
    if parsed.query:
        query_params = parse_qs(parsed.query)
        ssl_mode = query_params.get('sslmode', [''])[0]
        if ssl_mode in ('require', 'verify-ca', 'verify-full'):
            use_ssl = True

    # Cloud providers always require SSL
    if parsed.hostname and any(host in parsed.hostname for host in ['neon.tech', 'rds.amazonaws.com', 'supabase.co']):
        use_ssl = True

    # CRITICAL: Remove ALL query parameters - asyncpg doesn't support any of them
    # We handle SSL via connect_args instead
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        '',  # params
        '',  # query - EMPTY to remove all parameters
        ''   # fragment
    ))

    # Prepare connect_args based on SSL requirement
    connect_args = {}
    if use_ssl:
        # Enable SSL for cloud databases (Neon, RDS, etc.)
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE  # Required for Neon
        connect_args['ssl'] = ssl_context
    else:
        # Disable SSL for local development
        connect_args['ssl'] = False

    return clean_url, connect_args


# Prepare database URL and connection arguments
database_url, connect_args = prepare_database_url(settings.database_url)

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    connect_args=connect_args,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """
    Initialize database schema.

    NOTE: In production, use Alembic migrations instead.
    This is mainly for development/testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session (async context manager).

    Usage:
        async with get_session() as session:
            result = await session.execute(select(CampaignDB))
            campaigns = result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
