"""
Approval workflow service.

Business logic for managing approval workflows and requests.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    ApprovalRequest,
    ApprovalRequestStep,
    ApprovalStatus,
    ApproverType,
    CampaignMembership,
    Role,
)
from app.schemas.approval import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowStepCreate,
    WorkflowStepUpdate,
    ApprovalRequestCreate,
    RequestStepDecision,
    ApprovalRequestFilter,
)


# =============================================================================
# Exceptions
# =============================================================================


class WorkflowNotFoundError(Exception):
    """Raised when workflow is not found."""

    pass


class ApprovalRequestNotFoundError(Exception):
    """Raised when approval request is not found."""

    pass


class InvalidApprovalStateError(Exception):
    """Raised when approval action is invalid for current state."""

    pass


class UnauthorizedApproverError(Exception):
    """Raised when user is not authorized to approve."""

    pass


# =============================================================================
# Workflow Service
# =============================================================================


class ApprovalService:
    """Service for managing approval workflows and requests."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------------------------------------------------------
    # Workflow Management
    # -------------------------------------------------------------------------

    async def create_workflow(
        self,
        campaign_id: int,
        data: WorkflowCreate,
    ) -> ApprovalWorkflow:
        """Create a new approval workflow with steps."""
        workflow = ApprovalWorkflow(
            campaign_id=campaign_id,
            name=data.name,
            description=data.description,
            entity_type=data.entity_type,
            require_all_steps=data.require_all_steps,
            auto_expire_hours=data.auto_expire_hours,
            is_active=True,
        )
        self.db.add(workflow)
        await self.db.flush()

        # Add steps
        for order, step_data in enumerate(data.steps):
            step = ApprovalWorkflowStep(
                workflow_id=workflow.id,
                step_order=order,
                name=step_data.name,
                description=step_data.description,
                approver_type=step_data.approver_type,
                approver_id=step_data.approver_id,
                is_optional=step_data.is_optional,
                can_reject=step_data.can_reject,
            )
            self.db.add(step)

        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def get_workflow(
        self,
        workflow_id: int,
        campaign_id: int,
    ) -> Optional[ApprovalWorkflow]:
        """Get a workflow by ID."""
        result = await self.db.execute(
            select(ApprovalWorkflow)
            .options(selectinload(ApprovalWorkflow.steps))
            .where(
                ApprovalWorkflow.id == workflow_id,
                ApprovalWorkflow.campaign_id == campaign_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self,
        campaign_id: int,
        entity_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ApprovalWorkflow], int]:
        """
        List workflows for a campaign with pagination.

        Returns:
            Tuple of (workflows list, total count)
        """
        # Build base conditions
        base_conditions = [ApprovalWorkflow.campaign_id == campaign_id]

        if entity_type:
            base_conditions.append(ApprovalWorkflow.entity_type == entity_type)
        if is_active is not None:
            base_conditions.append(ApprovalWorkflow.is_active == is_active)

        # Count total
        count_query = select(func.count(ApprovalWorkflow.id)).where(*base_conditions)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated data
        offset = (page - 1) * page_size
        query = (
            select(ApprovalWorkflow)
            .options(selectinload(ApprovalWorkflow.steps))
            .where(*base_conditions)
            .order_by(ApprovalWorkflow.name)
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        workflows = list(result.scalars().all())

        return workflows, total

    async def update_workflow(
        self,
        workflow_id: int,
        campaign_id: int,
        data: WorkflowUpdate,
    ) -> ApprovalWorkflow:
        """Update a workflow."""
        workflow = await self.get_workflow(workflow_id, campaign_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workflow, field, value)

        await self.db.commit()
        await self.db.refresh(workflow)
        return workflow

    async def delete_workflow(
        self,
        workflow_id: int,
        campaign_id: int,
    ) -> bool:
        """Delete a workflow (soft delete by deactivating)."""
        workflow = await self.get_workflow(workflow_id, campaign_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        workflow.is_active = False
        await self.db.commit()
        return True

    # -------------------------------------------------------------------------
    # Workflow Steps Management
    # -------------------------------------------------------------------------

    async def add_workflow_step(
        self,
        workflow_id: int,
        campaign_id: int,
        data: WorkflowStepCreate,
        position: Optional[int] = None,
    ) -> ApprovalWorkflowStep:
        """Add a step to a workflow."""
        workflow = await self.get_workflow(workflow_id, campaign_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        # Determine step order
        if position is None:
            step_order = len(workflow.steps)
        else:
            step_order = position
            # Shift existing steps
            for step in workflow.steps:
                if step.step_order >= position:
                    step.step_order += 1

        step = ApprovalWorkflowStep(
            workflow_id=workflow_id,
            step_order=step_order,
            name=data.name,
            description=data.description,
            approver_type=data.approver_type,
            approver_id=data.approver_id,
            is_optional=data.is_optional,
            can_reject=data.can_reject,
        )
        self.db.add(step)
        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def update_workflow_step(
        self,
        step_id: int,
        workflow_id: int,
        campaign_id: int,
        data: WorkflowStepUpdate,
    ) -> ApprovalWorkflowStep:
        """Update a workflow step."""
        workflow = await self.get_workflow(workflow_id, campaign_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        step = next((s for s in workflow.steps if s.id == step_id), None)
        if not step:
            raise WorkflowNotFoundError(f"Step {step_id} not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(step, field, value)

        await self.db.commit()
        await self.db.refresh(step)
        return step

    async def delete_workflow_step(
        self,
        step_id: int,
        workflow_id: int,
        campaign_id: int,
    ) -> bool:
        """Delete a workflow step and reorder remaining steps."""
        workflow = await self.get_workflow(workflow_id, campaign_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        step = next((s for s in workflow.steps if s.id == step_id), None)
        if not step:
            raise WorkflowNotFoundError(f"Step {step_id} not found")

        deleted_order = step.step_order
        await self.db.delete(step)

        # Reorder remaining steps
        for s in workflow.steps:
            if s.step_order > deleted_order:
                s.step_order -= 1

        await self.db.commit()
        return True

    async def reorder_workflow_steps(
        self,
        workflow_id: int,
        campaign_id: int,
        step_ids: list[int],
    ) -> list[ApprovalWorkflowStep]:
        """Reorder workflow steps."""
        workflow = await self.get_workflow(workflow_id, campaign_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")

        step_map = {s.id: s for s in workflow.steps}

        for order, step_id in enumerate(step_ids):
            if step_id in step_map:
                step_map[step_id].step_order = order

        await self.db.commit()
        return sorted(workflow.steps, key=lambda s: s.step_order)

    # -------------------------------------------------------------------------
    # Approval Request Management
    # -------------------------------------------------------------------------

    async def create_request(
        self,
        campaign_id: int,
        requested_by_id: int,
        data: ApprovalRequestCreate,
    ) -> ApprovalRequest:
        """Create a new approval request."""
        workflow = await self.get_workflow(data.workflow_id, campaign_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {data.workflow_id} not found")
        if not workflow.is_active:
            raise InvalidApprovalStateError("Workflow is not active")

        # Calculate expiration
        expires_at = None
        if workflow.auto_expire_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=workflow.auto_expire_hours)

        request = ApprovalRequest(
            campaign_id=campaign_id,
            workflow_id=data.workflow_id,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            title=data.title,
            description=data.description,
            current_step_order=0,
            status=ApprovalStatus.PENDING,
            requested_by_id=requested_by_id,
            expires_at=expires_at,
        )
        self.db.add(request)
        await self.db.flush()

        # Create step decision records for each workflow step
        for step in workflow.steps:
            step_decision = ApprovalRequestStep(
                request_id=request.id,
                workflow_step_id=step.id,
                step_order=step.step_order,
                status=ApprovalStatus.PENDING,
            )
            self.db.add(step_decision)

        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def get_request(
        self,
        request_id: int,
        campaign_id: int,
    ) -> Optional[ApprovalRequest]:
        """Get an approval request by ID."""
        result = await self.db.execute(
            select(ApprovalRequest)
            .options(
                selectinload(ApprovalRequest.workflow).selectinload(
                    ApprovalWorkflow.steps
                ),
                selectinload(ApprovalRequest.step_decisions),
            )
            .where(
                ApprovalRequest.id == request_id,
                ApprovalRequest.campaign_id == campaign_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        campaign_id: int,
        filters: ApprovalRequestFilter,
        member_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ApprovalRequest], int]:
        """List approval requests with filtering."""
        # Base query with eager loading to prevent N+1 queries
        query = (
            select(ApprovalRequest)
            .options(
                selectinload(ApprovalRequest.workflow).selectinload(
                    ApprovalWorkflow.steps
                ),
                selectinload(ApprovalRequest.step_decisions),
            )
            .where(ApprovalRequest.campaign_id == campaign_id)
        )

        if filters.status:
            query = query.where(ApprovalRequest.status == filters.status)
        if filters.entity_type:
            query = query.where(ApprovalRequest.entity_type == filters.entity_type)
        if filters.requested_by_id:
            query = query.where(
                ApprovalRequest.requested_by_id == filters.requested_by_id
            )
        if filters.workflow_id:
            query = query.where(ApprovalRequest.workflow_id == filters.workflow_id)

        # Count total (without options for efficiency)
        count_query = select(func.count()).select_from(
            select(ApprovalRequest.id)
            .where(ApprovalRequest.campaign_id == campaign_id)
            .subquery()
        )
        if filters.status:
            count_query = select(func.count()).select_from(
                select(ApprovalRequest.id)
                .where(
                    ApprovalRequest.campaign_id == campaign_id,
                    ApprovalRequest.status == filters.status,
                )
                .subquery()
            )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # Paginate
        query = query.order_by(ApprovalRequest.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def make_decision(
        self,
        request_id: int,
        campaign_id: int,
        member_id: int,
        decision: RequestStepDecision,
    ) -> ApprovalRequest:
        """Make a decision on the current step of an approval request."""
        request = await self.get_request(request_id, campaign_id)
        if not request:
            raise ApprovalRequestNotFoundError(f"Request {request_id} not found")

        if request.status != ApprovalStatus.PENDING:
            raise InvalidApprovalStateError(
                f"Request is not pending (status: {request.status})"
            )

        # Check expiration
        if request.expires_at and datetime.utcnow() > request.expires_at:
            request.status = ApprovalStatus.EXPIRED
            await self.db.commit()
            raise InvalidApprovalStateError("Request has expired")

        # Get current step
        current_step_decision = next(
            (s for s in request.step_decisions if s.step_order == request.current_step_order),
            None,
        )
        if not current_step_decision:
            raise InvalidApprovalStateError("No pending step found")

        # Verify user is authorized to approve
        await self._verify_approver(request, current_step_decision, member_id)

        # Record the decision
        current_step_decision.status = decision.status
        current_step_decision.decided_by_id = member_id
        current_step_decision.decision_note = decision.decision_note
        current_step_decision.decided_at = datetime.utcnow()

        # Process the decision
        if decision.status == ApprovalStatus.REJECTED:
            request.status = ApprovalStatus.REJECTED
            request.completed_at = datetime.utcnow()
        elif decision.status == ApprovalStatus.APPROVED:
            # Check if there are more steps
            next_step_order = request.current_step_order + 1
            remaining_steps = [
                s for s in request.step_decisions if s.step_order >= next_step_order
            ]

            if remaining_steps and request.workflow.require_all_steps:
                # Move to next step
                request.current_step_order = next_step_order
            else:
                # All steps completed or any-approval mode
                request.status = ApprovalStatus.APPROVED
                request.completed_at = datetime.utcnow()
        elif decision.status == ApprovalStatus.CANCELLED:
            request.status = ApprovalStatus.CANCELLED
            request.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def cancel_request(
        self,
        request_id: int,
        campaign_id: int,
        cancelled_by_id: int,
    ) -> ApprovalRequest:
        """Cancel an approval request."""
        request = await self.get_request(request_id, campaign_id)
        if not request:
            raise ApprovalRequestNotFoundError(f"Request {request_id} not found")

        if request.status != ApprovalStatus.PENDING:
            raise InvalidApprovalStateError("Only pending requests can be cancelled")

        # Only requester or admin can cancel
        if request.requested_by_id != cancelled_by_id:
            # Check if user has admin permission (would need to verify separately)
            pass

        request.status = ApprovalStatus.CANCELLED
        request.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def _verify_approver(
        self,
        request: ApprovalRequest,
        step_decision: ApprovalRequestStep,
        member_id: int,
    ) -> bool:
        """Verify that a member is authorized to approve a step."""
        workflow_step = step_decision.workflow_step

        if workflow_step.approver_type == ApproverType.MEMBER:
            # Specific member must approve
            if workflow_step.approver_id != member_id:
                raise UnauthorizedApproverError(
                    "You are not authorized to approve this step"
                )

        elif workflow_step.approver_type == ApproverType.ROLE:
            # Any member with the specified role can approve
            result = await self.db.execute(
                select(CampaignMembership).where(
                    CampaignMembership.id == member_id,
                    CampaignMembership.role_id == workflow_step.approver_id,
                )
            )
            if not result.scalar_one_or_none():
                raise UnauthorizedApproverError(
                    "You do not have the required role to approve this step"
                )

        elif workflow_step.approver_type == ApproverType.DEPARTMENT_HEAD:
            # Department head must approve
            result = await self.db.execute(
                select(CampaignMembership).where(
                    CampaignMembership.id == member_id,
                    CampaignMembership.department_id == workflow_step.approver_id,
                    CampaignMembership.is_department_head == True,
                )
            )
            if not result.scalar_one_or_none():
                raise UnauthorizedApproverError(
                    "You are not the department head for this step"
                )

        elif workflow_step.approver_type == ApproverType.CREATOR_MANAGER:
            # Manager of the request creator must approve
            # This requires looking up the requester's manager
            requester = await self.db.execute(
                select(CampaignMembership).where(
                    CampaignMembership.id == request.requested_by_id
                )
            )
            requester_membership = requester.scalar_one_or_none()
            if not requester_membership or requester_membership.reports_to_id != member_id:
                raise UnauthorizedApproverError(
                    "You are not the manager of the request creator"
                )

        return True

    async def get_pending_for_member(
        self,
        campaign_id: int,
        member_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ApprovalRequest], int]:
        """Get approval requests pending for a specific member."""
        # Get member info for role-based checks
        member_result = await self.db.execute(
            select(CampaignMembership).where(CampaignMembership.id == member_id)
        )
        member = member_result.scalar_one_or_none()
        if not member:
            return [], 0

        # Build query for pending requests where member can approve
        query = (
            select(ApprovalRequest)
            .join(ApprovalRequestStep)
            .join(ApprovalWorkflowStep)
            .where(
                ApprovalRequest.campaign_id == campaign_id,
                ApprovalRequest.status == ApprovalStatus.PENDING,
                ApprovalRequestStep.step_order == ApprovalRequest.current_step_order,
                ApprovalRequestStep.status == ApprovalStatus.PENDING,
            )
            .where(
                or_(
                    # Specific member approver
                    and_(
                        ApprovalWorkflowStep.approver_type == ApproverType.MEMBER,
                        ApprovalWorkflowStep.approver_id == member_id,
                    ),
                    # Role-based approver
                    and_(
                        ApprovalWorkflowStep.approver_type == ApproverType.ROLE,
                        ApprovalWorkflowStep.approver_id == member.role_id,
                    ),
                    # Department head approver
                    and_(
                        ApprovalWorkflowStep.approver_type == ApproverType.DEPARTMENT_HEAD,
                        ApprovalWorkflowStep.approver_id == member.department_id,
                        member.is_department_head == True,
                    ),
                )
            )
        )

        # Count total
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Paginate
        query = query.order_by(ApprovalRequest.created_at.asc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total
