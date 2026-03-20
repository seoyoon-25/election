"""
Task management models for Kanban boards.

Includes:
- TaskBoard: Container for columns, usually one per department
- TaskColumn: Kanban columns (To Do, In Progress, Review, Done)
- Task: Individual task items
- TaskAssignment: Many-to-many relationship for task assignees
- TaskComment: Comments on tasks
- TaskHistory: Audit log of task changes
- TaskAttachment: File attachments on tasks
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
    JSON,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.department import Department
    from app.models.membership import CampaignMembership
    from app.models.user import User


class TaskPriority(str, enum.Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskHistoryAction(str, enum.Enum):
    """Types of task history actions."""

    CREATED = "created"
    UPDATED = "updated"
    MOVED = "moved"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    COMMENTED = "commented"
    ATTACHMENT_ADDED = "attachment_added"
    ATTACHMENT_REMOVED = "attachment_removed"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    DUE_DATE_CHANGED = "due_date_changed"


class TaskBoard(Base, TimestampMixin, TenantMixin):
    """
    Kanban board container.

    Each board contains multiple columns and is typically associated
    with a department. A campaign can have multiple boards.

    Attributes:
        name: Display name of the board
        description: Optional board description
        department_id: Optional department association
        is_default: Whether this is the default board for the department
        is_archived: Whether the board is archived
    """

    __tablename__ = "task_boards"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        backref="task_boards",
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        backref="task_boards",
    )
    columns: Mapped[list["TaskColumn"]] = relationship(
        "TaskColumn",
        back_populates="board",
        order_by="TaskColumn.sort_order",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TaskBoard(id={self.id}, name='{self.name}')>"


class TaskColumn(Base, TimestampMixin):
    """
    Kanban column within a board.

    Columns represent workflow stages (e.g., To Do, In Progress, Done).

    Attributes:
        board_id: Parent board
        name: Column name
        description: Optional description
        color: Hex color for UI
        sort_order: Position in the board
        is_done_column: Whether tasks here are considered "done"
        wip_limit: Optional work-in-progress limit
    """

    __tablename__ = "task_columns"

    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("task_boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    color: Mapped[str] = mapped_column(
        String(7),
        default="#6B7280",
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    is_done_column: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    wip_limit: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    board: Mapped["TaskBoard"] = relationship(
        "TaskBoard",
        back_populates="columns",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="column",
        order_by="Task.sort_order",
    )

    def __repr__(self) -> str:
        return f"<TaskColumn(id={self.id}, name='{self.name}')>"

    @property
    def task_count(self) -> int:
        """Get number of tasks in this column."""
        return len(self.tasks)


class Task(Base, TimestampMixin, TenantMixin):
    """
    Individual task item.

    Tasks belong to a column and can have subtasks, assignments,
    comments, and attachments.

    Attributes:
        board_id: Parent board (denormalized for query performance)
        column_id: Current column
        parent_id: Parent task for subtasks
        title: Task title
        description: Detailed description (markdown supported)
        priority: Task priority level
        due_date: Optional due date
        sort_order: Position within the column
        created_by_id: User who created the task
        completed_at: When the task was completed
    """

    __tablename__ = "tasks"

    # Location
    board_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("task_boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    column_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("task_columns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    # Content
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Metadata
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Tracking
    created_by_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        backref="tasks",
    )
    board: Mapped["TaskBoard"] = relationship(
        "TaskBoard",
        backref="tasks",
    )
    column: Mapped["TaskColumn"] = relationship(
        "TaskColumn",
        back_populates="tasks",
    )
    parent: Mapped[Optional["Task"]] = relationship(
        "Task",
        remote_side="Task.id",
        back_populates="subtasks",
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    created_by: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        foreign_keys=[created_by_id],
    )
    assignments: Mapped[list["TaskAssignment"]] = relationship(
        "TaskAssignment",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    comments: Mapped[list["TaskComment"]] = relationship(
        "TaskComment",
        back_populates="task",
        order_by="TaskComment.created_at",
        cascade="all, delete-orphan",
    )
    history: Mapped[list["TaskHistory"]] = relationship(
        "TaskHistory",
        back_populates="task",
        order_by="TaskHistory.created_at.desc()",
        cascade="all, delete-orphan",
    )
    attachments: Mapped[list["TaskAttachment"]] = relationship(
        "TaskAttachment",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("ix_tasks_campaign_board", "campaign_id", "board_id"),
        Index("ix_tasks_due_date", "due_date"),
        Index("ix_tasks_column_order", "column_id", "sort_order"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title[:30]}...')>"

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.completed_at is not None

    @property
    def assignee_ids(self) -> list[int]:
        """Get list of assigned member IDs."""
        return [a.member_id for a in self.assignments]

    @property
    def comment_count(self) -> int:
        """Get number of comments."""
        return len(self.comments)

    @property
    def attachment_count(self) -> int:
        """Get number of attachments."""
        return len(self.attachments)

    @property
    def subtask_count(self) -> int:
        """Get number of subtasks."""
        return len(self.subtasks)


class TaskAssignment(Base, TimestampMixin):
    """
    Task assignment (many-to-many between Task and CampaignMembership).

    Tracks who is assigned to a task and who made the assignment.
    """

    __tablename__ = "task_assignments"

    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    member_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="assignments",
    )
    member: Mapped["CampaignMembership"] = relationship(
        "CampaignMembership",
        foreign_keys=[member_id],
    )
    assigned_by: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        foreign_keys=[assigned_by_id],
    )

    # Constraints
    __table_args__ = (
        Index("ix_task_assignments_task_member", "task_id", "member_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<TaskAssignment(task_id={self.task_id}, member_id={self.member_id})>"


class TaskComment(Base, TimestampMixin):
    """
    Comment on a task.

    Supports markdown content and tracks edit history.
    """

    __tablename__ = "task_comments"

    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    edited_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="comments",
    )
    author: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        foreign_keys=[author_id],
    )

    def __repr__(self) -> str:
        return f"<TaskComment(id={self.id}, task_id={self.task_id})>"

    @property
    def is_edited(self) -> bool:
        """Check if comment has been edited."""
        return self.edited_at is not None


class TaskHistory(Base):
    """
    Audit log for task changes.

    Records all changes made to tasks for accountability and debugging.
    """

    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[TaskHistoryAction] = mapped_column(
        Enum(TaskHistoryAction),
        nullable=False,
    )
    field_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    old_value: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    new_value: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="history",
    )
    actor: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        foreign_keys=[actor_id],
    )

    def __repr__(self) -> str:
        return f"<TaskHistory(id={self.id}, action='{self.action}')>"


class TaskAttachment(Base, TimestampMixin):
    """
    File attachment on a task.

    Stores metadata about uploaded files. Actual files are stored in S3.
    """

    __tablename__ = "task_attachments"

    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )

    # File metadata
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="attachments",
    )
    uploaded_by: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        foreign_keys=[uploaded_by_id],
    )

    def __repr__(self) -> str:
        return f"<TaskAttachment(id={self.id}, file_name='{self.file_name}')>"

    @property
    def file_size_human(self) -> str:
        """Get human-readable file size."""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# Default columns for new boards
DEFAULT_COLUMNS: list[dict] = [
    {
        "name": "To Do",
        "color": "#6B7280",
        "sort_order": 0,
        "is_done_column": False,
    },
    {
        "name": "In Progress",
        "color": "#3B82F6",
        "sort_order": 1,
        "is_done_column": False,
    },
    {
        "name": "Review",
        "color": "#F59E0B",
        "sort_order": 2,
        "is_done_column": False,
    },
    {
        "name": "Done",
        "color": "#10B981",
        "sort_order": 3,
        "is_done_column": True,
    },
]
