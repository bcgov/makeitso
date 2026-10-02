"""cancelled and interrupted deploy statuses

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-02 12:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # Alembic doesn't detect new enum values, so this is written by hand
    op.execute("ALTER TYPE deploystatus ADD VALUE IF NOT EXISTS 'CANCELLED'")
    op.execute("ALTER TYPE deploystatus ADD VALUE IF NOT EXISTS 'INTERRUPTED'")


def downgrade():
    # Postgres can't drop enum values; move the rows back to ABORTED and leave the values unused
    op.execute("UPDATE deploy SET status = 'ABORTED' WHERE status IN ('CANCELLED', 'INTERRUPTED')")
