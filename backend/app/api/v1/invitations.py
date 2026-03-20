"""
Invitation API Endpoints

Handles campaign invitation management:
- POST /invitations - Create invitation (campaign admin)
- GET /invitations/verify/{token} - Verify invitation token (public)
- POST /invitations/accept/{token} - Accept invitation and create account (public)
"""

from typing import Annotated, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_campaign_membership
from app.models import (
    User,
    Invitation,
    InvitationStatus,
    CampaignMembership,
    Role,
    Department,
    Permission,
    Campaign,
)
from app.services.auth_service import AuthService
from app.schemas.auth import TokenResponse
from app.core.security import create_token_pair


router = APIRouter(prefix="/invitations", tags=["Invitations"])

DB = Annotated[AsyncSession, Depends(get_db)]


# =============================================================================
# Schemas
# =============================================================================


class InvitationCreateRequest(BaseModel):
    """Request to create an invitation."""

    email: EmailStr
    role_id: int
    department_id: Optional[int] = None
    title: Optional[str] = None


class InvitationResponse(BaseModel):
    """Response with invitation details."""

    id: int
    email: str
    token: str
    campaign_name: str
    role_name: str
    department_name: Optional[str] = None
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationVerifyResponse(BaseModel):
    """Response when verifying an invitation."""

    valid: bool
    email: Optional[str] = None
    campaign_name: Optional[str] = None
    role_name: Optional[str] = None
    expires_at: Optional[datetime] = None
    error: Optional[str] = None


class InvitationAcceptRequest(BaseModel):
    """Request to accept an invitation."""

    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)


class InvitationAcceptResponse(BaseModel):
    """Response after accepting an invitation."""

    user_id: int
    email: str
    full_name: str
    campaign_id: int
    campaign_name: str
    tokens: TokenResponse


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create invitation",
    description="Create a new invitation to join the campaign.",
)
async def create_invitation(
    campaign_id: int,
    data: InvitationCreateRequest,
    membership: Annotated[CampaignMembership, Depends(get_campaign_membership)],
    db: DB,
):
    """
    Create an invitation for a new user to join the campaign.

    Requires CAMPAIGN_MANAGE_MEMBERS permission.
    """
    # Check permission
    if not membership.has_permission(Permission.CAMPAIGN_MANAGE_MEMBERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: manage members permission required",
        )

    # Check if user already exists
    existing_user = await db.execute(
        select(User).where(User.email == data.email.lower())
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists. Use the invite member endpoint instead.",
        )

    # Check for existing pending invitation
    existing_invite = await db.execute(
        select(Invitation).where(
            and_(
                Invitation.email == data.email.lower(),
                Invitation.campaign_id == campaign_id,
                Invitation.status == InvitationStatus.PENDING,
            )
        )
    )
    if existing_invite.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending invitation for this email already exists",
        )

    # Validate role
    role_result = await db.execute(
        select(Role).where(
            and_(Role.id == data.role_id, Role.campaign_id == campaign_id)
        )
    )
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )

    # Validate department if provided
    department = None
    if data.department_id:
        dept_result = await db.execute(
            select(Department).where(
                and_(
                    Department.id == data.department_id,
                    Department.campaign_id == campaign_id,
                )
            )
        )
        department = dept_result.scalar_one_or_none()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid department",
            )

    # Get campaign name
    campaign_result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = campaign_result.scalar_one()

    # Create invitation
    invitation = Invitation(
        email=data.email.lower(),
        token=Invitation.generate_token(),
        campaign_id=campaign_id,
        role_id=data.role_id,
        department_id=data.department_id,
        title=data.title,
        invited_by_id=membership.user_id,
        status=InvitationStatus.PENDING,
        expires_at=Invitation.default_expiry(),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return InvitationResponse(
        id=invitation.id,
        email=invitation.email,
        token=invitation.token,
        campaign_name=campaign.name,
        role_name=role.name,
        department_name=department.name if department else None,
        status=invitation.status.value,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
    )


@router.get(
    "/verify/{token}",
    response_model=InvitationVerifyResponse,
    summary="Verify invitation",
    description="Verify if an invitation token is valid.",
)
async def verify_invitation(
    token: str,
    db: DB,
):
    """
    Verify an invitation token.

    Returns invitation details if valid, error message if not.
    This endpoint is public (no auth required).
    """
    result = await db.execute(
        select(Invitation)
        .options(
            selectinload(Invitation.campaign),
            selectinload(Invitation.role),
        )
        .where(Invitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        return InvitationVerifyResponse(
            valid=False,
            error="Invitation not found",
        )

    if invitation.status == InvitationStatus.ACCEPTED.value:
        return InvitationVerifyResponse(
            valid=False,
            error="Invitation has already been accepted",
        )

    if invitation.status == InvitationStatus.CANCELLED.value:
        return InvitationVerifyResponse(
            valid=False,
            error="Invitation has been cancelled",
        )

    if invitation.is_expired:
        return InvitationVerifyResponse(
            valid=False,
            error="Invitation has expired",
        )

    return InvitationVerifyResponse(
        valid=True,
        email=invitation.email,
        campaign_name=invitation.campaign.name,
        role_name=invitation.role.name if invitation.role else None,
        expires_at=invitation.expires_at,
    )


@router.post(
    "/accept/{token}",
    response_model=InvitationAcceptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Accept invitation",
    description="Accept an invitation and create an account.",
)
async def accept_invitation(
    token: str,
    data: InvitationAcceptRequest,
    db: DB,
):
    """
    Accept an invitation, create a user account, and join the campaign.

    This endpoint is public (no auth required).
    """
    # Get invitation with relations
    result = await db.execute(
        select(Invitation)
        .options(
            selectinload(Invitation.campaign),
            selectinload(Invitation.role),
        )
        .where(Invitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if not invitation.is_valid:
        if invitation.status == InvitationStatus.ACCEPTED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invitation has already been accepted",
            )
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation has expired or been cancelled",
        )

    # Check if user already exists (shouldn't happen but just in case)
    existing_user = await db.execute(
        select(User).where(User.email == invitation.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Create auth service for password hashing
    auth_service = AuthService(db)

    # Create user
    user = User(
        email=invitation.email,
        password_hash=auth_service._hash_password(data.password),
        full_name=data.full_name,
        is_active=True,
        email_verified_at=datetime.now(timezone.utc),  # Auto-verify since they came from invite link
    )
    db.add(user)
    await db.flush()

    # Create campaign membership
    membership = CampaignMembership(
        user_id=user.id,
        campaign_id=invitation.campaign_id,
        role_id=invitation.role_id,
        department_id=invitation.department_id,
        title=invitation.title,
        invited_by_id=invitation.invited_by_id,
        is_active=True,
    )
    db.add(membership)

    # Update invitation status
    invitation.status = InvitationStatus.ACCEPTED.value
    invitation.accepted_at = datetime.now(timezone.utc)

    await db.commit()

    # Generate tokens
    tokens = create_token_pair(user.id)

    return InvitationAcceptResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        campaign_id=invitation.campaign_id,
        campaign_name=invitation.campaign.name,
        tokens=TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        ),
    )
