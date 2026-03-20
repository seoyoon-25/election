"""Role schemas for API validation."""

from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class RoleBase(BaseSchema):
    """Base role schema with common fields."""

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: list[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    """Schema for creating a new role."""

    slug: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    is_default: bool = False


class RoleUpdate(BaseSchema):
    """Schema for updating a role."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: Optional[list[str]] = None
    is_default: Optional[bool] = None


class RoleResponse(RoleBase, TimestampSchema):
    """Schema for role response."""

    id: int
    campaign_id: int
    slug: str
    is_system: bool
    is_default: bool


class RoleBrief(BaseSchema):
    """Brief role info for embedding in other responses."""

    id: int
    name: str
    slug: str
    is_system: bool


class PermissionInfo(BaseSchema):
    """Information about a permission."""

    code: str
    name: str
    description: str
    category: str
