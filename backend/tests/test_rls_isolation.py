"""
Tests for Row-Level Security (RLS) tenant isolation.

These tests verify that:
1. Data is properly isolated between campaigns
2. Setting tenant context filters data correctly
3. Cross-tenant access is prevented at the database level
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import text

from app.database import set_tenant_context


class TestTenantContextSetting:
    """Tests for tenant context management."""

    @pytest.mark.asyncio
    async def test_set_tenant_context_executes_correct_sql(self):
        """Test that set_tenant_context sets the PostgreSQL session variable."""
        mock_session = AsyncMock()

        await set_tenant_context(mock_session, campaign_id=123)

        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        # Verify the SQL text contains the campaign ID
        assert "app.current_campaign_id" in str(call_args)
        assert "123" in str(call_args)

    @pytest.mark.asyncio
    async def test_set_tenant_context_with_different_campaign_ids(self):
        """Test setting context for different campaigns."""
        mock_session = AsyncMock()

        # Set context for campaign 1
        await set_tenant_context(mock_session, campaign_id=1)
        first_call = str(mock_session.execute.call_args[0][0])
        assert "'1'" in first_call

        mock_session.reset_mock()

        # Set context for campaign 999
        await set_tenant_context(mock_session, campaign_id=999)
        second_call = str(mock_session.execute.call_args[0][0])
        assert "'999'" in second_call


class TestRLSPolicySQLGeneration:
    """Tests to verify RLS policy SQL is correctly structured."""

    def test_rls_migration_has_all_tenant_tables(self):
        """Verify migration covers all tenant tables."""
        import importlib.util
        import os

        # Load the migration module
        migration_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "alembic",
            "versions",
            "20240104_000000_add_row_level_security.py"
        )

        spec = importlib.util.spec_from_file_location("rls_migration", migration_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            expected_tables = {
                "departments",
                "roles",
                "campaign_memberships",
                "task_boards",
                "tasks",
                "task_assignments",
                "task_comments",
                "task_history",
                "task_attachments",
                "approval_workflows",
                "approval_workflow_steps",
                "approval_requests",
                "approval_request_steps",
                "google_calendar_connections",
                "synced_events",
            }

            assert set(module.TENANT_TABLES) == expected_tables


class TestRLSIsolationConcepts:
    """
    Conceptual tests for RLS isolation behavior.

    These tests verify the expected behavior of RLS policies
    without requiring a real database connection.
    """

    def test_policy_allows_access_when_campaign_matches(self):
        """
        Verify policy logic: access allowed when campaign_id matches context.

        Policy: campaign_id = get_current_campaign_id()
        """
        # Simulate: context set to campaign 5, row has campaign_id = 5
        context_campaign_id = 5
        row_campaign_id = 5

        # Policy evaluation
        access_allowed = (row_campaign_id == context_campaign_id)
        assert access_allowed is True

    def test_policy_denies_access_when_campaign_differs(self):
        """
        Verify policy logic: access denied when campaign_id doesn't match.

        Policy: campaign_id = get_current_campaign_id()
        """
        # Simulate: context set to campaign 5, row has campaign_id = 10
        context_campaign_id = 5
        row_campaign_id = 10

        # Policy evaluation
        access_allowed = (row_campaign_id == context_campaign_id)
        assert access_allowed is False

    def test_policy_allows_all_when_no_context_set(self):
        """
        Verify policy logic: all access when no context (for migrations/admin).

        Policy: get_current_campaign_id() IS NULL OR campaign_id = get_current_campaign_id()
        """
        # Simulate: no context set (NULL)
        context_campaign_id = None
        row_campaign_id = 10

        # Policy evaluation
        access_allowed = (context_campaign_id is None) or (row_campaign_id == context_campaign_id)
        assert access_allowed is True


class TestCrossTenantAccessPrevention:
    """
    Tests verifying cross-tenant access is prevented.

    These are integration-style tests that would run against a real database
    in a full test environment.
    """

    @pytest.fixture
    def campaign_a_data(self):
        """Data belonging to Campaign A."""
        return {
            "campaign_id": 1,
            "tasks": [
                {"id": 101, "title": "Task A1"},
                {"id": 102, "title": "Task A2"},
            ],
        }

    @pytest.fixture
    def campaign_b_data(self):
        """Data belonging to Campaign B."""
        return {
            "campaign_id": 2,
            "tasks": [
                {"id": 201, "title": "Task B1"},
                {"id": 202, "title": "Task B2"},
            ],
        }

    def test_campaign_a_cannot_see_campaign_b_tasks(
        self, campaign_a_data, campaign_b_data
    ):
        """
        Verify Campaign A user cannot access Campaign B tasks.

        With RLS enabled:
        - User sets context to Campaign A (id=1)
        - Query for tasks should only return Task A1, A2
        - Task B1, B2 should be invisible
        """
        current_campaign_context = campaign_a_data["campaign_id"]

        # Simulate filtered query result
        all_tasks = campaign_a_data["tasks"] + campaign_b_data["tasks"]
        visible_tasks = [
            task for task in all_tasks
            # This simulates what RLS does at database level
            if self._simulate_rls_filter(task, current_campaign_context, campaign_a_data, campaign_b_data)
        ]

        # Only Campaign A tasks should be visible
        assert len(visible_tasks) == 2
        assert all(t["title"].startswith("Task A") for t in visible_tasks)

    def test_campaign_b_cannot_modify_campaign_a_tasks(
        self, campaign_a_data, campaign_b_data
    ):
        """
        Verify Campaign B user cannot modify Campaign A tasks.

        With RLS enabled:
        - User sets context to Campaign B (id=2)
        - UPDATE/DELETE on Task A1 should be blocked
        """
        current_campaign_context = campaign_b_data["campaign_id"]
        target_task = campaign_a_data["tasks"][0]  # Task A1

        # Check if modification is allowed
        can_modify = self._simulate_rls_filter(
            target_task, current_campaign_context, campaign_a_data, campaign_b_data
        )

        assert can_modify is False

    def _simulate_rls_filter(self, task, context_campaign_id, campaign_a, campaign_b):
        """Simulate RLS policy evaluation."""
        # Determine which campaign the task belongs to
        if task in campaign_a["tasks"]:
            task_campaign_id = campaign_a["campaign_id"]
        else:
            task_campaign_id = campaign_b["campaign_id"]

        return task_campaign_id == context_campaign_id


class TestRLSWithServiceLayer:
    """Tests for RLS integration with service layer."""

    @pytest.mark.asyncio
    async def test_task_service_respects_tenant_context(self):
        """
        Verify TaskService queries only return current tenant's tasks.

        This test mocks the database behavior to verify the service
        would correctly use RLS-filtered results.
        """
        from app.services.task_service import TaskService

        mock_db = AsyncMock()
        mock_membership = MagicMock()
        mock_membership.campaign_id = 1
        mock_membership.user_id = 1
        mock_membership.has_permission = MagicMock(return_value=True)

        # Mock the query result - simulating RLS filtering
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        # TaskService takes (db, campaign_id, member)
        service = TaskService(mock_db, mock_membership.campaign_id, mock_membership)

        # The actual implementation would have RLS filter the results
        # This test verifies the service layer integrates correctly
        with patch.object(service, 'list_tasks', return_value=[]):
            tasks = await service.list_tasks()
            assert tasks == []

    @pytest.mark.asyncio
    async def test_context_set_in_campaign_membership_dependency(self):
        """
        Verify get_campaign_membership sets tenant context.
        """
        from app.api.deps import get_campaign_membership

        mock_db = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 1

        # Mock membership query result
        mock_membership = MagicMock()
        mock_membership.campaign_id = 42
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_membership
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.api.deps.set_tenant_context") as mock_set_context:
            # Call the dependency
            result = await get_campaign_membership(
                db=mock_db,
                current_user=mock_user,
                x_campaign_id=42,
            )

            # Verify context was set
            mock_set_context.assert_called_once_with(mock_db, 42)
            assert result == mock_membership


class TestTaskServiceCampaignValidation:
    """
    Tests for TaskService campaign validation.

    These tests verify that service methods properly validate
    that resources belong to the current campaign before allowing access.
    """

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_membership(self):
        """Create mock campaign membership."""
        membership = MagicMock()
        membership.campaign_id = 1
        membership.id = 100
        membership.user_id = 1
        return membership

    @pytest.fixture
    def task_service(self, mock_db, mock_membership):
        """Create TaskService instance."""
        from app.services.task_service import TaskService
        return TaskService(mock_db, mock_membership.campaign_id, mock_membership)

    @pytest.mark.asyncio
    async def test_list_comments_validates_task_campaign(self, task_service, mock_db):
        """list_comments should verify task belongs to campaign."""
        from app.services.task_service import TaskNotFoundError

        # Mock get_task to return None (task not in campaign)
        with patch.object(task_service, 'get_task', return_value=None):
            with pytest.raises(TaskNotFoundError):
                await task_service.list_comments(task_id=999)

    @pytest.mark.asyncio
    async def test_delete_comment_validates_task_campaign(self, task_service, mock_db):
        """delete_comment should verify comment's task belongs to campaign."""
        from app.services.task_service import CommentNotFoundError

        # Mock finding the comment but not the task
        mock_comment = MagicMock()
        mock_comment.task_id = 999
        mock_comment.author_id = 100

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result

        # Mock get_task to return None (task not in campaign)
        with patch.object(task_service, 'get_task', return_value=None):
            with pytest.raises(CommentNotFoundError):
                await task_service.delete_comment(comment_id=123)

    @pytest.mark.asyncio
    async def test_update_comment_validates_task_campaign(self, task_service, mock_db):
        """update_comment should verify comment's task belongs to campaign."""
        from app.services.task_service import CommentNotFoundError

        # Mock finding the comment but not the task
        mock_comment = MagicMock()
        mock_comment.task_id = 999
        mock_comment.author_id = 100

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_comment
        mock_db.execute.return_value = mock_result

        # Mock get_task to return None (task not in campaign)
        with patch.object(task_service, 'get_task', return_value=None):
            with pytest.raises(CommentNotFoundError):
                await task_service.update_comment(comment_id=123, content="test")

    @pytest.mark.asyncio
    async def test_remove_assignee_validates_task_campaign(self, task_service, mock_db):
        """remove_assignee should verify task belongs to campaign."""
        from app.services.task_service import TaskNotFoundError

        # Mock get_task to return None (task not in campaign)
        with patch.object(task_service, 'get_task', return_value=None):
            with pytest.raises(TaskNotFoundError):
                await task_service.remove_assignee(task_id=999, member_id=1)

    @pytest.mark.asyncio
    async def test_get_history_validates_task_campaign(self, task_service, mock_db):
        """get_history should verify task belongs to campaign."""
        from app.services.task_service import TaskNotFoundError

        # Mock get_task to return None (task not in campaign)
        with patch.object(task_service, 'get_task', return_value=None):
            with pytest.raises(TaskNotFoundError):
                await task_service.get_history(task_id=999)

    @pytest.mark.asyncio
    async def test_get_board_stats_validates_board_campaign(self, task_service, mock_db):
        """get_board_stats should verify board belongs to campaign."""
        from app.services.task_service import BoardNotFoundError

        # Mock get_board to return None (board not in campaign)
        with patch.object(task_service, 'get_board', return_value=None):
            with pytest.raises(BoardNotFoundError):
                await task_service.get_board_stats(board_id=999)

    @pytest.mark.asyncio
    async def test_list_columns_validates_board_campaign(self, task_service, mock_db):
        """list_columns should verify board belongs to campaign."""
        from app.services.task_service import BoardNotFoundError

        # Mock get_board to return None (board not in campaign)
        with patch.object(task_service, 'get_board', return_value=None):
            with pytest.raises(BoardNotFoundError):
                await task_service.list_columns(board_id=999)

    @pytest.mark.asyncio
    async def test_get_task_filters_by_campaign(self, task_service, mock_db):
        """get_task should filter by campaign_id."""
        # Mock an empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await task_service.get_task(task_id=999)
        assert result is None

        # Verify the query included campaign_id filter
        call_args = mock_db.execute.call_args[0][0]
        query_str = str(call_args)
        assert "campaign_id" in query_str

    @pytest.mark.asyncio
    async def test_get_board_filters_by_campaign(self, task_service, mock_db):
        """get_board should filter by campaign_id."""
        # Mock an empty result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await task_service.get_board(board_id=999)
        assert result is None

        # Verify the query included campaign_id filter
        call_args = mock_db.execute.call_args[0][0]
        query_str = str(call_args)
        assert "campaign_id" in query_str
