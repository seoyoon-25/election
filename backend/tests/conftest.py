"""
Pytest configuration and fixtures for Campaign Operations OS tests.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models import (
    User,
    Campaign,
    CampaignMembership,
    Role,
    Permission,
    CampaignStatus,
)
from app.models.google_calendar import (
    GoogleCalendarConnection,
    SyncedEvent,
    ConnectionStatus,
    SyncedEventStatus,
)
from app.api.deps import get_db, get_current_user, get_campaign_membership
from app.core.security import create_access_token
from app.core.encryption import TokenEncryption


# Initialize encryption without key for tests
TokenEncryption.initialize(None)


# =============================================================================
# Model Fixtures
# =============================================================================


@pytest.fixture
def test_user() -> User:
    """Create a test user."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.is_superadmin = False
    return user


@pytest.fixture
def test_campaign() -> Campaign:
    """Create a test campaign."""
    campaign = MagicMock(spec=Campaign)
    campaign.id = 1
    campaign.name = "Test Campaign"
    campaign.slug = "test-campaign"
    campaign.status = CampaignStatus.ACTIVE
    return campaign


@pytest.fixture
def admin_role() -> Role:
    """Create an admin role with all permissions."""
    role = MagicMock(spec=Role)
    role.id = 1
    role.campaign_id = 1
    role.name = "Admin"
    role.permissions = [p.value for p in Permission]
    role.is_system = True
    return role


@pytest.fixture
def test_membership(test_user, test_campaign, admin_role) -> CampaignMembership:
    """Create a test campaign membership with admin role."""
    membership = MagicMock(spec=CampaignMembership)
    membership.id = 1
    membership.user_id = test_user.id
    membership.campaign_id = test_campaign.id
    membership.role_id = admin_role.id
    membership.is_active = True
    membership.role = admin_role
    membership.user = test_user
    membership.campaign = test_campaign

    # Mock has_permission to return True for all permissions
    membership.has_permission = MagicMock(return_value=True)
    membership.has_any_permission = MagicMock(return_value=True)

    return membership


@pytest.fixture
def test_connection(test_campaign) -> GoogleCalendarConnection:
    """Create a test Google Calendar connection."""
    conn = MagicMock(spec=GoogleCalendarConnection)
    conn.id = 1
    conn.campaign_id = test_campaign.id
    conn.google_calendar_id = "primary"
    conn.google_account_email = "calendar@example.com"
    conn.display_name = "Test Calendar"
    conn.status = ConnectionStatus.ACTIVE
    conn.is_primary = True
    conn.scopes = [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
    ]
    conn.last_sync_at = datetime.now(timezone.utc)
    conn.access_token = "test_access_token"
    conn.refresh_token = "test_refresh_token"
    conn.error_message = None
    return conn


@pytest.fixture
def test_synced_event(test_connection) -> SyncedEvent:
    """Create a test synced event."""
    event = MagicMock(spec=SyncedEvent)
    event.id = 1
    event.campaign_id = test_connection.campaign_id
    event.connection_id = test_connection.id
    event.google_event_id = "event123"
    event.title = "Test Event"
    event.description = "Test event description"
    event.start_time = datetime.now(timezone.utc) + timedelta(hours=1)
    event.end_time = datetime.now(timezone.utc) + timedelta(hours=2)
    event.location = "Test Location"
    event.status = SyncedEventStatus.CONFIRMED
    event.html_link = "https://calendar.google.com/event?eid=event123"
    event.creator_email = "creator@example.com"
    event.is_recurring = False
    event.last_synced_at = datetime.now(timezone.utc)
    return event


# =============================================================================
# Google Calendar Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_google_event():
    """Create a mock Google Calendar event response."""
    now = datetime.now(timezone.utc)
    return {
        "id": "event123",
        "summary": "Test Event",
        "description": "Test event description",
        "location": "Test Location",
        "start": {"dateTime": (now + timedelta(hours=1)).isoformat()},
        "end": {"dateTime": (now + timedelta(hours=2)).isoformat()},
        "status": "confirmed",
        "htmlLink": "https://calendar.google.com/event?eid=event123",
        "creator": {"email": "creator@example.com"},
        "organizer": {"email": "organizer@example.com"},
        "attendees": [
            {
                "email": "attendee1@example.com",
                "displayName": "Attendee One",
                "responseStatus": "accepted",
            },
            {
                "email": "attendee2@example.com",
                "responseStatus": "needsAction",
            },
        ],
        "created": now.isoformat(),
        "updated": now.isoformat(),
    }


@pytest.fixture
def mock_google_events_list(mock_google_event):
    """Create a mock Google Calendar events list response."""
    return {
        "items": [mock_google_event],
        "nextPageToken": None,
    }


@pytest.fixture
def mock_calendar_service(mock_google_event, mock_google_events_list):
    """Create a mock Google Calendar API service."""
    service = MagicMock()

    # Mock events().list()
    events_list = MagicMock()
    events_list.execute.return_value = mock_google_events_list

    # Mock events().get()
    events_get = MagicMock()
    events_get.execute.return_value = mock_google_event

    # Mock events().insert()
    events_insert = MagicMock()
    events_insert.execute.return_value = mock_google_event

    # Mock events().update()
    events_update = MagicMock()
    events_update.execute.return_value = mock_google_event

    # Mock events().delete()
    events_delete = MagicMock()
    events_delete.execute.return_value = None

    # Wire up the service
    events = MagicMock()
    events.list.return_value = events_list
    events.get.return_value = events_get
    events.insert.return_value = events_insert
    events.update.return_value = events_update
    events.delete.return_value = events_delete

    service.events.return_value = events

    return service


# =============================================================================
# Database Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


# =============================================================================
# HTTP Client Fixtures
# =============================================================================


@pytest.fixture
def auth_headers(test_user) -> dict:
    """Create authentication headers with a valid JWT token."""
    token = create_access_token(test_user.id)
    return {
        "Authorization": f"Bearer {token}",
        "X-Campaign-ID": "1",
    }


@pytest.fixture
async def client(
    mock_db_session,
    test_user: User,
    test_membership: CampaignMembership,
) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with mocked dependencies."""

    async def override_get_db():
        yield mock_db_session

    async def override_get_current_user():
        return test_user

    async def override_get_campaign_membership():
        return test_membership

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_campaign_membership] = override_get_campaign_membership

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sync_client(
    mock_db_session,
    test_user: User,
    test_membership: CampaignMembership,
) -> TestClient:
    """Create a synchronous test client."""

    async def override_get_db():
        yield mock_db_session

    async def override_get_current_user():
        return test_user

    async def override_get_campaign_membership():
        return test_membership

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_campaign_membership] = override_get_campaign_membership

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# =============================================================================
# Settings Fixtures
# =============================================================================


@pytest.fixture
def mock_settings():
    """Create mock application settings."""
    settings = MagicMock()
    settings.google_oauth_client_id = "test_client_id"
    settings.google_oauth_client_secret = "test_client_secret"
    settings.api_base_url = "http://localhost:8000"
    settings.frontend_base_url = "http://localhost:3000"
    return settings
