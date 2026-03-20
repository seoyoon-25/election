"""
Approval workflow API endpoints.

Provides endpoints for managing approval workflows and processing requests.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db,
    require_permission,
    CampaignMember,
)
from app.models import Permission, ApprovalStatus
from app.schemas.base import PaginatedResponse, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.schemas.approval import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowDetail,
    WorkflowStepCreate,
    WorkflowStepUpdate,
    WorkflowStepResponse,
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalRequestDetail,
    ApprovalRequestList,
    RequestStepDecision,
    ApprovalRequestFilter,
)
from app.services.approval_service import (
    ApprovalService,
    WorkflowNotFoundError,
    ApprovalRequestNotFoundError,
    InvalidApprovalStateError,
    UnauthorizedApproverError,
)


router = APIRouter(prefix="/approvals", tags=["Approvals"])


# =============================================================================
# Workflow Endpoints
# =============================================================================


@router.post(
    "/workflows",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow(
    data: WorkflowCreate,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.APPROVAL_MANAGE_WORKFLOWS))] = None,
):
    """Create a new approval workflow."""
    service = ApprovalService(db)
    workflow = await service.create_workflow(membership.campaign_id, data)
    return workflow


@router.get("/workflows", response_model=PaginatedResponse[WorkflowResponse])
async def list_workflows(
    membership: CampaignMember,
    entity_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """List approval workflows for the campaign with pagination."""
    service = ApprovalService(db)
    workflows, total = await service.list_workflows(
        membership.campaign_id,
        entity_type=entity_type,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse.create(
        items=workflows,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/workflows/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(
    workflow_id: int,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific workflow with its steps."""
    service = ApprovalService(db)
    workflow = await service.get_workflow(workflow_id, membership.campaign_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    return workflow


@router.patch("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: int,
    data: WorkflowUpdate,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.APPROVAL_MANAGE_WORKFLOWS))] = None,
):
    """Update a workflow."""
    service = ApprovalService(db)
    try:
        workflow = await service.update_workflow(
            workflow_id, membership.campaign_id, data
        )
        return workflow
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/workflows/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: int,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.APPROVAL_MANAGE_WORKFLOWS))] = None,
):
    """Delete (deactivate) a workflow."""
    service = ApprovalService(db)
    try:
        await service.delete_workflow(workflow_id, membership.campaign_id)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# Workflow Step Endpoints
# =============================================================================


@router.post(
    "/workflows/{workflow_id}/steps",
    response_model=WorkflowStepResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workflow_step(
    workflow_id: int,
    data: WorkflowStepCreate,
    membership: CampaignMember,
    position: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.APPROVAL_MANAGE_WORKFLOWS))] = None,
):
    """Add a step to a workflow."""
    service = ApprovalService(db)
    try:
        step = await service.add_workflow_step(
            workflow_id, membership.campaign_id, data, position
        )
        return step
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch(
    "/workflows/{workflow_id}/steps/{step_id}",
    response_model=WorkflowStepResponse,
)
async def update_workflow_step(
    workflow_id: int,
    step_id: int,
    data: WorkflowStepUpdate,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.APPROVAL_MANAGE_WORKFLOWS))] = None,
):
    """Update a workflow step."""
    service = ApprovalService(db)
    try:
        step = await service.update_workflow_step(
            step_id, workflow_id, membership.campaign_id, data
        )
        return step
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/workflows/{workflow_id}/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workflow_step(
    workflow_id: int,
    step_id: int,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.APPROVAL_MANAGE_WORKFLOWS))] = None,
):
    """Delete a workflow step."""
    service = ApprovalService(db)
    try:
        await service.delete_workflow_step(step_id, workflow_id, membership.campaign_id)
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    "/workflows/{workflow_id}/steps/reorder",
    response_model=list[WorkflowStepResponse],
)
async def reorder_workflow_steps(
    workflow_id: int,
    step_ids: list[int],
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
    _: Annotated[None, Depends(require_permission(Permission.APPROVAL_MANAGE_WORKFLOWS))] = None,
):
    """Reorder workflow steps."""
    service = ApprovalService(db)
    try:
        steps = await service.reorder_workflow_steps(
            workflow_id, membership.campaign_id, step_ids
        )
        return steps
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


# =============================================================================
# Approval Request Endpoints
# =============================================================================


@router.post(
    "/requests",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_approval_request(
    data: ApprovalRequestCreate,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
):
    """Create a new approval request."""
    service = ApprovalService(db)
    try:
        request = await service.create_request(
            membership.campaign_id, membership.id, data
        )
        return request
    except WorkflowNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidApprovalStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/requests", response_model=ApprovalRequestList)
async def list_approval_requests(
    membership: CampaignMember,
    status_filter: Optional[ApprovalStatus] = Query(None, alias="status"),
    entity_type: Optional[str] = Query(None),
    requested_by_id: Optional[int] = Query(None),
    workflow_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List approval requests."""
    service = ApprovalService(db)
    filters = ApprovalRequestFilter(
        status=status_filter,
        entity_type=entity_type,
        requested_by_id=requested_by_id,
        workflow_id=workflow_id,
    )
    requests, total = await service.list_requests(
        membership.campaign_id,
        filters,
        page=page,
        page_size=page_size,
    )
    return ApprovalRequestList(
        items=requests,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/requests/pending", response_model=ApprovalRequestList)
async def get_pending_requests(
    membership: CampaignMember,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get approval requests pending for the current user."""
    service = ApprovalService(db)
    requests, total = await service.get_pending_for_member(
        membership.campaign_id,
        membership.id,
        page=page,
        page_size=page_size,
    )
    return ApprovalRequestList(
        items=requests,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.get("/requests/{request_id}", response_model=ApprovalRequestDetail)
async def get_approval_request(
    request_id: int,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific approval request."""
    service = ApprovalService(db)
    request = await service.get_request(request_id, membership.campaign_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found",
        )
    return request


@router.post("/requests/{request_id}/decide", response_model=ApprovalRequestResponse)
async def decide_on_request(
    request_id: int,
    decision: RequestStepDecision,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
):
    """Make a decision on an approval request."""
    service = ApprovalService(db)
    try:
        request = await service.make_decision(
            request_id, membership.campaign_id, membership.id, decision
        )
        return request
    except ApprovalRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidApprovalStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except UnauthorizedApproverError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )


@router.post(
    "/requests/{request_id}/cancel",
    response_model=ApprovalRequestResponse,
)
async def cancel_approval_request(
    request_id: int,
    membership: CampaignMember,
    db: AsyncSession = Depends(get_db),
):
    """Cancel an approval request."""
    service = ApprovalService(db)
    try:
        request = await service.cancel_request(
            request_id, membership.campaign_id, membership.id
        )
        return request
    except ApprovalRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidApprovalStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
