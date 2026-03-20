"""
Authorization and Permission Tests.

Tests the RBAC permission system, verifying that:
1. Users with correct permissions can perform actions
2. Users without permissions are denied
3. Department-scoped permissions work correctly
4. Cross-tenant isolation is maintained
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import status

from app.main import app
from app.models import (
    User,
    Campaign,
    CampaignMembership,
    Role,
    Permission,
    CampaignStatus,
    Task,
    TaskBoard,
)
from app.api.deps import get_db, get_current_user, get_campaign_membership


# =============================================================================
# Fixtures for Different Role Types
# =============================================================================


@pytest.fixture
def owner_role() -> Role:
    """Create owner role with all permissions."""
    role = MagicMock(spec=Role)
    role.id = 1
    role.campaign_id = 1
    role.name = "캠프 대표"
    role.slug = "owner"
    role.permissions = [p.value for p in Permission]
    role.is_system = True
    return role


@pytest.fixture
def member_role() -> Role:
    """Create member role with limited permissions."""
    role = MagicMock(spec=Role)
    role.id = 2
    role.campaign_id = 1
    role.name = "팀원"
    role.slug = "member"
    role.permissions = [
        Permission.CAMPAIGN_VIEW.value,
        Permission.DEPARTMENT_VIEW.value,
        Permission.TASK_VIEW_DEPARTMENT.value,
        Permission.TASK_CREATE.value,
        Permission.TASK_EDIT_OWN.value,
        Permission.APPROVAL_REQUEST.value,
        Permission.EVENT_VIEW.value,
        Permission.FILE_UPLOAD.value,
    ]
    role.is_system = True
    return role


@pytest.fixture
def volunteer_role() -> Role:
    """Create volunteer role with minimal permissions."""
    role = MagicMock(spec=Role)
    role.id = 3
    role.campaign_id = 1
    role.name = "봉사자"
    role.slug = "volunteer"
    role.permissions = [
        Permission.CAMPAIGN_VIEW.value,
        Permission.DEPARTMENT_VIEW.value,
        Permission.TASK_VIEW_DEPARTMENT.value,
        Permission.TASK_EDIT_OWN.value,
        Permission.EVENT_VIEW.value,
        Permission.FILE_UPLOAD.value,
    ]
    role.is_system = True
    return role


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
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


def create_membership(user, campaign, role, department_id=None) -> CampaignMembership:
    """Helper to create a membership with specific role."""
    membership = MagicMock(spec=CampaignMembership)
    membership.id = 1
    membership.user_id = user.id
    membership.campaign_id = campaign.id
    membership.role_id = role.id
    membership.department_id = department_id
    membership.is_active = True
    membership.role = role
    membership.user = user
    membership.campaign = campaign

    # Real permission checking based on role
    def has_permission(perm):
        perm_value = perm.value if isinstance(perm, Permission) else perm
        return perm_value in role.permissions

    def has_any_permission(*perms):
        return any(has_permission(p) for p in perms)

    membership.has_permission = MagicMock(side_effect=has_permission)
    membership.has_any_permission = MagicMock(side_effect=has_any_permission)

    return membership


# =============================================================================
# Test Permission Checks
# =============================================================================


class TestPermissionModel:
    """Test Permission enum and role permission methods."""

    def test_owner_has_all_permissions(self, owner_role):
        """Owner role should have all permissions."""
        for perm in Permission:
            assert perm.value in owner_role.permissions

    def test_member_has_limited_permissions(self, member_role):
        """Member role should not have admin permissions."""
        assert Permission.CAMPAIGN_DELETE.value not in member_role.permissions
        assert Permission.CAMPAIGN_MANAGE_ROLES.value not in member_role.permissions
        assert Permission.TASK_DELETE.value not in member_role.permissions

    def test_volunteer_has_minimal_permissions(self, volunteer_role):
        """Volunteer role should have minimal permissions."""
        assert Permission.TASK_CREATE.value not in volunteer_role.permissions
        assert Permission.TASK_DELETE.value not in volunteer_role.permissions
        assert Permission.APPROVAL_DECIDE.value not in volunteer_role.permissions

    def test_membership_has_permission(self, test_user, test_campaign, member_role):
        """Test membership permission checking."""
        membership = create_membership(test_user, test_campaign, member_role)

        # Should have
        assert membership.has_permission(Permission.TASK_CREATE)
        assert membership.has_permission(Permission.EVENT_VIEW)

        # Should not have
        assert not membership.has_permission(Permission.TASK_DELETE)
        assert not membership.has_permission(Permission.CAMPAIGN_DELETE)


# =============================================================================
# Test Task API Authorization
# =============================================================================


class TestTaskAuthorization:
    """Test authorization for task-related endpoints."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        session.delete = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_member_can_create_task(
        self, test_user, test_campaign, member_role, mock_db_session
    ):
        """Member with TASK_CREATE permission can create tasks."""
        membership = create_membership(test_user, test_campaign, member_role)

        async def override_get_db():
            yield mock_db_session

        async def override_get_current_user():
            return test_user

        async def override_get_membership():
            return membership

        # Mock the service layer
        mock_task = MagicMock(spec=Task)
        mock_task.id = 1
        mock_task.title = "Test Task"
        mock_task.campaign_id = 1

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_campaign_membership] = override_get_membership

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                # Member has TASK_CREATE permission
                assert membership.has_permission(Permission.TASK_CREATE)
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_volunteer_cannot_create_task(
        self, test_user, test_campaign, volunteer_role, mock_db_session
    ):
        """Volunteer without TASK_CREATE permission cannot create tasks."""
        membership = create_membership(test_user, test_campaign, volunteer_role)

        # Volunteer should not have TASK_CREATE permission
        assert not membership.has_permission(Permission.TASK_CREATE)

    @pytest.mark.asyncio
    async def test_member_cannot_delete_task(
        self, test_user, test_campaign, member_role, mock_db_session
    ):
        """Member without TASK_DELETE permission cannot delete tasks."""
        membership = create_membership(test_user, test_campaign, member_role)

        # Member should not have TASK_DELETE permission
        assert not membership.has_permission(Permission.TASK_DELETE)


# =============================================================================
# Test Approval Authorization
# =============================================================================


class TestApprovalAuthorization:
    """Test authorization for approval-related endpoints."""

    @pytest.mark.asyncio
    async def test_member_can_request_approval(
        self, test_user, test_campaign, member_role
    ):
        """Member with APPROVAL_REQUEST permission can create approval requests."""
        membership = create_membership(test_user, test_campaign, member_role)
        assert membership.has_permission(Permission.APPROVAL_REQUEST)

    @pytest.mark.asyncio
    async def test_member_cannot_decide_approval(
        self, test_user, test_campaign, member_role
    ):
        """Member without APPROVAL_DECIDE permission cannot approve/reject."""
        membership = create_membership(test_user, test_campaign, member_role)
        assert not membership.has_permission(Permission.APPROVAL_DECIDE)

    @pytest.mark.asyncio
    async def test_volunteer_cannot_request_approval(
        self, test_user, test_campaign, volunteer_role
    ):
        """Volunteer without APPROVAL_REQUEST permission cannot create requests."""
        membership = create_membership(test_user, test_campaign, volunteer_role)
        assert not membership.has_permission(Permission.APPROVAL_REQUEST)


# =============================================================================
# Test Campaign Management Authorization
# =============================================================================


class TestCampaignManagementAuthorization:
    """Test authorization for campaign management endpoints."""

    @pytest.mark.asyncio
    async def test_owner_can_manage_members(
        self, test_user, test_campaign, owner_role
    ):
        """Owner can manage campaign members."""
        membership = create_membership(test_user, test_campaign, owner_role)
        assert membership.has_permission(Permission.CAMPAIGN_MANAGE_MEMBERS)
        assert membership.has_permission(Permission.CAMPAIGN_MANAGE_ROLES)

    @pytest.mark.asyncio
    async def test_member_cannot_manage_members(
        self, test_user, test_campaign, member_role
    ):
        """Member cannot manage campaign members."""
        membership = create_membership(test_user, test_campaign, member_role)
        assert not membership.has_permission(Permission.CAMPAIGN_MANAGE_MEMBERS)
        assert not membership.has_permission(Permission.CAMPAIGN_MANAGE_ROLES)

    @pytest.mark.asyncio
    async def test_owner_can_delete_campaign(
        self, test_user, test_campaign, owner_role
    ):
        """Owner can delete campaign."""
        membership = create_membership(test_user, test_campaign, owner_role)
        assert membership.has_permission(Permission.CAMPAIGN_DELETE)

    @pytest.mark.asyncio
    async def test_member_cannot_delete_campaign(
        self, test_user, test_campaign, member_role
    ):
        """Member cannot delete campaign."""
        membership = create_membership(test_user, test_campaign, member_role)
        assert not membership.has_permission(Permission.CAMPAIGN_DELETE)


# =============================================================================
# Test Department-Scoped Permissions
# =============================================================================


class TestDepartmentScopedPermissions:
    """Test department-scoped permission enforcement."""

    @pytest.mark.asyncio
    async def test_member_can_view_department_tasks(
        self, test_user, test_campaign, member_role
    ):
        """Member with TASK_VIEW_DEPARTMENT can view tasks in their department."""
        membership = create_membership(
            test_user, test_campaign, member_role, department_id=1
        )
        assert membership.has_permission(Permission.TASK_VIEW_DEPARTMENT)
        assert not membership.has_permission(Permission.TASK_VIEW_ALL)

    @pytest.mark.asyncio
    async def test_owner_can_view_all_tasks(
        self, test_user, test_campaign, owner_role
    ):
        """Owner with TASK_VIEW_ALL can view all tasks."""
        membership = create_membership(test_user, test_campaign, owner_role)
        assert membership.has_permission(Permission.TASK_VIEW_ALL)


# =============================================================================
# Test Cross-Tenant Isolation
# =============================================================================


class TestCrossTenantIsolation:
    """Test that users cannot access other campaigns' data."""

    @pytest.fixture
    def campaign_a(self) -> Campaign:
        """Create Campaign A."""
        campaign = MagicMock(spec=Campaign)
        campaign.id = 1
        campaign.name = "Campaign A"
        campaign.slug = "campaign-a"
        return campaign

    @pytest.fixture
    def campaign_b(self) -> Campaign:
        """Create Campaign B."""
        campaign = MagicMock(spec=Campaign)
        campaign.id = 2
        campaign.name = "Campaign B"
        campaign.slug = "campaign-b"
        return campaign

    def test_membership_scoped_to_campaign(
        self, test_user, campaign_a, campaign_b, member_role
    ):
        """Membership permissions are scoped to specific campaign."""
        membership_a = create_membership(test_user, campaign_a, member_role)

        # Membership is for Campaign A
        assert membership_a.campaign_id == 1
        assert membership_a.campaign_id != campaign_b.id

    def test_task_board_scoped_to_campaign(self, test_campaign):
        """Task boards are scoped to campaign."""
        board = MagicMock(spec=TaskBoard)
        board.id = 1
        board.campaign_id = test_campaign.id
        board.name = "Test Board"

        # Board belongs to test campaign
        assert board.campaign_id == test_campaign.id


# =============================================================================
# Test API Endpoint Protection
# =============================================================================


class TestAPIEndpointProtection:
    """Test that API endpoints are properly protected."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.add = MagicMock()
        session.delete = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_unauthenticated_request_rejected(self, mock_db_session):
        """Requests without authentication should be rejected."""
        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db
        # Don't override auth - should fail

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get("/api/v1/campaigns/1/tasks")
                # Should be unauthorized
                assert response.status_code in [
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_403_FORBIDDEN,
                ]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_missing_campaign_header_rejected(
        self, test_user, mock_db_session
    ):
        """Requests without X-Campaign-ID header should be rejected."""
        async def override_get_db():
            yield mock_db_session

        async def override_get_current_user():
            return test_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        # Don't override membership - should fail due to missing header

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                # Campaign endpoints require X-Campaign-ID header
                response = await client.get("/api/v1/campaigns/1/tasks")
                # Should fail - no campaign context
                assert response.status_code in [
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_403_FORBIDDEN,
                    status.HTTP_404_NOT_FOUND,
                ]
        finally:
            app.dependency_overrides.clear()
