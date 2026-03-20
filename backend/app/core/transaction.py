"""
Transaction management utilities.

Provides explicit transaction boundaries for multi-step operations
to ensure data consistency and proper rollback on failures.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for explicit transaction boundaries.

    Usage:
        async with transaction(db) as session:
            task = await create_task(session, ...)
            await add_assignee(session, task.id, ...)
            await add_history(session, task.id, ...)
        # Commits on success, rolls back on exception

    Args:
        db: SQLAlchemy async session

    Yields:
        The same session wrapped in a transaction

    Raises:
        Exception: Re-raises any exception after rollback
    """
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise


@asynccontextmanager
async def nested_transaction(db: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for nested transactions (savepoints).

    Use when you need a partial rollback within a larger transaction.

    Usage:
        async with transaction(db) as session:
            await step1(session)
            try:
                async with nested_transaction(session) as savepoint:
                    await risky_step(savepoint)
            except SomeError:
                # Only risky_step is rolled back
                pass
            await step3(session)

    Args:
        db: SQLAlchemy async session

    Yields:
        The same session with a savepoint

    Raises:
        Exception: Re-raises any exception after savepoint rollback
    """
    try:
        async with db.begin_nested():
            yield db
    except Exception:
        raise


class TransactionManager:
    """
    Helper class for managing transactions in services.

    Example usage in a service:
        class TaskService:
            def __init__(self, db: AsyncSession, ...):
                self.db = db
                self.tx = TransactionManager(db)

            async def create_task_with_assignees(self, ...):
                async with self.tx.atomic():
                    task = await self._create_task(...)
                    await self._add_assignees(task, ...)
                    await self._log_history(task, ...)
                return task
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    @asynccontextmanager
    async def atomic(self) -> AsyncGenerator[AsyncSession, None]:
        """Execute operations atomically (all or nothing)."""
        async with transaction(self.db) as session:
            yield session

    @asynccontextmanager
    async def savepoint(self) -> AsyncGenerator[AsyncSession, None]:
        """Create a savepoint for partial rollback."""
        async with nested_transaction(self.db) as session:
            yield session

    async def commit(self) -> None:
        """Explicitly commit the current transaction."""
        await self.db.commit()

    async def rollback(self) -> None:
        """Explicitly rollback the current transaction."""
        await self.db.rollback()

    async def flush(self) -> None:
        """Flush pending changes without committing."""
        await self.db.flush()
