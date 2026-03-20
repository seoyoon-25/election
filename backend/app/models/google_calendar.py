"""
Google Calendar integration models.

Provides OAuth connection management and event sync tracking:
- GoogleCalendarConnection: OAuth tokens and calendar settings per campaign
- SyncedEvent: Local cache/audit trail of Google Calendar events
"""

import enum
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Index,
    ARRAY,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.membership import CampaignMembership


class ConnectionStatus(str, enum.Enum):
    """Status of a Google Calendar connection."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"  # Token refresh failed, needs re-auth


class SyncedEventStatus(str, enum.Enum):
    """Status of a synced event (mirrors Google Calendar status)."""

    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class GoogleCalendarConnection(Base, TimestampMixin, TenantMixin):
    """
    Google Calendar OAuth connection for a campaign.

    Stores OAuth credentials and connection settings.
    Designed to support multiple calendars per campaign in the future,
    but Phase 1 enforces one active connection per campaign.

    Attributes:
        campaign_id: Parent campaign
        google_calendar_id: Google Calendar ID (e.g., "primary" or email)
        google_account_email: Email of the connected Google account
        display_name: User-friendly name for this calendar
        access_token: Encrypted OAuth access token
        refresh_token: Encrypted OAuth refresh token
        token_expires_at: When the access token expires
        scopes: List of granted OAuth scopes
        status: Connection status (active, inactive, error)
        is_primary: Whether this is the primary calendar for the campaign
        last_sync_at: When events were last synced
        error_message: Last error message if status is ERROR
    """

    __tablename__ = "google_calendar_connections"

    # Google Calendar info
    google_calendar_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="primary",
    )
    google_account_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # OAuth tokens (stored encrypted - see property accessors)
    _access_token: Mapped[Optional[str]] = mapped_column(
        "access_token",
        Text,
        nullable=True,
    )
    _refresh_token: Mapped[Optional[str]] = mapped_column(
        "refresh_token",
        Text,
        nullable=True,
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    scopes: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=list,
        nullable=False,
    )

    # Connection state
    status: Mapped[ConnectionStatus] = mapped_column(
        Enum(ConnectionStatus),
        default=ConnectionStatus.ACTIVE,
        nullable=False,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        backref="google_calendar_connections",
    )
    synced_events: Mapped[list["SyncedEvent"]] = relationship(
        "SyncedEvent",
        back_populates="connection",
        cascade="all, delete-orphan",
    )

    # Indexes and constraints
    __table_args__ = (
        # Index for finding active connections
        Index("ix_gcal_conn_campaign_status", "campaign_id", "status"),
        # Index for finding primary calendar
        Index("ix_gcal_conn_campaign_primary", "campaign_id", "is_primary"),
    )

    def __repr__(self) -> str:
        return (
            f"<GoogleCalendarConnection("
            f"id={self.id}, "
            f"campaign_id={self.campaign_id}, "
            f"email='{self.google_account_email}')>"
        )

    # Token encryption/decryption via properties
    # Import here to avoid circular imports
    @property
    def access_token(self) -> Optional[str]:
        """Decrypt and return access token."""
        if self._access_token is None:
            return None
        from app.core.encryption import TokenEncryption
        return TokenEncryption.decrypt(self._access_token)

    @access_token.setter
    def access_token(self, value: Optional[str]) -> None:
        """Encrypt and store access token."""
        if value is None:
            self._access_token = None
        else:
            from app.core.encryption import TokenEncryption
            self._access_token = TokenEncryption.encrypt(value)

    @property
    def refresh_token(self) -> Optional[str]:
        """Decrypt and return refresh token."""
        if self._refresh_token is None:
            return None
        from app.core.encryption import TokenEncryption
        return TokenEncryption.decrypt(self._refresh_token)

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        """Encrypt and store refresh token."""
        if value is None:
            self._refresh_token = None
        else:
            from app.core.encryption import TokenEncryption
            self._refresh_token = TokenEncryption.encrypt(value)

    @property
    def is_token_expired(self) -> bool:
        """Check if access token is expired."""
        if self.token_expires_at is None:
            return True
        from datetime import timezone
        return datetime.now(timezone.utc) >= self.token_expires_at

    @property
    def is_active(self) -> bool:
        """Check if connection is active and usable."""
        return self.status == ConnectionStatus.ACTIVE


class SyncedEvent(Base, TimestampMixin, TenantMixin):
    """
    Local cache and audit trail for Google Calendar events.

    Stores minimal event data for:
    - Audit trail of events created/modified through our system
    - Caching to reduce Google API calls
    - Quick lookups without hitting Google API

    Attributes:
        campaign_id: Parent campaign
        connection_id: Parent Google Calendar connection
        google_event_id: Google Calendar event ID
        title: Event title
        description: Event description (truncated for storage)
        start_time: Event start datetime
        end_time: Event end datetime
        location: Event location
        status: Event status (confirmed, tentative, cancelled)
        html_link: Link to view event in Google Calendar
        creator_email: Email of event creator
        created_by_id: Our system user who created the event (if applicable)
        google_etag: Google's ETag for change detection
        is_recurring: Whether this is part of a recurring series
        recurring_event_id: Parent recurring event ID
        last_synced_at: When this event was last synced from Google
    """

    __tablename__ = "synced_events"

    # Parent references
    connection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("google_calendar_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Google Calendar identifiers
    google_event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    google_etag: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Event details
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    status: Mapped[SyncedEventStatus] = mapped_column(
        Enum(SyncedEventStatus),
        default=SyncedEventStatus.CONFIRMED,
        nullable=False,
    )
    html_link: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Creator tracking
    creator_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Recurrence info
    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    recurring_event_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Sync tracking
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Relationships
    connection: Mapped["GoogleCalendarConnection"] = relationship(
        "GoogleCalendarConnection",
        back_populates="synced_events",
    )
    created_by: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        foreign_keys=[created_by_id],
    )

    # Indexes
    __table_args__ = (
        # Unique event per connection
        Index(
            "ix_synced_event_unique",
            "connection_id",
            "google_event_id",
            unique=True,
        ),
        # Time-based queries
        Index("ix_synced_event_campaign_time", "campaign_id", "start_time"),
        # Status filtering
        Index("ix_synced_event_campaign_status", "campaign_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<SyncedEvent("
            f"id={self.id}, "
            f"google_event_id='{self.google_event_id}', "
            f"title='{self.title[:30]}')>"
        )
