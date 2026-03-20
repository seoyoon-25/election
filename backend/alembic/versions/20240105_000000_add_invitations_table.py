"""Add invitations table for pending campaign invitations

Revision ID: 005_invitations
Revises: 004_rls_policies
Create Date: 2024-01-05 00:00:00.000000

This migration adds the invitations table for storing pending
invitations to users who don't have accounts yet.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005_invitations"
down_revision: Union[str, None] = "004_rls_policies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create invitations table."""
    # Note: The enum type 'invitationstatus' may already exist from a previous partial migration.
    # We use create_type=False in the Enum column definition to avoid re-creation.
    # If starting fresh, uncomment the following line:
    # op.execute("CREATE TYPE invitationstatus AS ENUM ('pending', 'accepted', 'expired', 'cancelled');")

    op.create_table(
        "invitations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=True),
        sa.Column("department_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(100), nullable=True),
        sa.Column("invited_by_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "accepted", "expired", "cancelled", name="invitationstatus", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["invited_by_id"], ["users.id"], ondelete="SET NULL"),
    )

    # Create indexes
    op.create_index("ix_invitations_email", "invitations", ["email"])
    op.create_index("ix_invitations_token", "invitations", ["token"], unique=True)
    op.create_index("ix_invitations_campaign_status", "invitations", ["campaign_id", "status"])


def downgrade() -> None:
    """Drop invitations table."""
    op.drop_index("ix_invitations_campaign_status", "invitations")
    op.drop_index("ix_invitations_token", "invitations")
    op.drop_index("ix_invitations_email", "invitations")
    op.drop_table("invitations")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS invitationstatus")
