"""
Campaign Service

Handles campaign-related business logic:
- Campaign CRUD operations
- Default role and department creation
- Member management
"""

from typing import Optional
from slugify import slugify

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Campaign,
    CampaignStatus,
    CampaignMembership,
    Role,
    Department,
    User,
    SYSTEM_ROLES,
    DEFAULT_DEPARTMENTS,
)
from app.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignServiceError(Exception):
    """Base exception for campaign service errors."""

    def __init__(self, message: str, code: str = "campaign_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class CampaignNotFoundError(CampaignServiceError):
    """Raised when campaign is not found."""

    def __init__(self):
        super().__init__("Campaign not found", "campaign_not_found")


class SlugAlreadyExistsError(CampaignServiceError):
    """Raised when campaign slug already exists."""

    def __init__(self):
        super().__init__("Campaign slug already exists", "slug_exists")


class CampaignService:
    """Service for handling campaign operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_unique_slug(self, name: str, exclude_id: Optional[int] = None) -> str:
        """Generate a unique slug from campaign name."""
        base_slug = slugify(name, max_length=90)
        slug = base_slug
        counter = 1

        while True:
            query = select(Campaign).where(Campaign.slug == slug)
            if exclude_id:
                query = query.where(Campaign.id != exclude_id)

            result = await self.db.execute(query)
            if not result.scalar_one_or_none():
                return slug

            slug = f"{base_slug}-{counter}"
            counter += 1

    async def get_campaign_by_id(
        self,
        campaign_id: int,
        load_relations: bool = False,
    ) -> Optional[Campaign]:
        """Get campaign by ID."""
        query = select(Campaign).where(Campaign.id == campaign_id)

        if load_relations:
            query = query.options(
                selectinload(Campaign.roles),
                selectinload(Campaign.departments),
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_campaign_by_slug(self, slug: str) -> Optional[Campaign]:
        """Get campaign by slug."""
        result = await self.db.execute(
            select(Campaign).where(Campaign.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_user_campaigns(self, user: User) -> list[Campaign]:
        """Get all campaigns a user is a member of."""
        result = await self.db.execute(
            select(Campaign)
            .join(CampaignMembership)
            .where(
                CampaignMembership.user_id == user.id,
                CampaignMembership.is_active == True,
            )
            .order_by(Campaign.name)
        )
        return list(result.scalars().all())

    async def create_campaign(
        self,
        data: CampaignCreate,
        owner: User,
    ) -> Campaign:
        """
        Create a new campaign with default roles and departments.

        The creating user becomes the campaign owner.
        """
        # Generate slug if not provided
        slug = data.slug if data.slug else await self._generate_unique_slug(data.name)

        # Check if slug exists
        existing = await self.get_campaign_by_slug(slug)
        if existing:
            raise SlugAlreadyExistsError()

        # Create campaign
        campaign = Campaign(
            name=data.name,
            slug=slug,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            timezone=data.timezone,
            status=CampaignStatus.DRAFT,
        )
        self.db.add(campaign)
        await self.db.flush()

        # Create system roles
        owner_role = None
        for role_slug, role_data in SYSTEM_ROLES.items():
            role = Role(
                campaign_id=campaign.id,
                name=role_data["name"],
                slug=role_slug,
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_system=True,
                is_default=(role_slug == "staff"),
            )
            self.db.add(role)
            if role_slug == "owner":
                owner_role = role

        await self.db.flush()

        # Create default departments
        for dept_data in DEFAULT_DEPARTMENTS:
            dept = Department(
                campaign_id=campaign.id,
                **dept_data,
            )
            self.db.add(dept)

        await self.db.flush()

        # Add creator as owner
        membership = CampaignMembership(
            user_id=owner.id,
            campaign_id=campaign.id,
            role_id=owner_role.id,
            is_active=True,
        )
        self.db.add(membership)

        await self.db.flush()
        await self.db.refresh(campaign)

        return campaign

    async def update_campaign(
        self,
        campaign: Campaign,
        data: CampaignUpdate,
    ) -> Campaign:
        """Update campaign details."""
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(campaign, field, value)

        await self.db.flush()
        await self.db.refresh(campaign)

        return campaign

    async def delete_campaign(self, campaign: Campaign) -> None:
        """
        Delete a campaign.

        This will cascade delete all related data (roles, departments,
        memberships, tasks, etc.)
        """
        await self.db.delete(campaign)
        await self.db.flush()

    async def archive_campaign(self, campaign: Campaign) -> Campaign:
        """Archive a campaign."""
        campaign.status = CampaignStatus.ARCHIVED
        await self.db.flush()
        return campaign

    async def activate_campaign(self, campaign: Campaign) -> Campaign:
        """Activate a campaign."""
        campaign.status = CampaignStatus.ACTIVE
        await self.db.flush()
        return campaign

    async def get_campaign_stats(self, campaign_id: int) -> dict:
        """Get statistics for a campaign."""
        # Member count
        member_count = await self.db.execute(
            select(func.count(CampaignMembership.id))
            .where(
                CampaignMembership.campaign_id == campaign_id,
                CampaignMembership.is_active == True,
            )
        )

        # Department count
        dept_count = await self.db.execute(
            select(func.count(Department.id))
            .where(Department.campaign_id == campaign_id)
        )

        return {
            "member_count": member_count.scalar() or 0,
            "department_count": dept_count.scalar() or 0,
        }
