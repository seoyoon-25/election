"""Add check constraint to prevent circular department hierarchy.

Revision ID: 20240107_000000
Revises: 20240106_000000
Create Date: 2026-03-20

Prevents a department from being its own parent (direct self-reference).
Application-level validation handles multi-level cycles.
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20240107_000000"
down_revision = "20240106_000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Prevent direct self-reference: department cannot be its own parent
    op.create_check_constraint(
        "ck_departments_no_self_parent",
        "departments",
        "id != parent_id OR parent_id IS NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_departments_no_self_parent", "departments", type_="check")
