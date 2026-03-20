"""Campaign schemas for API validation."""

from datetime import date
from typing import Optional, Any

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema
from app.models.campaign import CampaignStatus


class CampaignBase(BaseSchema):
    """Base campaign schema with common fields."""

    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    timezone: str = Field(default="UTC", max_length=50)


class CampaignCreate(CampaignBase):
    """Schema for creating a new campaign."""

    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    # If slug is not provided, it will be generated from the name


class CampaignUpdate(BaseSchema):
    """Schema for updating a campaign."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[CampaignStatus] = None
    timezone: Optional[str] = Field(None, max_length=50)
    settings: Optional[dict[str, Any]] = None


class CampaignResponse(CampaignBase, TimestampSchema):
    """Schema for campaign response."""

    id: int
    slug: str
    status: CampaignStatus
    settings: Optional[dict[str, Any]] = None
    member_count: Optional[int] = None
    days_until_end: Optional[int] = None


class CampaignBrief(BaseSchema):
    """Brief campaign info for embedding in other responses."""

    id: int
    name: str
    slug: str
    status: CampaignStatus


class CampaignWithRole(CampaignBrief):
    """Campaign info with user's role in it."""

    role_name: str
    role_slug: str
    department_name: Optional[str] = None
