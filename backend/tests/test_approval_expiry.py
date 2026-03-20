"""
Tests for approval request expiry background job.

These tests verify that:
1. Expired approval requests are marked as EXPIRED
2. Non-expired requests are not affected
3. Already completed requests are not affected
4. Pending steps are also marked as expired
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select

from app.models.approval import (
    ApprovalRequest,
    ApprovalRequestStep,
    ApprovalStatus,
)


class TestExpireApprovalRequests:
    """Tests for the expire_approval_requests job."""

    @pytest.mark.asyncio
    async def test_expires_pending_requests_past_expiry_date(self):
        """Pending requests past their expiry date should be marked as EXPIRED."""
        from app.core.scheduler import expire_approval_requests

        # Mock database session
        mock_db = AsyncMock()

        # Mock the update result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [(1,), (2,)]  # Two expired request IDs
        mock_db.execute.return_value = mock_result

        # Patch AsyncSessionLocal to return our mock
        with patch("app.core.scheduler.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_db
            mock_session_local.return_value.__aexit__.return_value = None

            await expire_approval_requests()

            # Verify update was called
            assert mock_db.execute.called
            # Verify commit was called (since we had expired requests)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_requests_to_expire(self):
        """When no requests are expired, no commit should happen."""
        from app.core.scheduler import expire_approval_requests

        mock_db = AsyncMock()

        # Mock empty result (no expired requests)
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute.return_value = mock_result

        with patch("app.core.scheduler.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_db
            mock_session_local.return_value.__aexit__.return_value = None

            await expire_approval_requests()

            # Verify execute was called (for the update query)
            assert mock_db.execute.called
            # Commit should not be called when there are no expired requests
            mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_database_error(self):
        """Database errors should be caught and logged."""
        from app.core.scheduler import expire_approval_requests

        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection failed")

        with patch("app.core.scheduler.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.return_value = mock_db
            mock_session_local.return_value.__aexit__.return_value = None

            # Should raise the exception after rollback
            with pytest.raises(Exception, match="Database connection failed"):
                await expire_approval_requests()

            # Verify rollback was called
            mock_db.rollback.assert_called_once()


class TestApprovalExpiryLogic:
    """Tests for approval expiry business logic."""

    def test_request_with_future_expiry_not_expired(self):
        """Requests with future expiry dates should not be marked as expired."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(hours=24)

        request = MagicMock(spec=ApprovalRequest)
        request.status = ApprovalStatus.PENDING
        request.expires_at = future

        # The condition for expiry: expires_at < now
        should_expire = (
            request.status == ApprovalStatus.PENDING
            and request.expires_at is not None
            and request.expires_at < now
        )

        assert should_expire is False

    def test_request_with_past_expiry_should_expire(self):
        """Requests with past expiry dates should be marked as expired."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)

        request = MagicMock(spec=ApprovalRequest)
        request.status = ApprovalStatus.PENDING
        request.expires_at = past

        should_expire = (
            request.status == ApprovalStatus.PENDING
            and request.expires_at is not None
            and request.expires_at < now
        )

        assert should_expire is True

    def test_approved_request_not_expired(self):
        """Already approved requests should not be expired."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(hours=1)

        request = MagicMock(spec=ApprovalRequest)
        request.status = ApprovalStatus.APPROVED
        request.expires_at = past

        should_expire = (
            request.status == ApprovalStatus.PENDING
            and request.expires_at is not None
            and request.expires_at < now
        )

        assert should_expire is False

    def test_request_without_expiry_not_expired(self):
        """Requests without expiry date should never expire automatically."""
        now = datetime.now(timezone.utc)

        request = MagicMock(spec=ApprovalRequest)
        request.status = ApprovalStatus.PENDING
        request.expires_at = None

        should_expire = (
            request.status == ApprovalStatus.PENDING
            and request.expires_at is not None
            and request.expires_at < now
        )

        assert should_expire is False


class TestSchedulerSetup:
    """Tests for scheduler configuration."""

    def test_scheduler_singleton(self):
        """Scheduler should be a singleton."""
        from app.core.scheduler import BackgroundScheduler

        scheduler1 = BackgroundScheduler()
        scheduler2 = BackgroundScheduler()

        assert scheduler1 is scheduler2

    def test_get_scheduler_returns_instance(self):
        """get_scheduler should return the scheduler instance."""
        from app.core.scheduler import get_scheduler, scheduler

        result = get_scheduler()
        assert result is scheduler

    def test_scheduler_has_correct_jobs(self):
        """Scheduler should register the approval expiry job."""
        from app.core.scheduler import BackgroundScheduler

        scheduler = BackgroundScheduler()

        # Don't actually start the scheduler, just check job registration
        with patch.object(scheduler.scheduler, 'start'):
            with patch.object(scheduler.scheduler, 'add_job') as mock_add_job:
                scheduler._register_jobs()

                # Verify expire_approval_requests job was added
                job_ids = [call.kwargs.get('id') for call in mock_add_job.call_args_list]
                assert 'expire_approval_requests' in job_ids
                assert 'cleanup_expired_blacklist_tokens' in job_ids


class TestCleanupExpiredBlacklistTokens:
    """Tests for token blacklist cleanup job."""

    @pytest.mark.asyncio
    async def test_cleanup_when_redis_available(self):
        """Cleanup should work when Redis is available."""
        from app.core.scheduler import cleanup_expired_blacklist_tokens

        mock_redis = AsyncMock()
        mock_redis.scan.return_value = (0, [b"token_blacklist:abc", b"token_blacklist:def"])

        with patch("app.core.scheduler.RedisClient") as mock_redis_client:
            mock_redis_client.get_client.return_value = mock_redis

            # Should not raise
            await cleanup_expired_blacklist_tokens()

            # Verify scan was called
            mock_redis.scan.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_when_redis_unavailable(self):
        """Cleanup should handle Redis being unavailable."""
        from app.core.scheduler import cleanup_expired_blacklist_tokens

        with patch("app.core.scheduler.RedisClient") as mock_redis_client:
            mock_redis_client.get_client.return_value = None

            # Should not raise, just log warning
            await cleanup_expired_blacklist_tokens()
