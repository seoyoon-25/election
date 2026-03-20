"""
Tests for Google Calendar API endpoints.

Tests cover:
- OAuth flow (connect, callback, disconnect, status)
- Event CRUD operations (list, create, get, update, delete)
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlencode, parse_qs, urlparse

from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.google_calendar import (
    GoogleCalendarConnection,
    ConnectionStatus,
    SyncedEvent,
)
from app.services.google_auth_service import OAuthStateStore
from app.api.deps import get_db, get_current_user, get_campaign_membership


# =============================================================================
# Helper to create unauthenticated client
# =============================================================================


@pytest.fixture
async def unauthenticated_client() -> AsyncClient:
    """Create an async test client without authentication overrides."""
    # Clear any existing overrides
    app.dependency_overrides.clear()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# =============================================================================
# OAuth Flow Tests
# =============================================================================


class TestOAuthConnect:
    """Tests for GET /campaigns/{id}/calendar/connect"""

    @pytest.mark.asyncio
    async def test_start_oauth_flow_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test starting OAuth flow returns authorization URL."""
        with patch("app.api.v1.calendar.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.api_base_url = "http://localhost:8000"
            mock_settings.google_oauth_client_id = "test_client_id"
            mock_settings.google_oauth_client_secret = "test_secret"
            mock_get_settings.return_value = mock_settings

            with patch(
                "app.services.google_auth_service.Flow.from_client_config"
            ) as mock_flow:
                mock_flow_instance = MagicMock()
                mock_flow_instance.authorization_url.return_value = (
                    "https://accounts.google.com/o/oauth2/auth?client_id=test",
                    "test_state",
                )
                mock_flow.return_value = mock_flow_instance

                response = await client.get(
                    "/api/v1/campaigns/1/calendar/connect",
                    params={"redirect_uri": "http://localhost:3000/callback"},
                    headers=auth_headers,
                )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "authorization_url" in data
        assert "state" in data
        assert data["authorization_url"].startswith("https://accounts.google.com")

    @pytest.mark.asyncio
    async def test_start_oauth_flow_requires_auth(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test that OAuth flow requires authentication."""
        response = await unauthenticated_client.get(
            "/api/v1/campaigns/1/calendar/connect",
            params={"redirect_uri": "http://localhost:3000/callback"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_start_oauth_flow_requires_redirect_uri(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test that redirect_uri is required."""
        response = await client.get(
            "/api/v1/campaigns/1/calendar/connect",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestOAuthCallback:
    """Tests for GET /campaigns/{id}/calendar/callback"""

    @pytest.mark.asyncio
    async def test_callback_invalid_state(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test callback with invalid state redirects with error."""
        response = await unauthenticated_client.get(
            "/api/v1/campaigns/1/calendar/callback",
            params={"state": "invalid_state", "code": "auth_code"},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        location = response.headers.get("location")
        assert "status=error" in location
        assert "invalid_state" in location

    @pytest.mark.asyncio
    async def test_callback_with_oauth_error(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test callback handles OAuth error from Google."""
        # Create a valid state first
        state = OAuthStateStore.create_state(
            campaign_id=1,
            redirect_uri="http://localhost:3000/calendar",
        )

        response = await unauthenticated_client.get(
            "/api/v1/campaigns/1/calendar/callback",
            params={
                "state": state,
                "error": "access_denied",
                "error_description": "User denied access",
            },
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        location = response.headers.get("location")
        assert "status=error" in location
        assert "access_denied" in location

    @pytest.mark.asyncio
    async def test_callback_without_code(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test callback without authorization code redirects with error."""
        state = OAuthStateStore.create_state(
            campaign_id=1,
            redirect_uri="http://localhost:3000/calendar",
        )

        response = await unauthenticated_client.get(
            "/api/v1/campaigns/1/calendar/callback",
            params={"state": state},
            follow_redirects=False,
        )

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        location = response.headers.get("location")
        assert "status=error" in location
        assert "no_code" in location

    @pytest.mark.asyncio
    async def test_callback_success(
        self,
        mock_db_session,
    ):
        """Test successful OAuth callback creates connection."""
        # Create a valid state
        state = OAuthStateStore.create_state(
            campaign_id=1,
            redirect_uri="http://localhost:3000/calendar",
        )

        # Override only the db dependency for this test
        async def override_get_db():
            yield mock_db_session

        app.dependency_overrides[get_db] = override_get_db

        try:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                with patch("app.api.v1.calendar.get_settings") as mock_settings:
                    settings = MagicMock()
                    settings.api_base_url = "http://localhost:8000"
                    settings.frontend_base_url = "http://localhost:3000"
                    settings.google_oauth_client_id = "test_client_id"
                    settings.google_oauth_client_secret = "test_secret"
                    mock_settings.return_value = settings

                    with patch(
                        "app.services.google_auth_service.GoogleAuthService.exchange_code_for_tokens"
                    ) as mock_exchange:
                        mock_connection = MagicMock()
                        mock_connection.id = 1
                        mock_exchange.return_value = mock_connection

                        # Re-add state since it was consumed by validation
                        OAuthStateStore._states[state] = {
                            "campaign_id": 1,
                            "redirect_uri": "http://localhost:3000/calendar",
                            "created_at": datetime.now(timezone.utc),
                        }

                        response = await client.get(
                            "/api/v1/campaigns/1/calendar/callback",
                            params={"state": state, "code": "auth_code"},
                            follow_redirects=False,
                        )

            assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
            location = response.headers.get("location")
            assert "status=success" in location
        finally:
            app.dependency_overrides.clear()


class TestDisconnect:
    """Tests for DELETE /campaigns/{id}/calendar/disconnect"""

    @pytest.mark.asyncio
    async def test_disconnect_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test successful disconnect."""
        with patch(
            "app.api.v1.calendar.GoogleAuthService"
        ) as MockAuthService:
            mock_service = AsyncMock()
            mock_service.disconnect_calendar = AsyncMock(return_value=True)
            MockAuthService.return_value = mock_service

            response = await client.delete(
                "/api/v1/campaigns/1/calendar/disconnect",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_disconnect_no_connection(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test disconnect when no connection exists."""
        from app.services.google_auth_service import ConnectionNotFoundError

        with patch(
            "app.api.v1.calendar.GoogleAuthService"
        ) as MockAuthService:
            mock_service = AsyncMock()
            mock_service.disconnect_calendar = AsyncMock(
                side_effect=ConnectionNotFoundError("No connection")
            )
            MockAuthService.return_value = mock_service

            response = await client.delete(
                "/api/v1/campaigns/1/calendar/disconnect",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_disconnect_requires_auth(
        self,
        unauthenticated_client: AsyncClient,
    ):
        """Test disconnect requires authentication."""
        response = await unauthenticated_client.delete(
            "/api/v1/campaigns/1/calendar/disconnect"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestConnectionStatus:
    """Tests for GET /campaigns/{id}/calendar/status"""

    @pytest.mark.asyncio
    async def test_get_status_connected(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting status when calendar is connected."""
        from app.schemas.google_calendar import GoogleCalendarConnectionStatus

        mock_status = GoogleCalendarConnectionStatus(
            is_connected=True,
            connection_id=1,
            google_account_email="test@example.com",
            calendar_id="primary",
            display_name="Test Calendar",
            status="active",
            last_sync_at=datetime.now(timezone.utc),
        )

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.get_connection_status = AsyncMock(return_value=mock_status)
            MockCalendarService.return_value = mock_service

            response = await client.get(
                "/api/v1/campaigns/1/calendar/status",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_connected"] is True
        assert data["google_account_email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_status_not_connected(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting status when calendar is not connected."""
        from app.schemas.google_calendar import GoogleCalendarConnectionStatus

        mock_status = GoogleCalendarConnectionStatus(is_connected=False)

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.get_connection_status = AsyncMock(return_value=mock_status)
            MockCalendarService.return_value = mock_service

            response = await client.get(
                "/api/v1/campaigns/1/calendar/status",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_connected"] is False


# =============================================================================
# Event Endpoint Tests
# =============================================================================


class TestListEvents:
    """Tests for GET /campaigns/{id}/calendar/events"""

    @pytest.mark.asyncio
    async def test_list_events_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing events successfully."""
        from app.schemas.google_calendar import CalendarEventList, CalendarEventResponse

        now = datetime.now(timezone.utc)
        mock_event = CalendarEventResponse(
            id="event123",
            title="Test Event",
            description="Test description",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            all_day=False,
            status="confirmed",
            html_link="https://calendar.google.com/event",
            attendees=[],
            created=now,
            updated=now,
        )
        mock_list = CalendarEventList(
            items=[mock_event],
            next_page_token=None,
            time_min=now,
            time_max=now + timedelta(days=30),
            total_items=1,
        )

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.list_events = AsyncMock(return_value=mock_list)
            MockCalendarService.return_value = mock_service

            response = await client.get(
                "/api/v1/campaigns/1/calendar/events",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["summary"] == "Test Event"

    @pytest.mark.asyncio
    async def test_list_events_with_time_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing events with time range parameters."""
        from app.schemas.google_calendar import CalendarEventList

        now = datetime.now(timezone.utc)
        mock_list = CalendarEventList(
            items=[],
            next_page_token=None,
            time_min=now,
            time_max=now + timedelta(days=7),
            total_items=0,
        )

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.list_events = AsyncMock(return_value=mock_list)
            MockCalendarService.return_value = mock_service

            response = await client.get(
                "/api/v1/campaigns/1/calendar/events",
                params={
                    "time_min": now.isoformat(),
                    "time_max": (now + timedelta(days=7)).isoformat(),
                    "max_results": 10,
                },
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_list_events_not_connected(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing events when calendar is not connected."""
        from app.services.google_calendar_service import CalendarNotConnectedError

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.list_events = AsyncMock(
                side_effect=CalendarNotConnectedError("Not connected")
            )
            MockCalendarService.return_value = mock_service

            response = await client.get(
                "/api/v1/campaigns/1/calendar/events",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCreateEvent:
    """Tests for POST /campaigns/{id}/calendar/events"""

    @pytest.mark.asyncio
    async def test_create_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating an event successfully."""
        from app.schemas.google_calendar import CalendarEventResponse

        now = datetime.now(timezone.utc)
        mock_event = CalendarEventResponse(
            id="new_event123",
            title="New Event",
            description="New event description",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            all_day=False,
            status="confirmed",
            html_link="https://calendar.google.com/event",
            attendees=[],
            created=now,
            updated=now,
        )

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.create_event = AsyncMock(return_value=mock_event)
            MockCalendarService.return_value = mock_service

            response = await client.post(
                "/api/v1/campaigns/1/calendar/events",
                headers=auth_headers,
                json={
                    "title": "New Event",
                    "description": "New event description",
                    "start_time": (now + timedelta(hours=1)).isoformat(),
                    "end_time": (now + timedelta(hours=2)).isoformat(),
                    "all_day": False,
                },
            )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["summary"] == "New Event"
        assert data["id"] == "new_event123"

    @pytest.mark.asyncio
    async def test_create_event_with_attendees(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating an event with attendees."""
        from app.schemas.google_calendar import CalendarEventResponse

        now = datetime.now(timezone.utc)
        mock_event = CalendarEventResponse(
            id="event_with_attendees",
            title="Meeting",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            all_day=False,
            status="confirmed",
            html_link="https://calendar.google.com/event",
            attendees=[],
            created=now,
            updated=now,
        )

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.create_event = AsyncMock(return_value=mock_event)
            MockCalendarService.return_value = mock_service

            response = await client.post(
                "/api/v1/campaigns/1/calendar/events",
                headers=auth_headers,
                json={
                    "title": "Meeting",
                    "start_time": (now + timedelta(hours=1)).isoformat(),
                    "end_time": (now + timedelta(hours=2)).isoformat(),
                    "attendees": [
                        "attendee1@example.com",
                        "attendee2@example.com",
                    ],
                    "send_notifications": True,
                },
            )

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_create_event_validation_error(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating an event with invalid data."""
        response = await client.post(
            "/api/v1/campaigns/1/calendar/events",
            headers=auth_headers,
            json={
                "title": "",  # Empty title should fail
                "start_time": "invalid-date",
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetEvent:
    """Tests for GET /campaigns/{id}/calendar/events/{event_id}"""

    @pytest.mark.asyncio
    async def test_get_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting a single event."""
        from app.schemas.google_calendar import CalendarEventResponse

        now = datetime.now(timezone.utc)
        mock_event = CalendarEventResponse(
            id="event123",
            title="Test Event",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            all_day=False,
            status="confirmed",
            html_link="https://calendar.google.com/event",
            attendees=[],
            created=now,
            updated=now,
        )

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.get_event = AsyncMock(return_value=mock_event)
            MockCalendarService.return_value = mock_service

            response = await client.get(
                "/api/v1/campaigns/1/calendar/events/event123",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "event123"

    @pytest.mark.asyncio
    async def test_get_event_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting a non-existent event."""
        from app.services.google_calendar_service import EventNotFoundError

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.get_event = AsyncMock(
                side_effect=EventNotFoundError("Event not found")
            )
            MockCalendarService.return_value = mock_service

            response = await client.get(
                "/api/v1/campaigns/1/calendar/events/nonexistent",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateEvent:
    """Tests for PATCH /campaigns/{id}/calendar/events/{event_id}"""

    @pytest.mark.asyncio
    async def test_update_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating an event."""
        from app.schemas.google_calendar import CalendarEventResponse

        now = datetime.now(timezone.utc)
        mock_event = CalendarEventResponse(
            id="event123",
            title="Updated Event",
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            all_day=False,
            status="confirmed",
            html_link="https://calendar.google.com/event",
            attendees=[],
            created=now,
            updated=now,
        )

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.update_event = AsyncMock(return_value=mock_event)
            MockCalendarService.return_value = mock_service

            response = await client.patch(
                "/api/v1/campaigns/1/calendar/events/event123",
                headers=auth_headers,
                json={"title": "Updated Event"},
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["summary"] == "Updated Event"

    @pytest.mark.asyncio
    async def test_update_event_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test updating a non-existent event."""
        from app.services.google_calendar_service import EventNotFoundError

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.update_event = AsyncMock(
                side_effect=EventNotFoundError("Event not found")
            )
            MockCalendarService.return_value = mock_service

            response = await client.patch(
                "/api/v1/campaigns/1/calendar/events/nonexistent",
                headers=auth_headers,
                json={"title": "Updated"},
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteEvent:
    """Tests for DELETE /campaigns/{id}/calendar/events/{event_id}"""

    @pytest.mark.asyncio
    async def test_delete_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting an event."""
        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.delete_event = AsyncMock(return_value=None)
            MockCalendarService.return_value = mock_service

            response = await client.delete(
                "/api/v1/campaigns/1/calendar/events/event123",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_event_with_notifications(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting an event with notification option."""
        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.delete_event = AsyncMock(return_value=None)
            MockCalendarService.return_value = mock_service

            response = await client.delete(
                "/api/v1/campaigns/1/calendar/events/event123",
                params={"send_notifications": "false"},
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_event_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test deleting a non-existent event."""
        from app.services.google_calendar_service import EventNotFoundError

        with patch(
            "app.api.v1.calendar.GoogleCalendarService"
        ) as MockCalendarService:
            mock_service = AsyncMock()
            mock_service.delete_event = AsyncMock(
                side_effect=EventNotFoundError("Event not found")
            )
            MockCalendarService.return_value = mock_service

            response = await client.delete(
                "/api/v1/campaigns/1/calendar/events/nonexistent",
                headers=auth_headers,
            )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# Service Layer Tests
# =============================================================================


class TestGoogleAuthService:
    """Tests for GoogleAuthService."""

    def test_oauth_state_store_create_and_validate(self):
        """Test OAuth state creation and validation."""
        state = OAuthStateStore.create_state(
            campaign_id=1,
            redirect_uri="http://localhost:3000/callback",
        )

        assert state is not None
        assert len(state) > 20  # Should be a secure random token

        # Validate the state
        data = OAuthStateStore.validate_state(state)
        assert data is not None
        assert data["campaign_id"] == 1
        assert data["redirect_uri"] == "http://localhost:3000/callback"

        # State should be consumed
        data = OAuthStateStore.validate_state(state)
        assert data is None

    def test_oauth_state_store_invalid_state(self):
        """Test validation of invalid state."""
        data = OAuthStateStore.validate_state("invalid_state")
        assert data is None

    def test_oauth_state_store_expired_state(self):
        """Test validation of expired state."""
        state = OAuthStateStore.create_state(
            campaign_id=1,
            redirect_uri="http://localhost:3000/callback",
        )

        # Manually expire the state
        OAuthStateStore._states[state]["created_at"] = datetime(
            2020, 1, 1, tzinfo=timezone.utc
        )

        data = OAuthStateStore.validate_state(state)
        assert data is None


class TestTokenEncryption:
    """Tests for token encryption utility."""

    def test_encryption_without_key(self):
        """Test encryption works without key (plaintext mode)."""
        from app.core.encryption import TokenEncryption

        TokenEncryption.initialize(None)

        original = "test_token_value"
        encrypted = TokenEncryption.encrypt(original)
        decrypted = TokenEncryption.decrypt(encrypted)

        assert decrypted == original

    def test_encryption_with_key(self):
        """Test encryption with Fernet key."""
        from app.core.encryption import TokenEncryption
        from cryptography.fernet import Fernet

        key = Fernet.generate_key().decode()
        TokenEncryption.initialize(key)

        original = "test_token_value"
        encrypted = TokenEncryption.encrypt(original)
        decrypted = TokenEncryption.decrypt(encrypted)

        # Encrypted value should be different
        assert encrypted != original
        # But decrypted should match
        assert decrypted == original

        # Reset to no key for other tests
        TokenEncryption.initialize(None)
