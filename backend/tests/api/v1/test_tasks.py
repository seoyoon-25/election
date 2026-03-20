"""
Tests for Task/Kanban API endpoints.

Tests cover:
- Board CRUD operations
- Column management
- Task CRUD operations
- Task movement and reordering
- Assignee management
- Comment management
- Task history
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
    TaskBoard,
    TaskColumn,
    Task,
    TaskAssignment,
    TaskComment,
    TaskHistory,
    TaskPriority,
    TaskHistoryAction,
)
from app.models.department import Department
from app.api.deps import get_db, get_current_user, get_campaign_membership
from app.core.security import create_access_token
from app.services.task_service import (
    TaskService,
    BoardNotFoundError,
    ColumnNotFoundError,
    TaskNotFoundError,
    CommentNotFoundError,
    TaskServiceError,
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
def test_department() -> Department:
    """Create a test department."""
    dept = MagicMock(spec=Department)
    dept.id = 1
    dept.name = "Operations"
    dept.slug = "operations"
    dept.color = "#3B82F6"
    return dept


@pytest.fixture
def test_board(test_campaign, test_department) -> TaskBoard:
    """Create a test board."""
    board = MagicMock(spec=TaskBoard)
    board.id = 1
    board.campaign_id = test_campaign.id
    board.name = "Main Board"
    board.description = "Main task board"
    board.department_id = test_department.id
    board.department = test_department
    board.is_default = True
    board.is_archived = False
    board.columns = []
    board.created_at = datetime.now(timezone.utc)
    board.updated_at = datetime.now(timezone.utc)
    return board


@pytest.fixture
def test_column(test_board) -> TaskColumn:
    """Create a test column."""
    column = MagicMock(spec=TaskColumn)
    column.id = 1
    column.board_id = test_board.id
    column.name = "To Do"
    column.description = "Tasks to be done"
    column.color = "#6B7280"
    column.sort_order = 0
    column.is_done_column = False
    column.wip_limit = None
    column.task_count = 5
    column.created_at = datetime.now(timezone.utc)
    column.updated_at = datetime.now(timezone.utc)
    return column


@pytest.fixture
def test_task(test_campaign, test_board, test_column, test_membership) -> Task:
    """Create a test task."""
    task = MagicMock(spec=Task)
    task.id = 1
    task.campaign_id = test_campaign.id
    task.board_id = test_board.id
    task.column_id = test_column.id
    task.parent_id = None
    task.title = "Test Task"
    task.description = "Test task description"
    task.priority = TaskPriority.MEDIUM
    task.due_date = datetime.now(timezone.utc) + timedelta(days=7)
    task.sort_order = 0
    task.created_by_id = test_membership.id
    task.created_by = test_membership
    task.completed_at = None
    task.is_completed = False
    task.subtask_count = 0
    task.comment_count = 2
    task.attachment_count = 1
    task.column = test_column
    task.board = test_board
    task.assignments = []
    task.assignee_ids = []
    task.comments = []
    task.attachments = []
    task.subtasks = []
    task.history = []
    task.created_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)
    return task


@pytest.fixture
def test_assignment(test_task, test_membership) -> TaskAssignment:
    """Create a test task assignment."""
    assignment = MagicMock(spec=TaskAssignment)
    assignment.id = 1
    assignment.task_id = test_task.id
    assignment.member_id = test_membership.id
    assignment.member = test_membership
    assignment.assigned_by_id = test_membership.id
    assignment.assigned_by = test_membership
    assignment.assigned_at = datetime.now(timezone.utc)
    return assignment


@pytest.fixture
def test_comment(test_task, test_membership) -> TaskComment:
    """Create a test task comment."""
    comment = MagicMock(spec=TaskComment)
    comment.id = 1
    comment.task_id = test_task.id
    comment.author_id = test_membership.id
    comment.author = test_membership
    comment.content = "This is a test comment"
    comment.edited_at = None
    comment.is_edited = False
    comment.created_at = datetime.now(timezone.utc)
    comment.updated_at = datetime.now(timezone.utc)
    return comment


@pytest.fixture
def test_history(test_task, test_membership) -> TaskHistory:
    """Create a test task history entry."""
    history = MagicMock(spec=TaskHistory)
    history.id = 1
    history.task_id = test_task.id
    history.actor_id = test_membership.id
    history.actor = test_membership
    history.action = TaskHistoryAction.CREATED
    history.field_name = None
    history.old_value = None
    history.new_value = None
    history.created_at = datetime.now(timezone.utc)
    return history


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
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
async def unauthenticated_client(mock_db_session):
    """Create an async test client without authentication."""

    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db
    # Don't override get_current_user - let it fail

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# =============================================================================
# Board Tests
# =============================================================================


class TestListBoards:
    """Tests for GET /boards endpoint."""

    async def test_list_boards_success(self, client, test_board):
        """Test listing boards returns board list."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_boards = AsyncMock(return_value=[test_board])

            response = await client.get(
                "/api/v1/boards",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["name"] == "Main Board"

    async def test_list_boards_with_department_filter(self, client, test_board):
        """Test listing boards with department filter."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_boards = AsyncMock(return_value=[test_board])

            response = await client.get(
                "/api/v1/boards?department_id=1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            mock_service.list_boards.assert_called_once()

    async def test_list_boards_include_archived(self, client, test_board):
        """Test listing boards including archived."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_boards = AsyncMock(return_value=[test_board])

            response = await client.get(
                "/api/v1/boards?include_archived=true",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200


class TestCreateBoard:
    """Tests for POST /boards endpoint."""

    async def test_create_board_success(self, client, test_board):
        """Test creating a board successfully."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_board = AsyncMock(return_value=test_board)

            response = await client.post(
                "/api/v1/boards",
                headers={"X-Campaign-ID": "1"},
                json={
                    "name": "New Board",
                    "description": "A new board",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "Main Board"

    async def test_create_board_with_department(self, client, test_board):
        """Test creating a board with department."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_board = AsyncMock(return_value=test_board)

            response = await client.post(
                "/api/v1/boards",
                headers={"X-Campaign-ID": "1"},
                json={
                    "name": "Department Board",
                    "department_id": 1,
                },
            )

            assert response.status_code == 201

    async def test_create_board_validation_error(self, client):
        """Test creating a board with invalid data."""
        response = await client.post(
            "/api/v1/boards",
            headers={"X-Campaign-ID": "1"},
            json={
                "name": "",  # Empty name should fail
            },
        )

        assert response.status_code == 422

    async def test_create_board_permission_denied(self, client, test_membership):
        """Test creating a board without permission."""
        test_membership.has_permission = MagicMock(return_value=False)

        response = await client.post(
            "/api/v1/boards",
            headers={"X-Campaign-ID": "1"},
            json={"name": "New Board"},
        )

        assert response.status_code == 403


class TestGetBoard:
    """Tests for GET /boards/{board_id} endpoint."""

    async def test_get_board_success(self, client, test_board, test_column, mock_db_session):
        """Test getting a board with columns."""
        test_board.columns = [test_column]

        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_board = AsyncMock(return_value=test_board)

            # Mock db.execute for tasks query
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db_session.execute.return_value = mock_result

            response = await client.get(
                "/api/v1/boards/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Main Board"
            assert "columns" in data

    async def test_get_board_not_found(self, client):
        """Test getting a non-existent board."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_board = AsyncMock(return_value=None)

            response = await client.get(
                "/api/v1/boards/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestUpdateBoard:
    """Tests for PATCH /boards/{board_id} endpoint."""

    async def test_update_board_success(self, client, test_board):
        """Test updating a board."""
        test_board.name = "Updated Board"

        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_board = AsyncMock(return_value=test_board)

            response = await client.patch(
                "/api/v1/boards/1",
                headers={"X-Campaign-ID": "1"},
                json={"name": "Updated Board"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Board"

    async def test_update_board_not_found(self, client):
        """Test updating a non-existent board."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_board = AsyncMock(
                side_effect=BoardNotFoundError()
            )

            response = await client.patch(
                "/api/v1/boards/999",
                headers={"X-Campaign-ID": "1"},
                json={"name": "Updated Board"},
            )

            assert response.status_code == 404

    async def test_update_board_permission_denied(self, client, test_membership):
        """Test updating a board without permission."""
        test_membership.has_permission = MagicMock(return_value=False)

        response = await client.patch(
            "/api/v1/boards/1",
            headers={"X-Campaign-ID": "1"},
            json={"name": "Updated Board"},
        )

        assert response.status_code == 403


class TestDeleteBoard:
    """Tests for DELETE /boards/{board_id} endpoint."""

    async def test_delete_board_success(self, client):
        """Test deleting a board."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_board = AsyncMock(return_value=None)

            response = await client.delete(
                "/api/v1/boards/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 204

    async def test_delete_board_not_found(self, client):
        """Test deleting a non-existent board."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_board = AsyncMock(
                side_effect=BoardNotFoundError()
            )

            response = await client.delete(
                "/api/v1/boards/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestBoardStats:
    """Tests for GET /boards/{board_id}/stats endpoint."""

    async def test_get_board_stats_success(self, client, test_board):
        """Test getting board statistics."""
        stats = {
            "total_tasks": 10,
            "completed_tasks": 3,
            "overdue_tasks": 1,
            "tasks_by_priority": {
                "low": 2,
                "medium": 5,
                "high": 2,
                "urgent": 1,
            },
            "tasks_by_column": {
                "To Do": 4,
                "In Progress": 3,
                "Done": 3,
            },
        }

        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_board = AsyncMock(return_value=test_board)
            mock_service.get_board_stats = AsyncMock(return_value=stats)

            response = await client.get(
                "/api/v1/boards/1/stats",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total_tasks"] == 10
            assert data["completed_tasks"] == 3


# =============================================================================
# Column Tests
# =============================================================================


class TestListColumns:
    """Tests for GET /boards/{board_id}/columns endpoint."""

    async def test_list_columns_success(self, client, test_board, test_column):
        """Test listing columns."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_board = AsyncMock(return_value=test_board)
            mock_service.list_columns = AsyncMock(return_value=[test_column])

            response = await client.get(
                "/api/v1/boards/1/columns",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["name"] == "To Do"


class TestCreateColumn:
    """Tests for POST /boards/{board_id}/columns endpoint."""

    async def test_create_column_success(self, client, test_column):
        """Test creating a column."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_column = AsyncMock(return_value=test_column)

            response = await client.post(
                "/api/v1/boards/1/columns",
                headers={"X-Campaign-ID": "1"},
                json={
                    "name": "New Column",
                    "color": "#FF5733",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "To Do"

    async def test_create_column_board_not_found(self, client):
        """Test creating a column on non-existent board."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_column = AsyncMock(
                side_effect=BoardNotFoundError()
            )

            response = await client.post(
                "/api/v1/boards/999/columns",
                headers={"X-Campaign-ID": "1"},
                json={"name": "New Column"},
            )

            assert response.status_code == 404


class TestUpdateColumn:
    """Tests for PATCH /boards/{board_id}/columns/{column_id} endpoint."""

    async def test_update_column_success(self, client, test_column):
        """Test updating a column."""
        test_column.name = "Updated Column"

        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_column = AsyncMock(return_value=test_column)

            response = await client.patch(
                "/api/v1/boards/1/columns/1",
                headers={"X-Campaign-ID": "1"},
                json={"name": "Updated Column"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Column"

    async def test_update_column_not_found(self, client):
        """Test updating a non-existent column."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_column = AsyncMock(
                side_effect=ColumnNotFoundError()
            )

            response = await client.patch(
                "/api/v1/boards/1/columns/999",
                headers={"X-Campaign-ID": "1"},
                json={"name": "Updated Column"},
            )

            assert response.status_code == 404


class TestDeleteColumn:
    """Tests for DELETE /boards/{board_id}/columns/{column_id} endpoint."""

    async def test_delete_column_success(self, client, test_column):
        """Test deleting a column."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_column = AsyncMock(return_value=test_column)
            mock_service.delete_column = AsyncMock(return_value=None)

            response = await client.delete(
                "/api/v1/boards/1/columns/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 204

    async def test_delete_column_not_found(self, client):
        """Test deleting a non-existent column."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_column = AsyncMock(return_value=None)

            response = await client.delete(
                "/api/v1/boards/1/columns/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestReorderColumns:
    """Tests for PUT /boards/{board_id}/columns/reorder endpoint."""

    async def test_reorder_columns_success(self, client, test_column):
        """Test reordering columns."""
        with patch(
            "app.api.v1.boards.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.reorder_columns = AsyncMock(return_value=[test_column])

            response = await client.put(
                "/api/v1/boards/1/columns/reorder",
                headers={"X-Campaign-ID": "1"},
                json={"column_ids": [1, 2, 3]},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# =============================================================================
# Task Tests
# =============================================================================


class TestListTasks:
    """Tests for GET /tasks endpoint."""

    async def test_list_tasks_success(self, client, test_task):
        """Test listing tasks."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_tasks = AsyncMock(return_value=[test_task])
            mock_service.get_task = AsyncMock(return_value=test_task)

            response = await client.get(
                "/api/v1/tasks",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["title"] == "Test Task"

    async def test_list_tasks_with_filters(self, client, test_task):
        """Test listing tasks with filters."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.list_tasks = AsyncMock(return_value=[test_task])
            mock_service.get_task = AsyncMock(return_value=test_task)

            response = await client.get(
                "/api/v1/tasks?board_id=1&priority=high",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200


class TestCreateTask:
    """Tests for POST /tasks endpoint."""

    async def test_create_task_success(self, client, test_task):
        """Test creating a task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_task = AsyncMock(return_value=test_task)
            mock_service.get_task = AsyncMock(return_value=test_task)

            response = await client.post(
                "/api/v1/tasks?board_id=1",
                headers={"X-Campaign-ID": "1"},
                json={
                    "title": "New Task",
                    "column_id": 1,
                    "priority": "medium",
                },
            )

            assert response.status_code == 201
            data = response.json()
            assert data["title"] == "Test Task"

    async def test_create_task_with_assignees(self, client, test_task):
        """Test creating a task with assignees."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_task = AsyncMock(return_value=test_task)
            mock_service.get_task = AsyncMock(return_value=test_task)

            response = await client.post(
                "/api/v1/tasks?board_id=1",
                headers={"X-Campaign-ID": "1"},
                json={
                    "title": "New Task",
                    "column_id": 1,
                    "assignee_ids": [1, 2],
                },
            )

            assert response.status_code == 201

    async def test_create_task_board_not_found(self, client):
        """Test creating a task with non-existent board."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_task = AsyncMock(
                side_effect=BoardNotFoundError()
            )

            response = await client.post(
                "/api/v1/tasks?board_id=999",
                headers={"X-Campaign-ID": "1"},
                json={
                    "title": "New Task",
                    "column_id": 1,
                },
            )

            assert response.status_code == 404

    async def test_create_task_column_not_found(self, client):
        """Test creating a task with non-existent column."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.create_task = AsyncMock(
                side_effect=ColumnNotFoundError()
            )

            response = await client.post(
                "/api/v1/tasks?board_id=1",
                headers={"X-Campaign-ID": "1"},
                json={
                    "title": "New Task",
                    "column_id": 999,
                },
            )

            assert response.status_code == 400

    async def test_create_task_permission_denied(self, client, test_membership):
        """Test creating a task without permission."""
        test_membership.has_permission = MagicMock(return_value=False)

        response = await client.post(
            "/api/v1/tasks?board_id=1",
            headers={"X-Campaign-ID": "1"},
            json={
                "title": "New Task",
                "column_id": 1,
            },
        )

        assert response.status_code == 403


class TestGetTask:
    """Tests for GET /tasks/{task_id} endpoint."""

    async def test_get_task_success(self, client, test_task):
        """Test getting a task with details."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)

            response = await client.get(
                "/api/v1/tasks/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test Task"
            assert data["priority"] == "medium"

    async def test_get_task_not_found(self, client):
        """Test getting a non-existent task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=None)

            response = await client.get(
                "/api/v1/tasks/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestUpdateTask:
    """Tests for PATCH /tasks/{task_id} endpoint."""

    async def test_update_task_success(self, client, test_task):
        """Test updating a task."""
        test_task.title = "Updated Task"

        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)
            mock_service.update_task = AsyncMock(return_value=test_task)

            response = await client.patch(
                "/api/v1/tasks/1",
                headers={"X-Campaign-ID": "1"},
                json={"title": "Updated Task"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Updated Task"

    async def test_update_task_not_found(self, client):
        """Test updating a non-existent task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=None)

            response = await client.patch(
                "/api/v1/tasks/999",
                headers={"X-Campaign-ID": "1"},
                json={"title": "Updated Task"},
            )

            assert response.status_code == 404

    async def test_update_task_permission_denied(self, client, test_task, test_membership):
        """Test updating a task without permission."""
        test_task.created_by_id = 999  # Different user
        test_task.assignee_ids = []
        test_membership.has_permission = MagicMock(return_value=False)

        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)

            response = await client.patch(
                "/api/v1/tasks/1",
                headers={"X-Campaign-ID": "1"},
                json={"title": "Updated Task"},
            )

            assert response.status_code == 403


class TestDeleteTask:
    """Tests for DELETE /tasks/{task_id} endpoint."""

    async def test_delete_task_success(self, client):
        """Test deleting a task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_task = AsyncMock(return_value=None)

            response = await client.delete(
                "/api/v1/tasks/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 204

    async def test_delete_task_not_found(self, client):
        """Test deleting a non-existent task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_task = AsyncMock(
                side_effect=TaskNotFoundError()
            )

            response = await client.delete(
                "/api/v1/tasks/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestMoveTask:
    """Tests for POST /tasks/{task_id}/move endpoint."""

    async def test_move_task_success(self, client, test_task):
        """Test moving a task to another column."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)
            mock_service.move_task = AsyncMock(return_value=test_task)

            response = await client.post(
                "/api/v1/tasks/1/move",
                headers={"X-Campaign-ID": "1"},
                json={
                    "column_id": 2,
                    "sort_order": 0,
                },
            )

            assert response.status_code == 200

    async def test_move_task_column_not_found(self, client, test_task):
        """Test moving a task to non-existent column."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)
            mock_service.move_task = AsyncMock(
                side_effect=ColumnNotFoundError()
            )

            response = await client.post(
                "/api/v1/tasks/1/move",
                headers={"X-Campaign-ID": "1"},
                json={"column_id": 999},
            )

            assert response.status_code == 404


class TestReorderTasks:
    """Tests for PUT /tasks/reorder endpoint."""

    async def test_reorder_tasks_success(self, client, test_task):
        """Test reordering tasks in a column."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.reorder_tasks = AsyncMock(return_value=[test_task])

            response = await client.put(
                "/api/v1/tasks/reorder?column_id=1",
                headers={"X-Campaign-ID": "1"},
                json={"task_ids": [3, 1, 2]},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# =============================================================================
# Assignee Tests
# =============================================================================


class TestListAssignees:
    """Tests for GET /tasks/{task_id}/assignees endpoint."""

    async def test_list_assignees_success(self, client, test_task, test_assignment):
        """Test listing task assignees."""
        test_task.assignments = [test_assignment]

        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)

            response = await client.get(
                "/api/v1/tasks/1/assignees",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1

    async def test_list_assignees_task_not_found(self, client):
        """Test listing assignees for non-existent task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=None)

            response = await client.get(
                "/api/v1/tasks/999/assignees",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestAddAssignee:
    """Tests for POST /tasks/{task_id}/assignees endpoint."""

    async def test_add_assignee_success(self, client, test_assignment, mock_db_session):
        """Test adding an assignee."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.add_assignee = AsyncMock(return_value=test_assignment)
            mock_service.db = mock_db_session

            # Mock the reload query
            mock_result = MagicMock()
            mock_result.scalar_one.return_value = test_assignment
            mock_db_session.execute.return_value = mock_result

            response = await client.post(
                "/api/v1/tasks/1/assignees",
                headers={"X-Campaign-ID": "1"},
                json={"member_id": 2},
            )

            assert response.status_code == 201

    async def test_add_assignee_task_not_found(self, client):
        """Test adding an assignee to non-existent task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.add_assignee = AsyncMock(
                side_effect=TaskNotFoundError()
            )

            response = await client.post(
                "/api/v1/tasks/999/assignees",
                headers={"X-Campaign-ID": "1"},
                json={"member_id": 2},
            )

            assert response.status_code == 404

    async def test_add_assignee_already_assigned(self, client):
        """Test adding an already assigned member."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.add_assignee = AsyncMock(
                side_effect=TaskServiceError("Member already assigned")
            )

            response = await client.post(
                "/api/v1/tasks/1/assignees",
                headers={"X-Campaign-ID": "1"},
                json={"member_id": 1},
            )

            assert response.status_code == 400


class TestRemoveAssignee:
    """Tests for DELETE /tasks/{task_id}/assignees/{member_id} endpoint."""

    async def test_remove_assignee_success(self, client):
        """Test removing an assignee."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.remove_assignee = AsyncMock(return_value=None)

            response = await client.delete(
                "/api/v1/tasks/1/assignees/2",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 204

    async def test_remove_assignee_not_found(self, client):
        """Test removing a non-existent assignee."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.remove_assignee = AsyncMock(
                side_effect=TaskServiceError("Assignment not found")
            )

            response = await client.delete(
                "/api/v1/tasks/1/assignees/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


# =============================================================================
# Comment Tests
# =============================================================================


class TestListComments:
    """Tests for GET /tasks/{task_id}/comments endpoint."""

    async def test_list_comments_success(self, client, test_task, test_comment):
        """Test listing task comments."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)
            mock_service.list_comments = AsyncMock(return_value=[test_comment])

            response = await client.get(
                "/api/v1/tasks/1/comments",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["content"] == "This is a test comment"

    async def test_list_comments_task_not_found(self, client):
        """Test listing comments for non-existent task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=None)

            response = await client.get(
                "/api/v1/tasks/999/comments",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


class TestAddComment:
    """Tests for POST /tasks/{task_id}/comments endpoint."""

    async def test_add_comment_success(self, client, test_comment):
        """Test adding a comment."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.add_comment = AsyncMock(return_value=test_comment)

            response = await client.post(
                "/api/v1/tasks/1/comments",
                headers={"X-Campaign-ID": "1"},
                json={"content": "This is a new comment"},
            )

            assert response.status_code == 201
            data = response.json()
            assert data["content"] == "This is a test comment"

    async def test_add_comment_task_not_found(self, client):
        """Test adding a comment to non-existent task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.add_comment = AsyncMock(
                side_effect=TaskNotFoundError()
            )

            response = await client.post(
                "/api/v1/tasks/999/comments",
                headers={"X-Campaign-ID": "1"},
                json={"content": "Comment"},
            )

            assert response.status_code == 404

    async def test_add_comment_validation_error(self, client):
        """Test adding a comment with empty content."""
        response = await client.post(
            "/api/v1/tasks/1/comments",
            headers={"X-Campaign-ID": "1"},
            json={"content": ""},
        )

        assert response.status_code == 422


class TestUpdateComment:
    """Tests for PATCH /tasks/{task_id}/comments/{comment_id} endpoint."""

    async def test_update_comment_success(self, client, test_comment):
        """Test updating a comment."""
        test_comment.content = "Updated comment"
        test_comment.is_edited = True
        test_comment.edited_at = datetime.now(timezone.utc)

        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_comment = AsyncMock(return_value=test_comment)

            response = await client.patch(
                "/api/v1/tasks/1/comments/1",
                headers={"X-Campaign-ID": "1"},
                json={"content": "Updated comment"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "Updated comment"
            assert data["is_edited"] is True

    async def test_update_comment_not_found(self, client):
        """Test updating a non-existent comment."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_comment = AsyncMock(
                side_effect=CommentNotFoundError()
            )

            response = await client.patch(
                "/api/v1/tasks/1/comments/999",
                headers={"X-Campaign-ID": "1"},
                json={"content": "Updated"},
            )

            assert response.status_code == 404

    async def test_update_comment_not_author(self, client):
        """Test updating someone else's comment."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.update_comment = AsyncMock(
                side_effect=TaskServiceError("Not authorized")
            )

            response = await client.patch(
                "/api/v1/tasks/1/comments/1",
                headers={"X-Campaign-ID": "1"},
                json={"content": "Updated"},
            )

            assert response.status_code == 403


class TestDeleteComment:
    """Tests for DELETE /tasks/{task_id}/comments/{comment_id} endpoint."""

    async def test_delete_comment_success(self, client):
        """Test deleting a comment."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_comment = AsyncMock(return_value=None)

            response = await client.delete(
                "/api/v1/tasks/1/comments/1",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 204

    async def test_delete_comment_not_found(self, client):
        """Test deleting a non-existent comment."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.delete_comment = AsyncMock(
                side_effect=CommentNotFoundError()
            )

            response = await client.delete(
                "/api/v1/tasks/1/comments/999",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


# =============================================================================
# History Tests
# =============================================================================


class TestGetHistory:
    """Tests for GET /tasks/{task_id}/history endpoint."""

    async def test_get_history_success(self, client, test_task, test_history):
        """Test getting task history."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)
            mock_service.get_history = AsyncMock(return_value=[test_history])

            response = await client.get(
                "/api/v1/tasks/1/history",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["action"] == "created"

    async def test_get_history_with_limit(self, client, test_task, test_history):
        """Test getting task history with limit."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=test_task)
            mock_service.get_history = AsyncMock(return_value=[test_history])

            response = await client.get(
                "/api/v1/tasks/1/history?limit=10",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 200
            mock_service.get_history.assert_called_once()

    async def test_get_history_task_not_found(self, client):
        """Test getting history for non-existent task."""
        with patch(
            "app.api.v1.tasks.TaskService"
        ) as MockService:
            mock_service = MockService.return_value
            mock_service.get_task = AsyncMock(return_value=None)

            response = await client.get(
                "/api/v1/tasks/999/history",
                headers={"X-Campaign-ID": "1"},
            )

            assert response.status_code == 404


# =============================================================================
# Authentication Tests
# =============================================================================


class TestAuthentication:
    """Tests for authentication requirements."""

    async def test_boards_requires_auth(self, unauthenticated_client):
        """Test that boards endpoint requires authentication."""
        response = await unauthenticated_client.get("/api/v1/boards")
        assert response.status_code == 401

    async def test_tasks_requires_auth(self, unauthenticated_client):
        """Test that tasks endpoint requires authentication."""
        response = await unauthenticated_client.get("/api/v1/tasks")
        assert response.status_code == 401

    async def test_create_task_requires_auth(self, unauthenticated_client):
        """Test that creating a task requires authentication."""
        response = await unauthenticated_client.post(
            "/api/v1/tasks?board_id=1",
            json={"title": "Test", "column_id": 1},
        )
        assert response.status_code == 401
