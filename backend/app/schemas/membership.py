"""Membership schemas for API validation."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.user import UserBrief
from app.schemas.role import RoleBrief
from app.schemas.department import DepartmentBrief


class MembershipBase(BaseSchema):
    """Base membership schema with common fields."""

    role_id: int
    department_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=100)


class MembershipCreate(MembershipBase):
    """Schema for creating a new membership (inviting a user)."""

    user_id: Optional[int] = None  # For existing users
    email: Optional[str] = None  # For inviting by email


class MembershipUpdate(BaseSchema):
    """Schema for updating a membership."""

    role_id: Optional[int] = None
    department_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_department_head: Optional[bool] = None


class MembershipResponse(MembershipBase, TimestampSchema):
    """Schema for membership response."""

    id: int
    user_id: int
    campaign_id: int
    is_active: bool
    is_department_head: bool = False
    joined_at: datetime
    invited_by_id: Optional[int] = None

    # Nested objects
    user: Optional[UserBrief] = None
    role: Optional[RoleBrief] = None
    department: Optional[DepartmentBrief] = None


class MembershipBrief(BaseSchema):
    """Brief membership info."""

    id: int
    user_id: int
    role_name: str
    department_name: Optional[str] = None
    title: Optional[str] = None
    is_active: bool


class MemberResponse(BaseSchema):
    """Full member info combining user and membership."""

    id: int  # membership id
    user: UserBrief
    role: RoleBrief
    department: Optional[DepartmentBrief] = None
    title: Optional[str] = None
    is_active: bool
    is_department_head: bool = False
    joined_at: datetime
    is_owner: bool
    is_admin: bool


class InvitationCreate(BaseSchema):
    """Schema for creating an invitation."""

    email: str
    role_id: int
    department_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=100)
    message: Optional[str] = None  # Optional personal message
