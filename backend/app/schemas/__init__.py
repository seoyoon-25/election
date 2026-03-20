"""Pydantic schemas for API request/response validation."""

from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
)
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.schemas.membership import (
    MembershipCreate,
    MembershipUpdate,
    MembershipResponse,
)
from app.schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
)
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
)
from app.schemas.approval import (
    WorkflowStepCreate,
    WorkflowStepUpdate,
    WorkflowStepResponse,
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowDetail,
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalRequestDetail,
    ApprovalRequestList,
    RequestStepResponse,
    RequestStepDecision,
    ApprovalRequestFilter,
)
from app.schemas.google_calendar import (
    OAuthStartResponse,
    GoogleCalendarConnectionResponse,
    GoogleCalendarConnectionStatus,
    GoogleCalendarDisconnectResponse,
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarEventList,
    CalendarEventAttendee,
    SyncedEventResponse,
    SyncedEventList,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    # Campaign
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignResponse",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Membership
    "MembershipCreate",
    "MembershipUpdate",
    "MembershipResponse",
    # Role
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    # Department
    "DepartmentCreate",
    "DepartmentUpdate",
    "DepartmentResponse",
    # Approval
    "WorkflowStepCreate",
    "WorkflowStepUpdate",
    "WorkflowStepResponse",
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowResponse",
    "WorkflowDetail",
    "ApprovalRequestCreate",
    "ApprovalRequestResponse",
    "ApprovalRequestDetail",
    "ApprovalRequestList",
    "RequestStepResponse",
    "RequestStepDecision",
    "ApprovalRequestFilter",
    # Google Calendar
    "OAuthStartResponse",
    "GoogleCalendarConnectionResponse",
    "GoogleCalendarConnectionStatus",
    "GoogleCalendarDisconnectResponse",
    "CalendarEventCreate",
    "CalendarEventUpdate",
    "CalendarEventResponse",
    "CalendarEventList",
    "CalendarEventAttendee",
    "SyncedEventResponse",
    "SyncedEventList",
]
