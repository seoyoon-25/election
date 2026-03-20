"""
Members API Endpoints

Handles campaign member management:
- GET /members - List campaign members
- GET /members/{id} - Get member details
- GET /members/me - Get current user's membership
- PATCH /members/{id} - Update member (role, department, title)
- DELETE /members/{id} - Remove member from campaign
- POST /members/invite - Invite new member
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_campaign_membership
from app.models import CampaignMembership, User, Role, Department, Permission
from app.schemas.base import PaginatedResponse, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.schemas.membership import (
    MembershipUpdate,
    MemberResponse,
    InvitationCreate,
)
from app.schemas.user import UserBrief
from app.schemas.role import RoleBrief
from app.schemas.department import DepartmentBrief


router = APIRouter(prefix="/members", tags=["Members"])


DB = Annotated[AsyncSession, Depends(get_db)]
CampaignMember = Annotated[CampaignMembership, Depends(get_campaign_membership)]


@router.get(
    "",
    response_model=PaginatedResponse[MemberResponse],
    summary="List members",
    description="List all members in the current campaign with pagination.",
)
async def list_members(
    membership: CampaignMember,
    db: DB,
    department_id: Optional[int] = Query(None, description="Filter by department"),
    role_id: Optional[int] = Query(None, description="Filter by role"),
    is_active: bool = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="Items per page"),
):
    """
    List all members in the campaign with pagination.

    Supports filtering by department, role, and active status.
    """
    # Build base conditions
    base_conditions = [CampaignMembership.campaign_id == membership.campaign_id]

    if department_id:
        base_conditions.append(CampaignMembership.department_id == department_id)
    if role_id:
        base_conditions.append(CampaignMembership.role_id == role_id)
    if is_active is not None:
        base_conditions.append(CampaignMembership.is_active == is_active)

    # Count total
    count_query = select(func.count(CampaignMembership.id)).where(*base_conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated data
    offset = (page - 1) * page_size
    query = (
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.user),
            selectinload(CampaignMembership.role),
            selectinload(CampaignMembership.department),
        )
        .where(*base_conditions)
        .order_by(CampaignMembership.joined_at.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(query)
    members = result.scalars().all()

    items = [
        MemberResponse(
            id=m.id,
            user=UserBrief(
                id=m.user.id,
                email=m.user.email,
                full_name=m.user.full_name,
                avatar_url=m.user.avatar_url,
            ),
            role=RoleBrief(
                id=m.role.id,
                name=m.role.name,
                slug=m.role.slug,
                is_system=m.role.is_system,
            ),
            department=DepartmentBrief(
                id=m.department.id,
                name=m.department.name,
                slug=m.department.slug,
                color=m.department.color,
            ) if m.department else None,
            title=m.title,
            is_active=m.is_active,
            joined_at=m.joined_at,
            is_owner=m.is_owner,
            is_admin=m.is_admin,
        )
        for m in members
    ]

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/me",
    response_model=MemberResponse,
    summary="Get my membership",
    description="Get current user's membership in this campaign.",
)
async def get_my_membership(
    membership: CampaignMember,
    db: DB,
):
    """
    Get current user's membership details in the campaign.

    Returns role, department, permissions, and other membership info.
    """
    # Reload with relations
    result = await db.execute(
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.user),
            selectinload(CampaignMembership.role),
            selectinload(CampaignMembership.department),
        )
        .where(CampaignMembership.id == membership.id)
    )
    m = result.scalar_one()

    return MemberResponse(
        id=m.id,
        user=UserBrief(
            id=m.user.id,
            email=m.user.email,
            full_name=m.user.full_name,
            avatar_url=m.user.avatar_url,
        ),
        role=RoleBrief(
            id=m.role.id,
            name=m.role.name,
            slug=m.role.slug,
            is_system=m.role.is_system,
        ),
        department=DepartmentBrief(
            id=m.department.id,
            name=m.department.name,
            slug=m.department.slug,
            color=m.department.color,
        ) if m.department else None,
        title=m.title,
        is_active=m.is_active,
        joined_at=m.joined_at,
        is_owner=m.is_owner,
        is_admin=m.is_admin,
    )


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Get member",
    description="Get details of a specific member.",
)
async def get_member(
    member_id: int,
    membership: CampaignMember,
    db: DB,
):
    """Get details of a specific member."""
    result = await db.execute(
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.user),
            selectinload(CampaignMembership.role),
            selectinload(CampaignMembership.department),
        )
        .where(
            CampaignMembership.id == member_id,
            CampaignMembership.campaign_id == membership.campaign_id,
        )
    )
    m = result.scalar_one_or_none()

    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    return MemberResponse(
        id=m.id,
        user=UserBrief(
            id=m.user.id,
            email=m.user.email,
            full_name=m.user.full_name,
            avatar_url=m.user.avatar_url,
        ),
        role=RoleBrief(
            id=m.role.id,
            name=m.role.name,
            slug=m.role.slug,
            is_system=m.role.is_system,
        ),
        department=DepartmentBrief(
            id=m.department.id,
            name=m.department.name,
            slug=m.department.slug,
            color=m.department.color,
        ) if m.department else None,
        title=m.title,
        is_active=m.is_active,
        joined_at=m.joined_at,
        is_owner=m.is_owner,
        is_admin=m.is_admin,
    )


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Update member",
    description="Update a member's role, department, or title.",
)
async def update_member(
    member_id: int,
    data: MembershipUpdate,
    membership: CampaignMember,
    db: DB,
):
    """
    Update a member's details.

    Requires CAMPAIGN_MANAGE_MEMBERS permission.
    Cannot demote the last owner.
    """
    # Check permission
    if not membership.has_permission(Permission.CAMPAIGN_MANAGE_MEMBERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: campaign:manage_members required",
        )

    # Get target member
    result = await db.execute(
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.user),
            selectinload(CampaignMembership.role),
            selectinload(CampaignMembership.department),
        )
        .where(
            CampaignMembership.id == member_id,
            CampaignMembership.campaign_id == membership.campaign_id,
        )
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # Prevent demoting the last owner
    if target.is_owner and data.role_id:
        # Check if there would be other owners
        owner_count = await db.execute(
            select(CampaignMembership)
            .join(Role)
            .where(
                CampaignMembership.campaign_id == membership.campaign_id,
                CampaignMembership.is_active == True,
                Role.slug == "owner",
                CampaignMembership.id != member_id,
            )
        )
        if not owner_count.scalar_one_or_none():
            new_role = await db.execute(
                select(Role).where(Role.id == data.role_id)
            )
            new_role_obj = new_role.scalar_one_or_none()
            if new_role_obj and new_role_obj.slug != "owner":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot demote the last owner",
                )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # Validate role exists in this campaign
    if "role_id" in update_data:
        role_result = await db.execute(
            select(Role).where(
                Role.id == update_data["role_id"],
                Role.campaign_id == membership.campaign_id,
            )
        )
        if not role_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )

    # Validate department exists in this campaign
    if "department_id" in update_data and update_data["department_id"]:
        dept_result = await db.execute(
            select(Department).where(
                Department.id == update_data["department_id"],
                Department.campaign_id == membership.campaign_id,
            )
        )
        if not dept_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department",
            )

    for field, value in update_data.items():
        setattr(target, field, value)

    await db.flush()
    await db.refresh(target)

    # Reload with relations
    result = await db.execute(
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.user),
            selectinload(CampaignMembership.role),
            selectinload(CampaignMembership.department),
        )
        .where(CampaignMembership.id == target.id)
    )
    m = result.scalar_one()

    return MemberResponse(
        id=m.id,
        user=UserBrief(
            id=m.user.id,
            email=m.user.email,
            full_name=m.user.full_name,
            avatar_url=m.user.avatar_url,
        ),
        role=RoleBrief(
            id=m.role.id,
            name=m.role.name,
            slug=m.role.slug,
            is_system=m.role.is_system,
        ),
        department=DepartmentBrief(
            id=m.department.id,
            name=m.department.name,
            slug=m.department.slug,
            color=m.department.color,
        ) if m.department else None,
        title=m.title,
        is_active=m.is_active,
        joined_at=m.joined_at,
        is_owner=m.is_owner,
        is_admin=m.is_admin,
    )


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member",
    description="Remove a member from the campaign.",
)
async def remove_member(
    member_id: int,
    membership: CampaignMember,
    db: DB,
):
    """
    Remove a member from the campaign.

    Requires CAMPAIGN_MANAGE_MEMBERS permission.
    Cannot remove the last owner.
    Cannot remove yourself (use leave endpoint instead).
    """
    # Check permission
    if not membership.has_permission(Permission.CAMPAIGN_MANAGE_MEMBERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: campaign:manage_members required",
        )

    # Get target member
    result = await db.execute(
        select(CampaignMembership)
        .options(selectinload(CampaignMembership.role))
        .where(
            CampaignMembership.id == member_id,
            CampaignMembership.campaign_id == membership.campaign_id,
        )
    )
    target = result.scalar_one_or_none()

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    # Cannot remove yourself
    if target.user_id == membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself. Use the leave endpoint instead.",
        )

    # Cannot remove the last owner
    if target.is_owner:
        owner_count_result = await db.execute(
            select(CampaignMembership)
            .join(Role)
            .where(
                CampaignMembership.campaign_id == membership.campaign_id,
                CampaignMembership.is_active == True,
                Role.slug == "owner",
            )
        )
        owners = owner_count_result.scalars().all()
        if len(owners) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner",
            )

    # Soft delete - set inactive
    target.is_active = False
    await db.flush()

    return None


@router.post(
    "/invite",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite member",
    description="Invite a new member to the campaign.",
)
async def invite_member(
    data: InvitationCreate,
    membership: CampaignMember,
    db: DB,
):
    """
    Invite a new member to the campaign.

    Requires CAMPAIGN_MANAGE_MEMBERS permission.

    If the user already exists, they are added to the campaign.
    If not, an invitation would be sent (email functionality to be implemented).
    """
    # Check permission
    if not membership.has_permission(Permission.CAMPAIGN_MANAGE_MEMBERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: campaign:manage_members required",
        )

    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    user = result.scalar_one_or_none()

    if not user:
        # In production, send invitation email
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Email invitation feature coming soon.",
        )

    # Check if already a member
    existing = await db.execute(
        select(CampaignMembership).where(
            CampaignMembership.user_id == user.id,
            CampaignMembership.campaign_id == membership.campaign_id,
        )
    )
    existing_membership = existing.scalar_one_or_none()

    if existing_membership:
        if existing_membership.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this campaign",
            )
        else:
            # Reactivate membership
            existing_membership.is_active = True
            existing_membership.role_id = data.role_id
            existing_membership.department_id = data.department_id
            existing_membership.title = data.title
            await db.flush()
            new_membership = existing_membership
    else:
        # Validate role
        role_result = await db.execute(
            select(Role).where(
                Role.id == data.role_id,
                Role.campaign_id == membership.campaign_id,
            )
        )
        if not role_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )

        # Validate department if provided
        if data.department_id:
            dept_result = await db.execute(
                select(Department).where(
                    Department.id == data.department_id,
                    Department.campaign_id == membership.campaign_id,
                )
            )
            if not dept_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid department",
                )

        # Create membership
        new_membership = CampaignMembership(
            user_id=user.id,
            campaign_id=membership.campaign_id,
            role_id=data.role_id,
            department_id=data.department_id,
            title=data.title,
            invited_by_id=membership.user_id,
            is_active=True,
        )
        db.add(new_membership)
        await db.flush()

    # Load relations and return
    result = await db.execute(
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.user),
            selectinload(CampaignMembership.role),
            selectinload(CampaignMembership.department),
        )
        .where(CampaignMembership.id == new_membership.id)
    )
    m = result.scalar_one()

    return MemberResponse(
        id=m.id,
        user=UserBrief(
            id=m.user.id,
            email=m.user.email,
            full_name=m.user.full_name,
            avatar_url=m.user.avatar_url,
        ),
        role=RoleBrief(
            id=m.role.id,
            name=m.role.name,
            slug=m.role.slug,
            is_system=m.role.is_system,
        ),
        department=DepartmentBrief(
            id=m.department.id,
            name=m.department.name,
            slug=m.department.slug,
            color=m.department.color,
        ) if m.department else None,
        title=m.title,
        is_active=m.is_active,
        joined_at=m.joined_at,
        is_owner=m.is_owner,
        is_admin=m.is_admin,
    )
