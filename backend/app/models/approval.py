"""
Approval workflow models.

Provides configurable multi-step approval chains:
- ApprovalWorkflow: Template defining approval process
- ApprovalWorkflowStep: Individual steps in the workflow
- ApprovalRequest: Instance of an approval request
- ApprovalRequestStep: Tracking decisions for each step
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.membership import CampaignMembership
    from app.models.role import Role
    from app.models.department import Department


class ApproverType(str, enum.Enum):
    """Type of approver for a workflow step."""

    MEMBER = "member"          # Specific member
    ROLE = "role"              # Any member with this role
    DEPARTMENT_HEAD = "department_head"  # Head of a department
    CREATOR_MANAGER = "creator_manager"  # Manager of the requester


class ApprovalStatus(str, enum.Enum):
    """Status of an approval request or step."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class ApprovalWorkflow(Base, TimestampMixin, TenantMixin):
    """
    Approval workflow template.

    Defines the approval process for a specific type of entity
    (e.g., tasks, documents, expenses).

    Attributes:
        name: Workflow name (e.g., "Document Approval", "Task Sign-off")
        description: Detailed description
        entity_type: Type of entity this workflow applies to
        is_active: Whether the workflow is currently active
        require_all_steps: If True, all steps must approve; if False, any step can approve
        auto_expire_hours: Hours until request auto-expires (None = no expiry)
    """

    __tablename__ = "approval_workflows"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    require_all_steps: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    auto_expire_hours: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        backref="approval_workflows",
    )
    steps: Mapped[list["ApprovalWorkflowStep"]] = relationship(
        "ApprovalWorkflowStep",
        back_populates="workflow",
        order_by="ApprovalWorkflowStep.step_order",
        cascade="all, delete-orphan",
    )
    requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="workflow",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ApprovalWorkflow(id={self.id}, name='{self.name}')>"

    @property
    def step_count(self) -> int:
        """Get number of steps in the workflow."""
        return len(self.steps)


class ApprovalWorkflowStep(Base, TimestampMixin):
    """
    Individual step in an approval workflow.

    Defines who can approve at each step and the order of steps.

    Attributes:
        workflow_id: Parent workflow
        step_order: Order in the workflow (0-indexed)
        name: Step name (e.g., "Department Head Review")
        description: Optional description
        approver_type: Type of approver (member, role, department_head)
        approver_id: ID of the approver (interpretation depends on approver_type)
        is_optional: Whether this step can be skipped
        can_reject: Whether this step can reject (or only approve/skip)
    """

    __tablename__ = "approval_workflow_steps"

    workflow_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("approval_workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    approver_type: Mapped[ApproverType] = mapped_column(
        Enum(ApproverType),
        nullable=False,
    )
    approver_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    is_optional: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    can_reject: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    workflow: Mapped["ApprovalWorkflow"] = relationship(
        "ApprovalWorkflow",
        back_populates="steps",
    )

    # Constraints
    __table_args__ = (
        Index("ix_workflow_step_order", "workflow_id", "step_order", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ApprovalWorkflowStep(id={self.id}, name='{self.name}', order={self.step_order})>"


class ApprovalRequest(Base, TimestampMixin, TenantMixin):
    """
    Instance of an approval request.

    Tracks the approval process for a specific entity.

    Attributes:
        workflow_id: Workflow being used
        entity_type: Type of entity being approved
        entity_id: ID of the entity being approved
        title: Request title
        description: Request description
        current_step_order: Current step in the workflow
        status: Overall status of the request
        requested_by_id: Member who submitted the request
        expires_at: When the request expires
        completed_at: When the request was completed
    """

    __tablename__ = "approval_requests"

    workflow_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("approval_workflows.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    entity_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    current_step_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
        index=True,
    )
    requested_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        backref="approval_requests",
    )
    workflow: Mapped["ApprovalWorkflow"] = relationship(
        "ApprovalWorkflow",
        back_populates="requests",
    )
    requested_by: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        foreign_keys=[requested_by_id],
    )
    step_decisions: Mapped[list["ApprovalRequestStep"]] = relationship(
        "ApprovalRequestStep",
        back_populates="request",
        order_by="ApprovalRequestStep.step_order",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        Index("ix_approval_request_entity", "entity_type", "entity_id"),
        Index("ix_approval_request_status", "campaign_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequest(id={self.id}, status='{self.status}')>"

    @property
    def is_pending(self) -> bool:
        """Check if request is still pending."""
        return self.status == ApprovalStatus.PENDING

    @property
    def is_completed(self) -> bool:
        """Check if request is completed (approved or rejected)."""
        return self.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)

    @property
    def current_step(self) -> Optional["ApprovalWorkflowStep"]:
        """Get the current workflow step."""
        for step in self.workflow.steps:
            if step.step_order == self.current_step_order:
                return step
        return None


class ApprovalRequestStep(Base, TimestampMixin):
    """
    Decision record for each step in an approval request.

    Tracks who decided, what they decided, and when.

    Attributes:
        request_id: Parent approval request
        workflow_step_id: The workflow step this decision is for
        step_order: Order of this step (denormalized for queries)
        status: Decision status
        decided_by_id: Member who made the decision
        decision_note: Optional note explaining the decision
        decided_at: When the decision was made
    """

    __tablename__ = "approval_request_steps"

    request_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("approval_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_step_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("approval_workflow_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
    )
    decided_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    request: Mapped["ApprovalRequest"] = relationship(
        "ApprovalRequest",
        back_populates="step_decisions",
    )
    workflow_step: Mapped["ApprovalWorkflowStep"] = relationship(
        "ApprovalWorkflowStep",
    )
    decided_by: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        foreign_keys=[decided_by_id],
    )

    # Constraints
    __table_args__ = (
        Index("ix_request_step_order", "request_id", "step_order", unique=True),
    )

    def __repr__(self) -> str:
        return f"<ApprovalRequestStep(request_id={self.request_id}, step={self.step_order}, status='{self.status}')>"

    @property
    def is_decided(self) -> bool:
        """Check if this step has been decided."""
        return self.status != ApprovalStatus.PENDING
