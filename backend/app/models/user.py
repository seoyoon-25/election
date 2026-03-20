"""
User model for authentication and identity management.

Users are global entities (not tenant-scoped) that can belong to
multiple campaigns through CampaignMembership.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.membership import CampaignMembership


class User(Base, TimestampMixin):
    """
    User account for authentication.

    Users are global and can be members of multiple campaigns.
    Authentication is handled via email/password with JWT tokens.

    Attributes:
        email: Unique email address for login
        password_hash: Argon2 hashed password
        full_name: User's display name
        phone: Optional phone number for contact
        avatar_url: URL to user's profile picture
        is_active: Whether the user can log in
        is_superadmin: Platform-level admin (can manage all campaigns)
        email_verified_at: When email was verified (None if not verified)
        last_login_at: Timestamp of most recent login
    """

    __tablename__ = "users"

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Profile fields
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superadmin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Verification and login tracking
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships (lazy loading by default)
    memberships: Mapped[list["CampaignMembership"]] = relationship(
        "CampaignMembership",
        back_populates="user",
        lazy="select",  # Lazy load to avoid N+1 when not needed
        cascade="all, delete-orphan",
        foreign_keys="CampaignMembership.user_id",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"

    @property
    def is_email_verified(self) -> bool:
        """Check if the user's email has been verified."""
        return self.email_verified_at is not None

    @property
    def campaigns(self) -> list:
        """Get list of campaigns user is a member of."""
        return [m.campaign for m in self.memberships if m.is_active]
