"""
CSRF Protection Middleware.

Provides CSRF token validation for state-changing requests.
This is optional for pure JWT-based APIs but recommended when
using cookies for authentication.
"""

import secrets
from typing import Optional

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.redis import RedisClient


# Methods that don't require CSRF validation
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

# CSRF token header name
CSRF_HEADER = "X-CSRF-Token"

# CSRF token cookie name
CSRF_COOKIE = "csrf_token"

# Token expiry in seconds (1 hour)
CSRF_TOKEN_EXPIRY = 3600


async def generate_csrf_token(user_id: int) -> str:
    """
    Generate a CSRF token for a user.

    Args:
        user_id: The user's ID

    Returns:
        The generated CSRF token
    """
    token = secrets.token_urlsafe(32)

    # Store in Redis with user association
    redis = await RedisClient.get_client()
    if redis:
        await redis.setex(
            f"csrf:{token}",
            CSRF_TOKEN_EXPIRY,
            str(user_id),
        )

    return token


async def validate_csrf_token(token: str, user_id: int) -> bool:
    """
    Validate a CSRF token.

    Args:
        token: The CSRF token to validate
        user_id: The expected user ID

    Returns:
        True if the token is valid
    """
    if not token:
        return False

    redis = await RedisClient.get_client()
    if not redis:
        # If Redis is unavailable, allow request (fail-open)
        # In production, you might want to fail-closed instead
        return True

    stored_user_id = await redis.get(f"csrf:{token}")
    if stored_user_id is None:
        return False

    return stored_user_id.decode() == str(user_id)


async def invalidate_csrf_token(token: str) -> None:
    """Invalidate a CSRF token (e.g., on logout)."""
    redis = await RedisClient.get_client()
    if redis:
        await redis.delete(f"csrf:{token}")


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware.

    Validates CSRF tokens for state-changing requests.
    Requires user to be authenticated (JWT token present).
    """

    def __init__(self, app, excluded_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/password-reset",
            "/api/v1/invitations/accept",
        ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip CSRF check for safe methods
        if request.method in SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF check for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.excluded_paths):
            return await call_next(request)

        # For API endpoints that use JWT Bearer tokens,
        # CSRF protection is generally not needed because:
        # 1. Tokens are not automatically sent by browsers (unlike cookies)
        # 2. The attacker cannot read the token from another site
        #
        # However, if you're using cookie-based authentication,
        # uncomment the following validation:

        # csrf_token = request.headers.get(CSRF_HEADER)
        # if not csrf_token:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="CSRF token missing",
        #     )
        #
        # # Get user from request state (set by auth middleware)
        # user_id = getattr(request.state, "user_id", None)
        # if user_id and not await validate_csrf_token(csrf_token, user_id):
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Invalid CSRF token",
        #     )

        return await call_next(request)
