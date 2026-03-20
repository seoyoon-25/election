"""
Task API Endpoints

Handles task management:
- GET /tasks - List tasks (with filters)
- POST /tasks - Create task
- GET /tasks/{id} - Get task details
- PATCH /tasks/{id} - Update task
- DELETE /tasks/{id} - Delete task
- POST /tasks/{id}/move - Move task to different column
- PUT /tasks/reorder - Reorder tasks in a column

Assignees:
- GET /tasks/{id}/assignees - List assignees
- POST /tasks/{id}/assignees - Add assignee
- DELETE /tasks/{id}/assignees/{member_id} - Remove assignee

Comments:
- GET /tasks/{id}/comments - List comments
- POST /tasks/{id}/comments - Add comment
- PATCH /tasks/{id}/comments/{comment_id} - Update comment
- DELETE /tasks/{id}/comments/{comment_id} - Delete comment

History:
- GET /tasks/{id}/history - Get task history
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.api.deps import get_db, get_campaign_membership
from app.models import (
    CampaignMembership,
    Permission,
    Task,
    TaskAssignment,
    TaskPriority,
)
from app.schemas.base import PaginatedResponse, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskMove,
    TaskReorder,
    TaskResponse,
    TaskDetail,
    TaskBrief,
    TaskAssigneeResponse,
    TaskAssigneeCreate,
    TaskCommentCreate,
    TaskCommentUpdate,
    TaskCommentResponse,
    TaskAttachmentResponse,
    TaskHistoryResponse,
    TaskColumnBrief,
    TaskBoardBrief,
)
from app.schemas.user import UserBrief
from app.services.task_service import (
    TaskService,
    TaskNotFoundError,
    ColumnNotFoundError,
    BoardNotFoundError,
    CommentNotFoundError,
    TaskServiceError,
)


router = APIRouter(prefix="/tasks", tags=["Tasks"])


DB = Annotated[AsyncSession, Depends(get_db)]
CampaignMember = Annotated[CampaignMembership, Depends(get_campaign_membership)]


def get_task_service(
    db: DB,
    membership: CampaignMember,
) -> TaskService:
    """Get task service instance."""
    return TaskService(db, membership.campaign_id, membership)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


def _user_brief_from_membership(m: CampaignMembership) -> UserBrief:
    """Convert membership to UserBrief."""
    return UserBrief(
        id=m.user.id,
        email=m.user.email,
        full_name=m.user.full_name,
        avatar_url=m.user.avatar_url,
    )


# =============================================================================
# Task CRUD
# =============================================================================

@router.get(
    "",
    response_model=PaginatedResponse[TaskResponse],
    summary="List tasks",
    description="List tasks with optional filters and pagination.",
)
async def list_tasks(
    task_service: TaskServiceDep,
    db: DB,
    board_id: Optional[int] = Query(None, description="Filter by board"),
    column_id: Optional[int] = Query(None, description="Filter by column"),
    assignee_id: Optional[int] = Query(None, description="Filter by assignee"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    include_completed: bool = Query(True, description="Include completed tasks"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
):
    """List tasks with filters and pagination."""
    tasks, total = await task_service.list_tasks(
        board_id=board_id,
        column_id=column_id,
        assignee_id=assignee_id,
        priority=priority,
        include_completed=include_completed,
        page=page,
        page_size=page_size,
    )

    # Convert to response models
    items = [_task_to_response(task) for task in tasks]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Create a new task.",
)
async def create_task(
    data: TaskCreate,
    membership: CampaignMember,
    task_service: TaskServiceDep,
    db: DB,
    board_id: int = Query(..., description="Board to create task in"),
):
    """Create a new task. Requires TASK_CREATE permission."""
    if not membership.has_permission(Permission.TASK_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: task:create required",
        )

    try:
        task = await task_service.create_task(board_id, data)
        # Reload with relations
        full_task = await task_service.get_task(task.id)
        return _task_to_response(full_task)
    except BoardNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )
    except ColumnNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Column not found or not in this board",
        )


@router.get(
    "/{task_id}",
    response_model=TaskDetail,
    summary="Get task",
    description="Get task with full details.",
)
async def get_task(
    task_id: int,
    task_service: TaskServiceDep,
):
    """Get task with all details."""
    task = await task_service.get_task(task_id, with_details=True)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return _task_to_detail(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update task details.",
)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Update a task. Requires TASK_EDIT_OWN or TASK_EDIT_ALL permission."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permissions
    is_creator = task.created_by_id == membership.id
    is_assignee = membership.id in task.assignee_ids
    can_edit_own = membership.has_permission(Permission.TASK_EDIT_OWN) and (is_creator or is_assignee)
    can_edit_all = membership.has_permission(Permission.TASK_EDIT_ALL)

    if not (can_edit_own or can_edit_all):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    try:
        updated = await task_service.update_task(task_id, data)
        full_task = await task_service.get_task(updated.id)
        return _task_to_response(full_task)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete a task.",
)
async def delete_task(
    task_id: int,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Delete a task. Requires TASK_DELETE permission."""
    if not membership.has_permission(Permission.TASK_DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: task:delete required",
        )

    try:
        await task_service.delete_task(task_id)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return None


@router.post(
    "/{task_id}/move",
    response_model=TaskResponse,
    summary="Move task",
    description="Move task to a different column.",
)
async def move_task(
    task_id: int,
    data: TaskMove,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Move a task to a different column."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Check permissions
    is_creator = task.created_by_id == membership.id
    is_assignee = membership.id in task.assignee_ids
    can_edit_own = membership.has_permission(Permission.TASK_EDIT_OWN) and (is_creator or is_assignee)
    can_edit_all = membership.has_permission(Permission.TASK_EDIT_ALL)

    if not (can_edit_own or can_edit_all):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    try:
        moved = await task_service.move_task(task_id, data.column_id, data.sort_order)
        full_task = await task_service.get_task(moved.id)
        return _task_to_response(full_task)
    except (TaskNotFoundError, ColumnNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except TaskServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.put(
    "/reorder",
    response_model=list[TaskBrief],
    summary="Reorder tasks",
    description="Reorder tasks within a column.",
)
async def reorder_tasks(
    data: TaskReorder,
    membership: CampaignMember,
    task_service: TaskServiceDep,
    column_id: int = Query(..., description="Column to reorder tasks in"),
):
    """Reorder tasks within a column."""
    if not membership.has_permission(Permission.TASK_EDIT_ALL):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: task:edit_all required",
        )

    try:
        tasks = await task_service.reorder_tasks(column_id, data.task_ids)
        return [
            TaskBrief(
                id=t.id,
                title=t.title,
                priority=t.priority,
                due_date=t.due_date,
                is_completed=t.is_completed,
                assignee_count=len(t.assignments) if t.assignments else 0,
                comment_count=len(t.comments) if t.comments else 0,
                attachment_count=len(t.attachments) if t.attachments else 0,
            )
            for t in tasks
        ]
    except ColumnNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found",
        )


# =============================================================================
# Assignees
# =============================================================================

@router.get(
    "/{task_id}/assignees",
    response_model=list[TaskAssigneeResponse],
    summary="List assignees",
    description="List all assignees of a task.",
)
async def list_assignees(
    task_id: int,
    task_service: TaskServiceDep,
    db: DB,
):
    """List task assignees."""
    task = await task_service.get_task(task_id, with_details=True)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return [
        TaskAssigneeResponse(
            id=a.id,
            member_id=a.member_id,
            user=_user_brief_from_membership(a.member),
            assigned_at=a.assigned_at,
            assigned_by=_user_brief_from_membership(a.assigned_by) if a.assigned_by else None,
        )
        for a in task.assignments
    ]


@router.post(
    "/{task_id}/assignees",
    response_model=TaskAssigneeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add assignee",
    description="Add an assignee to a task.",
)
async def add_assignee(
    task_id: int,
    data: TaskAssigneeCreate,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Add an assignee. Requires TASK_ASSIGN permission."""
    if not membership.has_permission(Permission.TASK_ASSIGN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: task:assign required",
        )

    try:
        assignment = await task_service.add_assignee(task_id, data.member_id)

        # Reload with relations
        from sqlalchemy import select
        result = await task_service.db.execute(
            select(TaskAssignment)
            .options(
                selectinload(TaskAssignment.member).selectinload(CampaignMembership.user),
                selectinload(TaskAssignment.assigned_by).selectinload(CampaignMembership.user),
            )
            .where(TaskAssignment.id == assignment.id)
        )
        a = result.scalar_one()

        return TaskAssigneeResponse(
            id=a.id,
            member_id=a.member_id,
            user=_user_brief_from_membership(a.member),
            assigned_at=a.assigned_at,
            assigned_by=_user_brief_from_membership(a.assigned_by) if a.assigned_by else None,
        )
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    except TaskServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.delete(
    "/{task_id}/assignees/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove assignee",
    description="Remove an assignee from a task.",
)
async def remove_assignee(
    task_id: int,
    member_id: int,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Remove an assignee. Requires TASK_ASSIGN permission."""
    if not membership.has_permission(Permission.TASK_ASSIGN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: task:assign required",
        )

    try:
        await task_service.remove_assignee(task_id, member_id)
    except TaskServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )

    return None


# =============================================================================
# Comments
# =============================================================================

@router.get(
    "/{task_id}/comments",
    response_model=list[TaskCommentResponse],
    summary="List comments",
    description="List all comments on a task.",
)
async def list_comments(
    task_id: int,
    task_service: TaskServiceDep,
):
    """List task comments."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    comments = await task_service.list_comments(task_id)

    return [
        TaskCommentResponse(
            id=c.id,
            task_id=c.task_id,
            content=c.content,
            author=_user_brief_from_membership(c.author) if c.author else None,
            edited_at=c.edited_at,
            is_edited=c.is_edited,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in comments
    ]


@router.post(
    "/{task_id}/comments",
    response_model=TaskCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
    description="Add a comment to a task.",
)
async def add_comment(
    task_id: int,
    data: TaskCommentCreate,
    task_service: TaskServiceDep,
):
    """Add a comment to a task."""
    try:
        comment = await task_service.add_comment(task_id, data.content)

        return TaskCommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            content=comment.content,
            author=_user_brief_from_membership(comment.author) if comment.author else None,
            edited_at=comment.edited_at,
            is_edited=comment.is_edited,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )


@router.patch(
    "/{task_id}/comments/{comment_id}",
    response_model=TaskCommentResponse,
    summary="Update comment",
    description="Update a comment.",
)
async def update_comment(
    task_id: int,
    comment_id: int,
    data: TaskCommentUpdate,
    task_service: TaskServiceDep,
):
    """Update a comment. Only the author can edit."""
    try:
        comment = await task_service.update_comment(comment_id, data.content)

        return TaskCommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            content=comment.content,
            author=_user_brief_from_membership(comment.author) if comment.author else None,
            edited_at=comment.edited_at,
            is_edited=comment.is_edited,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    except TaskServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )


@router.delete(
    "/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
    description="Delete a comment.",
)
async def delete_comment(
    task_id: int,
    comment_id: int,
    task_service: TaskServiceDep,
):
    """Delete a comment. Only the author can delete."""
    try:
        await task_service.delete_comment(comment_id)
    except CommentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    except TaskServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )

    return None


# =============================================================================
# History
# =============================================================================

@router.get(
    "/{task_id}/history",
    response_model=list[TaskHistoryResponse],
    summary="Get history",
    description="Get task change history.",
)
async def get_history(
    task_id: int,
    task_service: TaskServiceDep,
    limit: int = Query(50, ge=1, le=200),
):
    """Get task history."""
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    history = await task_service.get_history(task_id, limit=limit)

    return [
        TaskHistoryResponse(
            id=h.id,
            task_id=h.task_id,
            action=h.action,
            field_name=h.field_name,
            old_value=h.old_value,
            new_value=h.new_value,
            actor=_user_brief_from_membership(h.actor) if h.actor else None,
            created_at=h.created_at,
        )
        for h in history
    ]


# =============================================================================
# Helper Functions
# =============================================================================

def _task_to_response(task: Task) -> TaskResponse:
    """Convert Task model to TaskResponse schema."""
    return TaskResponse(
        id=task.id,
        campaign_id=task.campaign_id,
        board_id=task.board_id,
        column_id=task.column_id,
        parent_id=task.parent_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
        sort_order=task.sort_order,
        completed_at=task.completed_at,
        is_completed=task.is_completed,
        subtask_count=task.subtask_count,
        comment_count=task.comment_count,
        attachment_count=task.attachment_count,
        column=TaskColumnBrief(
            id=task.column.id,
            name=task.column.name,
            color=task.column.color,
            is_done_column=task.column.is_done_column,
        ) if task.column else None,
        created_by=_user_brief_from_membership(task.created_by) if task.created_by else None,
        assignees=[
            TaskAssigneeResponse(
                id=a.id,
                member_id=a.member_id,
                user=_user_brief_from_membership(a.member),
                assigned_at=a.assigned_at,
                assigned_by=_user_brief_from_membership(a.assigned_by) if a.assigned_by else None,
            )
            for a in task.assignments
        ],
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _task_to_detail(task: Task) -> TaskDetail:
    """Convert Task model to TaskDetail schema."""
    return TaskDetail(
        id=task.id,
        campaign_id=task.campaign_id,
        board_id=task.board_id,
        column_id=task.column_id,
        parent_id=task.parent_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
        sort_order=task.sort_order,
        completed_at=task.completed_at,
        is_completed=task.is_completed,
        subtask_count=task.subtask_count,
        comment_count=task.comment_count,
        attachment_count=task.attachment_count,
        column=TaskColumnBrief(
            id=task.column.id,
            name=task.column.name,
            color=task.column.color,
            is_done_column=task.column.is_done_column,
        ) if task.column else None,
        board=TaskBoardBrief(
            id=task.board.id,
            name=task.board.name,
            department_id=task.board.department_id,
        ) if task.board else None,
        created_by=_user_brief_from_membership(task.created_by) if task.created_by else None,
        assignees=[
            TaskAssigneeResponse(
                id=a.id,
                member_id=a.member_id,
                user=_user_brief_from_membership(a.member),
                assigned_at=a.assigned_at,
                assigned_by=_user_brief_from_membership(a.assigned_by) if a.assigned_by else None,
            )
            for a in task.assignments
        ],
        subtasks=[
            TaskBrief(
                id=s.id,
                title=s.title,
                priority=s.priority,
                due_date=s.due_date,
                is_completed=s.is_completed,
                assignee_count=len(s.assignments) if s.assignments else 0,
                comment_count=len(s.comments) if s.comments else 0,
                attachment_count=len(s.attachments) if s.attachments else 0,
            )
            for s in task.subtasks
        ],
        comments=[
            TaskCommentResponse(
                id=c.id,
                task_id=c.task_id,
                content=c.content,
                author=_user_brief_from_membership(c.author) if c.author else None,
                edited_at=c.edited_at,
                is_edited=c.is_edited,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in task.comments
        ],
        attachments=[
            TaskAttachmentResponse(
                id=att.id,
                task_id=att.task_id,
                file_name=att.file_name,
                file_size=att.file_size,
                file_size_human=att.file_size_human,
                mime_type=att.mime_type,
                uploaded_by=_user_brief_from_membership(att.uploaded_by) if att.uploaded_by else None,
                created_at=att.created_at,
                updated_at=att.updated_at,
            )
            for att in task.attachments
        ],
        history=[
            TaskHistoryResponse(
                id=h.id,
                task_id=h.task_id,
                action=h.action,
                field_name=h.field_name,
                old_value=h.old_value,
                new_value=h.new_value,
                actor=_user_brief_from_membership(h.actor) if h.actor else None,
                created_at=h.created_at,
            )
            for h in task.history[:20]  # Limit history in detail view
        ],
        created_at=task.created_at,
        updated_at=task.updated_at,
    )
