"""
Approval workflow schemas.

Pydantic models for approval workflow API requests and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.approval import ApproverType, ApprovalStatus


# =============================================================================
# Workflow Step Schemas
# =============================================================================


class WorkflowStepBase(BaseModel):
    """Base schema for workflow steps."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    approver_type: ApproverType
    approver_id: Optional[int] = None
    is_optional: bool = False
    can_reject: bool = True


class WorkflowStepCreate(WorkflowStepBase):
    """Schema for creating a workflow step."""

    pass


class WorkflowStepUpdate(BaseModel):
    """Schema for updating a workflow step."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    approver_type: Optional[ApproverType] = None
    approver_id: Optional[int] = None
    is_optional: Optional[bool] = None
    can_reject: Optional[bool] = None


class WorkflowStepResponse(WorkflowStepBase):
    """Schema for workflow step response."""

    id: int
    workflow_id: int
    step_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Workflow Schemas
# =============================================================================


class WorkflowBase(BaseModel):
    """Base schema for approval workflows."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    entity_type: str = Field(..., min_length=1, max_length=50)
    require_all_steps: bool = True
    auto_expire_hours: Optional[int] = Field(None, ge=1)


class WorkflowCreate(WorkflowBase):
    """Schema for creating an approval workflow."""

    steps: list[WorkflowStepCreate] = Field(default_factory=list)


class WorkflowUpdate(BaseModel):
    """Schema for updating an approval workflow."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    require_all_steps: Optional[bool] = None
    auto_expire_hours: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class WorkflowResponse(WorkflowBase):
    """Schema for approval workflow response."""

    id: int
    campaign_id: int
    is_active: bool
    step_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowDetail(WorkflowResponse):
    """Detailed workflow response including steps."""

    steps: list[WorkflowStepResponse] = []


# =============================================================================
# Request Step Schemas
# =============================================================================


class RequestStepResponse(BaseModel):
    """Schema for approval request step response."""

    id: int
    request_id: int
    workflow_step_id: int
    step_order: int
    status: ApprovalStatus
    decided_by_id: Optional[int] = None
    decision_note: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequestStepDecision(BaseModel):
    """Schema for making a decision on a request step."""

    status: ApprovalStatus = Field(
        ...,
        description="Decision: approved, rejected, or cancelled",
    )
    decision_note: Optional[str] = Field(
        None,
        max_length=2000,
        description="Optional note explaining the decision",
    )


# =============================================================================
# Approval Request Schemas
# =============================================================================


class ApprovalRequestBase(BaseModel):
    """Base schema for approval requests."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ApprovalRequestCreate(ApprovalRequestBase):
    """Schema for creating an approval request."""

    workflow_id: int
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: int


class ApprovalRequestResponse(ApprovalRequestBase):
    """Schema for approval request response."""

    id: int
    campaign_id: int
    workflow_id: int
    entity_type: str
    entity_id: int
    current_step_order: int
    status: ApprovalStatus
    requested_by_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRequestDetail(ApprovalRequestResponse):
    """Detailed approval request response including step decisions."""

    workflow: WorkflowResponse
    step_decisions: list[RequestStepResponse] = []


class ApprovalRequestList(BaseModel):
    """Paginated list of approval requests."""

    items: list[ApprovalRequestResponse]
    total: int
    page: int
    page_size: int
    pages: int


# =============================================================================
# Query Parameters
# =============================================================================


class ApprovalRequestFilter(BaseModel):
    """Filter parameters for approval requests."""

    status: Optional[ApprovalStatus] = None
    entity_type: Optional[str] = None
    requested_by_id: Optional[int] = None
    workflow_id: Optional[int] = None
    pending_for_me: bool = False
