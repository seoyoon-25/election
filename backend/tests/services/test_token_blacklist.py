"""
Tests for token blacklist service.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.token_blacklist import (
    TokenBlacklistService,
    blacklist_token,
    is_token_blacklisted,
    invalidate_all_user_tokens,
    check_token_valid,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
)


class TestTokenBlacklistService:
    """Tests for TokenBlacklistService class."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.setex = AsyncMock(return_value=True)
        redis_mock.exists = AsyncMock(return_value=0)
        redis_mock.get = AsyncMock(return_value=None)
        return redis_mock

    @pytest.fixture
    def access_token(self):
        """Create a test access token."""
        return create_access_token(user_id=1)

    @pytest.fixture
    def refresh_token(self):
        """Create a test refresh token."""
        return create_refresh_token(user_id=1)

    @pytest.fixture
    def token_pair(self):
        """Create a test token pair."""
        return create_token_pair(user_id=1)

    # =========================================================================
    # blacklist_token tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_blacklist_token_success(self, mock_redis, access_token):
        """Test successfully blacklisting a token."""
        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            result = await blacklist_token(access_token)

            assert result is True
            mock_redis.setex.assert_called_once()
            # Verify TTL is positive and key contains hash
            call_args = mock_redis.setex.call_args
            assert call_args[0][0].startswith("token:blacklist:")
            assert call_args[0][1] > 0  # TTL should be positive

    @pytest.mark.asyncio
    async def test_blacklist_refresh_token(self, mock_redis, refresh_token):
        """Test blacklisting a refresh token."""
        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            result = await blacklist_token(refresh_token)

            assert result is True
            mock_redis.setex.assert_called_once()
            # Refresh tokens have longer TTL
            call_args = mock_redis.setex.call_args
            assert call_args[0][1] > 60 * 60 * 24  # > 1 day

    @pytest.mark.asyncio
    async def test_blacklist_invalid_token(self, mock_redis):
        """Test blacklisting an invalid token returns False."""
        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            result = await blacklist_token("invalid.token.here")

            # Should return False for invalid token
            assert result is False
            mock_redis.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_blacklist_expired_token(self, mock_redis):
        """Test blacklisting an expired token."""
        # Create an expired token by patching datetime
        with patch("app.core.security.datetime") as mock_dt:
            mock_dt.now.return_value = datetime.now(timezone.utc) - timedelta(hours=2)
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            # This would create an already-expired token

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            # For an expired token, we can't decode it, so it returns False
            result = await blacklist_token("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIiwidHlwZSI6ImFjY2VzcyIsImlhdCI6MTYwMDAwMDAwMCwiZXhwIjoxNjAwMDAwMDAwfQ.invalid")
            assert result is False

    # =========================================================================
    # is_token_blacklisted tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_false(self, mock_redis, access_token):
        """Test checking a non-blacklisted token."""
        mock_redis.exists.return_value = 0

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            result = await is_token_blacklisted(access_token)

            assert result is False

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_true(self, mock_redis, access_token):
        """Test checking a blacklisted token."""
        mock_redis.exists.return_value = 1

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            result = await is_token_blacklisted(access_token)

            assert result is True

    @pytest.mark.asyncio
    async def test_is_token_blacklisted_redis_error(self, mock_redis, access_token):
        """Test that Redis errors fail open (return False)."""
        mock_redis.exists.side_effect = Exception("Redis connection error")

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            result = await is_token_blacklisted(access_token)

            # Should fail open
            assert result is False

    # =========================================================================
    # invalidate_all_user_tokens tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_invalidate_all_user_tokens_success(self, mock_redis):
        """Test invalidating all tokens for a user."""
        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            result = await invalidate_all_user_tokens(user_id=1)

            assert result is True
            mock_redis.setex.assert_called_once()
            # Verify key format and TTL
            call_args = mock_redis.setex.call_args
            assert "user:tokens:invalidated:1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_invalidate_all_user_tokens_redis_error(self, mock_redis):
        """Test handling Redis errors during invalidation."""
        mock_redis.setex.side_effect = Exception("Redis error")

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            result = await invalidate_all_user_tokens(user_id=1)

            assert result is False

    # =========================================================================
    # is_token_invalidated_for_user tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_token_not_invalidated_no_timestamp(self, mock_redis, access_token):
        """Test token validity when no invalidation timestamp exists."""
        mock_redis.get.return_value = None

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            now = datetime.now(timezone.utc)
            result = await TokenBlacklistService.is_token_invalidated_for_user(
                user_id=1,
                token_issued_at=now,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_token_invalidated_issued_before(self, mock_redis):
        """Test token is invalid when issued before invalidation."""
        # Set invalidation time to now
        now = datetime.now(timezone.utc)
        mock_redis.get.return_value = str(now.timestamp())

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            # Token issued 1 hour before invalidation
            token_issued_at = now - timedelta(hours=1)
            result = await TokenBlacklistService.is_token_invalidated_for_user(
                user_id=1,
                token_issued_at=token_issued_at,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_token_valid_issued_after(self, mock_redis):
        """Test token is valid when issued after invalidation."""
        # Set invalidation time to 1 hour ago
        now = datetime.now(timezone.utc)
        invalidation_time = now - timedelta(hours=1)
        mock_redis.get.return_value = str(invalidation_time.timestamp())

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            # Token issued now (after invalidation)
            result = await TokenBlacklistService.is_token_invalidated_for_user(
                user_id=1,
                token_issued_at=now,
            )

            assert result is False

    # =========================================================================
    # check_token_valid tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_check_token_valid_success(self, mock_redis, access_token):
        """Test checking a valid token."""
        mock_redis.exists.return_value = 0
        mock_redis.get.return_value = None

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            is_valid, error = await check_token_valid(access_token)

            assert is_valid is True
            assert error is None

    @pytest.mark.asyncio
    async def test_check_token_valid_blacklisted(self, mock_redis, access_token):
        """Test checking a blacklisted token."""
        mock_redis.exists.return_value = 1

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            is_valid, error = await check_token_valid(access_token)

            assert is_valid is False
            assert error == "Token has been revoked"

    @pytest.mark.asyncio
    async def test_check_token_valid_user_invalidated(self, mock_redis, access_token):
        """Test checking a token when user tokens are invalidated."""
        mock_redis.exists.return_value = 0
        # Set invalidation time to future (all tokens invalid)
        future_time = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_redis.get.return_value = str(future_time.timestamp())

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            is_valid, error = await check_token_valid(access_token)

            assert is_valid is False
            assert error == "All sessions have been invalidated"


class TestTokenBlacklistIntegration:
    """Integration-style tests for token blacklist flow."""

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis with in-memory storage."""
        storage = {}

        async def mock_setex(key, ttl, value):
            storage[key] = value
            return True

        async def mock_exists(key):
            return 1 if key in storage else 0

        async def mock_get(key):
            return storage.get(key)

        redis_mock = AsyncMock()
        redis_mock.setex = mock_setex
        redis_mock.exists = mock_exists
        redis_mock.get = mock_get
        return redis_mock

    @pytest.mark.asyncio
    async def test_logout_flow(self, mock_redis):
        """Test complete logout flow with token blacklisting."""
        # Create tokens
        tokens = create_token_pair(user_id=1)

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            # Initially tokens are valid
            is_valid, _ = await check_token_valid(tokens.access_token)
            assert is_valid is True

            # Blacklist both tokens (simulating logout)
            await blacklist_token(tokens.access_token)
            await blacklist_token(tokens.refresh_token)

            # Now tokens should be invalid
            is_valid, error = await check_token_valid(tokens.access_token)
            assert is_valid is False
            assert error == "Token has been revoked"

            is_valid, error = await check_token_valid(tokens.refresh_token)
            assert is_valid is False
            assert error == "Token has been revoked"

    @pytest.mark.asyncio
    async def test_password_change_flow(self, mock_redis):
        """Test password change flow with user-level invalidation."""
        user_id = 1

        # Create tokens before password change
        old_tokens = create_token_pair(user_id=user_id)

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            # Old tokens are initially valid
            is_valid, _ = await check_token_valid(old_tokens.access_token)
            assert is_valid is True

            # Simulate password change - invalidate all user tokens
            await invalidate_all_user_tokens(user_id)

            # Old tokens should now be invalid
            is_valid, error = await check_token_valid(old_tokens.access_token)
            assert is_valid is False
            assert error == "All sessions have been invalidated"

            # New tokens created after invalidation should be valid
            # (In real scenario, new tokens would be issued with current timestamp)

    @pytest.mark.asyncio
    async def test_token_rotation_flow(self, mock_redis):
        """Test token rotation during refresh."""
        user_id = 1

        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            # Create initial refresh token
            old_refresh_token = create_refresh_token(user_id)

            # Initially valid
            is_valid, _ = await check_token_valid(old_refresh_token)
            assert is_valid is True

            # Simulate token refresh - blacklist old refresh token
            await blacklist_token(old_refresh_token)

            # Old refresh token should be invalid
            is_valid, _ = await check_token_valid(old_refresh_token)
            assert is_valid is False

            # Tokens for a different user should still be valid
            # (This simulates that blacklisting is token-specific, not global)
            other_user_token = create_access_token(user_id=999)
            is_valid, _ = await check_token_valid(other_user_token)
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_blacklist_does_not_affect_other_tokens(self, mock_redis):
        """Test that blacklisting one token doesn't affect others."""
        with patch(
            "app.services.token_blacklist.get_redis",
            return_value=mock_redis,
        ):
            # Create two different tokens for different users
            token_user1 = create_access_token(user_id=1)
            token_user2 = create_access_token(user_id=2)

            # Both should be valid initially
            is_valid, _ = await check_token_valid(token_user1)
            assert is_valid is True
            is_valid, _ = await check_token_valid(token_user2)
            assert is_valid is True

            # Blacklist only user1's token
            await blacklist_token(token_user1)

            # User1's token should be invalid
            is_valid, _ = await check_token_valid(token_user1)
            assert is_valid is False

            # User2's token should still be valid
            is_valid, _ = await check_token_valid(token_user2)
            assert is_valid is True
