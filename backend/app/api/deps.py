"""
API Dependencies

Common dependencies used across API endpoints for:
- Database sessions
- Authentication
- Authorization
- Tenant context
"""

from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_session, set_tenant_context
from app.core.security import verify_access_token
from app.core.cookies import get_access_token_from_cookie
from app.config import get_settings
from app.models import User, CampaignMembership, Role, Permission
from app.services.token_blacklist import check_token_valid


# HTTP Bearer scheme for JWT
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async for session in get_async_session():
        yield session


# Type alias for database dependency
DB = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    request: Request,
    db: DB,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Supports both:
    1. Authorization header (Bearer token)
    2. httpOnly cookie (when use_cookie_auth is enabled)

    Raises:
        HTTPException: If token is missing, invalid, blacklisted, or user not found
    """
    token: Optional[str] = None

    # Try to get token from Authorization header first
    if credentials:
        token = credentials.credentials
    else:
        # Fall back to cookie if cookie auth is enabled
        settings = get_settings()
        if settings.use_cookie_auth:
            token = get_access_token_from_cookie(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # First verify token signature and expiration
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is blacklisted or user tokens invalidated
    is_valid, error_msg = await check_token_valid(token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


# Type alias for current user dependency
CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_optional(
    db: DB,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Use for endpoints that work both with and without authentication.
    """
    if not credentials:
        return None

    user_id = verify_access_token(credentials.credentials)
    if not user_id:
        return None

    # Check if token is blacklisted
    is_valid, _ = await check_token_valid(credentials.credentials)
    if not is_valid:
        return None

    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_campaign_membership(
    db: DB,
    current_user: CurrentUser,
    x_campaign_id: Annotated[int, Header(alias="X-Campaign-ID")],
) -> CampaignMembership:
    """
    Get current user's membership in the requested campaign.

    This dependency:
    1. Validates the user has access to the campaign
    2. Sets the tenant context for Row-Level Security
    3. Returns the membership with role information

    Raises:
        HTTPException: If user doesn't have access to the campaign
    """
    result = await db.execute(
        select(CampaignMembership)
        .options(selectinload(CampaignMembership.role))
        .options(selectinload(CampaignMembership.department))
        .where(
            CampaignMembership.user_id == current_user.id,
            CampaignMembership.campaign_id == x_campaign_id,
            CampaignMembership.is_active == True,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No access to this campaign",
        )

    # Set tenant context for RLS
    await set_tenant_context(db, x_campaign_id)

    return membership


# Type alias for campaign membership dependency
CampaignMember = Annotated[CampaignMembership, Depends(get_campaign_membership)]


def require_permission(permission: Permission):
    """
    Create a dependency that requires a specific permission.

    Usage:
        @router.post("/tasks")
        async def create_task(
            membership: CampaignMember,
            _: Annotated[None, Depends(require_permission(Permission.TASK_CREATE))],
        ):
            ...
    """

    async def check_permission(membership: CampaignMember) -> None:
        if not membership.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )

    return check_permission


def require_any_permission(*permissions: Permission):
    """
    Create a dependency that requires any of the specified permissions.
    """

    async def check_permissions(membership: CampaignMember) -> None:
        if not membership.has_any_permission(list(permissions)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

    return check_permissions


async def require_superadmin(current_user: CurrentUser) -> User:
    """
    Dependency that requires superadmin privileges.
    """
    if not current_user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required",
        )
    return current_user


SuperAdmin = Annotated[User, Depends(require_superadmin)]
