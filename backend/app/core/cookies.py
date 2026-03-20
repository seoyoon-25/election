"""
Cookie-based authentication utilities.

Provides httpOnly cookie support for secure token storage.
This is more secure than localStorage because:
1. Cookies are not accessible via JavaScript (XSS protection)
2. httpOnly flag prevents client-side access
3. SameSite flag provides CSRF protection
"""

from fastapi import Response, Request
from typing import Optional

from app.config import get_settings


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    access_token_max_age: int,
    refresh_token_max_age: int,
) -> None:
    """
    Set authentication cookies on the response.

    Args:
        response: FastAPI Response object
        access_token: JWT access token
        refresh_token: JWT refresh token
        access_token_max_age: Access token expiry in seconds
        refresh_token_max_age: Refresh token expiry in seconds
    """
    settings = get_settings()

    if not settings.use_cookie_auth:
        return

    # Set access token cookie
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=access_token,
        max_age=access_token_max_age,
        httponly=True,  # Not accessible via JavaScript
        secure=settings.cookie_secure,  # HTTPS only
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path=settings.cookie_path,
    )

    # Set refresh token cookie
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        max_age=refresh_token_max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/api/v1/auth",  # Only sent to auth endpoints
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Clear authentication cookies on logout.

    Args:
        response: FastAPI Response object
    """
    settings = get_settings()

    if not settings.use_cookie_auth:
        return

    response.delete_cookie(
        key=settings.access_token_cookie_name,
        domain=settings.cookie_domain,
        path=settings.cookie_path,
    )

    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        domain=settings.cookie_domain,
        path="/api/v1/auth",
    )


def get_token_from_cookie(request: Request, cookie_name: str) -> Optional[str]:
    """
    Extract token from cookie.

    Args:
        request: FastAPI Request object
        cookie_name: Name of the cookie

    Returns:
        Token value or None if not found
    """
    return request.cookies.get(cookie_name)


def get_access_token_from_cookie(request: Request) -> Optional[str]:
    """Get access token from cookie."""
    settings = get_settings()
    return get_token_from_cookie(request, settings.access_token_cookie_name)


def get_refresh_token_from_cookie(request: Request) -> Optional[str]:
    """Get refresh token from cookie."""
    settings = get_settings()
    return get_token_from_cookie(request, settings.refresh_token_cookie_name)
