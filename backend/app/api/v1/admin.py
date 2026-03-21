"""
Admin API Endpoints

Superadmin-only endpoints for managing all campaigns, users, and invitations.
Requires is_superadmin = True on the user.
"""

from datetime import datetime, timezone, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, SuperAdmin
from app.models import (
    User,
    Campaign,
    CampaignMembership,
    Role,
    Invitation,
    Department,
)
from app.models.campaign import CampaignStatus
from app.models.invitation import InvitationStatus
from app.schemas.admin import (
    AdminStatsResponse,
    AdminCampaignItem,
    AdminCampaignList,
    AdminCampaignStatusUpdate,
    AdminCampaignStats,
    AdminUserItem,
    AdminUserDetail,
    AdminUserList,
    AdminUserCampaign,
    AdminAddUserToCampaign,
    AdminUpdateUserRole,
    AdminInvitationItem,
    AdminInvitationList,
    AdminCreateInvitation,
    AdminResendInvitation,
)
from app.schemas.base import PaginatedResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

DB = Annotated[AsyncSession, Depends(get_db)]


# ============================================================================
# Stats Endpoint
# ============================================================================

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    summary="통계 조회",
    description="플랫폼 전체 통계 조회 (캠프 수, 사용자 수, 오늘 가입자 등)",
)
async def get_admin_stats(
    db: DB,
    admin: SuperAdmin,
):
    """Get platform-wide statistics."""
    today = datetime.now(timezone.utc).date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

    # Campaign stats
    total_campaigns = await db.scalar(select(func.count(Campaign.id)))
    active_campaigns = await db.scalar(
        select(func.count(Campaign.id)).where(Campaign.status == CampaignStatus.ACTIVE)
    )
    today_campaigns = await db.scalar(
        select(func.count(Campaign.id)).where(Campaign.created_at >= today_start)
    )

    # User stats
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(
        select(func.count(User.id)).where(User.is_active == True)
    )
    today_signups = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )

    # Invitation stats
    total_invitations = await db.scalar(select(func.count(Invitation.id)))
    pending_invitations = await db.scalar(
        select(func.count(Invitation.id)).where(
            Invitation.status == InvitationStatus.PENDING.value
        )
    )

    return AdminStatsResponse(
        total_campaigns=total_campaigns or 0,
        active_campaigns=active_campaigns or 0,
        total_users=total_users or 0,
        active_users=active_users or 0,
        total_invitations=total_invitations or 0,
        pending_invitations=pending_invitations or 0,
        today_signups=today_signups or 0,
        today_campaigns=today_campaigns or 0,
    )


# ============================================================================
# Campaign Management Endpoints
# ============================================================================

@router.get(
    "/campaigns",
    response_model=AdminCampaignList,
    summary="캠프 목록 조회",
    description="전체 캠프 목록 조회 (페이지네이션, 검색, 필터 지원)",
)
async def list_campaigns(
    db: DB,
    admin: SuperAdmin,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (이름, 설명)"),
    status: Optional[CampaignStatus] = Query(None, description="상태 필터"),
):
    """List all campaigns with pagination and filters."""
    query = select(Campaign).options(selectinload(Campaign.memberships))

    # Apply filters
    conditions = []
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                Campaign.name.ilike(search_pattern),
                Campaign.description.ilike(search_pattern),
                Campaign.slug.ilike(search_pattern),
            )
        )
    if status:
        conditions.append(Campaign.status == status)

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count(Campaign.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.order_by(Campaign.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    campaigns = result.scalars().all()

    # Get owner info for each campaign
    items = []
    for campaign in campaigns:
        # Find owner membership
        owner = None
        for m in campaign.memberships:
            if m.is_active and m.role and m.role.slug == "owner":
                # Need to load user
                user_result = await db.execute(
                    select(User).where(User.id == m.user_id)
                )
                owner = user_result.scalar_one_or_none()
                break

        items.append(
            AdminCampaignItem(
                id=campaign.id,
                name=campaign.name,
                slug=campaign.slug,
                description=campaign.description,
                status=campaign.status,
                member_count=sum(1 for m in campaign.memberships if m.is_active),
                owner_name=owner.full_name if owner else None,
                owner_email=owner.email if owner else None,
                created_at=campaign.created_at,
                updated_at=campaign.updated_at,
            )
        )

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/campaigns/{campaign_id}/stats",
    response_model=AdminCampaignStats,
    summary="캠프 상세 통계",
    description="특정 캠프의 상세 통계 조회",
)
async def get_campaign_stats(
    campaign_id: int,
    db: DB,
    admin: SuperAdmin,
):
    """Get detailed statistics for a specific campaign."""
    # Get campaign
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.memberships))
        .where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="캠프를 찾을 수 없습니다",
        )

    # Import Task model dynamically to avoid circular imports
    from app.models.task import Task, TaskStatus

    # Count tasks
    task_count = await db.scalar(
        select(func.count(Task.id)).where(Task.campaign_id == campaign_id)
    ) or 0
    pending_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.campaign_id == campaign_id,
            Task.status.in_([TaskStatus.BACKLOG, TaskStatus.TODO, TaskStatus.IN_PROGRESS])
        )
    ) or 0
    completed_tasks = await db.scalar(
        select(func.count(Task.id)).where(
            Task.campaign_id == campaign_id,
            Task.status == TaskStatus.DONE
        )
    ) or 0

    # Import Approval model
    from app.models.approval import ApprovalRequest, ApprovalStatus

    # Count approvals
    approval_count = await db.scalar(
        select(func.count(ApprovalRequest.id)).where(
            ApprovalRequest.campaign_id == campaign_id
        )
    ) or 0
    pending_approvals = await db.scalar(
        select(func.count(ApprovalRequest.id)).where(
            ApprovalRequest.campaign_id == campaign_id,
            ApprovalRequest.status == ApprovalStatus.PENDING
        )
    ) or 0

    # Import CalendarEvent model
    from app.models.google_calendar import CalendarEvent

    event_count = await db.scalar(
        select(func.count(CalendarEvent.id)).where(
            CalendarEvent.campaign_id == campaign_id
        )
    ) or 0

    return AdminCampaignStats(
        id=campaign.id,
        name=campaign.name,
        slug=campaign.slug,
        status=campaign.status,
        member_count=sum(1 for m in campaign.memberships if m.is_active),
        task_count=task_count,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        approval_count=approval_count,
        pending_approvals=pending_approvals,
        event_count=event_count,
        created_at=campaign.created_at,
    )


@router.patch(
    "/campaigns/{campaign_id}",
    response_model=AdminCampaignItem,
    summary="캠프 상태 변경",
    description="캠프 상태 변경 (활성화, 일시정지, 보관 등)",
)
async def update_campaign_status(
    campaign_id: int,
    data: AdminCampaignStatusUpdate,
    db: DB,
    admin: SuperAdmin,
):
    """Update campaign status."""
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.memberships))
        .where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="캠프를 찾을 수 없습니다",
        )

    campaign.status = data.status
    campaign.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(campaign)

    # Find owner
    owner = None
    for m in campaign.memberships:
        if m.is_active and m.role and m.role.slug == "owner":
            user_result = await db.execute(
                select(User).where(User.id == m.user_id)
            )
            owner = user_result.scalar_one_or_none()
            break

    return AdminCampaignItem(
        id=campaign.id,
        name=campaign.name,
        slug=campaign.slug,
        description=campaign.description,
        status=campaign.status,
        member_count=sum(1 for m in campaign.memberships if m.is_active),
        owner_name=owner.full_name if owner else None,
        owner_email=owner.email if owner else None,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@router.get(
    "/campaigns/export",
    summary="캠프 CSV 내보내기",
    description="전체 캠프 목록을 CSV 형식으로 내보내기",
)
async def export_campaigns_csv(
    db: DB,
    admin: SuperAdmin,
):
    """Export all campaigns as CSV."""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.memberships))
        .order_by(Campaign.created_at.desc())
    )
    campaigns = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "이름", "슬러그", "상태", "멤버 수", "생성일", "수정일"
    ])

    for campaign in campaigns:
        member_count = sum(1 for m in campaign.memberships if m.is_active)
        writer.writerow([
            campaign.id,
            campaign.name,
            campaign.slug,
            campaign.status.value,
            member_count,
            campaign.created_at.isoformat(),
            campaign.updated_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=campaigns.csv"
        }
    )


# ============================================================================
# User Management Endpoints
# ============================================================================

@router.get(
    "/users",
    response_model=AdminUserList,
    summary="사용자 목록 조회",
    description="전체 사용자 목록 조회 (페이지네이션, 검색 지원)",
)
async def list_users(
    db: DB,
    admin: SuperAdmin,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (이름, 이메일)"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
):
    """List all users with pagination and filters."""
    query = select(User).options(selectinload(User.memberships))

    # Apply filters
    conditions = []
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                User.full_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )
    if is_active is not None:
        conditions.append(User.is_active == is_active)

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count(User.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    items = [
        AdminUserItem(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_superadmin=user.is_superadmin,
            is_email_verified=user.email_verified_at is not None,
            campaign_count=sum(1 for m in user.memberships if m.is_active),
            last_login_at=user.last_login_at,
            created_at=user.created_at,
        )
        for user in users
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}",
    response_model=AdminUserDetail,
    summary="사용자 상세 조회",
    description="사용자 상세 정보 및 소속 캠프 목록 조회",
)
async def get_user_detail(
    user_id: int,
    db: DB,
    admin: SuperAdmin,
):
    """Get detailed user info including campaigns."""
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.memberships).selectinload(CampaignMembership.campaign),
            selectinload(User.memberships).selectinload(CampaignMembership.role),
            selectinload(User.memberships).selectinload(CampaignMembership.department),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    campaigns = [
        AdminUserCampaign(
            campaign_id=m.campaign.id,
            campaign_name=m.campaign.name,
            campaign_slug=m.campaign.slug,
            role_name=m.role.name if m.role else "Unknown",
            department_name=m.department.name if m.department else None,
            joined_at=m.joined_at,
        )
        for m in user.memberships
        if m.is_active
    ]

    return AdminUserDetail(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_superadmin=user.is_superadmin,
        is_email_verified=user.email_verified_at is not None,
        campaign_count=len(campaigns),
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        campaigns=campaigns,
    )


@router.post(
    "/users/{user_id}/campaigns",
    response_model=AdminUserCampaign,
    status_code=status.HTTP_201_CREATED,
    summary="사용자 캠프 추가",
    description="사용자를 특정 캠프에 추가",
)
async def add_user_to_campaign(
    user_id: int,
    data: AdminAddUserToCampaign,
    db: DB,
    admin: SuperAdmin,
):
    """Add a user to a campaign."""
    # Check user exists
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    # Check campaign exists
    campaign = await db.get(Campaign, data.campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="캠프를 찾을 수 없습니다",
        )

    # Check role exists in campaign
    role_result = await db.execute(
        select(Role).where(
            Role.id == data.role_id,
            Role.campaign_id == data.campaign_id,
        )
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="역할을 찾을 수 없습니다",
        )

    # Check department if provided
    department = None
    if data.department_id:
        dept_result = await db.execute(
            select(Department).where(
                Department.id == data.department_id,
                Department.campaign_id == data.campaign_id,
            )
        )
        department = dept_result.scalar_one_or_none()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="부서를 찾을 수 없습니다",
            )

    # Check if membership already exists
    existing = await db.execute(
        select(CampaignMembership).where(
            CampaignMembership.user_id == user_id,
            CampaignMembership.campaign_id == data.campaign_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 캠프에 가입된 사용자입니다",
        )

    # Create membership
    membership = CampaignMembership(
        user_id=user_id,
        campaign_id=data.campaign_id,
        role_id=data.role_id,
        department_id=data.department_id,
        title=data.title,
        is_active=True,
        invited_by_id=admin.id,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(membership)

    return AdminUserCampaign(
        campaign_id=campaign.id,
        campaign_name=campaign.name,
        campaign_slug=campaign.slug,
        role_name=role.name,
        department_name=department.name if department else None,
        joined_at=membership.joined_at,
    )


@router.patch(
    "/users/{user_id}/campaigns/{campaign_id}/role",
    response_model=AdminUserCampaign,
    summary="사용자 역할 변경",
    description="특정 캠프에서 사용자의 역할 변경",
)
async def update_user_role(
    user_id: int,
    campaign_id: int,
    data: AdminUpdateUserRole,
    db: DB,
    admin: SuperAdmin,
):
    """Update user's role in a campaign."""
    # Get membership
    result = await db.execute(
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.campaign),
            selectinload(CampaignMembership.role),
            selectinload(CampaignMembership.department),
        )
        .where(
            CampaignMembership.user_id == user_id,
            CampaignMembership.campaign_id == campaign_id,
            CampaignMembership.is_active == True,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="멤버십을 찾을 수 없습니다",
        )

    # Check new role exists
    role_result = await db.execute(
        select(Role).where(
            Role.id == data.role_id,
            Role.campaign_id == campaign_id,
        )
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="역할을 찾을 수 없습니다",
        )

    # Check department if provided
    department = None
    if data.department_id:
        dept_result = await db.execute(
            select(Department).where(
                Department.id == data.department_id,
                Department.campaign_id == campaign_id,
            )
        )
        department = dept_result.scalar_one_or_none()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="부서를 찾을 수 없습니다",
            )

    # Update membership
    membership.role_id = data.role_id
    if data.department_id is not None:
        membership.department_id = data.department_id

    await db.commit()
    await db.refresh(membership)

    return AdminUserCampaign(
        campaign_id=membership.campaign.id,
        campaign_name=membership.campaign.name,
        campaign_slug=membership.campaign.slug,
        role_name=role.name,
        department_name=department.name if department else None,
        joined_at=membership.joined_at,
    )


@router.patch(
    "/users/{user_id}/activate",
    response_model=AdminUserItem,
    summary="사용자 활성화/비활성화",
    description="사용자 계정을 활성화하거나 비활성화합니다",
)
async def toggle_user_active(
    user_id: int,
    db: DB,
    admin: SuperAdmin,
    is_active: bool = Query(..., description="활성화 여부"),
):
    """Toggle user active status (approve/deactivate user)."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.memberships))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다",
        )

    # Prevent deactivating superadmin by non-superadmin (extra safety)
    if user.is_superadmin and not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="슈퍼관리자는 비활성화할 수 없습니다",
        )

    user.is_active = is_active
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    return AdminUserItem(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_superadmin=user.is_superadmin,
        is_email_verified=user.email_verified_at is not None,
        campaign_count=sum(1 for m in user.memberships if m.is_active),
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.get(
    "/users/export",
    summary="사용자 CSV 내보내기",
    description="전체 사용자 목록을 CSV 형식으로 내보내기",
)
async def export_users_csv(
    db: DB,
    admin: SuperAdmin,
):
    """Export all users as CSV."""
    from fastapi.responses import StreamingResponse
    import csv
    import io

    result = await db.execute(
        select(User)
        .options(selectinload(User.memberships))
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "이메일", "이름", "전화번호", "활성", "슈퍼관리자",
        "이메일인증", "캠프수", "마지막로그인", "가입일"
    ])

    for user in users:
        campaign_count = sum(1 for m in user.memberships if m.is_active)
        writer.writerow([
            user.id,
            user.email,
            user.full_name,
            user.phone or "",
            "Y" if user.is_active else "N",
            "Y" if user.is_superadmin else "N",
            "Y" if user.email_verified_at else "N",
            campaign_count,
            user.last_login_at.isoformat() if user.last_login_at else "",
            user.created_at.isoformat(),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv"
        }
    )


# ============================================================================
# Invitation Management Endpoints
# ============================================================================

@router.get(
    "/invitations",
    response_model=AdminInvitationList,
    summary="초대 목록 조회",
    description="전체 초대 목록 조회 (페이지네이션, 검색, 필터 지원)",
)
async def list_invitations(
    db: DB,
    admin: SuperAdmin,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    search: Optional[str] = Query(None, description="검색어 (이메일)"),
    status_filter: Optional[str] = Query(None, alias="status", description="상태 필터"),
    campaign_id: Optional[int] = Query(None, description="캠프 ID 필터"),
):
    """List all invitations with pagination and filters."""
    query = (
        select(Invitation)
        .options(
            selectinload(Invitation.campaign),
            selectinload(Invitation.role),
            selectinload(Invitation.department),
            selectinload(Invitation.invited_by),
        )
    )

    # Apply filters
    conditions = []
    if search:
        conditions.append(Invitation.email.ilike(f"%{search}%"))
    if status_filter:
        conditions.append(Invitation.status == status_filter)
    if campaign_id:
        conditions.append(Invitation.campaign_id == campaign_id)

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count(Invitation.id))
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.order_by(Invitation.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    invitations = result.scalars().all()

    items = [
        AdminInvitationItem(
            id=inv.id,
            email=inv.email,
            campaign_id=inv.campaign_id,
            campaign_name=inv.campaign.name if inv.campaign else "Unknown",
            role_name=inv.role.name if inv.role else None,
            department_name=inv.department.name if inv.department else None,
            status=inv.status if isinstance(inv.status, str) else inv.status.value,
            invited_by_name=inv.invited_by.full_name if inv.invited_by else None,
            invited_by_email=inv.invited_by.email if inv.invited_by else None,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
            accepted_at=inv.accepted_at,
        )
        for inv in invitations
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/invitations",
    response_model=AdminInvitationItem,
    status_code=status.HTTP_201_CREATED,
    summary="초대 생성",
    description="새 초대 생성",
)
async def create_invitation(
    data: AdminCreateInvitation,
    db: DB,
    admin: SuperAdmin,
):
    """Create a new invitation."""
    # Check campaign exists
    result = await db.execute(
        select(Campaign).where(Campaign.id == data.campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="캠프를 찾을 수 없습니다",
        )

    # Check role exists
    role_result = await db.execute(
        select(Role).where(
            Role.id == data.role_id,
            Role.campaign_id == data.campaign_id,
        )
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="역할을 찾을 수 없습니다",
        )

    # Check department if provided
    department = None
    if data.department_id:
        dept_result = await db.execute(
            select(Department).where(
                Department.id == data.department_id,
                Department.campaign_id == data.campaign_id,
            )
        )
        department = dept_result.scalar_one_or_none()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="부서를 찾을 수 없습니다",
            )

    # Check if user already exists and is a member
    existing_user = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = existing_user.scalar_one_or_none()
    if user:
        existing_membership = await db.execute(
            select(CampaignMembership).where(
                CampaignMembership.user_id == user.id,
                CampaignMembership.campaign_id == data.campaign_id,
                CampaignMembership.is_active == True,
            )
        )
        if existing_membership.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 캠프에 가입된 사용자입니다",
            )

    # Check for existing pending invitation
    existing_inv = await db.execute(
        select(Invitation).where(
            Invitation.email == data.email,
            Invitation.campaign_id == data.campaign_id,
            Invitation.status == InvitationStatus.PENDING.value,
        )
    )
    if existing_inv.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 대기 중인 초대가 있습니다",
        )

    # Create invitation
    invitation = Invitation(
        email=data.email,
        token=Invitation.generate_token(),
        campaign_id=data.campaign_id,
        role_id=data.role_id,
        department_id=data.department_id,
        title=data.title,
        invited_by_id=admin.id,
        expires_at=Invitation.default_expiry(),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return AdminInvitationItem(
        id=invitation.id,
        email=invitation.email,
        campaign_id=invitation.campaign_id,
        campaign_name=campaign.name,
        role_name=role.name,
        department_name=department.name if department else None,
        status=invitation.status,
        invited_by_name=admin.full_name,
        invited_by_email=admin.email,
        created_at=invitation.created_at,
        expires_at=invitation.expires_at,
        accepted_at=None,
    )


@router.post(
    "/invitations/{invitation_id}/resend",
    response_model=AdminResendInvitation,
    summary="초대 재발송",
    description="초대 만료일 갱신 및 재발송",
)
async def resend_invitation(
    invitation_id: int,
    db: DB,
    admin: SuperAdmin,
):
    """Resend an invitation by extending its expiration."""
    result = await db.execute(
        select(Invitation).where(Invitation.id == invitation_id)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="초대를 찾을 수 없습니다",
        )

    # Check status
    inv_status = invitation.status if isinstance(invitation.status, str) else invitation.status.value
    if inv_status == InvitationStatus.ACCEPTED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 수락된 초대입니다",
        )

    # Reset to pending and extend expiration
    invitation.status = InvitationStatus.PENDING.value
    invitation.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    invitation.token = Invitation.generate_token()

    await db.commit()
    await db.refresh(invitation)

    return AdminResendInvitation(
        id=invitation.id,
        email=invitation.email,
        new_expires_at=invitation.expires_at,
        message="초대가 재발송되었습니다",
    )


@router.delete(
    "/invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="초대 취소",
    description="대기 중인 초대 취소",
)
async def cancel_invitation(
    invitation_id: int,
    db: DB,
    admin: SuperAdmin,
):
    """Cancel a pending invitation."""
    result = await db.execute(
        select(Invitation).where(Invitation.id == invitation_id)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="초대를 찾을 수 없습니다",
        )

    inv_status = invitation.status if isinstance(invitation.status, str) else invitation.status.value
    if inv_status != InvitationStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="대기 중인 초대만 취소할 수 있습니다",
        )

    invitation.status = InvitationStatus.CANCELLED.value
    await db.commit()

    return None
