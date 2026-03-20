"""
Task Service

Handles all task-related business logic:
- Board CRUD
- Column CRUD and reordering
- Task CRUD, moving, and reordering
- Assignments, comments, history tracking
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    TaskBoard,
    TaskColumn,
    Task,
    TaskAssignment,
    TaskComment,
    TaskHistory,
    TaskAttachment,
    TaskPriority,
    TaskHistoryAction,
    CampaignMembership,
    Permission,
    DEFAULT_COLUMNS,
)
from app.schemas.task import (
    TaskBoardCreate,
    TaskBoardUpdate,
    TaskColumnCreate,
    TaskColumnUpdate,
    TaskCreate,
    TaskUpdate,
)


class TaskServiceError(Exception):
    """Base exception for task service errors."""

    def __init__(self, message: str, code: str = "task_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class BoardNotFoundError(TaskServiceError):
    def __init__(self):
        super().__init__("Board not found", "board_not_found")


class ColumnNotFoundError(TaskServiceError):
    def __init__(self):
        super().__init__("Column not found", "column_not_found")


class TaskNotFoundError(TaskServiceError):
    def __init__(self):
        super().__init__("Task not found", "task_not_found")


class CommentNotFoundError(TaskServiceError):
    def __init__(self):
        super().__init__("Comment not found", "comment_not_found")


class TaskService:
    """Service for handling task operations."""

    def __init__(self, db: AsyncSession, campaign_id: int, member: CampaignMembership):
        self.db = db
        self.campaign_id = campaign_id
        self.member = member

    # =========================================================================
    # Board Operations
    # =========================================================================

    async def list_boards(
        self,
        department_id: Optional[int] = None,
        include_archived: bool = False,
    ) -> list[TaskBoard]:
        """
        List boards in the campaign.

        Permission-based filtering:
        - TASK_VIEW_ALL: Can view all boards
        - TASK_VIEW_DEPARTMENT: Can view department boards + shared boards
        - Neither: Can view shared boards only (department_id is None)
        """
        from sqlalchemy import or_

        query = (
            select(TaskBoard)
            .options(selectinload(TaskBoard.department))
            .where(TaskBoard.campaign_id == self.campaign_id)
        )

        if department_id:
            query = query.where(TaskBoard.department_id == department_id)

        if not include_archived:
            query = query.where(TaskBoard.is_archived == False)

        # Permission-based filtering (RBAC)
        has_view_all = self.member.has_permission(Permission.TASK_VIEW_ALL)
        has_view_dept = self.member.has_permission(Permission.TASK_VIEW_DEPARTMENT)

        if not has_view_all and not department_id:
            # Apply permission filter only when not filtering by specific department
            if has_view_dept and self.member.department_id:
                # Can view own department boards + shared boards (no department)
                query = query.where(
                    or_(
                        TaskBoard.department_id == self.member.department_id,
                        TaskBoard.department_id.is_(None),
                    )
                )
            elif not has_view_dept:
                # Can only view shared boards (no department)
                query = query.where(TaskBoard.department_id.is_(None))

        query = query.order_by(TaskBoard.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_board(
        self,
        board_id: int,
        with_columns: bool = False,
        with_tasks: bool = False,
    ) -> Optional[TaskBoard]:
        """Get a board by ID."""
        query = select(TaskBoard).where(
            TaskBoard.id == board_id,
            TaskBoard.campaign_id == self.campaign_id,
        )

        if with_columns:
            query = query.options(selectinload(TaskBoard.columns))
        if with_tasks:
            query = query.options(
                selectinload(TaskBoard.columns).selectinload(TaskColumn.tasks)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_board(self, data: TaskBoardCreate) -> TaskBoard:
        """Create a new board with optional default columns."""
        board = TaskBoard(
            campaign_id=self.campaign_id,
            name=data.name,
            description=data.description,
            department_id=data.department_id,
            is_default=data.is_default,
        )
        self.db.add(board)
        await self.db.flush()

        if data.create_default_columns:
            for col_data in DEFAULT_COLUMNS:
                column = TaskColumn(
                    board_id=board.id,
                    **col_data,
                )
                self.db.add(column)

        await self.db.flush()
        await self.db.refresh(board)
        return board

    async def update_board(self, board_id: int, data: TaskBoardUpdate) -> TaskBoard:
        """Update a board."""
        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundError()

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(board, field, value)

        await self.db.flush()
        await self.db.refresh(board)
        return board

    async def delete_board(self, board_id: int) -> None:
        """Delete a board and all its contents."""
        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundError()

        await self.db.delete(board)
        await self.db.flush()

    # =========================================================================
    # Column Operations
    # =========================================================================

    async def list_columns(self, board_id: int) -> list[TaskColumn]:
        """List all columns in a board."""
        # Verify board belongs to campaign
        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundError()

        result = await self.db.execute(
            select(TaskColumn)
            .where(TaskColumn.board_id == board_id)
            .order_by(TaskColumn.sort_order)
        )
        return list(result.scalars().all())

    async def get_column(self, column_id: int) -> Optional[TaskColumn]:
        """Get a column by ID."""
        result = await self.db.execute(
            select(TaskColumn)
            .options(selectinload(TaskColumn.board))
            .where(TaskColumn.id == column_id)
        )
        column = result.scalar_one_or_none()

        # Verify campaign access
        if column and column.board.campaign_id != self.campaign_id:
            return None

        return column

    async def create_column(self, board_id: int, data: TaskColumnCreate) -> TaskColumn:
        """Create a new column."""
        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundError()

        # Get max sort order
        max_order_result = await self.db.execute(
            select(func.max(TaskColumn.sort_order))
            .where(TaskColumn.board_id == board_id)
        )
        max_order = max_order_result.scalar() or -1

        column = TaskColumn(
            board_id=board_id,
            name=data.name,
            description=data.description,
            color=data.color,
            is_done_column=data.is_done_column,
            wip_limit=data.wip_limit,
            sort_order=max_order + 1,
        )
        self.db.add(column)
        await self.db.flush()
        await self.db.refresh(column)
        return column

    async def update_column(self, column_id: int, data: TaskColumnUpdate) -> TaskColumn:
        """Update a column."""
        column = await self.get_column(column_id)
        if not column:
            raise ColumnNotFoundError()

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(column, field, value)

        await self.db.flush()
        await self.db.refresh(column)
        return column

    async def delete_column(self, column_id: int) -> None:
        """Delete a column."""
        column = await self.get_column(column_id)
        if not column:
            raise ColumnNotFoundError()

        await self.db.delete(column)
        await self.db.flush()

    async def reorder_columns(self, board_id: int, column_ids: list[int]) -> list[TaskColumn]:
        """Reorder columns by providing new order."""
        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundError()

        for index, column_id in enumerate(column_ids):
            await self.db.execute(
                update(TaskColumn)
                .where(TaskColumn.id == column_id, TaskColumn.board_id == board_id)
                .values(sort_order=index)
            )

        await self.db.flush()
        return await self.list_columns(board_id)

    # =========================================================================
    # Task Operations
    # =========================================================================

    async def list_tasks(
        self,
        board_id: Optional[int] = None,
        column_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        priority: Optional[TaskPriority] = None,
        include_completed: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Task], int]:
        """
        List tasks with filters and pagination.

        Permission-based filtering:
        - TASK_VIEW_ALL: Can view all tasks in the campaign
        - TASK_VIEW_DEPARTMENT: Can view tasks in their department + assigned tasks
        - Neither: Can only view tasks assigned to them

        Returns:
            Tuple of (tasks list, total count)
        """
        from sqlalchemy import or_

        # Base query conditions
        base_conditions = [Task.campaign_id == self.campaign_id]

        if board_id:
            base_conditions.append(Task.board_id == board_id)
        if column_id:
            base_conditions.append(Task.column_id == column_id)
        if priority:
            base_conditions.append(Task.priority == priority)
        if not include_completed:
            base_conditions.append(Task.completed_at.is_(None))

        # Permission-based filtering (RBAC)
        has_view_all = self.member.has_permission(Permission.TASK_VIEW_ALL)
        has_view_dept = self.member.has_permission(Permission.TASK_VIEW_DEPARTMENT)

        # Determine if we need to filter by assignment or department
        needs_assignment_filter = False
        permission_conditions = []

        if not has_view_all:
            if has_view_dept:
                # Can view department tasks + assigned tasks
                if self.member.department_id:
                    # Tasks in member's department OR assigned to member
                    permission_conditions.append(
                        or_(
                            Task.board.has(TaskBoard.department_id == self.member.department_id),
                            Task.id.in_(
                                select(TaskAssignment.task_id).where(
                                    TaskAssignment.member_id == self.member.id
                                )
                            )
                        )
                    )
                else:
                    # No department - only assigned tasks
                    needs_assignment_filter = True
            else:
                # No department view permission - only assigned tasks
                needs_assignment_filter = True

        # Build count query
        count_query = select(func.count(func.distinct(Task.id))).where(*base_conditions)

        if permission_conditions:
            count_query = count_query.where(*permission_conditions)

        if needs_assignment_filter:
            count_query = count_query.join(TaskAssignment).where(
                TaskAssignment.member_id == self.member.id
            )
        elif assignee_id:
            count_query = count_query.join(TaskAssignment).where(
                TaskAssignment.member_id == assignee_id
            )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Build data query with pagination
        query = (
            select(Task)
            .options(
                selectinload(Task.column),
                selectinload(Task.board),
                selectinload(Task.assignments).selectinload(TaskAssignment.member),
            )
            .where(*base_conditions)
        )

        if permission_conditions:
            query = query.where(*permission_conditions)

        if needs_assignment_filter:
            query = query.join(TaskAssignment).where(
                TaskAssignment.member_id == self.member.id
            )
        elif assignee_id:
            query = query.join(TaskAssignment).where(
                TaskAssignment.member_id == assignee_id
            )

        # Apply ordering and pagination
        offset = (page - 1) * page_size
        query = query.order_by(Task.sort_order).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        tasks = list(result.scalars().unique().all())

        return tasks, total

    async def get_task(
        self,
        task_id: int,
        with_details: bool = False,
    ) -> Optional[Task]:
        """Get a task by ID."""
        query = select(Task).where(
            Task.id == task_id,
            Task.campaign_id == self.campaign_id,
        )

        if with_details:
            query = query.options(
                selectinload(Task.column),
                selectinload(Task.board),
                selectinload(Task.assignments).selectinload(TaskAssignment.member),
                selectinload(Task.comments).selectinload(TaskComment.author),
                selectinload(Task.attachments),
                selectinload(Task.subtasks),
                selectinload(Task.history).selectinload(TaskHistory.actor),
            )
        else:
            query = query.options(
                selectinload(Task.column),
                selectinload(Task.assignments).selectinload(TaskAssignment.member),
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_task(self, board_id: int, data: TaskCreate) -> Task:
        """Create a new task."""
        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundError()

        column = await self.get_column(data.column_id)
        if not column or column.board_id != board_id:
            raise ColumnNotFoundError()

        # Get max sort order in column
        max_order_result = await self.db.execute(
            select(func.max(Task.sort_order))
            .where(Task.column_id == data.column_id)
        )
        max_order = max_order_result.scalar() or -1

        task = Task(
            campaign_id=self.campaign_id,
            board_id=board_id,
            column_id=data.column_id,
            parent_id=data.parent_id,
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            sort_order=max_order + 1,
            created_by_id=self.member.id,
        )
        self.db.add(task)
        await self.db.flush()

        # Add history entry
        await self._add_history(task.id, TaskHistoryAction.CREATED)

        # Add assignees if provided
        if data.assignee_ids:
            for member_id in data.assignee_ids:
                await self.add_assignee(task.id, member_id)

        await self.db.refresh(task)
        return task

    async def update_task(self, task_id: int, data: TaskUpdate) -> Task:
        """Update a task."""
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError()

        update_data = data.model_dump(exclude_unset=True)

        # Track changes for history
        for field, new_value in update_data.items():
            old_value = getattr(task, field)
            if old_value != new_value:
                action = TaskHistoryAction.UPDATED
                if field == "priority":
                    action = TaskHistoryAction.PRIORITY_CHANGED
                elif field == "due_date":
                    action = TaskHistoryAction.DUE_DATE_CHANGED

                await self._add_history(
                    task_id,
                    action,
                    field_name=field,
                    old_value={"value": str(old_value) if old_value else None},
                    new_value={"value": str(new_value) if new_value else None},
                )
                setattr(task, field, new_value)

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int) -> None:
        """Delete a task."""
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError()

        await self.db.delete(task)
        await self.db.flush()

    async def move_task(
        self,
        task_id: int,
        column_id: int,
        sort_order: Optional[int] = None,
    ) -> Task:
        """Move a task to a different column."""
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError()

        column = await self.get_column(column_id)
        if not column:
            raise ColumnNotFoundError()

        # Ensure same board
        if column.board_id != task.board_id:
            raise TaskServiceError("Cannot move task to a different board", "invalid_move")

        old_column_id = task.column_id
        task.column_id = column_id

        if sort_order is not None:
            task.sort_order = sort_order
        else:
            # Put at end of column
            max_order_result = await self.db.execute(
                select(func.max(Task.sort_order))
                .where(Task.column_id == column_id, Task.id != task_id)
            )
            max_order = max_order_result.scalar() or -1
            task.sort_order = max_order + 1

        # Mark as completed if moved to done column
        if column.is_done_column and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
            await self._add_history(task_id, TaskHistoryAction.STATUS_CHANGED,
                                   new_value={"status": "completed"})
        elif not column.is_done_column and task.completed_at:
            task.completed_at = None
            await self._add_history(task_id, TaskHistoryAction.STATUS_CHANGED,
                                   new_value={"status": "reopened"})

        await self._add_history(
            task_id,
            TaskHistoryAction.MOVED,
            old_value={"column_id": old_column_id},
            new_value={"column_id": column_id},
        )

        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def reorder_tasks(self, column_id: int, task_ids: list[int]) -> list[Task]:
        """Reorder tasks within a column."""
        column = await self.get_column(column_id)
        if not column:
            raise ColumnNotFoundError()

        for index, task_id in enumerate(task_ids):
            await self.db.execute(
                update(Task)
                .where(Task.id == task_id, Task.column_id == column_id)
                .values(sort_order=index)
            )

        await self.db.flush()
        return await self.list_tasks(column_id=column_id)

    # =========================================================================
    # Assignment Operations
    # =========================================================================

    async def add_assignee(self, task_id: int, member_id: int) -> TaskAssignment:
        """Add an assignee to a task."""
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError()

        # Check if already assigned
        existing = await self.db.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task_id,
                TaskAssignment.member_id == member_id,
            )
        )
        if existing.scalar_one_or_none():
            raise TaskServiceError("Member already assigned", "already_assigned")

        assignment = TaskAssignment(
            task_id=task_id,
            member_id=member_id,
            assigned_by_id=self.member.id,
        )
        self.db.add(assignment)

        await self._add_history(
            task_id,
            TaskHistoryAction.ASSIGNED,
            new_value={"member_id": member_id},
        )

        await self.db.flush()
        await self.db.refresh(assignment)
        return assignment

    async def remove_assignee(self, task_id: int, member_id: int) -> None:
        """Remove an assignee from a task."""
        # Verify task belongs to campaign
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError()

        result = await self.db.execute(
            select(TaskAssignment).where(
                TaskAssignment.task_id == task_id,
                TaskAssignment.member_id == member_id,
            )
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise TaskServiceError("Assignment not found", "assignment_not_found")

        await self._add_history(
            task_id,
            TaskHistoryAction.UNASSIGNED,
            old_value={"member_id": member_id},
        )

        await self.db.delete(assignment)
        await self.db.flush()

    # =========================================================================
    # Comment Operations
    # =========================================================================

    async def list_comments(self, task_id: int) -> list[TaskComment]:
        """List all comments on a task."""
        # Verify task belongs to campaign
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError()

        result = await self.db.execute(
            select(TaskComment)
            .options(selectinload(TaskComment.author))
            .where(TaskComment.task_id == task_id)
            .order_by(TaskComment.created_at)
        )
        return list(result.scalars().all())

    async def add_comment(self, task_id: int, content: str) -> TaskComment:
        """Add a comment to a task."""
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError()

        comment = TaskComment(
            task_id=task_id,
            author_id=self.member.id,
            content=content,
        )
        self.db.add(comment)

        await self._add_history(task_id, TaskHistoryAction.COMMENTED)

        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def update_comment(self, comment_id: int, content: str) -> TaskComment:
        """Update a comment."""
        result = await self.db.execute(
            select(TaskComment)
            .options(selectinload(TaskComment.author))
            .where(TaskComment.id == comment_id)
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise CommentNotFoundError()

        # Verify the comment's task belongs to current campaign
        task = await self.get_task(comment.task_id)
        if not task:
            raise CommentNotFoundError()

        # Only author can edit
        if comment.author_id != self.member.id:
            raise TaskServiceError("Cannot edit another user's comment", "forbidden")

        comment.content = content
        comment.edited_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def delete_comment(self, comment_id: int) -> None:
        """Delete a comment."""
        result = await self.db.execute(
            select(TaskComment).where(TaskComment.id == comment_id)
        )
        comment = result.scalar_one_or_none()

        if not comment:
            raise CommentNotFoundError()

        # Verify the comment's task belongs to current campaign
        task = await self.get_task(comment.task_id)
        if not task:
            raise CommentNotFoundError()

        # Only author can delete
        if comment.author_id != self.member.id:
            raise TaskServiceError("Cannot delete another user's comment", "forbidden")

        await self.db.delete(comment)
        await self.db.flush()

    # =========================================================================
    # History Operations
    # =========================================================================

    async def _add_history(
        self,
        task_id: int,
        action: TaskHistoryAction,
        field_name: Optional[str] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
    ) -> TaskHistory:
        """Add a history entry for a task."""
        history = TaskHistory(
            task_id=task_id,
            actor_id=self.member.id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(history)
        return history

    async def get_history(self, task_id: int, limit: int = 50) -> list[TaskHistory]:
        """Get task history."""
        # Verify task belongs to campaign
        task = await self.get_task(task_id)
        if not task:
            raise TaskNotFoundError()

        result = await self.db.execute(
            select(TaskHistory)
            .options(selectinload(TaskHistory.actor))
            .where(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_board_stats(self, board_id: int) -> dict:
        """Get statistics for a board."""
        # Verify board belongs to campaign
        board = await self.get_board(board_id)
        if not board:
            raise BoardNotFoundError()

        # Task counts by column
        column_stats = await self.db.execute(
            select(
                TaskColumn.id,
                TaskColumn.name,
                func.count(Task.id).label("task_count")
            )
            .outerjoin(Task)
            .where(TaskColumn.board_id == board_id)
            .group_by(TaskColumn.id, TaskColumn.name)
        )

        # Total tasks
        total_result = await self.db.execute(
            select(func.count(Task.id))
            .where(Task.board_id == board_id)
        )
        total = total_result.scalar() or 0

        # Completed tasks
        completed_result = await self.db.execute(
            select(func.count(Task.id))
            .where(Task.board_id == board_id, Task.completed_at.isnot(None))
        )
        completed = completed_result.scalar() or 0

        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "columns": [
                {"id": row.id, "name": row.name, "task_count": row.task_count}
                for row in column_stats
            ],
        }
