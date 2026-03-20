"""
Task/Kanban schemas for API validation.

Includes schemas for boards, columns, tasks, assignments, comments, and attachments.
"""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.user import UserBrief
from app.schemas.department import DepartmentBrief
from app.models.task import TaskPriority, TaskHistoryAction


# =============================================================================
# Board Schemas
# =============================================================================

class TaskBoardBase(BaseSchema):
    """Base board schema."""

    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None


class TaskBoardCreate(TaskBoardBase):
    """Schema for creating a board."""

    department_id: Optional[int] = None
    is_default: bool = False
    create_default_columns: bool = True


class TaskBoardUpdate(BaseSchema):
    """Schema for updating a board."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    department_id: Optional[int] = None
    is_archived: Optional[bool] = None


class TaskBoardResponse(TaskBoardBase, TimestampSchema):
    """Schema for board response."""

    id: int
    campaign_id: int
    department_id: Optional[int] = None
    department: Optional[DepartmentBrief] = None
    is_default: bool
    is_archived: bool
    column_count: Optional[int] = None
    task_count: Optional[int] = None


class TaskBoardBrief(BaseSchema):
    """Brief board info for embedding."""

    id: int
    name: str
    department_id: Optional[int] = None


# =============================================================================
# Column Schemas
# =============================================================================

class TaskColumnBase(BaseSchema):
    """Base column schema."""

    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#6B7280", pattern=r"^#[0-9A-Fa-f]{6}$")
    is_done_column: bool = False
    wip_limit: Optional[int] = Field(None, ge=1)


class TaskColumnCreate(TaskColumnBase):
    """Schema for creating a column."""

    description: Optional[str] = None


class TaskColumnUpdate(BaseSchema):
    """Schema for updating a column."""

    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_done_column: Optional[bool] = None
    wip_limit: Optional[int] = Field(None, ge=1)


class TaskColumnResponse(TaskColumnBase, TimestampSchema):
    """Schema for column response."""

    id: int
    board_id: int
    description: Optional[str] = None
    sort_order: int
    task_count: Optional[int] = None


class TaskColumnBrief(BaseSchema):
    """Brief column info for embedding."""

    id: int
    name: str
    color: str
    is_done_column: bool


class TaskColumnReorder(BaseSchema):
    """Schema for reordering columns."""

    column_ids: list[int] = Field(min_length=1)


# =============================================================================
# Assignee Schema
# =============================================================================

class TaskAssigneeResponse(BaseSchema):
    """Schema for task assignee."""

    id: int  # assignment id
    member_id: int
    user: UserBrief
    assigned_at: datetime
    assigned_by: Optional[UserBrief] = None


class TaskAssigneeCreate(BaseSchema):
    """Schema for adding an assignee."""

    member_id: int


# =============================================================================
# Comment Schemas
# =============================================================================

class TaskCommentBase(BaseSchema):
    """Base comment schema."""

    content: str = Field(min_length=1)


class TaskCommentCreate(TaskCommentBase):
    """Schema for creating a comment."""

    pass


class TaskCommentUpdate(BaseSchema):
    """Schema for updating a comment."""

    content: str = Field(min_length=1)


class TaskCommentResponse(TaskCommentBase, TimestampSchema):
    """Schema for comment response."""

    id: int
    task_id: int
    author: Optional[UserBrief] = None
    edited_at: Optional[datetime] = None
    is_edited: bool = False


# =============================================================================
# Attachment Schemas
# =============================================================================

class TaskAttachmentResponse(TimestampSchema):
    """Schema for attachment response."""

    id: int
    task_id: int
    file_name: str
    file_size: int
    file_size_human: str
    mime_type: str
    uploaded_by: Optional[UserBrief] = None
    download_url: Optional[str] = None


# =============================================================================
# History Schemas
# =============================================================================

class TaskHistoryResponse(BaseSchema):
    """Schema for task history entry."""

    id: int
    task_id: int
    action: TaskHistoryAction
    field_name: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    actor: Optional[UserBrief] = None
    created_at: datetime


# =============================================================================
# Task Schemas
# =============================================================================

class TaskBase(BaseSchema):
    """Base task schema."""

    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    column_id: int
    parent_id: Optional[int] = None
    assignee_ids: Optional[list[int]] = None


class TaskUpdate(BaseSchema):
    """Schema for updating a task."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None


class TaskMove(BaseSchema):
    """Schema for moving a task to a different column."""

    column_id: int
    sort_order: Optional[int] = None


class TaskReorder(BaseSchema):
    """Schema for reordering tasks within a column."""

    task_ids: list[int] = Field(min_length=1)


class TaskResponse(TaskBase, TimestampSchema):
    """Schema for task response."""

    id: int
    campaign_id: int
    board_id: int
    column_id: int
    parent_id: Optional[int] = None
    sort_order: int
    completed_at: Optional[datetime] = None
    is_completed: bool = False

    # Counts
    subtask_count: int = 0
    comment_count: int = 0
    attachment_count: int = 0

    # Related data
    column: Optional[TaskColumnBrief] = None
    created_by: Optional[UserBrief] = None
    assignees: list[TaskAssigneeResponse] = []


class TaskDetail(TaskResponse):
    """Schema for detailed task view with all related data."""

    board: Optional[TaskBoardBrief] = None
    subtasks: list["TaskBrief"] = []
    comments: list[TaskCommentResponse] = []
    attachments: list[TaskAttachmentResponse] = []
    history: list[TaskHistoryResponse] = []


class TaskBrief(BaseSchema):
    """Brief task info for lists and embedding."""

    id: int
    title: str
    priority: TaskPriority
    due_date: Optional[datetime] = None
    is_completed: bool = False
    assignee_count: int = 0
    comment_count: int = 0
    attachment_count: int = 0


# =============================================================================
# Board with Full Data
# =============================================================================

class TaskColumnWithTasks(TaskColumnResponse):
    """Column with its tasks for board view."""

    tasks: list[TaskBrief] = []


class TaskBoardWithColumns(TaskBoardResponse):
    """Board with all columns and tasks for Kanban view."""

    columns: list[TaskColumnWithTasks] = []


# Fix forward reference
TaskDetail.model_rebuild()
