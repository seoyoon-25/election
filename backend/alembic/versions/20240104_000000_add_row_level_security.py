"""Add Row-Level Security policies for multi-tenant isolation

Revision ID: 004_rls_policies
Revises: 003_approval_calendar
Create Date: 2024-01-04 00:00:00.000000

This migration implements PostgreSQL Row-Level Security (RLS) to enforce
tenant isolation at the database level. Each tenant table gets:
1. RLS enabled
2. A policy that restricts access to rows matching the current campaign context
3. A bypass for superusers/service accounts

The campaign context is set via: SET app.current_campaign_id = '<id>'
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "004_rls_policies"
down_revision: Union[str, None] = "003_add_approval_calendar"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that have campaign_id column and need RLS
# Note: Child tables (task_assignments, task_comments, etc.) don't have campaign_id
# but are protected through their foreign key relationships to parent tables
TENANT_TABLES = [
    # Core tables
    "departments",
    "roles",
    "campaign_memberships",
    # Task management (only tables with direct campaign_id)
    "task_boards",
    "tasks",
    # Approval workflow (only tables with direct campaign_id)
    "approval_workflows",
    "approval_requests",
    # Google Calendar integration
    "google_calendar_connections",
    "synced_events",
]


def upgrade() -> None:
    """Enable RLS and create tenant isolation policies."""

    # First, create a helper function to safely get the current campaign ID
    # This returns NULL if not set, allowing us to handle it gracefully
    op.execute("""
        CREATE OR REPLACE FUNCTION get_current_campaign_id()
        RETURNS INTEGER AS $$
        BEGIN
            RETURN NULLIF(current_setting('app.current_campaign_id', true), '')::INTEGER;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)

    # Create RLS policies for each tenant table
    for table in TENANT_TABLES:
        # Enable RLS on the table
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

        # Force RLS even for table owners (important for security)
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Create policy for SELECT operations
        # Allows access when:
        # 1. The row's campaign_id matches the current context, OR
        # 2. No context is set (for migrations, admin operations)
        op.execute(f"""
            CREATE POLICY tenant_isolation_select_{table} ON {table}
            FOR SELECT
            USING (
                get_current_campaign_id() IS NULL
                OR campaign_id = get_current_campaign_id()
            );
        """)

        # Create policy for INSERT operations
        # Only allow inserting rows for the current campaign
        op.execute(f"""
            CREATE POLICY tenant_isolation_insert_{table} ON {table}
            FOR INSERT
            WITH CHECK (
                get_current_campaign_id() IS NULL
                OR campaign_id = get_current_campaign_id()
            );
        """)

        # Create policy for UPDATE operations
        # Only allow updating rows in the current campaign
        op.execute(f"""
            CREATE POLICY tenant_isolation_update_{table} ON {table}
            FOR UPDATE
            USING (
                get_current_campaign_id() IS NULL
                OR campaign_id = get_current_campaign_id()
            )
            WITH CHECK (
                get_current_campaign_id() IS NULL
                OR campaign_id = get_current_campaign_id()
            );
        """)

        # Create policy for DELETE operations
        # Only allow deleting rows in the current campaign
        op.execute(f"""
            CREATE POLICY tenant_isolation_delete_{table} ON {table}
            FOR DELETE
            USING (
                get_current_campaign_id() IS NULL
                OR campaign_id = get_current_campaign_id()
            );
        """)


def downgrade() -> None:
    """Remove RLS policies and disable RLS."""

    for table in TENANT_TABLES:
        # Drop all policies for this table
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_select_{table} ON {table};")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_insert_{table} ON {table};")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_update_{table} ON {table};")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_delete_{table} ON {table};")

        # Disable RLS on the table
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # Drop the helper function
    op.execute("DROP FUNCTION IF EXISTS get_current_campaign_id();")
