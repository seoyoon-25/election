"""
Google Calendar API service.

Wraps Google Calendar API calls for event management:
- Listing events
- Creating events
- Updating events
- Deleting events
- Syncing events to local cache
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models.google_calendar import (
    GoogleCalendarConnection,
    SyncedEvent,
    SyncedEventStatus,
    ConnectionStatus,
)
from app.schemas.google_calendar import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventResponse,
    CalendarEventList,
    CalendarEventAttendee,
    GoogleCalendarConnectionStatus,
)
from app.services.google_auth_service import (
    GoogleAuthService,
    ConnectionNotFoundError,
    TokenRefreshError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class GoogleCalendarError(Exception):
    """Base exception for Google Calendar errors."""

    pass


class CalendarNotConnectedError(GoogleCalendarError):
    """No Google Calendar connected for this campaign."""

    pass


class EventNotFoundError(GoogleCalendarError):
    """Event not found in Google Calendar."""

    pass


class CalendarAPIError(GoogleCalendarError):
    """Error from Google Calendar API."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


# =============================================================================
# Google Calendar Service
# =============================================================================


class GoogleCalendarService:
    """
    Service for interacting with Google Calendar API.

    Provides methods for listing, creating, updating, and deleting events
    in connected Google Calendars.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = GoogleAuthService(db)

    async def _get_calendar_service(
        self,
        connection: GoogleCalendarConnection,
    ):
        """
        Build Google Calendar API service client.

        Args:
            connection: The Google Calendar connection

        Returns:
            Google Calendar API service resource
        """
        credentials = await self.auth_service.get_valid_credentials(connection)
        return build("calendar", "v3", credentials=credentials)

    async def _get_connection_or_raise(
        self,
        campaign_id: int,
    ) -> GoogleCalendarConnection:
        """Get active connection or raise error."""
        connection = await self.auth_service.get_connection(campaign_id)
        if connection is None:
            raise CalendarNotConnectedError(
                f"No Google Calendar connected for campaign {campaign_id}"
            )
        return connection

    # -------------------------------------------------------------------------
    # Connection Status
    # -------------------------------------------------------------------------

    async def get_connection_status(
        self,
        campaign_id: int,
    ) -> GoogleCalendarConnectionStatus:
        """
        Get the current connection status for a campaign.

        Args:
            campaign_id: Campaign to check

        Returns:
            Connection status details
        """
        connection = await self.auth_service.get_connection(
            campaign_id, active_only=False
        )

        if connection is None:
            return GoogleCalendarConnectionStatus(is_connected=False)

        return GoogleCalendarConnectionStatus(
            is_connected=connection.status == ConnectionStatus.ACTIVE,
            connection_id=connection.id,
            google_account_email=connection.google_account_email,
            calendar_id=connection.google_calendar_id,
            display_name=connection.display_name,
            status=connection.status.value,
            last_sync_at=connection.last_sync_at,
            error_message=connection.error_message,
        )

    # -------------------------------------------------------------------------
    # Event Listing
    # -------------------------------------------------------------------------

    async def list_events(
        self,
        campaign_id: int,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 50,
        page_token: Optional[str] = None,
        sync_to_local: bool = True,
    ) -> CalendarEventList:
        """
        List events from Google Calendar.

        Args:
            campaign_id: Campaign to list events for
            time_min: Start of time range (defaults to now)
            time_max: End of time range (defaults to 30 days from now)
            max_results: Maximum number of events to return
            page_token: Token for pagination
            sync_to_local: Whether to sync events to local cache

        Returns:
            List of calendar events
        """
        connection = await self._get_connection_or_raise(campaign_id)

        # Set default time range
        now = datetime.now(timezone.utc)
        if time_min is None:
            time_min = now
        if time_max is None:
            time_max = now + timedelta(days=30)

        try:
            service = await self._get_calendar_service(connection)

            # Build request
            request = service.events().list(
                calendarId=connection.google_calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=max_results,
                singleEvents=True,  # Expand recurring events
                orderBy="startTime",
                pageToken=page_token,
            )

            # Execute request
            result = request.execute()

            # Parse events
            events = []
            for item in result.get("items", []):
                event = self._parse_google_event(item)
                events.append(event)

            # Sync to local cache if requested
            if sync_to_local and events:
                await self._sync_events_to_local(connection, events)

            # Update last sync time
            connection.last_sync_at = now
            await self.db.commit()

            return CalendarEventList(
                items=events,
                next_page_token=result.get("nextPageToken"),
                time_min=time_min,
                time_max=time_max,
                total_items=len(events),
            )

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise CalendarAPIError(
                f"Failed to list events: {e.reason}",
                status_code=e.resp.status,
            )

    async def get_event(
        self,
        campaign_id: int,
        event_id: str,
    ) -> CalendarEventResponse:
        """
        Get a single event from Google Calendar.

        Args:
            campaign_id: Campaign the event belongs to
            event_id: Google Calendar event ID

        Returns:
            Event details
        """
        connection = await self._get_connection_or_raise(campaign_id)

        try:
            service = await self._get_calendar_service(connection)
            result = service.events().get(
                calendarId=connection.google_calendar_id,
                eventId=event_id,
            ).execute()

            return self._parse_google_event(result)

        except HttpError as e:
            if e.resp.status == 404:
                raise EventNotFoundError(f"Event {event_id} not found")
            logger.error(f"Google Calendar API error: {e}")
            raise CalendarAPIError(
                f"Failed to get event: {e.reason}",
                status_code=e.resp.status,
            )

    # -------------------------------------------------------------------------
    # Event Creation
    # -------------------------------------------------------------------------

    async def create_event(
        self,
        campaign_id: int,
        event_data: CalendarEventCreate,
        created_by_id: Optional[int] = None,
    ) -> CalendarEventResponse:
        """
        Create an event in Google Calendar.

        Args:
            campaign_id: Campaign to create event for
            event_data: Event data
            created_by_id: ID of the member creating the event

        Returns:
            Created event details
        """
        connection = await self._get_connection_or_raise(campaign_id)

        try:
            service = await self._get_calendar_service(connection)

            # Build event body
            body = self._build_event_body(event_data)

            # Create event
            result = service.events().insert(
                calendarId=connection.google_calendar_id,
                body=body,
                sendUpdates="all" if event_data.send_notifications else "none",
            ).execute()

            event = self._parse_google_event(result)

            # Sync to local cache
            await self._sync_event_to_local(connection, event, created_by_id)

            logger.info(
                f"Created event '{event.title}' (ID: {event.id}) "
                f"for campaign {campaign_id}"
            )

            return event

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise CalendarAPIError(
                f"Failed to create event: {e.reason}",
                status_code=e.resp.status,
            )

    # -------------------------------------------------------------------------
    # Event Update
    # -------------------------------------------------------------------------

    async def update_event(
        self,
        campaign_id: int,
        event_id: str,
        event_data: CalendarEventUpdate,
    ) -> CalendarEventResponse:
        """
        Update an event in Google Calendar.

        Args:
            campaign_id: Campaign the event belongs to
            event_id: Google Calendar event ID
            event_data: Updated event data

        Returns:
            Updated event details
        """
        connection = await self._get_connection_or_raise(campaign_id)

        try:
            service = await self._get_calendar_service(connection)

            # Get existing event first
            existing = service.events().get(
                calendarId=connection.google_calendar_id,
                eventId=event_id,
            ).execute()

            # Merge updates
            body = self._merge_event_updates(existing, event_data)

            # Update event
            result = service.events().update(
                calendarId=connection.google_calendar_id,
                eventId=event_id,
                body=body,
                sendUpdates="all" if event_data.send_notifications else "none",
            ).execute()

            event = self._parse_google_event(result)

            # Sync to local cache
            await self._sync_event_to_local(connection, event)

            logger.info(
                f"Updated event '{event.title}' (ID: {event.id}) "
                f"for campaign {campaign_id}"
            )

            return event

        except HttpError as e:
            if e.resp.status == 404:
                raise EventNotFoundError(f"Event {event_id} not found")
            logger.error(f"Google Calendar API error: {e}")
            raise CalendarAPIError(
                f"Failed to update event: {e.reason}",
                status_code=e.resp.status,
            )

    # -------------------------------------------------------------------------
    # Event Deletion
    # -------------------------------------------------------------------------

    async def delete_event(
        self,
        campaign_id: int,
        event_id: str,
        send_notifications: bool = True,
    ) -> None:
        """
        Delete an event from Google Calendar.

        Args:
            campaign_id: Campaign the event belongs to
            event_id: Google Calendar event ID
            send_notifications: Whether to notify attendees
        """
        connection = await self._get_connection_or_raise(campaign_id)

        try:
            service = await self._get_calendar_service(connection)

            service.events().delete(
                calendarId=connection.google_calendar_id,
                eventId=event_id,
                sendUpdates="all" if send_notifications else "none",
            ).execute()

            # Remove from local cache
            await self.db.execute(
                delete(SyncedEvent).where(
                    and_(
                        SyncedEvent.connection_id == connection.id,
                        SyncedEvent.google_event_id == event_id,
                    )
                )
            )
            await self.db.commit()

            logger.info(f"Deleted event {event_id} for campaign {campaign_id}")

        except HttpError as e:
            if e.resp.status == 404:
                # Event already deleted, clean up local cache
                await self.db.execute(
                    delete(SyncedEvent).where(
                        and_(
                            SyncedEvent.connection_id == connection.id,
                            SyncedEvent.google_event_id == event_id,
                        )
                    )
                )
                await self.db.commit()
                return

            logger.error(f"Google Calendar API error: {e}")
            raise CalendarAPIError(
                f"Failed to delete event: {e.reason}",
                status_code=e.resp.status,
            )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _parse_google_event(self, item: dict) -> CalendarEventResponse:
        """Parse Google Calendar event into our schema."""
        # Parse start/end times
        start = item.get("start", {})
        end = item.get("end", {})

        # Handle all-day events (date) vs timed events (dateTime)
        all_day = "date" in start
        if all_day:
            start_time = datetime.fromisoformat(start["date"])
            end_time = datetime.fromisoformat(end["date"])
        else:
            start_time = datetime.fromisoformat(
                start.get("dateTime", "").replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(
                end.get("dateTime", "").replace("Z", "+00:00")
            )

        # Parse attendees
        attendees = []
        for att in item.get("attendees", []):
            attendees.append(
                CalendarEventAttendee(
                    email=att.get("email", ""),
                    display_name=att.get("displayName"),
                    response_status=att.get("responseStatus"),
                    organizer=att.get("organizer", False),
                    self_=att.get("self", False),
                )
            )

        # Parse creator/organizer
        creator = item.get("creator", {})
        organizer = item.get("organizer", {})

        return CalendarEventResponse(
            id=item["id"],
            title=item.get("summary", "(No title)"),
            description=item.get("description"),
            location=item.get("location"),
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            status=item.get("status", "confirmed"),
            html_link=item.get("htmlLink", ""),
            creator_email=creator.get("email"),
            organizer_email=organizer.get("email"),
            attendees=attendees,
            created=datetime.fromisoformat(
                item.get("created", "").replace("Z", "+00:00")
            ),
            updated=datetime.fromisoformat(
                item.get("updated", "").replace("Z", "+00:00")
            ),
            recurring_event_id=item.get("recurringEventId"),
            recurrence=item.get("recurrence"),
        )

    def _build_event_body(self, event_data: CalendarEventCreate) -> dict:
        """Build Google Calendar event body from our schema."""
        body = {
            "summary": event_data.title,
        }

        if event_data.description:
            body["description"] = event_data.description

        if event_data.location:
            body["location"] = event_data.location

        # Handle all-day vs timed events
        if event_data.all_day:
            body["start"] = {"date": event_data.start_time.date().isoformat()}
            body["end"] = {"date": event_data.end_time.date().isoformat()}
        else:
            body["start"] = {"dateTime": event_data.start_time.isoformat()}
            body["end"] = {"dateTime": event_data.end_time.isoformat()}

        # Add attendees
        if event_data.attendees:
            body["attendees"] = [{"email": email} for email in event_data.attendees]

        return body

    def _merge_event_updates(
        self,
        existing: dict,
        updates: CalendarEventUpdate,
    ) -> dict:
        """Merge updates into existing event body."""
        body = existing.copy()

        if updates.title is not None:
            body["summary"] = updates.title

        if updates.description is not None:
            body["description"] = updates.description

        if updates.location is not None:
            body["location"] = updates.location

        if updates.start_time is not None:
            if "date" in body.get("start", {}):
                body["start"] = {"date": updates.start_time.date().isoformat()}
            else:
                body["start"] = {"dateTime": updates.start_time.isoformat()}

        if updates.end_time is not None:
            if "date" in body.get("end", {}):
                body["end"] = {"date": updates.end_time.date().isoformat()}
            else:
                body["end"] = {"dateTime": updates.end_time.isoformat()}

        if updates.attendees is not None:
            body["attendees"] = [{"email": email} for email in updates.attendees]

        return body

    async def _sync_events_to_local(
        self,
        connection: GoogleCalendarConnection,
        events: list[CalendarEventResponse],
    ) -> None:
        """Sync events to local cache."""
        for event in events:
            await self._sync_event_to_local(connection, event)

    async def _sync_event_to_local(
        self,
        connection: GoogleCalendarConnection,
        event: CalendarEventResponse,
        created_by_id: Optional[int] = None,
    ) -> None:
        """Sync a single event to local cache."""
        now = datetime.now(timezone.utc)

        # Check if event already exists
        result = await self.db.execute(
            select(SyncedEvent).where(
                and_(
                    SyncedEvent.connection_id == connection.id,
                    SyncedEvent.google_event_id == event.id,
                )
            )
        )
        existing = result.scalar_one_or_none()

        # Map status
        status_map = {
            "confirmed": SyncedEventStatus.CONFIRMED,
            "tentative": SyncedEventStatus.TENTATIVE,
            "cancelled": SyncedEventStatus.CANCELLED,
        }
        status = status_map.get(event.status, SyncedEventStatus.CONFIRMED)

        if existing:
            # Update existing record
            existing.title = event.title
            existing.description = event.description
            existing.start_time = event.start_time
            existing.end_time = event.end_time
            existing.location = event.location
            existing.status = status
            existing.html_link = event.html_link
            existing.creator_email = event.creator_email
            existing.is_recurring = event.recurring_event_id is not None
            existing.recurring_event_id = event.recurring_event_id
            existing.last_synced_at = now
        else:
            # Create new record
            synced = SyncedEvent(
                campaign_id=connection.campaign_id,
                connection_id=connection.id,
                google_event_id=event.id,
                title=event.title,
                description=event.description,
                start_time=event.start_time,
                end_time=event.end_time,
                location=event.location,
                status=status,
                html_link=event.html_link,
                creator_email=event.creator_email,
                created_by_id=created_by_id,
                is_recurring=event.recurring_event_id is not None,
                recurring_event_id=event.recurring_event_id,
                last_synced_at=now,
            )
            self.db.add(synced)

        await self.db.commit()
