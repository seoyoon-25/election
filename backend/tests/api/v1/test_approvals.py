"""
Tests for Approval Workflow API endpoints.

Tests cover:
- Workflow CRUD operations
- Workflow step management
- Approval request creation and listing
- Decision making (approve/reject)
- Request cancellation
- Pending requests for user
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import (
    User,
    Campaign,
    CampaignMembership,
    Role,
    Permission,
    CampaignStatus,
    ApprovalWorkflow,
    ApprovalWorkflowStep,
    ApprovalRequest,
    ApprovalRequestStep,
    ApproverType,
    ApprovalStatus,
)
from app.api.deps import get_db, get_current_user, get_campaign_membership
from app.services.approval_service import (
    ApprovalService,
    WorkflowNotFoundError,
    ApprovalRequestNotFoundError,
    InvalidApprovalStateError,
    UnauthorizedApproverError,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.avatar_url = None
    user.is_active = True
    user.is_superadmin = False
    return user


@pytest.fixture
def test_campaign() -> Campaign:
    """Create a test campaign."""
    campaign = MagicMock(spec=Campaign)
    campaign.id = 1
    campaign.name = "Test Campaign"
    campaign.slug = "test-campaign"
    campaign.status = CampaignStatus.ACTIVE
    return campaign


@pytest.fixture
def admin_role() -> Role:
    """Create an admin role with all permissions."""
    role = MagicMock(spec=Role)
    role.id = 1
    role.campaign_id = 1
    role.name = "Admin"
    role.permissions = [p.value for p in Permission]
    role.is_system = True
    return role


@pytest.fixture
def test_membership(test_user, test_campaign, admin_role) -> CampaignMembership:
    """Create a test campaign membership with admin role."""
    membership = MagicMock(spec=CampaignMembership)
    membership.id = 1
    membership.user_id = test_user.id
    membership.campaign_id = test_campaign.id
    membership.role_id = admin_role.id
    membership.is_active = True
    membership.role = admin_role
    membership.user = test_user
    membership.campaign = test_campaign
    membership.has_permission = MagicMock(return_value=True)
    membership.has_any_permission = MagicMock(return_value=True)
    return membership


@pytest.fixture
def viewer_membership(test_user, test_campaign) -> CampaignMembership:
    """Create a membership without admin permissions."""
    role = MagicMock(spec=Role)
    role.id = 2
    role.campaign_id = 1
    role.name = "Viewer"
    role.permissions = [Permission.EVENT_VIEW.value]
    role.is_system = False

    membership = MagicMock(spec=CampaignMembership)
    membership.id = 2
    membership.user_id = test_user.id
    membership.campaign_id = test_campaign.id
    membership.role_id = role.id
    membership.is_active = True
    membership.role = role
    membership.user = test_user
    membership.campaign = test_campaign
    membership.has_permission = MagicMock(return_value=False)
    membership.has_any_permission = MagicMock(return_value=False)
    return membership


@pytest.fixture
def test_workflow(test_campaign) -> ApprovalWorkflow:
    """Create a test approval workflow."""
    workflow = MagicMock(spec=ApprovalWorkflow)
    workflow.id = 1
    workflow.campaign_id = test_campaign.id
    workflow.name = "Document Approval"
    workflow.description = "Workflow for document approvals"
    workflow.entity_type = "document"
    workflow.is_active = True
    workflow.require_all_steps = True
    workflow.auto_expire_hours = 48
    workflow.steps = []
    workflow.step_count = 0
    workflow.created_at = datetime.now(timezone.utc)
    workflow.updated_at = datetime.now(timezone.utc)
    return workflow


@pytest.fixture
def test_workflow_step(test_workflow) -> ApprovalWorkflowStep:
    """Create a test workflow step."""
    step = MagicMock(spec=ApprovalWorkflowStep)
    step.id = 1
    step.workflow_id = test_workflow.id
    step.step_order = 0
    step.name = "Manager Review"
    step.description = "Review by department manager"
    step.approver_type = ApproverType.ROLE
    step.approver_id = 1
    step.is_optional = False
    step.can_reject = True
    step.created_at = datetime.now(timezone.utc)
    step.updated_at = datetime.now(timezone.utc)
    return step


@pytest.fixture
def test_approval_request(test_campaign, test_workflow, test_membership) -> ApprovalRequest:
    """Create a test approval request."""
    request = MagicMock(spec=ApprovalRequest)
    request.id = 1
    request.campaign_id = test_campaign.id
    request.workflow_id = test_workflow.id
    request.entity_type = "document"
    request.entity_id = 100
    request.title = "Approve Document #100"
    request.description = "Please review and approve this document"
    request.current_step_order = 0
    request.status = ApprovalStatus.PENDING
    request.requested_by_id = test_membership.id
    request.requested_by = test_membership
    request.expires_at = datetime.now(timezone.utc) + timedelta(hours=48)
    request.completed_at = None
    request.workflow = test_workflow
    request.step_decisions = []
    request.created_at = datetime.now(timezone.utc)
    request.updated_at = datetime.now(timezone.utc)
    return request


@pytest.fixture
def test_request_step(test_approval_request, test_workflow_step) -> ApprovalRequestStep:
    """Create a test approval request step."""
    step = MagicMock(spec=ApprovalRequestStep)
    step.id = 1
    step.request_id = test_approval_request.id
    step.workflow_step_id = test_workflow_step.id
    step.step_order = 0
    step.status = ApprovalStatus.PENDING
    step.decided_by_id = None
    step.decided_by = None
    step.decision_note = None
    step.decided_at = None
    step.workflow_step = test_workflow_step
    step.created_at = datetime.now(timezone.utc)
    step.updated_at = datetime.now(timezone.utc)
    return step


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
async def client(
    mock_db_session,
    test_user: User,
    test_membership: CampaignMembership,
):
    """Create an async test client with mocked dependencies."""

    async def override_get_db():
        yield mock_db_session

    async def override_get_current_user():
        return test_user

    async def override_get_campaign_membership():
        return test_membership

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_campaign_membership] = override_get_campaign_membership

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def viewer_client(
    mock_db_session,
    test_user: User,
    viewer_membership: CampaignMembership,
):
    """Create an async test client with viewer (non-admin) permissions."""

    async def override_get_db():
        yield mock_db_session

    async def override_get_current_user():
        return test_user

    async def override_get_campaign_membership():
        return viewer_membership

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_campaign_membership] = override_get_campaign_membership

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def unauthenticated_client(mock_db_session):
    """Create an async test client without authentication."""

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# =============================================================================
# Workflow CRUD Tests
# =============================================================================


class TestCreateWorkflow:
    """Tests for POST /approvals/workflows endpoint."""

    async def test_create_workflow_success(self, client, test_workflow):
        """Test creating a workflow successfully."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_workflow = AsyncMock(return_value=test_workflow)

            response = await client.post(
                "/api/v1/approvals/workflows",
                headers={"X-Campaign-ID": "1"},
                json={
                    "name": "Document Approval",
                    "description": "Workflow for document approvals",
                    "entity_type": "document",
                    "require_all_steps": True,
                    "auto_expire_hours": 48,
                    "steps": [],
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Document Approval"
            assert data["entity_type"] == "document"

    async def test_create_workflow_with_steps(self, client, test_workflow, test_workflow_step):
        """Test creating a workflow with initial steps."""
        test_workflow.steps = [test_workflow_step]
        test_workflow.step_count = 1

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_workflow = AsyncMock(return_value=test_workflow)

            response = await client.post(
                "/api/v1/approvals/workflows",
                headers={"X-Campaign-ID": "1"},
                json={
                    "name": "Document Approval",
                    "entity_type": "document",
                    "steps": [
                        {
                            "name": "Manager Review",
                            "approver_type": "role",
                            "approver_id": 1,
                            "is_optional": False,
                            "can_reject": True,
                        }
                    ],
                },
            )

            assert response.status_code == 201

    async def test_create_workflow_validation_error(self, client):
        """Test creating a workflow with invalid data."""
        response = await client.post(
            "/api/v1/approvals/workflows",
            headers={"X-Campaign-ID": "1"},
            json={
                "name": "",  # Empty name should fail
                "entity_type": "document",
            },
        )

        assert response.status_code == 422


class TestListWorkflows:
    """Tests for GET /approvals/workflows endpoint."""

    async def test_list_workflows_success(self, client, test_workflow):
        """Test listing workflows."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_workflows = AsyncMock(return_value=[test_workflow])

            response = await client.get(
                "/api/v1/approvals/workflows",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["name"] == "Document Approval"

    async def test_list_workflows_filter_by_entity_type(self, client, test_workflow):
        """Test listing workflows filtered by entity type."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_workflows = AsyncMock(return_value=[test_workflow])

            response = await client.get(
                "/api/v1/approvals/workflows?entity_type=document",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            mock_service.list_workflows.assert_called_once()

    async def test_list_workflows_filter_by_active(self, client, test_workflow):
        """Test listing only active workflows."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_workflows = AsyncMock(return_value=[test_workflow])

            response = await client.get(
                "/api/v1/approvals/workflows?is_active=true",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200


class TestGetWorkflow:
    """Tests for GET /approvals/workflows/{workflow_id} endpoint."""

    async def test_get_workflow_success(self, client, test_workflow, test_workflow_step):
        """Test getting a workflow with steps."""
        test_workflow.steps = [test_workflow_step]

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_workflow = AsyncMock(return_value=test_workflow)

            response = await client.get(
                "/api/v1/approvals/workflows/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Document Approval"
            assert "steps" in data

    async def test_get_workflow_not_found(self, client):
        """Test getting a non-existent workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_workflow = AsyncMock(return_value=None)

            response = await client.get(
                "/api/v1/approvals/workflows/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestUpdateWorkflow:
    """Tests for PATCH /approvals/workflows/{workflow_id} endpoint."""

    async def test_update_workflow_success(self, client, test_workflow):
        """Test updating a workflow."""
        test_workflow.name = "Updated Workflow"

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_workflow = AsyncMock(return_value=test_workflow)

            response = await client.patch(
                "/api/v1/approvals/workflows/1",
                headers={"X-Campaign-ID": "1"},
                json={"name": "Updated Workflow"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Workflow"

    async def test_update_workflow_not_found(self, client):
        """Test updating a non-existent workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_workflow = AsyncMock(
                side_effect=WorkflowNotFoundError("Workflow not found")
            )

            response = await client.patch(
                "/api/v1/approvals/workflows/999",
                headers={"X-Campaign-ID": "1"},
                json={"name": "Updated Workflow"},
            )

            assert response.status_code == 404

    async def test_update_workflow_deactivate(self, client, test_workflow):
        """Test deactivating a workflow."""
        test_workflow.is_active = False

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_workflow = AsyncMock(return_value=test_workflow)

            response = await client.patch(
                "/api/v1/approvals/workflows/1",
                headers={"X-Campaign-ID": "1"},
                json={"is_active": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_active"] is False


class TestDeleteWorkflow:
    """Tests for DELETE /approvals/workflows/{workflow_id} endpoint."""

    async def test_delete_workflow_success(self, client):
        """Test deleting (deactivating) a workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_workflow = AsyncMock(return_value=True)

            response = await client.delete(
                "/api/v1/approvals/workflows/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 204

    async def test_delete_workflow_not_found(self, client):
        """Test deleting a non-existent workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_workflow = AsyncMock(
                side_effect=WorkflowNotFoundError("Workflow not found")
            )

            response = await client.delete(
                "/api/v1/approvals/workflows/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


# =============================================================================
# Workflow Step Tests
# =============================================================================


class TestAddWorkflowStep:
    """Tests for POST /approvals/workflows/{workflow_id}/steps endpoint."""

    async def test_add_step_success(self, client, test_workflow_step):
        """Test adding a step to a workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.add_workflow_step = AsyncMock(return_value=test_workflow_step)

            response = await client.post(
                "/api/v1/approvals/workflows/1/steps",
                headers={"X-Campaign-ID": "1"},
                json={
                    "name": "Manager Review",
                    "approver_type": "role",
                    "approver_id": 1,
                    "is_optional": False,
                    "can_reject": True,
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Manager Review"

    async def test_add_step_with_position(self, client, test_workflow_step):
        """Test adding a step at a specific position."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.add_workflow_step = AsyncMock(return_value=test_workflow_step)

            response = await client.post(
                "/api/v1/approvals/workflows/1/steps?position=1",
                headers={"X-Campaign-ID": "1"},
                json={
                    "name": "Manager Review",
                    "approver_type": "role",
                    "approver_id": 1,
                },
            )

            assert response.status_code == 201

    async def test_add_step_workflow_not_found(self, client):
        """Test adding a step to non-existent workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.add_workflow_step = AsyncMock(
                side_effect=WorkflowNotFoundError("Workflow not found")
            )

            response = await client.post(
                "/api/v1/approvals/workflows/999/steps",
                headers={"X-Campaign-ID": "1"},
                json={
                    "name": "Manager Review",
                    "approver_type": "role",
                    "approver_id": 1,
                },
            )

            assert response.status_code == 404


class TestUpdateWorkflowStep:
    """Tests for PATCH /approvals/workflows/{workflow_id}/steps/{step_id} endpoint."""

    async def test_update_step_success(self, client, test_workflow_step):
        """Test updating a workflow step."""
        test_workflow_step.name = "Updated Step"

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_workflow_step = AsyncMock(return_value=test_workflow_step)

            response = await client.patch(
                "/api/v1/approvals/workflows/1/steps/1",
                headers={"X-Campaign-ID": "1"},
                json={"name": "Updated Step"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Step"

    async def test_update_step_not_found(self, client):
        """Test updating a non-existent step."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_workflow_step = AsyncMock(
                side_effect=WorkflowNotFoundError("Step not found")
            )

            response = await client.patch(
                "/api/v1/approvals/workflows/1/steps/999",
                headers={"X-Campaign-ID": "1"},
                json={"name": "Updated Step"},
            )

            assert response.status_code == 404


class TestDeleteWorkflowStep:
    """Tests for DELETE /approvals/workflows/{workflow_id}/steps/{step_id} endpoint."""

    async def test_delete_step_success(self, client):
        """Test deleting a workflow step."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_workflow_step = AsyncMock(return_value=True)

            response = await client.delete(
                "/api/v1/approvals/workflows/1/steps/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 204

    async def test_delete_step_not_found(self, client):
        """Test deleting a non-existent step."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_workflow_step = AsyncMock(
                side_effect=WorkflowNotFoundError("Step not found")
            )

            response = await client.delete(
                "/api/v1/approvals/workflows/1/steps/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestReorderWorkflowSteps:
    """Tests for PUT /approvals/workflows/{workflow_id}/steps/reorder endpoint."""

    async def test_reorder_steps_success(self, client, test_workflow_step):
        """Test reordering workflow steps."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.reorder_workflow_steps = AsyncMock(return_value=[test_workflow_step])

            response = await client.put(
                "/api/v1/approvals/workflows/1/steps/reorder",
                headers={"X-Campaign-ID": "1"},
                json=[2, 1, 3],
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_reorder_steps_workflow_not_found(self, client):
        """Test reordering steps of non-existent workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.reorder_workflow_steps = AsyncMock(
                side_effect=WorkflowNotFoundError("Workflow not found")
            )

            response = await client.put(
                "/api/v1/approvals/workflows/999/steps/reorder",
                headers={"X-Campaign-ID": "1"},
                json=[1, 2, 3],
            )

            assert response.status_code == 404


# =============================================================================
# Approval Request Tests
# =============================================================================


class TestCreateApprovalRequest:
    """Tests for POST /approvals/requests endpoint."""

    async def test_create_request_success(self, client, test_approval_request):
        """Test creating an approval request."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_request = AsyncMock(return_value=test_approval_request)

            response = await client.post(
                "/api/v1/approvals/requests",
                headers={"X-Campaign-ID": "1"},
                json={
                    "workflow_id": 1,
                    "entity_type": "document",
                    "entity_id": 100,
                    "title": "Approve Document #100",
                    "description": "Please review and approve",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Approve Document #100"
            assert data["status"] == "pending"

    async def test_create_request_workflow_not_found(self, client):
        """Test creating a request with non-existent workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_request = AsyncMock(
                side_effect=WorkflowNotFoundError("Workflow not found")
            )

            response = await client.post(
                "/api/v1/approvals/requests",
                headers={"X-Campaign-ID": "1"},
                json={
                    "workflow_id": 999,
                    "entity_type": "document",
                    "entity_id": 100,
                    "title": "Test Request",
                },
            )

            assert response.status_code == 404

    async def test_create_request_inactive_workflow(self, client):
        """Test creating a request with inactive workflow."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_request = AsyncMock(
                side_effect=InvalidApprovalStateError("Workflow is not active")
            )

            response = await client.post(
                "/api/v1/approvals/requests",
                headers={"X-Campaign-ID": "1"},
                json={
                    "workflow_id": 1,
                    "entity_type": "document",
                    "entity_id": 100,
                    "title": "Test Request",
                },
            )

            assert response.status_code == 400


class TestListApprovalRequests:
    """Tests for GET /approvals/requests endpoint."""

    async def test_list_requests_success(self, client, test_approval_request):
        """Test listing approval requests."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_requests = AsyncMock(
                return_value=([test_approval_request], 1)
            )

            response = await client.get(
                "/api/v1/approvals/requests",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert data["total"] == 1

    async def test_list_requests_with_status_filter(self, client, test_approval_request):
        """Test listing requests filtered by status."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_requests = AsyncMock(
                return_value=([test_approval_request], 1)
            )

            response = await client.get(
                "/api/v1/approvals/requests?status=pending",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200

    async def test_list_requests_pagination(self, client, test_approval_request):
        """Test listing requests with pagination."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_requests = AsyncMock(
                return_value=([test_approval_request], 50)
            )

            response = await client.get(
                "/api/v1/approvals/requests?page=2&page_size=10",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["page"] == 2
            assert data["page_size"] == 10


class TestGetPendingRequests:
    """Tests for GET /approvals/requests/pending endpoint."""

    async def test_get_pending_success(self, client, test_approval_request):
        """Test getting pending requests for current user."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_pending_for_member = AsyncMock(
                return_value=([test_approval_request], 1)
            )

            response = await client.get(
                "/api/v1/approvals/requests/pending",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 1

    async def test_get_pending_empty(self, client):
        """Test getting pending requests when none exist."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_pending_for_member = AsyncMock(
                return_value=([], 0)
            )

            response = await client.get(
                "/api/v1/approvals/requests/pending",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0


class TestGetApprovalRequest:
    """Tests for GET /approvals/requests/{request_id} endpoint."""

    async def test_get_request_success(self, client, test_approval_request, test_request_step):
        """Test getting an approval request with details."""
        test_approval_request.step_decisions = [test_request_step]

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_request = AsyncMock(return_value=test_approval_request)

            response = await client.get(
                "/api/v1/approvals/requests/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Approve Document #100"
            assert "step_decisions" in data

    async def test_get_request_not_found(self, client):
        """Test getting a non-existent request."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_request = AsyncMock(return_value=None)

            response = await client.get(
                "/api/v1/approvals/requests/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


# =============================================================================
# Decision Tests
# =============================================================================


class TestDecideOnRequest:
    """Tests for POST /approvals/requests/{request_id}/decide endpoint."""

    async def test_approve_success(self, client, test_approval_request):
        """Test approving a request."""
        test_approval_request.status = ApprovalStatus.APPROVED

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.make_decision = AsyncMock(return_value=test_approval_request)

            response = await client.post(
                "/api/v1/approvals/requests/1/decide",
                headers={"X-Campaign-ID": "1"},
                json={
                    "status": "approved",
                    "decision_note": "Looks good!",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "approved"

    async def test_reject_success(self, client, test_approval_request):
        """Test rejecting a request."""
        test_approval_request.status = ApprovalStatus.REJECTED

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.make_decision = AsyncMock(return_value=test_approval_request)

            response = await client.post(
                "/api/v1/approvals/requests/1/decide",
                headers={"X-Campaign-ID": "1"},
                json={
                    "status": "rejected",
                    "decision_note": "Needs more work",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "rejected"

    async def test_decide_request_not_found(self, client):
        """Test deciding on a non-existent request."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.make_decision = AsyncMock(
                side_effect=ApprovalRequestNotFoundError("Request not found")
            )

            response = await client.post(
                "/api/v1/approvals/requests/999/decide",
                headers={"X-Campaign-ID": "1"},
                json={"status": "approved"},
            )

            assert response.status_code == 404

    async def test_decide_already_completed(self, client):
        """Test deciding on an already completed request."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.make_decision = AsyncMock(
                side_effect=InvalidApprovalStateError("Request is not pending")
            )

            response = await client.post(
                "/api/v1/approvals/requests/1/decide",
                headers={"X-Campaign-ID": "1"},
                json={"status": "approved"},
            )

            assert response.status_code == 400

    async def test_decide_unauthorized_approver(self, client):
        """Test deciding without authorization."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.make_decision = AsyncMock(
                side_effect=UnauthorizedApproverError("Not authorized to approve")
            )

            response = await client.post(
                "/api/v1/approvals/requests/1/decide",
                headers={"X-Campaign-ID": "1"},
                json={"status": "approved"},
            )

            assert response.status_code == 403

    async def test_decide_expired_request(self, client):
        """Test deciding on an expired request."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.make_decision = AsyncMock(
                side_effect=InvalidApprovalStateError("Request has expired")
            )

            response = await client.post(
                "/api/v1/approvals/requests/1/decide",
                headers={"X-Campaign-ID": "1"},
                json={"status": "approved"},
            )

            assert response.status_code == 400


# =============================================================================
# Cancel Tests
# =============================================================================


class TestCancelRequest:
    """Tests for POST /approvals/requests/{request_id}/cancel endpoint."""

    async def test_cancel_success(self, client, test_approval_request):
        """Test cancelling a request."""
        test_approval_request.status = ApprovalStatus.CANCELLED

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.cancel_request = AsyncMock(return_value=test_approval_request)

            response = await client.post(
                "/api/v1/approvals/requests/1/cancel",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cancelled"

    async def test_cancel_not_found(self, client):
        """Test cancelling a non-existent request."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.cancel_request = AsyncMock(
                side_effect=ApprovalRequestNotFoundError("Request not found")
            )

            response = await client.post(
                "/api/v1/approvals/requests/999/cancel",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404

    async def test_cancel_already_completed(self, client):
        """Test cancelling an already completed request."""
        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.cancel_request = AsyncMock(
                side_effect=InvalidApprovalStateError("Only pending requests can be cancelled")
            )

            response = await client.post(
                "/api/v1/approvals/requests/1/cancel",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 400


# =============================================================================
# Authentication Tests
# =============================================================================


class TestAuthentication:
    """Tests for authentication requirements."""

    async def test_workflows_requires_auth(self, unauthenticated_client):
        """Test that workflows endpoint requires authentication."""
        response = await unauthenticated_client.get("/api/v1/approvals/workflows")
        assert response.status_code == 401

    async def test_requests_requires_auth(self, unauthenticated_client):
        """Test that requests endpoint requires authentication."""
        response = await unauthenticated_client.get("/api/v1/approvals/requests")
        assert response.status_code == 401

    async def test_create_workflow_requires_auth(self, unauthenticated_client):
        """Test that creating a workflow requires authentication."""
        response = await unauthenticated_client.post(
            "/api/v1/approvals/workflows",
            json={
                "name": "Test",
                "entity_type": "document",
            },
        )
        assert response.status_code == 401

    async def test_decide_requires_auth(self, unauthenticated_client):
        """Test that deciding requires authentication."""
        response = await unauthenticated_client.post(
            "/api/v1/approvals/requests/1/decide",
            json={"status": "approved"},
        )
        assert response.status_code == 401


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and complex scenarios."""

    async def test_create_workflow_all_approver_types(self, client, test_workflow):
        """Test creating workflow with different approver types."""
        for approver_type in ["member", "role", "department_head", "creator_manager"]:
            with patch(
                "app.api.v1.approvals.ApprovalService"
            ) as MockService:
                mock_service = MockService.return_value
                mock_service.create_workflow = AsyncMock(return_value=test_workflow)

                response = await client.post(
                    "/api/v1/approvals/workflows",
                    headers={"X-Campaign-ID": "1"},
                    json={
                        "name": f"Workflow with {approver_type}",
                        "entity_type": "document",
                        "steps": [
                            {
                                "name": "Step 1",
                                "approver_type": approver_type,
                                "approver_id": 1 if approver_type != "creator_manager" else None,
                            }
                        ],
                    },
                )

                assert response.status_code == 201

    async def test_list_requests_all_statuses(self, client, test_approval_request):
        """Test listing requests with different status filters."""
        for status in ["pending", "approved", "rejected", "cancelled", "expired"]:
            with patch(
                "app.api.v1.approvals.ApprovalService"
            ) as MockService:
                mock_service = MockService.return_value
                mock_service.list_requests = AsyncMock(return_value=([], 0))

                response = await client.get(
                    f"/api/v1/approvals/requests?status={status}",
                    headers={"X-Campaign-ID": "1"},
                )

                assert response.status_code == 200

    async def test_multi_step_workflow_progression(self, client, test_approval_request):
        """Test approval through multiple steps."""
        # First step approved, moves to next step
        test_approval_request.current_step_order = 1
        test_approval_request.status = ApprovalStatus.PENDING

        with patch(
            "app.api.v1.approvals.ApprovalService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.make_decision = AsyncMock(return_value=test_approval_request)

            response = await client.post(
                "/api/v1/approvals/requests/1/decide",
                headers={"X-Campaign-ID": "1"},
                json={"status": "approved"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["current_step_order"] == 1
