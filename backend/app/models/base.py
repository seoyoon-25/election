"""
Base model classes and mixins for the Campaign Operations OS.

This module provides:
- Base: SQLAlchemy declarative base for all models
- TimestampMixin: Adds created_at/updated_at columns
- TenantMixin: Adds campaign_id for multi-tenant isolation
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Integer, ForeignKey, event, DateTime
from sqlalchemy.orm import declared_attr, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantMixin:
    """
    Mixin that adds campaign_id for multi-tenant isolation.

    All tenant-scoped models should inherit from this mixin.
    The campaign_id is automatically indexed for query performance.
    """

    @declared_attr
    def campaign_id(cls) -> Mapped[int]:
        return mapped_column(
            Integer,
            ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


# Event listener to ensure updated_at is always set on update
@event.listens_for(TimestampMixin, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    """Ensure updated_at is set before any update."""
    target.updated_at = datetime.now(timezone.utc)
