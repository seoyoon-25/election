"""
SQLAlchemy models for Campaign Operations OS.

This package contains all database models for the application.
Models are organized by domain:
- user: User authentication and profile
- campaign: Campaign (tenant) management
- membership: User-Campaign relationships
- role: RBAC roles and permissions
- department: Organizational structure
- task: Kanban boards and task management
- approval: Approval workflows
- google_calendar: Google Calendar integration
"""

from app.models.base import Base, TimestampMixin, TenantMixin
from app.models.user import User
from app.models.campaign import Campaign, CampaignStatus
from app.models.membership import CampaignMembership
from app.models.role import Role, Permission, SYSTEM_ROLES
from app.models.department import Department, DEFAULT_DEPARTMENTS
from app.models.task import (
    TaskBoard,
    TaskColumn,
    Task,
    TaskAssignment,
    TaskComment,
    TaskHistory,
    TaskAttachment,
    TaskPriority,
    TaskHistoryAction,
    DEFAULT_COLUMNS,
)
from app.models.approval import (
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    ApprovalRequest,
    ApprovalRequestStep,
    ApproverType,
    ApprovalStatus,
)
from app.models.google_calendar import (
    GoogleCalendarConnection,
    SyncedEvent,
    ConnectionStatus,
    SyncedEventStatus,
)
from app.models.invitation import Invitation, InvitationStatus

__all__ = [
    # Base classes
    "Base",
    "TimestampMixin",
    "TenantMixin",
    # Models
    "User",
    "Campaign",
    "CampaignStatus",
    "CampaignMembership",
    "Role",
    "Permission",
    "SYSTEM_ROLES",
    "Department",
    "DEFAULT_DEPARTMENTS",
    # Task models
    "TaskBoard",
    "TaskColumn",
    "Task",
    "TaskAssignment",
    "TaskComment",
    "TaskHistory",
    "TaskAttachment",
    "TaskPriority",
    "TaskHistoryAction",
    "DEFAULT_COLUMNS",
    # Approval models
    "ApprovalWorkflow",
    "ApprovalWorkflowStep",
    "ApprovalRequest",
    "ApprovalRequestStep",
    "ApproverType",
    "ApprovalStatus",
    # Google Calendar models
    "GoogleCalendarConnection",
    "SyncedEvent",
    "ConnectionStatus",
    "SyncedEventStatus",
    # Invitation
    "Invitation",
    "InvitationStatus",
]
