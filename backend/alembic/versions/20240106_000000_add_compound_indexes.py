"""Add compound indexes for performance optimization.

Revision ID: 20240106_000000
Revises: 20240105_000000_add_invitations_table
Create Date: 2026-03-20

Adds missing compound indexes:
- task_history(task_id, created_at) for pagination
- task_assignments index optimization
- task_comments(task_id, created_at) for pagination
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20240106_000000"
down_revision = "20240105_000000_add_invitations_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Task history: for pagination queries (task_id + created_at DESC)
    op.create_index(
        "ix_task_history_task_created",
        "task_history",
        ["task_id", "created_at"],
        unique=False,
    )

    # Task comments: for pagination queries (task_id + created_at DESC)
    op.create_index(
        "ix_task_comments_task_created",
        "task_comments",
        ["task_id", "created_at"],
        unique=False,
    )

    # Task assignments: member_id index for "my tasks" query
    # (task_id, member_id) already exists as unique, add member_id alone
    op.create_index(
        "ix_task_assignments_member",
        "task_assignments",
        ["member_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_task_assignments_member", table_name="task_assignments")
    op.drop_index("ix_task_comments_task_created", table_name="task_comments")
    op.drop_index("ix_task_history_task_created", table_name="task_history")
