"""
Token blacklist service using Redis.

Provides token revocation functionality for:
- Logout (blacklist both access and refresh tokens)
- Password change (invalidate all user tokens)
- Security events (forced logout)
"""

from datetime import datetime, timezone
from typing import Optional
import hashlib

from app.core.redis import get_redis
from app.core.security import decode_token
from app.config import settings


# Redis key prefixes
TOKEN_BLACKLIST_PREFIX = "token:blacklist:"
USER_TOKEN_INVALIDATION_PREFIX = "user:tokens:invalidated:"


class TokenBlacklistService:
    """Service for managing token blacklist in Redis."""

    @staticmethod
    def _get_token_hash(token: str) -> str:
        """
        Get a hash of the token for storage.

        We store hashes instead of raw tokens for security.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def _get_token_key(token: str) -> str:
        """Get Redis key for a token."""
        token_hash = TokenBlacklistService._get_token_hash(token)
        return f"{TOKEN_BLACKLIST_PREFIX}{token_hash}"

    @staticmethod
    def _get_user_invalidation_key(user_id: int) -> str:
        """Get Redis key for user token invalidation timestamp."""
        return f"{USER_TOKEN_INVALIDATION_PREFIX}{user_id}"

    @classmethod
    async def blacklist_token(cls, token: str) -> bool:
        """
        Add a token to the blacklist.

        The token is blacklisted until its expiration time.

        Args:
            token: JWT token to blacklist

        Returns:
            True if blacklisted successfully, False otherwise
        """
        try:
            payload = decode_token(token)
            redis_client = await get_redis()

            # Calculate TTL from token expiration
            now = datetime.now(timezone.utc)
            ttl_seconds = int((payload.exp - now).total_seconds())

            if ttl_seconds <= 0:
                # Token already expired, no need to blacklist
                return True

            key = cls._get_token_key(token)
            await redis_client.setex(
                key,
                ttl_seconds,
                payload.type,  # Store token type for debugging
            )
            return True
        except Exception:
            # If decode fails, token is invalid anyway
            return False

    @classmethod
    async def is_token_blacklisted(cls, token: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            token: JWT token to check

        Returns:
            True if blacklisted, False otherwise
        """
        try:
            redis_client = await get_redis()
            key = cls._get_token_key(token)
            return await redis_client.exists(key) > 0
        except Exception:
            # If Redis is unavailable, fail open (allow token)
            # In production, you might want to fail closed instead
            return False

    @classmethod
    async def invalidate_all_user_tokens(cls, user_id: int) -> bool:
        """
        Invalidate all tokens for a user by setting an invalidation timestamp.

        Any token issued before this timestamp will be considered invalid.
        This is useful for:
        - Password changes
        - Account compromise
        - Forced logout from all devices

        Args:
            user_id: User ID whose tokens should be invalidated

        Returns:
            True if successful, False otherwise
        """
        try:
            redis_client = await get_redis()
            key = cls._get_user_invalidation_key(user_id)
            timestamp = datetime.now(timezone.utc).timestamp()

            # Set with TTL equal to max token lifetime (refresh token)
            ttl_seconds = settings.jwt_refresh_token_expire_days * 24 * 60 * 60
            await redis_client.setex(key, ttl_seconds, str(timestamp))
            return True
        except Exception:
            return False

    @classmethod
    async def is_token_invalidated_for_user(
        cls, user_id: int, token_issued_at: datetime
    ) -> bool:
        """
        Check if a token was invalidated by user-level invalidation.

        Args:
            user_id: User ID to check
            token_issued_at: When the token was issued (iat claim)

        Returns:
            True if token is invalidated, False otherwise
        """
        try:
            redis_client = await get_redis()
            key = cls._get_user_invalidation_key(user_id)
            invalidation_time = await redis_client.get(key)

            if invalidation_time is None:
                return False

            # Token is invalid if it was issued before the invalidation time
            invalidation_timestamp = float(invalidation_time)
            token_timestamp = token_issued_at.timestamp()
            return token_timestamp < invalidation_timestamp
        except Exception:
            return False

    @classmethod
    async def check_token_valid(cls, token: str) -> tuple[bool, Optional[str]]:
        """
        Comprehensive token validity check.

        Checks both individual token blacklist and user-level invalidation.

        Args:
            token: JWT token to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # First check individual blacklist
            if await cls.is_token_blacklisted(token):
                return False, "Token has been revoked"

            # Then check user-level invalidation
            payload = decode_token(token)
            user_id = int(payload.sub)

            if await cls.is_token_invalidated_for_user(user_id, payload.iat):
                return False, "All sessions have been invalidated"

            return True, None
        except Exception as e:
            return False, str(e)


# Convenience functions for direct import
async def blacklist_token(token: str) -> bool:
    """Blacklist a single token."""
    return await TokenBlacklistService.blacklist_token(token)


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    return await TokenBlacklistService.is_token_blacklisted(token)


async def invalidate_all_user_tokens(user_id: int) -> bool:
    """Invalidate all tokens for a user."""
    return await TokenBlacklistService.invalidate_all_user_tokens(user_id)


async def check_token_valid(token: str) -> tuple[bool, Optional[str]]:
    """Check if a token is valid (not blacklisted or invalidated)."""
    return await TokenBlacklistService.check_token_valid(token)
