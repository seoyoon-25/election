"""
Department model for organizational structure.

Departments represent organizational units within a campaign
(e.g., Policy, Communications, Field Operations, etc.)
"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, TenantMixin

if TYPE_CHECKING:
    from app.models.campaign import Campaign
    from app.models.membership import CampaignMembership


class Department(Base, TimestampMixin, TenantMixin):
    """
    Department within a campaign.

    Departments provide organizational structure and can be used
    to filter tasks, events, and permissions.

    Attributes:
        name: Display name of the department
        slug: URL-friendly identifier (unique within campaign)
        description: Optional description
        color: Hex color code for UI display
        sort_order: Order for display in lists
        parent_id: Optional parent department for hierarchy
    """

    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    color: Mapped[str] = mapped_column(
        String(7),  # Hex color like #FF5733
        default="#6B7280",
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Self-referential foreign key for hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        back_populates="departments",
    )
    memberships: Mapped[list["CampaignMembership"]] = relationship(
        "CampaignMembership",
        back_populates="department",
        foreign_keys="CampaignMembership.department_id",
    )
    parent: Mapped[Optional["Department"]] = relationship(
        "Department",
        remote_side="Department.id",
        back_populates="children",
    )
    children: Mapped[list["Department"]] = relationship(
        "Department",
        back_populates="parent",
    )

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}', campaign_id={self.campaign_id})>"

    @property
    def member_count(self) -> int:
        """Get count of active members in this department."""
        return sum(1 for m in self.memberships if m.is_active)

    @property
    def full_path(self) -> str:
        """Get full hierarchical path (e.g., 'Operations > Field')."""
        parts = [self.name]
        current = self.parent
        seen_ids = {self.id}

        # Traverse up the hierarchy with cycle detection
        while current is not None:
            if current.id in seen_ids:
                # Circular reference detected, stop traversal
                break
            seen_ids.add(current.id)
            parts.insert(0, current.name)
            current = current.parent

        return " > ".join(parts)

    def would_create_cycle(self, new_parent_id: int | None) -> bool:
        """
        Check if setting parent_id would create a circular reference.

        Args:
            new_parent_id: The proposed new parent department ID

        Returns:
            True if setting this parent would create a cycle
        """
        if new_parent_id is None:
            return False

        if new_parent_id == self.id:
            return True

        # Check if the new parent is a descendant of this department
        def is_descendant(dept_id: int, target_id: int, visited: set) -> bool:
            if dept_id in visited:
                return False
            visited.add(dept_id)

            for child in self.children:
                if child.id == target_id:
                    return True
                if is_descendant(child.id, target_id, visited):
                    return True
            return False

        return is_descendant(self.id, new_parent_id, set())


# Default departments created for new campaigns
DEFAULT_DEPARTMENTS: list[dict] = [
    {
        "name": "General Affairs",
        "slug": "general-affairs",
        "description": "Administrative and general operations",
        "color": "#6B7280",
        "sort_order": 1,
    },
    {
        "name": "Field Operations",
        "slug": "field-operations",
        "description": "Ground game, canvassing, and voter outreach",
        "color": "#10B981",
        "sort_order": 2,
    },
    {
        "name": "Policy",
        "slug": "policy",
        "description": "Policy research and position development",
        "color": "#3B82F6",
        "sort_order": 3,
    },
    {
        "name": "Digital & Social Media",
        "slug": "digital",
        "description": "Online presence, social media, and digital advertising",
        "color": "#8B5CF6",
        "sort_order": 4,
    },
    {
        "name": "Press & Communications",
        "slug": "press",
        "description": "Media relations and public communications",
        "color": "#F59E0B",
        "sort_order": 5,
    },
    {
        "name": "Spokesperson",
        "slug": "spokesperson",
        "description": "Official campaign spokesperson team",
        "color": "#EF4444",
        "sort_order": 6,
    },
    {
        "name": "Volunteers",
        "slug": "volunteers",
        "description": "Volunteer coordination and management",
        "color": "#EC4899",
        "sort_order": 7,
    },
]
