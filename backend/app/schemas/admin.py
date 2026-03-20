"""Admin schemas for superadmin management API."""

from datetime import datetime
from typing import Optional, List

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema, PaginatedResponse
from app.models.campaign import CampaignStatus


class AdminStatsResponse(BaseSchema):
    """Statistics response for admin dashboard."""

    total_campaigns: int
    active_campaigns: int
    total_users: int
    active_users: int
    total_invitations: int
    pending_invitations: int
    today_signups: int
    today_campaigns: int


class AdminCampaignItem(BaseSchema):
    """Campaign item for admin list."""

    id: int
    name: str
    slug: str
    description: Optional[str] = None
    status: CampaignStatus
    member_count: int
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AdminCampaignList(PaginatedResponse[AdminCampaignItem]):
    """Paginated campaign list for admin."""
    pass


class AdminCampaignStatusUpdate(BaseSchema):
    """Schema for updating campaign status."""

    status: CampaignStatus


class AdminUserItem(BaseSchema):
    """User item for admin list."""

    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    is_superadmin: bool
    is_email_verified: bool
    campaign_count: int
    last_login_at: Optional[datetime] = None
    created_at: datetime


class AdminUserCampaign(BaseSchema):
    """User's campaign membership info."""

    campaign_id: int
    campaign_name: str
    campaign_slug: str
    role_name: str
    department_name: Optional[str] = None
    joined_at: datetime


class AdminUserDetail(AdminUserItem):
    """Detailed user info including campaigns."""

    campaigns: List[AdminUserCampaign] = []


class AdminUserList(PaginatedResponse[AdminUserItem]):
    """Paginated user list for admin."""
    pass


class AdminAddUserToCampaign(BaseSchema):
    """Schema for adding user to a campaign."""

    campaign_id: int
    role_id: int
    department_id: Optional[int] = None
    title: Optional[str] = None


class AdminUpdateUserRole(BaseSchema):
    """Schema for updating user's role in a campaign."""

    role_id: int
    department_id: Optional[int] = None


class AdminInvitationItem(BaseSchema):
    """Invitation item for admin list."""

    id: int
    email: str
    campaign_id: int
    campaign_name: str
    role_name: Optional[str] = None
    department_name: Optional[str] = None
    status: str
    invited_by_name: Optional[str] = None
    invited_by_email: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    accepted_at: Optional[datetime] = None


class AdminInvitationList(PaginatedResponse[AdminInvitationItem]):
    """Paginated invitation list for admin."""
    pass


class AdminCreateInvitation(BaseSchema):
    """Schema for creating a new invitation."""

    email: EmailStr
    campaign_id: int
    role_id: int
    department_id: Optional[int] = None
    title: Optional[str] = None


class AdminResendInvitation(BaseSchema):
    """Response for resending invitation."""

    id: int
    email: str
    new_expires_at: datetime
    message: str


class AdminCampaignStats(BaseSchema):
    """Detailed stats for a single campaign."""

    id: int
    name: str
    slug: str
    status: CampaignStatus
    member_count: int
    task_count: int
    pending_tasks: int
    completed_tasks: int
    approval_count: int
    pending_approvals: int
    event_count: int
    created_at: datetime
