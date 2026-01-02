"""Add PostgreSQL ENUM types

Revision ID: 003
Revises: 002
Create Date: 2026-01-02 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types for PostgreSQL
    op.execute("CREATE TYPE campaignstatusenum AS ENUM ('draft', 'active', 'paused', 'completed', 'failed')")
    op.execute("CREATE TYPE roundstatusenum AS ENUM ('pending', 'planning', 'generating', 'evaluating', 'selecting', 'reporting', 'completed', 'failed')")
    op.execute("CREATE TYPE policytypeenum AS ENUM ('selection', 'mutation', 'termination')")


def downgrade() -> None:
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS policytypeenum")
    op.execute("DROP TYPE IF EXISTS roundstatusenum")
    op.execute("DROP TYPE IF EXISTS campaignstatusenum")
