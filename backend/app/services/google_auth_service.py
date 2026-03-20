"""
Google OAuth 2.0 authentication service.

Handles the OAuth flow for Google Calendar integration:
- Generating authorization URLs
- Exchanging authorization codes for tokens
- Refreshing access tokens
- Revoking tokens on disconnect
"""

import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import google.auth.exceptions

from app.config import get_settings
from app.models.google_calendar import GoogleCalendarConnection, ConnectionStatus

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class GoogleAuthError(Exception):
    """Base exception for Google Auth errors."""

    pass


class OAuthFlowError(GoogleAuthError):
    """Error during OAuth flow."""

    pass


class TokenRefreshError(GoogleAuthError):
    """Error refreshing access token."""

    pass


class ConnectionNotFoundError(GoogleAuthError):
    """Google Calendar connection not found."""

    pass


# =============================================================================
# OAuth State Management
# =============================================================================


class OAuthStateStore:
    """
    Simple in-memory store for OAuth state tokens.

    In production, consider using Redis or database-backed storage
    for distributed deployments.
    """

    _states: dict[str, dict] = {}
    _expiry_minutes: int = 10

    @classmethod
    def create_state(cls, campaign_id: int, redirect_uri: str) -> str:
        """Create and store a state token."""
        state = secrets.token_urlsafe(32)
        cls._states[state] = {
            "campaign_id": campaign_id,
            "redirect_uri": redirect_uri,
            "created_at": datetime.now(timezone.utc),
        }
        # Clean up old states
        cls._cleanup()
        return state

    @classmethod
    def validate_state(cls, state: str) -> Optional[dict]:
        """Validate and consume a state token."""
        if state not in cls._states:
            return None

        data = cls._states.pop(state)
        created_at = data["created_at"]

        # Check expiration
        if datetime.now(timezone.utc) - created_at > timedelta(minutes=cls._expiry_minutes):
            return None

        return data

    @classmethod
    def _cleanup(cls) -> None:
        """Remove expired states."""
        now = datetime.now(timezone.utc)
        expired = [
            state
            for state, data in cls._states.items()
            if now - data["created_at"] > timedelta(minutes=cls._expiry_minutes)
        ]
        for state in expired:
            cls._states.pop(state, None)


# =============================================================================
# Google Auth Service
# =============================================================================


class GoogleAuthService:
    """
    Service for handling Google OAuth 2.0 authentication.

    Manages the OAuth flow and token lifecycle for Google Calendar integration.
    """

    # OAuth scopes for Google Calendar
    SCOPES = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    def _get_client_config(self) -> dict:
        """Get OAuth client configuration."""
        return {
            "web": {
                "client_id": self.settings.google_oauth_client_id,
                "client_secret": self.settings.google_oauth_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [],
            }
        }

    def get_authorization_url(
        self,
        campaign_id: int,
        redirect_uri: str,
        frontend_redirect_uri: str,
    ) -> tuple[str, str]:
        """
        Generate Google OAuth authorization URL.

        Args:
            campaign_id: Campaign to connect calendar to
            redirect_uri: OAuth callback URL (our backend endpoint)
            frontend_redirect_uri: Where to redirect after OAuth completes

        Returns:
            Tuple of (authorization_url, state_token)
        """
        # Create state token
        state = OAuthStateStore.create_state(campaign_id, frontend_redirect_uri)

        # Create OAuth flow
        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=self.SCOPES,
            redirect_uri=redirect_uri,
        )

        # Generate authorization URL
        authorization_url, _ = flow.authorization_url(
            access_type="offline",  # Get refresh token
            include_granted_scopes="true",
            prompt="consent",  # Always show consent screen to get refresh token
            state=state,
        )

        return authorization_url, state

    async def exchange_code_for_tokens(
        self,
        code: str,
        state: str,
        redirect_uri: str,
    ) -> GoogleCalendarConnection:
        """
        Exchange authorization code for access/refresh tokens.

        Args:
            code: Authorization code from Google
            state: State token for validation
            redirect_uri: OAuth callback URL (must match original)

        Returns:
            Created GoogleCalendarConnection

        Raises:
            OAuthFlowError: If state is invalid or token exchange fails
        """
        # Validate state
        state_data = OAuthStateStore.validate_state(state)
        if state_data is None:
            raise OAuthFlowError("Invalid or expired state token")

        campaign_id = state_data["campaign_id"]

        try:
            # Create OAuth flow and exchange code
            flow = Flow.from_client_config(
                self._get_client_config(),
                scopes=self.SCOPES,
                redirect_uri=redirect_uri,
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Get user email
            from googleapiclient.discovery import build
            oauth2_service = build("oauth2", "v2", credentials=credentials)
            user_info = oauth2_service.userinfo().get().execute()
            email = user_info.get("email", "unknown@gmail.com")

            # Deactivate any existing active connections for this campaign
            await self._deactivate_existing_connections(campaign_id)

            # Create new connection
            connection = GoogleCalendarConnection(
                campaign_id=campaign_id,
                google_calendar_id="primary",
                google_account_email=email,
                display_name=f"{email}'s Calendar",
                status=ConnectionStatus.ACTIVE,
                is_primary=True,
                scopes=list(credentials.scopes or self.SCOPES),
                token_expires_at=credentials.expiry,
            )
            connection.access_token = credentials.token
            connection.refresh_token = credentials.refresh_token

            self.db.add(connection)
            await self.db.commit()
            await self.db.refresh(connection)

            logger.info(
                f"Created Google Calendar connection for campaign {campaign_id} "
                f"with account {email}"
            )
            return connection

        except Exception as e:
            logger.error(f"OAuth token exchange failed: {e}")
            raise OAuthFlowError(f"Failed to complete OAuth flow: {e}")

    async def _deactivate_existing_connections(self, campaign_id: int) -> None:
        """Deactivate any existing active connections for a campaign."""
        result = await self.db.execute(
            select(GoogleCalendarConnection).where(
                and_(
                    GoogleCalendarConnection.campaign_id == campaign_id,
                    GoogleCalendarConnection.status == ConnectionStatus.ACTIVE,
                )
            )
        )
        existing = result.scalars().all()
        for conn in existing:
            conn.status = ConnectionStatus.INACTIVE
            conn.is_primary = False

    async def get_valid_credentials(
        self,
        connection: GoogleCalendarConnection,
    ) -> Credentials:
        """
        Get valid OAuth credentials, refreshing if needed.

        Args:
            connection: The Google Calendar connection

        Returns:
            Valid Google OAuth credentials

        Raises:
            TokenRefreshError: If token refresh fails
        """
        credentials = Credentials(
            token=connection.access_token,
            refresh_token=connection.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.google_oauth_client_id,
            client_secret=self.settings.google_oauth_client_secret,
            scopes=connection.scopes,
        )

        # Check if token needs refresh
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())

                # Update stored tokens
                connection.access_token = credentials.token
                connection.token_expires_at = credentials.expiry
                connection.status = ConnectionStatus.ACTIVE
                connection.error_message = None
                await self.db.commit()

                logger.debug(f"Refreshed access token for connection {connection.id}")

            except google.auth.exceptions.RefreshError as e:
                # Token refresh failed - mark connection as errored
                connection.status = ConnectionStatus.ERROR
                connection.error_message = f"Token refresh failed: {e}"
                await self.db.commit()

                logger.error(f"Token refresh failed for connection {connection.id}: {e}")
                raise TokenRefreshError(f"Failed to refresh access token: {e}")

        return credentials

    async def revoke_tokens(self, connection: GoogleCalendarConnection) -> None:
        """
        Revoke OAuth tokens for a connection.

        Args:
            connection: The connection to revoke tokens for
        """
        if connection.access_token:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "https://oauth2.googleapis.com/revoke",
                        params={"token": connection.access_token},
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                logger.info(f"Revoked tokens for connection {connection.id}")
            except Exception as e:
                # Log but don't fail - tokens will expire anyway
                logger.warning(f"Failed to revoke tokens: {e}")

    async def disconnect_calendar(self, campaign_id: int) -> bool:
        """
        Disconnect Google Calendar from a campaign.

        Args:
            campaign_id: Campaign to disconnect

        Returns:
            True if a connection was disconnected

        Raises:
            ConnectionNotFoundError: If no active connection exists
        """
        result = await self.db.execute(
            select(GoogleCalendarConnection).where(
                and_(
                    GoogleCalendarConnection.campaign_id == campaign_id,
                    GoogleCalendarConnection.status == ConnectionStatus.ACTIVE,
                )
            )
        )
        connection = result.scalar_one_or_none()

        if connection is None:
            raise ConnectionNotFoundError(
                f"No active Google Calendar connection for campaign {campaign_id}"
            )

        # Revoke tokens
        await self.revoke_tokens(connection)

        # Mark as inactive
        connection.status = ConnectionStatus.INACTIVE
        connection.is_primary = False
        await self.db.commit()

        logger.info(f"Disconnected Google Calendar for campaign {campaign_id}")
        return True

    async def get_connection(
        self,
        campaign_id: int,
        active_only: bool = True,
    ) -> Optional[GoogleCalendarConnection]:
        """
        Get Google Calendar connection for a campaign.

        Args:
            campaign_id: Campaign to get connection for
            active_only: If True, only return active connections

        Returns:
            GoogleCalendarConnection or None if not found
        """
        query = select(GoogleCalendarConnection).where(
            GoogleCalendarConnection.campaign_id == campaign_id
        )

        if active_only:
            query = query.where(
                GoogleCalendarConnection.status == ConnectionStatus.ACTIVE
            )

        query = query.order_by(GoogleCalendarConnection.is_primary.desc())

        result = await self.db.execute(query)
        return result.scalar_one_or_none()
