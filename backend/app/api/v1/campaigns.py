"""
Campaign API Endpoints

Handles:
- POST /campaigns - Create new campaign
- GET /campaigns - List user's campaigns
- GET /campaigns/{id} - Get campaign details
- PATCH /campaigns/{id} - Update campaign
- DELETE /campaigns/{id} - Delete campaign
- POST /campaigns/{id}/activate - Activate campaign
- POST /campaigns/{id}/archive - Archive campaign
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_campaign_membership
from app.models import User, CampaignMembership, Permission
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignWithRole,
)
from app.services.campaign_service import (
    CampaignService,
    CampaignNotFoundError,
    SlugAlreadyExistsError,
)


router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def get_campaign_service(db: Annotated[AsyncSession, Depends(get_db)]) -> CampaignService:
    """Dependency to get campaign service instance."""
    return CampaignService(db)


CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CampaignMember = Annotated[CampaignMembership, Depends(get_campaign_membership)]


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create campaign",
    description="Create a new campaign. The creator becomes the campaign owner.",
)
async def create_campaign(
    data: CampaignCreate,
    current_user: CurrentUser,
    campaign_service: CampaignServiceDep,
):
    """
    Create a new campaign.

    - **name**: Campaign name
    - **slug**: Optional URL-friendly identifier (auto-generated if not provided)
    - **description**: Optional description
    - **start_date**: Optional start date
    - **end_date**: Optional end date (e.g., election day)
    - **timezone**: Timezone for the campaign (default: UTC)

    The creator automatically becomes the campaign owner with full permissions.
    Default roles and departments are created automatically.
    """
    try:
        campaign = await campaign_service.create_campaign(data, current_user)

        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            slug=campaign.slug,
            description=campaign.description,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            status=campaign.status,
            timezone=campaign.timezone,
            settings=campaign.settings,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
        )
    except SlugAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.get(
    "",
    response_model=list[CampaignWithRole],
    summary="List campaigns",
    description="List all campaigns the current user is a member of.",
)
async def list_campaigns(
    current_user: CurrentUser,
    campaign_service: CampaignServiceDep,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    List all campaigns the user is a member of.

    Returns campaigns with the user's role in each.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models import Campaign, CampaignMembership

    result = await db.execute(
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.campaign),
            selectinload(CampaignMembership.role),
            selectinload(CampaignMembership.department),
        )
        .where(
            CampaignMembership.user_id == current_user.id,
            CampaignMembership.is_active == True,
        )
        .order_by(CampaignMembership.joined_at.desc())
    )
    memberships = result.scalars().all()

    return [
        CampaignWithRole(
            id=m.campaign.id,
            name=m.campaign.name,
            slug=m.campaign.slug,
            status=m.campaign.status,
            role_name=m.role.name,
            role_slug=m.role.slug,
            department_name=m.department.name if m.department else None,
        )
        for m in memberships
    ]


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get campaign",
    description="Get details of a specific campaign.",
)
async def get_campaign(
    campaign_id: int,
    membership: CampaignMember,
    campaign_service: CampaignServiceDep,
):
    """
    Get campaign details.

    Requires membership in the campaign.
    """
    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    stats = await campaign_service.get_campaign_stats(campaign_id)

    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        slug=campaign.slug,
        description=campaign.description,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        status=campaign.status,
        timezone=campaign.timezone,
        settings=campaign.settings,
        member_count=stats["member_count"],
        days_until_end=campaign.days_until_end,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@router.patch(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Update campaign",
    description="Update campaign details.",
)
async def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    membership: CampaignMember,
    campaign_service: CampaignServiceDep,
):
    """
    Update campaign details.

    Requires CAMPAIGN_EDIT permission.
    """
    # Check permission
    if not membership.has_permission(Permission.CAMPAIGN_EDIT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: campaign:edit required",
        )

    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    updated = await campaign_service.update_campaign(campaign, data)

    return CampaignResponse(
        id=updated.id,
        name=updated.name,
        slug=updated.slug,
        description=updated.description,
        start_date=updated.start_date,
        end_date=updated.end_date,
        status=updated.status,
        timezone=updated.timezone,
        settings=updated.settings,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete campaign",
    description="Delete a campaign and all its data.",
)
async def delete_campaign(
    campaign_id: int,
    membership: CampaignMember,
    campaign_service: CampaignServiceDep,
):
    """
    Delete a campaign.

    Requires CAMPAIGN_DELETE permission (owner only by default).
    This will permanently delete all campaign data including:
    - All tasks and boards
    - All members and roles
    - All events and approvals
    - All attachments
    """
    # Check permission
    if not membership.has_permission(Permission.CAMPAIGN_DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: campaign:delete required",
        )

    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    await campaign_service.delete_campaign(campaign)
    return None


@router.post(
    "/{campaign_id}/activate",
    response_model=CampaignResponse,
    summary="Activate campaign",
    description="Change campaign status to active.",
)
async def activate_campaign(
    campaign_id: int,
    membership: CampaignMember,
    campaign_service: CampaignServiceDep,
):
    """
    Activate a campaign.

    Requires CAMPAIGN_EDIT permission.
    """
    if not membership.has_permission(Permission.CAMPAIGN_EDIT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: campaign:edit required",
        )

    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    updated = await campaign_service.activate_campaign(campaign)

    return CampaignResponse(
        id=updated.id,
        name=updated.name,
        slug=updated.slug,
        description=updated.description,
        start_date=updated.start_date,
        end_date=updated.end_date,
        status=updated.status,
        timezone=updated.timezone,
        settings=updated.settings,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.post(
    "/{campaign_id}/archive",
    response_model=CampaignResponse,
    summary="Archive campaign",
    description="Archive a completed campaign.",
)
async def archive_campaign(
    campaign_id: int,
    membership: CampaignMember,
    campaign_service: CampaignServiceDep,
):
    """
    Archive a campaign.

    Requires CAMPAIGN_EDIT permission.
    Archived campaigns are read-only.
    """
    if not membership.has_permission(Permission.CAMPAIGN_EDIT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: campaign:edit required",
        )

    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    updated = await campaign_service.archive_campaign(campaign)

    return CampaignResponse(
        id=updated.id,
        name=updated.name,
        slug=updated.slug,
        description=updated.description,
        start_date=updated.start_date,
        end_date=updated.end_date,
        status=updated.status,
        timezone=updated.timezone,
        settings=updated.settings,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )
