"""Department schemas for API validation."""

from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class DepartmentBase(BaseSchema):
    """Base department schema with common fields."""

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$")


class DepartmentCreate(DepartmentBase):
    """Schema for creating a new department."""

    slug: Optional[str] = Field(None, min_length=1, max_length=50, pattern=r"^[a-z0-9-]+$")
    parent_id: Optional[int] = None
    sort_order: int = 0


class DepartmentUpdate(BaseSchema):
    """Schema for updating a department."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class DepartmentResponse(DepartmentBase, TimestampSchema):
    """Schema for department response."""

    id: int
    campaign_id: int
    slug: str
    sort_order: int
    parent_id: Optional[int] = None
    member_count: Optional[int] = None


class DepartmentBrief(BaseSchema):
    """Brief department info for embedding in other responses."""

    id: int
    name: str
    slug: str
    color: str


class DepartmentTree(DepartmentResponse):
    """Department with nested children for tree view."""

    children: list["DepartmentTree"] = Field(default_factory=list)


class DepartmentReorder(BaseSchema):
    """Schema for reordering departments."""

    department_ids: list[int] = Field(min_length=1)
