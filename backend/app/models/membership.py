"""
CampaignMembership model - junction table connecting Users to Campaigns.

This model represents a user's membership in a campaign, including
their role, department assignment, and membership status.
"""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.role import Permission

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.campaign import Campaign
    from app.models.role import Role
    from app.models.department import Department


class CampaignMembership(Base, TimestampMixin):
    """
    User's membership in a campaign.

    This is the junction table that connects users to campaigns and
    defines their role and department within each campaign.

    Attributes:
        user_id: Reference to the user
        campaign_id: Reference to the campaign
        role_id: Reference to the role (defines permissions)
        department_id: Optional department assignment
        title: Optional job title within the campaign
        is_active: Whether the membership is currently active
        joined_at: When the user joined the campaign
        invited_by_id: Who invited this user (for audit trail)
    """

    __tablename__ = "campaign_memberships"

    # Foreign keys
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    invited_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reports_to_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("campaign_memberships.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Membership details
    title: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_department_head: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="memberships",
        foreign_keys=[user_id],
    )
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        back_populates="memberships",
    )
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="memberships",
    )
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="memberships",
        foreign_keys=[department_id],
    )
    invited_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[invited_by_id],
    )
    reports_to: Mapped[Optional["CampaignMembership"]] = relationship(
        "CampaignMembership",
        remote_side="CampaignMembership.id",
        foreign_keys=[reports_to_id],
    )

    # Constraints
    __table_args__ = (
        # A user can only have one active membership per campaign
        UniqueConstraint(
            "user_id",
            "campaign_id",
            name="uq_user_campaign_membership",
        ),
        # Common query patterns
        Index("ix_membership_campaign_active", "campaign_id", "is_active"),
        Index("ix_membership_user_active", "user_id", "is_active"),
        Index("ix_membership_department", "department_id"),
        Index("ix_membership_reports_to", "reports_to_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<CampaignMembership("
            f"user_id={self.user_id}, "
            f"campaign_id={self.campaign_id}, "
            f"role_id={self.role_id})>"
        )

    def has_permission(self, permission: Permission | str) -> bool:
        """Check if member has a specific permission through their role."""
        return self.role.has_permission(permission)

    def has_any_permission(self, permissions: list[Permission | str]) -> bool:
        """Check if member has any of the specified permissions."""
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: list[Permission | str]) -> bool:
        """Check if member has all of the specified permissions."""
        return all(self.has_permission(p) for p in permissions)

    @property
    def display_name(self) -> str:
        """Get display name (title if set, otherwise role name)."""
        return self.title or self.role.name

    @property
    def is_owner(self) -> bool:
        """Check if this member is a campaign owner."""
        return self.role.slug == "owner" if self.role else False

    @property
    def is_admin(self) -> bool:
        """Check if this member is an admin or owner."""
        return self.role.slug in ("owner", "admin") if self.role else False
