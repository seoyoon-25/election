"""
Authentication API Endpoints

Handles:
- POST /auth/register - Register new user
- POST /auth/login - Login and get tokens
- POST /auth/logout - Logout (client-side token removal)
- POST /auth/refresh - Refresh access token
- GET /auth/me - Get current user profile
- PATCH /auth/me - Update current user profile
- POST /auth/me/avatar - Upload avatar
- POST /auth/password/change - Change password
- POST /auth/password/reset-request - Request password reset
- POST /auth/password/reset-confirm - Confirm password reset
"""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, get_current_user_optional
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    AuthResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChangeRequest,
    LogoutRequest,
)
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserInactiveError,
    InvalidTokenError,
    InvalidPasswordError,
    UserNotFoundError,
)
from app.services.token_blacklist import blacklist_token, invalidate_all_user_tokens


router = APIRouter(prefix="/auth", tags=["Authentication"])

# Security scheme for getting raw access token
security = HTTPBearer(auto_error=False)


def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    """Dependency to get auth service instance."""
    return AuthService(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password.",
)
async def register(
    data: RegisterRequest,
    auth_service: AuthServiceDep,
):
    """
    Register a new user account.

    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)
    - **full_name**: User's full name
    - **phone**: Optional phone number

    Returns the created user and authentication tokens.
    """
    try:
        user, tokens = await auth_service.register(data)

        return AuthResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                phone=user.phone,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                is_email_verified=user.is_email_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
            ),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
                expires_in=tokens.expires_in,
            ),
        )
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login",
    description="Authenticate with email and password to get access tokens.",
)
async def login(
    data: LoginRequest,
    auth_service: AuthServiceDep,
):
    """
    Authenticate user and return tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns the user profile and authentication tokens.
    """
    try:
        user, tokens = await auth_service.login(data)

        return AuthResponse(
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                phone=user.phone,
                avatar_url=user.avatar_url,
                is_active=user.is_active,
                is_email_verified=user.is_email_verified,
                created_at=user.created_at,
                updated_at=user.updated_at,
            ),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
                expires_in=tokens.expires_in,
            ),
        )
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )
    except UserInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Logout the current user and invalidate tokens.",
)
async def logout(
    current_user: CurrentUser,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    data: Optional[LogoutRequest] = None,
):
    """
    Logout the current user and blacklist tokens.

    Blacklists the access token from the Authorization header.
    If a refresh_token is provided in the request body, it will also be blacklisted.

    The client should still discard tokens locally after logout.
    """
    # Blacklist the access token
    if credentials:
        await blacklist_token(credentials.credentials)

    # Blacklist refresh token if provided
    if data and data.refresh_token:
        await blacklist_token(data.refresh_token)

    return None


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Get new access token using refresh token.",
)
async def refresh_tokens(
    data: RefreshTokenRequest,
    auth_service: AuthServiceDep,
):
    """
    Refresh access token using a valid refresh token.

    - **refresh_token**: A valid refresh token

    Returns new access and refresh tokens.
    """
    try:
        user, tokens = await auth_service.refresh_tokens(data.refresh_token)

        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except (InvalidTokenError, UserNotFoundError, UserInactiveError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the profile of the currently authenticated user.",
)
async def get_me(
    current_user: CurrentUser,
):
    """
    Get current user's profile.

    Returns the authenticated user's profile information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the profile of the currently authenticated user.",
)
async def update_me(
    data: UserUpdate,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
):
    """
    Update current user's profile.

    - **full_name**: New full name (optional)
    - **phone**: New phone number (optional)
    - **avatar_url**: New avatar URL (optional)

    Returns the updated user profile.
    """
    updated_user = await auth_service.update_profile(
        user=current_user,
        full_name=data.full_name,
        phone=data.phone,
        avatar_url=data.avatar_url,
    )

    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        full_name=updated_user.full_name,
        phone=updated_user.phone,
        avatar_url=updated_user.avatar_url,
        is_active=updated_user.is_active,
        is_email_verified=updated_user.is_email_verified,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at,
    )


@router.post(
    "/password/change",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change password for the currently authenticated user.",
)
async def change_password(
    data: PasswordChangeRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
):
    """
    Change the current user's password.

    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)

    Returns 204 No Content on success.
    All existing sessions/tokens will be invalidated.
    """
    try:
        await auth_service.change_password(
            user=current_user,
            current_password=data.current_password,
            new_password=data.new_password,
        )
        # Invalidate all existing tokens for security
        await invalidate_all_user_tokens(current_user.id)
        return None
    except InvalidPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/password/reset-request",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request password reset",
    description="Request a password reset email.",
)
async def request_password_reset(
    data: PasswordResetRequest,
    auth_service: AuthServiceDep,
):
    """
    Request a password reset.

    - **email**: Email address of the account

    Always returns 202 Accepted to prevent email enumeration.
    If the email exists, a reset token will be generated.

    Note: In production, you would send an email with the reset link.
    For now, the token is returned in the response (remove in production!).
    """
    token = await auth_service.request_password_reset(data.email)

    # In production, send email and don't return the token
    # For development, we return the token
    return {
        "message": "If the email exists, a password reset link has been sent.",
        # Remove this in production:
        "debug_token": token,
    }


@router.post(
    "/password/reset-confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Confirm password reset",
    description="Reset password using the reset token.",
)
async def confirm_password_reset(
    data: PasswordResetConfirm,
    auth_service: AuthServiceDep,
):
    """
    Reset password using a reset token.

    - **token**: Password reset token from email
    - **new_password**: New password (minimum 8 characters)

    Returns 204 No Content on success.
    """
    try:
        await auth_service.reset_password(
            token=data.token,
            new_password=data.new_password,
        )
        return None
    except (InvalidTokenError, UserNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/check",
    summary="Check authentication status",
    description="Check if the current request is authenticated.",
)
async def check_auth(
    current_user: OptionalUser,
):
    """
    Check if the request is authenticated.

    Returns authentication status and user info if authenticated.
    Useful for frontend to check if the user is logged in.
    """
    if current_user:
        return {
            "authenticated": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "full_name": current_user.full_name,
            },
        }
    return {
        "authenticated": False,
        "user": None,
    }


# =============================================================================
# Google OAuth Endpoints
# =============================================================================

import secrets
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse
from app.config import get_settings


class GoogleOAuthStateStore:
    """Simple in-memory store for Google OAuth state tokens."""

    _states: dict[str, dict] = {}

    @classmethod
    def create_state(cls, redirect_uri: str) -> str:
        from datetime import datetime, timezone
        state = secrets.token_urlsafe(32)
        cls._states[state] = {
            "redirect_uri": redirect_uri,
            "created_at": datetime.now(timezone.utc),
        }
        return state

    @classmethod
    def validate_state(cls, state: str) -> Optional[str]:
        from datetime import datetime, timezone, timedelta
        if state not in cls._states:
            return None
        data = cls._states.pop(state)
        created_at = data["created_at"]
        if datetime.now(timezone.utc) - created_at > timedelta(minutes=10):
            return None
        return data["redirect_uri"]


@router.get(
    "/google",
    summary="Start Google OAuth",
    description="Start Google OAuth flow for login/signup.",
)
async def google_oauth_start(
    redirect_uri: str = "/login",
):
    """
    Start Google OAuth flow.

    - **redirect_uri**: Frontend URL to redirect after OAuth completes

    Returns the Google authorization URL to redirect the user to.
    """
    settings = get_settings()

    if not settings.google_oauth_client_id:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured",
        )

    state = GoogleOAuthStateStore.create_state(redirect_uri)
    callback_url = f"{settings.api_base_url}/api/v1/auth/google/callback"

    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }

    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return {"authorization_url": google_auth_url}


@router.get(
    "/google/callback",
    summary="Google OAuth callback",
    description="Handle callback from Google OAuth.",
)
async def google_oauth_callback(
    code: str,
    state: str,
    auth_service: AuthServiceDep,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Handle Google OAuth callback.

    Exchanges authorization code for tokens, gets user info,
    and either logs in existing user or creates new user if invited.
    """
    import httpx
    from sqlalchemy import select
    from app.models import User, Invitation

    settings = get_settings()

    # Validate state
    redirect_uri = GoogleOAuthStateStore.validate_state(state)
    if not redirect_uri:
        return RedirectResponse(
            url=f"{settings.frontend_base_url}/login?error=invalid_state"
        )

    callback_url = f"{settings.api_base_url}/api/v1/auth/google/callback"

    # Exchange code for tokens
    try:
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_oauth_client_id,
                    "client_secret": settings.google_oauth_client_secret,
                    "redirect_uri": callback_url,
                    "grant_type": "authorization_code",
                },
            )
            token_data = token_response.json()

            if "error" in token_data:
                return RedirectResponse(
                    url=f"{settings.frontend_base_url}/login?error=oauth_failed"
                )

            access_token = token_data["access_token"]

            # Get user info from Google
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo = userinfo_response.json()
    except Exception:
        return RedirectResponse(
            url=f"{settings.frontend_base_url}/login?error=oauth_failed"
        )

    email = userinfo.get("email")
    full_name = userinfo.get("name", email.split("@")[0])
    avatar_url = userinfo.get("picture")

    if not email:
        return RedirectResponse(
            url=f"{settings.frontend_base_url}/login?error=email_required"
        )

    # Check if user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        # Existing user - login
        if not user.is_active:
            return RedirectResponse(
                url=f"{settings.frontend_base_url}/login?error=account_disabled"
            )

        # Update avatar if not set
        if not user.avatar_url and avatar_url:
            user.avatar_url = avatar_url
            await db.commit()

        # Generate tokens
        tokens = auth_service._generate_tokens(user.id)

        # Redirect with tokens
        params = urlencode({
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
        })
        return RedirectResponse(
            url=f"{settings.frontend_base_url}/login/callback?{params}"
        )

    # New user - check for pending invitation
    from datetime import datetime, timezone
    from sqlalchemy.orm import selectinload
    from app.models import Invitation, InvitationStatus, CampaignMembership

    invitation_result = await db.execute(
        select(Invitation)
        .options(selectinload(Invitation.campaign))
        .where(
            Invitation.email == email.lower(),
            Invitation.status == InvitationStatus.PENDING.value,
        )
        .order_by(Invitation.created_at.desc())
    )
    invitation = invitation_result.scalar_one_or_none()

    # No invitation or expired - reject signup
    if not invitation or invitation.is_expired:
        return RedirectResponse(
            url=f"{settings.frontend_base_url}/login?error=invitation_required&email={email}"
        )

    # Valid invitation found - create user and membership
    # Create user
    new_user = User(
        email=email.lower(),
        password_hash="",  # No password for OAuth-only users
        full_name=full_name,
        avatar_url=avatar_url,
        is_active=True,
        email_verified_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    await db.flush()  # Get user ID

    # Create campaign membership
    membership = CampaignMembership(
        user_id=new_user.id,
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
    tokens = auth_service._generate_tokens(new_user.id)

    # Redirect with tokens
    params = urlencode({
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
    })
    return RedirectResponse(
        url=f"{settings.frontend_base_url}/login/callback?{params}"
    )
