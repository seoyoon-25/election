"""
Database connection and session management.

Provides both async and sync database engines and sessions:
- Async for API request handling (FastAPI)
- Sync for background tasks and migrations (Alembic)
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.base import Base


# Async engine for FastAPI
async_engine = create_async_engine(
    settings.async_database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before use
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine for Alembic and background tasks
sync_engine = create_engine(
    settings.sync_database_url,
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

# Sync session factory
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.

    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Session:
    """
    Get a sync database session for background tasks.

    Usage:
        with get_sync_session() as session:
            ...
    """
    session = SyncSessionLocal()
    try:
        return session
    except Exception:
        session.rollback()
        raise


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for async database sessions.

    Usage:
        async with get_async_session_context() as session:
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class TenantContext:
    """
    Context manager for setting tenant (campaign) context.

    This sets the PostgreSQL session variable for Row-Level Security.
    """

    def __init__(self, session: AsyncSession, campaign_id: int):
        self.session = session
        self.campaign_id = campaign_id

    async def __aenter__(self):
        """Set the tenant context in PostgreSQL."""
        await self.session.execute(
            text(f"SET app.current_campaign_id = '{self.campaign_id}'")
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Reset the tenant context."""
        await self.session.execute(
            text("RESET app.current_campaign_id")
        )


async def set_tenant_context(session: AsyncSession, campaign_id: int) -> None:
    """
    Set tenant context for Row-Level Security.

    Call this after authenticating a user to enable RLS policies.
    """
    await session.execute(
        text(f"SET app.current_campaign_id = '{campaign_id}'")
    )


async def init_db() -> None:
    """
    Initialize database tables.

    Only use in development. In production, use Alembic migrations.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, checkfirst=True))


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()
