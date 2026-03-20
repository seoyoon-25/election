"""
Background task scheduler using APScheduler.

Handles periodic background jobs like:
- Expiring stale approval requests
- Cleaning up old token blacklist entries
- Other maintenance tasks
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.approval import ApprovalRequest, ApprovalRequestStep, ApprovalStatus

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """
    Singleton scheduler for background tasks.

    Uses APScheduler's AsyncIOScheduler to run async jobs.
    """

    _instance: Optional["BackgroundScheduler"] = None
    _scheduler: Optional[AsyncIOScheduler] = None

    def __new__(cls) -> "BackgroundScheduler":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def scheduler(self) -> AsyncIOScheduler:
        """Get or create the scheduler instance."""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(
                timezone="UTC",
                job_defaults={
                    "coalesce": True,  # Combine missed runs
                    "max_instances": 1,  # Only one instance of each job
                    "misfire_grace_time": 60,  # 60 seconds grace period
                }
            )
        return self._scheduler

    def start(self) -> None:
        """Start the scheduler and register all jobs."""
        if self.scheduler.running:
            logger.warning("Scheduler is already running")
            return

        # Register jobs
        self._register_jobs()

        # Start the scheduler
        self.scheduler.start()
        logger.info("Background scheduler started")

    def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=True)
            logger.info("Background scheduler shut down")

    def _register_jobs(self) -> None:
        """Register all background jobs."""
        # Expire approval requests - run every 5 minutes
        self.scheduler.add_job(
            expire_approval_requests,
            trigger=IntervalTrigger(minutes=5),
            id="expire_approval_requests",
            name="Expire stale approval requests",
            replace_existing=True,
        )
        logger.info("Registered job: expire_approval_requests (every 5 minutes)")

        # Clean up old blacklisted tokens - run every hour
        # Note: Redis handles TTL expiry automatically, but this ensures cleanup
        self.scheduler.add_job(
            cleanup_expired_blacklist_tokens,
            trigger=IntervalTrigger(hours=1),
            id="cleanup_expired_blacklist_tokens",
            name="Cleanup expired blacklist tokens",
            replace_existing=True,
        )
        logger.info("Registered job: cleanup_expired_blacklist_tokens (every hour)")


# =============================================================================
# Background Jobs
# =============================================================================


async def expire_approval_requests() -> None:
    """
    Mark expired approval requests as EXPIRED.

    Finds all PENDING approval requests where expires_at < now()
    and updates their status to EXPIRED.
    """
    logger.debug("Running expire_approval_requests job")

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)

            # Update expired requests
            result = await db.execute(
                update(ApprovalRequest)
                .where(
                    and_(
                        ApprovalRequest.status == ApprovalStatus.PENDING,
                        ApprovalRequest.expires_at.isnot(None),
                        ApprovalRequest.expires_at < now,
                    )
                )
                .values(
                    status=ApprovalStatus.EXPIRED,
                    completed_at=now,
                )
                .returning(ApprovalRequest.id)
            )

            expired_ids = [row[0] for row in result.fetchall()]

            if expired_ids:
                # Also mark pending steps as expired
                await db.execute(
                    update(ApprovalRequestStep)
                    .where(
                        and_(
                            ApprovalRequestStep.request_id.in_(expired_ids),
                            ApprovalRequestStep.status == ApprovalStatus.PENDING,
                        )
                    )
                    .values(status=ApprovalStatus.EXPIRED)
                )

                await db.commit()
                logger.info(f"Expired {len(expired_ids)} approval requests: {expired_ids}")
            else:
                logger.debug("No approval requests to expire")

        except Exception as e:
            logger.error(f"Error expiring approval requests: {e}")
            await db.rollback()
            raise


async def cleanup_expired_blacklist_tokens() -> None:
    """
    Cleanup task for token blacklist.

    Redis handles TTL expiry automatically, so this is mostly
    a no-op that logs stats. Can be extended for custom cleanup logic.
    """
    logger.debug("Running cleanup_expired_blacklist_tokens job")

    try:
        from app.core.redis import RedisClient

        redis = await RedisClient.get_client()
        if redis is None:
            logger.warning("Redis not available, skipping blacklist cleanup")
            return

        # Get count of blacklisted tokens (keys matching pattern)
        # Note: KEYS command is expensive in production; consider SCAN for large datasets
        pattern = "token_blacklist:*"
        cursor = 0
        count = 0

        # Use SCAN for better performance
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            count += len(keys)
            if cursor == 0:
                break

        logger.debug(f"Current blacklisted tokens: {count}")

    except Exception as e:
        logger.error(f"Error in blacklist cleanup: {e}")


# =============================================================================
# Module-level scheduler instance
# =============================================================================

scheduler = BackgroundScheduler()


def get_scheduler() -> BackgroundScheduler:
    """Get the global scheduler instance."""
    return scheduler
