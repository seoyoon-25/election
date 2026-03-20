"""Add approval workflow and Google Calendar integration models

Revision ID: 003_add_approval_calendar
Revises: 002_add_tasks
Create Date: 2024-01-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_add_approval_calendar"
down_revision: Union[str, None] = "002_add_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # Enum Types
    # ==========================================================================

    # Approval workflow enums
    op.execute("CREATE TYPE approvertype AS ENUM ('member', 'role', 'department_head', 'creator_manager')")
    op.execute("CREATE TYPE approvalstatus AS ENUM ('pending', 'approved', 'rejected', 'cancelled', 'expired')")

    # Google Calendar integration enums
    op.execute("CREATE TYPE connectionstatus AS ENUM ('active', 'inactive', 'error')")
    op.execute("CREATE TYPE syncedeventstatus AS ENUM ('confirmed', 'tentative', 'cancelled')")

    # ==========================================================================
    # Approval Workflow Tables
    # ==========================================================================

    # Create approval_workflows table
    op.create_table(
        "approval_workflows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("require_all_steps", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("auto_expire_hours", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_workflows_campaign_id", "approval_workflows", ["campaign_id"])
    op.create_index("ix_approval_workflows_entity_type", "approval_workflows", ["entity_type"])

    # Create approval_workflow_steps table
    op.create_table(
        "approval_workflow_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "approver_type",
            postgresql.ENUM("member", "role", "department_head", "creator_manager", name="approvertype", create_type=False),
            nullable=False,
        ),
        sa.Column("approver_id", sa.Integer(), nullable=True),
        sa.Column("is_optional", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("can_reject", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["approval_workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_workflow_steps_workflow_id", "approval_workflow_steps", ["workflow_id"])
    op.create_index("ix_workflow_step_order", "approval_workflow_steps", ["workflow_id", "step_order"], unique=True)

    # Create approval_requests table
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("workflow_id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("current_step_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "approved", "rejected", "cancelled", "expired", name="approvalstatus", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("requested_by_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_id"], ["approval_workflows.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["campaign_memberships.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_requests_campaign_id", "approval_requests", ["campaign_id"])
    op.create_index("ix_approval_requests_workflow_id", "approval_requests", ["workflow_id"])
    op.create_index("ix_approval_request_entity", "approval_requests", ["entity_type", "entity_id"])
    op.create_index("ix_approval_request_status", "approval_requests", ["campaign_id", "status"])

    # Create approval_request_steps table
    op.create_table(
        "approval_request_steps",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("workflow_step_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("pending", "approved", "rejected", "cancelled", "expired", name="approvalstatus", create_type=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("decided_by_id", sa.Integer(), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["approval_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workflow_step_id"], ["approval_workflow_steps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decided_by_id"], ["campaign_memberships.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_request_steps_request_id", "approval_request_steps", ["request_id"])
    op.create_index("ix_request_step_order", "approval_request_steps", ["request_id", "step_order"], unique=True)

    # ==========================================================================
    # Google Calendar Integration Tables
    # ==========================================================================

    # Create google_calendar_connections table
    op.create_table(
        "google_calendar_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("google_calendar_id", sa.String(length=255), nullable=False, server_default="primary"),
        sa.Column("google_account_email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column(
            "status",
            postgresql.ENUM("active", "inactive", "error", name="connectionstatus", create_type=False),
            nullable=False,
            server_default="active",
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gcal_conn_campaign_id", "google_calendar_connections", ["campaign_id"])
    op.create_index("ix_gcal_conn_campaign_status", "google_calendar_connections", ["campaign_id", "status"])
    op.create_index("ix_gcal_conn_campaign_primary", "google_calendar_connections", ["campaign_id", "is_primary"])

    # Create synced_events table (local cache/audit of Google Calendar events)
    op.create_table(
        "synced_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("connection_id", sa.Integer(), nullable=False),
        sa.Column("google_event_id", sa.String(length=255), nullable=False),
        sa.Column("google_etag", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("confirmed", "tentative", "cancelled", name="syncedeventstatus", create_type=False),
            nullable=False,
            server_default="confirmed",
        ),
        sa.Column("html_link", sa.String(length=500), nullable=True),
        sa.Column("creator_email", sa.String(length=255), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recurring_event_id", sa.String(length=255), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["google_calendar_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["campaign_memberships.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_synced_events_campaign_id", "synced_events", ["campaign_id"])
    op.create_index("ix_synced_events_connection_id", "synced_events", ["connection_id"])
    op.create_index("ix_synced_events_start_time", "synced_events", ["start_time"])
    op.create_index("ix_synced_event_unique", "synced_events", ["connection_id", "google_event_id"], unique=True)
    op.create_index("ix_synced_event_campaign_time", "synced_events", ["campaign_id", "start_time"])
    op.create_index("ix_synced_event_campaign_status", "synced_events", ["campaign_id", "status"])

    # ==========================================================================
    # Triggers for updated_at
    # ==========================================================================

    for table in [
        "approval_workflows",
        "approval_workflow_steps",
        "approval_requests",
        "approval_request_steps",
        "google_calendar_connections",
        "synced_events",
    ]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in [
        "approval_workflows",
        "approval_workflow_steps",
        "approval_requests",
        "approval_request_steps",
        "google_calendar_connections",
        "synced_events",
    ]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")

    # Drop tables in reverse order
    op.drop_table("synced_events")
    op.drop_table("google_calendar_connections")
    op.drop_table("approval_request_steps")
    op.drop_table("approval_requests")
    op.drop_table("approval_workflow_steps")
    op.drop_table("approval_workflows")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS syncedeventstatus")
    op.execute("DROP TYPE IF EXISTS connectionstatus")
    op.execute("DROP TYPE IF EXISTS approvalstatus")
    op.execute("DROP TYPE IF EXISTS approvertype")
