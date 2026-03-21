"""
Invitation model for pending campaign invitations.

Stores invitations for users who don't have accounts yet.
When they accept, their account is created and they join the campaign.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import secrets

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base


class InvitationStatus(str, enum.Enum):
    """Status values for invitations."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Invitation(Base):
    """Pending invitation to join a campaign."""

    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Invitation details
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)

    # Campaign to join
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)

    # Role and department to assign
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(100), nullable=True)

    # Who invited
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Status tracking
    status = Column(
        Enum(
            InvitationStatus,
            values_callable=lambda x: [e.value for e in x],
            name="invitationstatus",
            create_constraint=False,
        ),
        default=InvitationStatus.PENDING,
        server_default='pending',
        nullable=False
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    campaign = relationship("Campaign", backref="invitations")
    role = relationship("Role")
    department = relationship("Department")
    invited_by = relationship("User")

    @staticmethod
    def generate_token() -> str:
        """Generate a secure invitation token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def default_expiry() -> datetime:
        """Default expiration: 7 days from now."""
        return datetime.now(timezone.utc) + timedelta(days=7)

    @property
    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if invitation is still valid (pending and not expired)."""
        status_val = self.status.value if isinstance(self.status, InvitationStatus) else self.status
        return status_val == InvitationStatus.PENDING.value and not self.is_expired
