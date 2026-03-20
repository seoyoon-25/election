"""
Role and Permission models for RBAC.

Roles are campaign-scoped and define what actions members can perform.
Each campaign has a set of default system roles plus custom roles.
"""

import enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.membership import CampaignMembership


class Permission(str, enum.Enum):
    """
    Available permissions in the system.

    Permissions follow the pattern: resource:action
    """

    # Campaign management
    CAMPAIGN_VIEW = "campaign:view"
    CAMPAIGN_EDIT = "campaign:edit"
    CAMPAIGN_MANAGE_MEMBERS = "campaign:manage_members"
    CAMPAIGN_MANAGE_ROLES = "campaign:manage_roles"
    CAMPAIGN_DELETE = "campaign:delete"

    # Department management
    DEPARTMENT_VIEW = "department:view"
    DEPARTMENT_CREATE = "department:create"
    DEPARTMENT_EDIT = "department:edit"
    DEPARTMENT_DELETE = "department:delete"

    # Task management
    TASK_VIEW_ALL = "task:view_all"
    TASK_VIEW_DEPARTMENT = "task:view_department"
    TASK_CREATE = "task:create"
    TASK_EDIT_OWN = "task:edit_own"
    TASK_EDIT_ALL = "task:edit_all"
    TASK_DELETE = "task:delete"
    TASK_ASSIGN = "task:assign"

    # Board management
    BOARD_CREATE = "board:create"
    BOARD_EDIT = "board:edit"
    BOARD_DELETE = "board:delete"

    # Approval workflow
    APPROVAL_REQUEST = "approval:request"
    APPROVAL_DECIDE = "approval:decide"
    APPROVAL_MANAGE_WORKFLOWS = "approval:manage_workflows"

    # Calendar/Events
    EVENT_VIEW = "event:view"
    EVENT_CREATE = "event:create"
    EVENT_EDIT_OWN = "event:edit_own"
    EVENT_EDIT_ALL = "event:edit_all"
    EVENT_DELETE = "event:delete"

    # Files/Attachments
    FILE_UPLOAD = "file:upload"
    FILE_DELETE_OWN = "file:delete_own"
    FILE_DELETE_ALL = "file:delete_all"

    # Notifications/Webhooks
    WEBHOOK_MANAGE = "webhook:manage"

    # Audit
    AUDIT_VIEW = "audit:view"


# System role definitions - created automatically for new campaigns
SYSTEM_ROLES: dict[str, dict] = {
    "owner": {
        "name": "캠프 대표",
        "name_en": "Campaign Owner",
        "description": "모든 캠프 기능에 대한 전체 권한",
        "permissions": [p.value for p in Permission],
    },
    "admin": {
        "name": "관리자",
        "name_en": "Administrator",
        "description": "캠프 설정, 멤버, 콘텐츠 관리",
        "permissions": [
            Permission.CAMPAIGN_VIEW.value,
            Permission.CAMPAIGN_EDIT.value,
            Permission.CAMPAIGN_MANAGE_MEMBERS.value,
            Permission.CAMPAIGN_MANAGE_ROLES.value,
            Permission.DEPARTMENT_VIEW.value,
            Permission.DEPARTMENT_CREATE.value,
            Permission.DEPARTMENT_EDIT.value,
            Permission.DEPARTMENT_DELETE.value,
            Permission.TASK_VIEW_ALL.value,
            Permission.TASK_CREATE.value,
            Permission.TASK_EDIT_ALL.value,
            Permission.TASK_DELETE.value,
            Permission.TASK_ASSIGN.value,
            Permission.BOARD_CREATE.value,
            Permission.BOARD_EDIT.value,
            Permission.BOARD_DELETE.value,
            Permission.APPROVAL_REQUEST.value,
            Permission.APPROVAL_DECIDE.value,
            Permission.APPROVAL_MANAGE_WORKFLOWS.value,
            Permission.EVENT_VIEW.value,
            Permission.EVENT_CREATE.value,
            Permission.EVENT_EDIT_ALL.value,
            Permission.EVENT_DELETE.value,
            Permission.FILE_UPLOAD.value,
            Permission.FILE_DELETE_ALL.value,
            Permission.AUDIT_VIEW.value,
        ],
    },
    "general_affairs": {
        "name": "총무",
        "name_en": "General Affairs",
        "description": "멤버 관리, 일정, 결재 승인",
        "permissions": [
            Permission.CAMPAIGN_VIEW.value,
            Permission.CAMPAIGN_MANAGE_MEMBERS.value,
            Permission.DEPARTMENT_VIEW.value,
            Permission.DEPARTMENT_CREATE.value,
            Permission.DEPARTMENT_EDIT.value,
            Permission.TASK_VIEW_ALL.value,
            Permission.TASK_CREATE.value,
            Permission.TASK_EDIT_OWN.value,
            Permission.APPROVAL_REQUEST.value,
            Permission.APPROVAL_DECIDE.value,
            Permission.EVENT_VIEW.value,
            Permission.EVENT_CREATE.value,
            Permission.EVENT_EDIT_ALL.value,
            Permission.FILE_UPLOAD.value,
            Permission.FILE_DELETE_OWN.value,
            Permission.AUDIT_VIEW.value,
        ],
    },
    "policy": {
        "name": "정책",
        "name_en": "Policy",
        "description": "태스크, 문서 작업",
        "permissions": [
            Permission.CAMPAIGN_VIEW.value,
            Permission.DEPARTMENT_VIEW.value,
            Permission.TASK_VIEW_DEPARTMENT.value,
            Permission.TASK_CREATE.value,
            Permission.TASK_EDIT_ALL.value,
            Permission.TASK_DELETE.value,
            Permission.TASK_ASSIGN.value,
            Permission.BOARD_CREATE.value,
            Permission.BOARD_EDIT.value,
            Permission.APPROVAL_REQUEST.value,
            Permission.EVENT_VIEW.value,
            Permission.EVENT_CREATE.value,
            Permission.EVENT_EDIT_OWN.value,
            Permission.FILE_UPLOAD.value,
            Permission.FILE_DELETE_OWN.value,
        ],
    },
    "communications": {
        "name": "홍보",
        "name_en": "Communications",
        "description": "태스크, 일정 관리",
        "permissions": [
            Permission.CAMPAIGN_VIEW.value,
            Permission.DEPARTMENT_VIEW.value,
            Permission.TASK_VIEW_DEPARTMENT.value,
            Permission.TASK_CREATE.value,
            Permission.TASK_EDIT_ALL.value,
            Permission.TASK_ASSIGN.value,
            Permission.APPROVAL_REQUEST.value,
            Permission.EVENT_VIEW.value,
            Permission.EVENT_CREATE.value,
            Permission.EVENT_EDIT_ALL.value,
            Permission.EVENT_DELETE.value,
            Permission.FILE_UPLOAD.value,
            Permission.FILE_DELETE_ALL.value,
        ],
    },
    "staff": {
        "name": "스태프",
        "name_en": "Staff",
        "description": "기본 조회 및 작성 권한",
        "permissions": [
            Permission.CAMPAIGN_VIEW.value,
            Permission.DEPARTMENT_VIEW.value,
            Permission.TASK_VIEW_DEPARTMENT.value,
            Permission.TASK_CREATE.value,
            Permission.TASK_EDIT_OWN.value,
            Permission.APPROVAL_REQUEST.value,
            Permission.EVENT_VIEW.value,
            Permission.EVENT_CREATE.value,
            Permission.EVENT_EDIT_OWN.value,
            Permission.FILE_UPLOAD.value,
            Permission.FILE_DELETE_OWN.value,
        ],
    },
    "department_head": {
        "name": "부서장",
        "name_en": "Department Head",
        "description": "부서 태스크 및 팀원 관리",
        "permissions": [
            Permission.CAMPAIGN_VIEW.value,
            Permission.DEPARTMENT_VIEW.value,
            Permission.TASK_VIEW_DEPARTMENT.value,
            Permission.TASK_CREATE.value,
            Permission.TASK_EDIT_ALL.value,
            Permission.TASK_ASSIGN.value,
            Permission.APPROVAL_REQUEST.value,
            Permission.APPROVAL_DECIDE.value,
            Permission.EVENT_VIEW.value,
            Permission.EVENT_CREATE.value,
            Permission.EVENT_EDIT_OWN.value,
            Permission.FILE_UPLOAD.value,
            Permission.FILE_DELETE_OWN.value,
        ],
    },
    "member": {
        "name": "팀원",
        "name_en": "Team Member",
        "description": "일반 캠프 팀원",
        "permissions": [
            Permission.CAMPAIGN_VIEW.value,
            Permission.DEPARTMENT_VIEW.value,
            Permission.TASK_VIEW_DEPARTMENT.value,
            Permission.TASK_CREATE.value,
            Permission.TASK_EDIT_OWN.value,
            Permission.APPROVAL_REQUEST.value,
            Permission.EVENT_VIEW.value,
            Permission.EVENT_CREATE.value,
            Permission.EVENT_EDIT_OWN.value,
            Permission.FILE_UPLOAD.value,
            Permission.FILE_DELETE_OWN.value,
        ],
    },
    "volunteer": {
        "name": "봉사자",
        "name_en": "Volunteer",
        "description": "제한된 접근 권한",
        "permissions": [
            Permission.CAMPAIGN_VIEW.value,
            Permission.DEPARTMENT_VIEW.value,
            Permission.TASK_VIEW_DEPARTMENT.value,
            Permission.TASK_EDIT_OWN.value,
            Permission.EVENT_VIEW.value,
            Permission.FILE_UPLOAD.value,
        ],
    },
}


class Role(Base, TimestampMixin, TenantMixin):
    """
    Role definition for RBAC.

    Roles are campaign-scoped and define a set of permissions.
    System roles are created automatically and cannot be deleted.

    Attributes:
        name: Display name of the role
        slug: URL-friendly identifier (unique within campaign)
        description: Optional description of the role
        permissions: List of permission strings
        is_system: Whether this is a built-in role (cannot be deleted)
        is_default: Whether this role is assigned to new members by default
    """

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    permissions: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        back_populates="roles",
    )
    memberships: Mapped[list["CampaignMembership"]] = relationship(
        "CampaignMembership",
        back_populates="role",
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, slug='{self.slug}', campaign_id={self.campaign_id})>"

    def has_permission(self, permission: Permission | str) -> bool:
        """Check if role has a specific permission."""
        perm_value = permission.value if isinstance(permission, Permission) else permission
        return perm_value in self.permissions

    def add_permission(self, permission: Permission | str) -> None:
        """Add a permission to this role."""
        perm_value = permission.value if isinstance(permission, Permission) else permission
        if perm_value not in self.permissions:
            self.permissions = [*self.permissions, perm_value]

    def remove_permission(self, permission: Permission | str) -> None:
        """Remove a permission from this role."""
        perm_value = permission.value if isinstance(permission, Permission) else permission
        self.permissions = [p for p in self.permissions if p != perm_value]
