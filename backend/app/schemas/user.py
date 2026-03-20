"""User schemas for API validation."""

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, TimestampSchema


class UserBase(BaseSchema):
    """Base user schema with common fields."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseSchema):
    """Schema for updating a user."""

    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = None


class UserPasswordUpdate(BaseSchema):
    """Schema for updating user password."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class UserResponse(UserBase, TimestampSchema):
    """Schema for user response."""

    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    is_email_verified: bool = False
    is_superadmin: bool = False


class UserInDB(UserResponse):
    """Schema for user with database fields (internal use)."""

    password_hash: str
    is_superadmin: bool
    email_verified_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None


class UserBrief(BaseSchema):
    """Brief user info for embedding in other responses."""

    id: int
    email: str
    full_name: str
    avatar_url: Optional[str] = None
