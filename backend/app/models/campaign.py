"""
Campaign model - the core tenant entity.

Each campaign represents an election campaign that can have its own
members, departments, tasks, and workflows.
"""

import enum
from datetime import date
from typing import Optional, Any, TYPE_CHECKING

from sqlalchemy import String, Text, Date, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.membership import CampaignMembership
    from app.models.role import Role
    from app.models.department import Department


class CampaignStatus(str, enum.Enum):
    """Status of a campaign."""

    DRAFT = "draft"           # Campaign is being set up
    ACTIVE = "active"         # Campaign is actively running
    PAUSED = "paused"         # Campaign is temporarily paused
    COMPLETED = "completed"   # Campaign has ended successfully
    ARCHIVED = "archived"     # Campaign is archived for record-keeping


class Campaign(Base, TimestampMixin):
    """
    Campaign (tenant) entity.

    Each campaign is a separate tenant with its own data isolation.
    Campaigns represent election campaigns that can span a specific
    time period and have their own organizational structure.

    Attributes:
        name: Display name of the campaign
        slug: URL-friendly unique identifier
        description: Optional description of the campaign
        start_date: When the campaign officially starts
        end_date: When the campaign ends (e.g., election day)
        status: Current status of the campaign
        settings: JSON blob for campaign-specific configuration
        timezone: Campaign's timezone for scheduling
    """

    __tablename__ = "campaigns"

    # Basic info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Campaign period
    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Status
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus),
        default=CampaignStatus.DRAFT,
        nullable=False,
    )

    # Configuration
    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        default=dict,
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        nullable=False,
    )

    # Relationships (lazy loading by default, use selectinload() when needed)
    memberships: Mapped[list["CampaignMembership"]] = relationship(
        "CampaignMembership",
        back_populates="campaign",
        lazy="select",  # Lazy load to avoid N+1 when not needed
        cascade="all, delete-orphan",
    )
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        back_populates="campaign",
        lazy="select",
        cascade="all, delete-orphan",
    )
    departments: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="campaign",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, slug='{self.slug}')>"

    @property
    def is_active(self) -> bool:
        """Check if the campaign is currently active."""
        return self.status == CampaignStatus.ACTIVE

    @property
    def member_count(self) -> int:
        """Get count of active members."""
        return sum(1 for m in self.memberships if m.is_active)

    @property
    def days_until_end(self) -> Optional[int]:
        """Calculate days until campaign ends."""
        if self.end_date:
            delta = self.end_date - date.today()
            return delta.days
        return None
