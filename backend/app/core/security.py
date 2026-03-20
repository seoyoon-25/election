"""
Security utilities for authentication and authorization.

Provides:
- Password hashing with bcrypt
- JWT token generation and verification
- Permission checking utilities
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt
from pydantic import BaseModel

from app.config import settings


# Token types
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # Subject (user_id)
    type: str  # Token type (access/refresh)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at time
    jti: Optional[str] = None  # JWT ID for token revocation


class TokenPair(BaseModel):
    """Access and refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt(rounds=settings.password_hash_rounds)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(
    user_id: int,
    additional_claims: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User ID to encode in token
        additional_claims: Optional additional claims to include

    Returns:
        Encoded JWT access token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": expire,
    }

    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: int) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens have a longer expiration and can be used
    to obtain new access tokens.

    Args:
        user_id: User ID to encode in token

    Returns:
        Encoded JWT refresh token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": str(user_id),
        "type": REFRESH_TOKEN_TYPE,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_token_pair(user_id: int) -> TokenPair:
    """
    Create an access and refresh token pair.

    Args:
        user_id: User ID to encode in tokens

    Returns:
        TokenPair with access and refresh tokens
    """
    return TokenPair(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def decode_token(token: str) -> TokenPayload:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    return TokenPayload(
        sub=payload["sub"],
        type=payload["type"],
        exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
        jti=payload.get("jti"),
    )


def verify_access_token(token: str) -> Optional[int]:
    """
    Verify an access token and return the user ID.

    Args:
        token: JWT access token

    Returns:
        User ID if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.type != ACCESS_TOKEN_TYPE:
            return None
        return int(payload.sub)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        return None


def verify_refresh_token(token: str) -> Optional[int]:
    """
    Verify a refresh token and return the user ID.

    Args:
        token: JWT refresh token

    Returns:
        User ID if valid, None otherwise
    """
    try:
        payload = decode_token(token)
        if payload.type != REFRESH_TOKEN_TYPE:
            return None
        return int(payload.sub)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        return None


def create_password_reset_token(user_id: int, email: str) -> str:
    """
    Create a password reset token.

    Valid for 1 hour.

    Args:
        user_id: User ID
        email: User email (included for verification)

    Returns:
        Password reset token
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=1)

    payload = {
        "sub": str(user_id),
        "type": "password_reset",
        "email": email,
        "iat": now,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_password_reset_token(token: str) -> Optional[dict[str, Any]]:
    """
    Verify a password reset token.

    Args:
        token: Password reset token

    Returns:
        Dict with user_id and email if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        if payload.get("type") != "password_reset":
            return None

        return {
            "user_id": int(payload["sub"]),
            "email": payload["email"],
        }
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, KeyError):
        return None
