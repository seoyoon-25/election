"""
Google Calendar integration schemas.

Pydantic models for Google Calendar API requests and responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, model_validator


# =============================================================================
# OAuth Flow Schemas
# =============================================================================


class OAuthStartResponse(BaseModel):
    """Response when initiating Google OAuth flow."""

    authorization_url: str = Field(
        ...,
        description="URL to redirect user to for Google authorization",
    )
    state: str = Field(
        ...,
        description="CSRF protection token (store in session for validation)",
    )


class OAuthCallbackParams(BaseModel):
    """Query parameters from OAuth callback."""

    code: str = Field(..., description="Authorization code from Google")
    state: str = Field(..., description="CSRF token for validation")
    error: Optional[str] = Field(None, description="Error code if authorization failed")
    error_description: Optional[str] = Field(None, description="Error description")


# =============================================================================
# Connection Schemas
# =============================================================================


class GoogleCalendarConnectionResponse(BaseModel):
    """Google Calendar connection details (safe for API response)."""

    id: int
    campaign_id: int
    google_calendar_id: str
    google_account_email: str
    display_name: Optional[str] = None
    status: str  # active, inactive, error
    is_primary: bool
    last_sync_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GoogleCalendarConnectionStatus(BaseModel):
    """Quick status check for frontend."""

    is_connected: bool
    connection_id: Optional[int] = None
    google_account_email: Optional[str] = None
    calendar_id: Optional[str] = None
    display_name: Optional[str] = None
    status: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    error_message: Optional[str] = None


class GoogleCalendarDisconnectResponse(BaseModel):
    """Response after disconnecting a calendar."""

    success: bool
    message: str


# =============================================================================
# Event Schemas
# =============================================================================


class CalendarEventAttendee(BaseModel):
    """Event attendee information."""

    email: EmailStr
    display_name: Optional[str] = None
    response_status: Optional[str] = None  # needsAction, accepted, declined, tentative
    organizer: bool = False
    self_: bool = Field(default=False, alias="self")

    model_config = {"populate_by_name": True}


class CalendarEventBase(BaseModel):
    """Base schema for calendar events."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        alias="summary",
        description="Event title",
    )
    description: Optional[str] = Field(
        None,
        max_length=8000,
        description="Event description",
    )
    location: Optional[str] = Field(
        None,
        max_length=500,
        description="Event location",
    )
    start_time: datetime = Field(
        ...,
        alias="start",
        description="Event start datetime",
    )
    end_time: datetime = Field(
        ...,
        alias="end",
        description="Event end datetime",
    )

    model_config = {"populate_by_name": True}


class CalendarEventCreate(CalendarEventBase):
    """Schema for creating an event in Google Calendar."""

    attendees: list[str] = Field(
        default_factory=list,
        description="List of attendee email addresses",
    )
    send_notifications: bool = Field(
        default=True,
        description="Whether to send email notifications to attendees",
    )
    all_day: bool = Field(
        default=False,
        description="Whether this is an all-day event",
    )

    @model_validator(mode="after")
    def validate_times(self) -> "CalendarEventCreate":
        """Ensure end_time is after start_time."""
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class CalendarEventUpdate(BaseModel):
    """Partial update for an event in Google Calendar."""

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        alias="summary",
    )
    description: Optional[str] = Field(None, max_length=8000)
    location: Optional[str] = Field(None, max_length=500)
    start_time: Optional[datetime] = Field(None, alias="start")
    end_time: Optional[datetime] = Field(None, alias="end")
    attendees: Optional[list[str]] = None
    send_notifications: bool = True

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_times(self) -> "CalendarEventUpdate":
        """Ensure end_time is after start_time if both provided."""
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time <= self.start_time
        ):
            raise ValueError("end_time must be after start_time")
        return self


class CalendarEventResponse(BaseModel):
    """Event from Google Calendar."""

    id: str = Field(..., description="Google Calendar event ID")
    title: str = Field(..., alias="summary")
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: datetime = Field(..., alias="start")
    end_time: datetime = Field(..., alias="end")
    all_day: bool = False
    status: str = Field(
        ...,
        description="Event status: confirmed, tentative, cancelled",
    )
    html_link: str = Field(
        ...,
        description="Link to view event in Google Calendar",
    )
    creator_email: Optional[str] = None
    organizer_email: Optional[str] = None
    attendees: list[CalendarEventAttendee] = Field(default_factory=list)
    created: datetime
    updated: datetime

    # Recurrence info (read-only)
    recurring_event_id: Optional[str] = Field(
        None,
        description="ID of the recurring event this instance belongs to",
    )
    recurrence: Optional[list[str]] = Field(
        None,
        description="RRULE strings for recurring events",
    )

    model_config = {"populate_by_name": True}


class CalendarEventList(BaseModel):
    """Paginated list of events from Google Calendar."""

    items: list[CalendarEventResponse]
    next_page_token: Optional[str] = Field(
        None,
        description="Token to fetch next page of results",
    )
    time_min: datetime = Field(
        ...,
        description="Start of the time range queried",
    )
    time_max: datetime = Field(
        ...,
        description="End of the time range queried",
    )
    total_items: Optional[int] = Field(
        None,
        description="Total number of events (if available)",
    )


# =============================================================================
# Sync/Audit Schemas
# =============================================================================


class SyncedEventResponse(BaseModel):
    """Cached/audit record of a synced event."""

    id: int
    campaign_id: int
    connection_id: int
    google_event_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None
    status: str
    html_link: Optional[str] = None
    creator_email: Optional[str] = None
    is_recurring: bool
    last_synced_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SyncedEventList(BaseModel):
    """List of synced events from local cache."""

    items: list[SyncedEventResponse]
    total: int
    page: int
    page_size: int
    pages: int
