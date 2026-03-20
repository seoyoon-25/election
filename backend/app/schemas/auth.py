"""Authentication schemas."""

from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema
from app.schemas.user import UserResponse


class LoginRequest(BaseSchema):
    """Schema for login request."""

    email: EmailStr
    password: str


class RegisterRequest(BaseSchema):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    full_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)


class TokenResponse(BaseSchema):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires


class AuthResponse(BaseSchema):
    """Schema for auth response with user and tokens."""

    user: UserResponse
    tokens: TokenResponse


class RefreshTokenRequest(BaseSchema):
    """Schema for refresh token request."""

    refresh_token: str


class PasswordResetRequest(BaseSchema):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseSchema):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(min_length=8, max_length=100)


class PasswordChangeRequest(BaseSchema):
    """Schema for authenticated password change."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class LogoutRequest(BaseSchema):
    """Schema for logout request."""

    refresh_token: Optional[str] = None  # Optional: blacklist refresh token too
