"""
Board API Endpoints

Handles Kanban board management:
- GET /boards - List boards
- POST /boards - Create board
- GET /boards/{id} - Get board with columns
- PATCH /boards/{id} - Update board
- DELETE /boards/{id} - Delete board
- GET /boards/{id}/stats - Get board statistics

Column endpoints:
- GET /boards/{id}/columns - List columns
- POST /boards/{id}/columns - Create column
- PATCH /boards/{id}/columns/{column_id} - Update column
- DELETE /boards/{id}/columns/{column_id} - Delete column
- PUT /boards/{id}/columns/reorder - Reorder columns
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func

from app.api.deps import get_db, get_campaign_membership
from app.models import CampaignMembership, Permission, TaskBoard, TaskColumn, Task
from app.schemas.base import PaginatedResponse, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.schemas.task import (
    TaskBoardCreate,
    TaskBoardUpdate,
    TaskBoardResponse,
    TaskBoardWithColumns,
    TaskColumnCreate,
    TaskColumnUpdate,
    TaskColumnResponse,
    TaskColumnReorder,
    TaskColumnWithTasks,
    TaskBrief,
)
from app.schemas.department import DepartmentBrief
from app.services.task_service import (
    TaskService,
    BoardNotFoundError,
    ColumnNotFoundError,
)


router = APIRouter(prefix="/boards", tags=["Boards"])


DB = Annotated[AsyncSession, Depends(get_db)]
CampaignMember = Annotated[CampaignMembership, Depends(get_campaign_membership)]


def get_task_service(
    db: DB,
    membership: CampaignMember,
) -> TaskService:
    """Get task service instance."""
    return TaskService(db, membership.campaign_id, membership)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]


# =============================================================================
# Board Endpoints
# =============================================================================

@router.get(
    "",
    response_model=PaginatedResponse[TaskBoardResponse],
    summary="List boards",
    description="List all boards in the campaign with pagination.",
)
async def list_boards(
    task_service: TaskServiceDep,
    membership: CampaignMember,
    db: DB,
    department_id: Optional[int] = Query(None, description="Filter by department"),
    include_archived: bool = Query(False, description="Include archived boards"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
):
    """List all boards with optional filters and pagination."""
    # Build base conditions
    base_conditions = [TaskBoard.campaign_id == membership.campaign_id]

    if department_id:
        base_conditions.append(TaskBoard.department_id == department_id)
    if not include_archived:
        base_conditions.append(TaskBoard.is_archived == False)

    # Count total
    count_query = select(func.count(TaskBoard.id)).where(*base_conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated data
    offset = (page - 1) * page_size
    query = (
        select(TaskBoard)
        .options(
            selectinload(TaskBoard.department),
            selectinload(TaskBoard.columns),
        )
        .where(*base_conditions)
        .order_by(TaskBoard.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    boards = result.scalars().all()

    items = [
        TaskBoardResponse(
            id=b.id,
            campaign_id=b.campaign_id,
            name=b.name,
            description=b.description,
            department_id=b.department_id,
            department=DepartmentBrief(
                id=b.department.id,
                name=b.department.name,
                slug=b.department.slug,
                color=b.department.color,
            ) if b.department else None,
            is_default=b.is_default,
            is_archived=b.is_archived,
            column_count=len(b.columns) if b.columns else 0,
            created_at=b.created_at,
            updated_at=b.updated_at,
        )
        for b in boards
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=TaskBoardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create board",
    description="Create a new Kanban board.",
)
async def create_board(
    data: TaskBoardCreate,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Create a new board. Requires BOARD_CREATE permission."""
    if not membership.has_permission(Permission.BOARD_CREATE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: board:create required",
        )

    board = await task_service.create_board(data)

    return TaskBoardResponse(
        id=board.id,
        campaign_id=board.campaign_id,
        name=board.name,
        description=board.description,
        department_id=board.department_id,
        is_default=board.is_default,
        is_archived=board.is_archived,
        created_at=board.created_at,
        updated_at=board.updated_at,
    )


@router.get(
    "/{board_id}",
    response_model=TaskBoardWithColumns,
    summary="Get board",
    description="Get board with all columns and tasks.",
)
async def get_board(
    board_id: int,
    task_service: TaskServiceDep,
    db: DB,
):
    """Get board with columns and tasks for Kanban view."""
    board = await task_service.get_board(board_id, with_columns=True)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    # Load tasks for each column
    columns_with_tasks = []
    for col in board.columns:
        # Get tasks for this column
        tasks_result = await db.execute(
            select(Task)
            .where(Task.column_id == col.id)
            .order_by(Task.sort_order)
        )
        tasks = tasks_result.scalars().all()

        columns_with_tasks.append(
            TaskColumnWithTasks(
                id=col.id,
                board_id=col.board_id,
                name=col.name,
                description=col.description,
                color=col.color,
                sort_order=col.sort_order,
                is_done_column=col.is_done_column,
                wip_limit=col.wip_limit,
                task_count=len(tasks),
                created_at=col.created_at,
                updated_at=col.updated_at,
                tasks=[
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
                ],
            )
        )

    return TaskBoardWithColumns(
        id=board.id,
        campaign_id=board.campaign_id,
        name=board.name,
        description=board.description,
        department_id=board.department_id,
        department=DepartmentBrief(
            id=board.department.id,
            name=board.department.name,
            slug=board.department.slug,
            color=board.department.color,
        ) if board.department else None,
        is_default=board.is_default,
        is_archived=board.is_archived,
        created_at=board.created_at,
        updated_at=board.updated_at,
        columns=columns_with_tasks,
    )


@router.patch(
    "/{board_id}",
    response_model=TaskBoardResponse,
    summary="Update board",
    description="Update board details.",
)
async def update_board(
    board_id: int,
    data: TaskBoardUpdate,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Update a board. Requires BOARD_EDIT permission."""
    if not membership.has_permission(Permission.BOARD_EDIT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: board:edit required",
        )

    try:
        board = await task_service.update_board(board_id, data)
    except BoardNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    return TaskBoardResponse(
        id=board.id,
        campaign_id=board.campaign_id,
        name=board.name,
        description=board.description,
        department_id=board.department_id,
        is_default=board.is_default,
        is_archived=board.is_archived,
        created_at=board.created_at,
        updated_at=board.updated_at,
    )


@router.delete(
    "/{board_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete board",
    description="Delete a board and all its contents.",
)
async def delete_board(
    board_id: int,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Delete a board. Requires BOARD_DELETE permission."""
    if not membership.has_permission(Permission.BOARD_DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: board:delete required",
        )

    try:
        await task_service.delete_board(board_id)
    except BoardNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    return None


@router.get(
    "/{board_id}/stats",
    summary="Get board statistics",
    description="Get task statistics for a board.",
)
async def get_board_stats(
    board_id: int,
    task_service: TaskServiceDep,
):
    """Get board statistics."""
    board = await task_service.get_board(board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    return await task_service.get_board_stats(board_id)


# =============================================================================
# Column Endpoints
# =============================================================================

@router.get(
    "/{board_id}/columns",
    response_model=list[TaskColumnResponse],
    summary="List columns",
    description="List all columns in a board.",
)
async def list_columns(
    board_id: int,
    task_service: TaskServiceDep,
):
    """List all columns in a board."""
    board = await task_service.get_board(board_id)
    if not board:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    columns = await task_service.list_columns(board_id)

    return [
        TaskColumnResponse(
            id=c.id,
            board_id=c.board_id,
            name=c.name,
            description=c.description,
            color=c.color,
            sort_order=c.sort_order,
            is_done_column=c.is_done_column,
            wip_limit=c.wip_limit,
            task_count=c.task_count,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in columns
    ]


@router.post(
    "/{board_id}/columns",
    response_model=TaskColumnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create column",
    description="Create a new column in a board.",
)
async def create_column(
    board_id: int,
    data: TaskColumnCreate,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Create a new column. Requires BOARD_EDIT permission."""
    if not membership.has_permission(Permission.BOARD_EDIT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: board:edit required",
        )

    try:
        column = await task_service.create_column(board_id, data)
    except BoardNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    return TaskColumnResponse(
        id=column.id,
        board_id=column.board_id,
        name=column.name,
        description=column.description,
        color=column.color,
        sort_order=column.sort_order,
        is_done_column=column.is_done_column,
        wip_limit=column.wip_limit,
        created_at=column.created_at,
        updated_at=column.updated_at,
    )


@router.patch(
    "/{board_id}/columns/{column_id}",
    response_model=TaskColumnResponse,
    summary="Update column",
    description="Update column details.",
)
async def update_column(
    board_id: int,
    column_id: int,
    data: TaskColumnUpdate,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Update a column. Requires BOARD_EDIT permission."""
    if not membership.has_permission(Permission.BOARD_EDIT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: board:edit required",
        )

    try:
        column = await task_service.update_column(column_id, data)
    except ColumnNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found",
        )

    # Verify column belongs to board
    if column.board_id != board_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found in this board",
        )

    return TaskColumnResponse(
        id=column.id,
        board_id=column.board_id,
        name=column.name,
        description=column.description,
        color=column.color,
        sort_order=column.sort_order,
        is_done_column=column.is_done_column,
        wip_limit=column.wip_limit,
        created_at=column.created_at,
        updated_at=column.updated_at,
    )


@router.delete(
    "/{board_id}/columns/{column_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete column",
    description="Delete a column and move tasks.",
)
async def delete_column(
    board_id: int,
    column_id: int,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Delete a column. Requires BOARD_EDIT permission. Tasks will be deleted."""
    if not membership.has_permission(Permission.BOARD_EDIT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: board:edit required",
        )

    column = await task_service.get_column(column_id)
    if not column or column.board_id != board_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found",
        )

    try:
        await task_service.delete_column(column_id)
    except ColumnNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Column not found",
        )

    return None


@router.put(
    "/{board_id}/columns/reorder",
    response_model=list[TaskColumnResponse],
    summary="Reorder columns",
    description="Reorder columns in a board.",
)
async def reorder_columns(
    board_id: int,
    data: TaskColumnReorder,
    membership: CampaignMember,
    task_service: TaskServiceDep,
):
    """Reorder columns. Requires BOARD_EDIT permission."""
    if not membership.has_permission(Permission.BOARD_EDIT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: board:edit required",
        )

    try:
        columns = await task_service.reorder_columns(board_id, data.column_ids)
    except BoardNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board not found",
        )

    return [
        TaskColumnResponse(
            id=c.id,
            board_id=c.board_id,
            name=c.name,
            description=c.description,
            color=c.color,
            sort_order=c.sort_order,
            is_done_column=c.is_done_column,
            wip_limit=c.wip_limit,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in columns
    ]
