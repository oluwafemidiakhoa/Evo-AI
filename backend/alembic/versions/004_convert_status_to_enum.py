"""Convert status columns to use ENUM types

Revision ID: 004
Revises: 003
Create Date: 2026-01-02 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update existing data to lowercase before converting to ENUM
    # Campaigns
    op.execute("UPDATE campaigns SET status = LOWER(status)")
    op.execute("ALTER TABLE campaigns ALTER COLUMN status TYPE campaignstatusenum USING status::campaignstatusenum")

    # Rounds
    op.execute("UPDATE rounds SET status = LOWER(status)")
    op.execute("ALTER TABLE rounds ALTER COLUMN status TYPE roundstatusenum USING status::roundstatusenum")

    # Policies
    op.execute("UPDATE policies SET policy_type = LOWER(policy_type)")
    op.execute("ALTER TABLE policies ALTER COLUMN policy_type TYPE policytypeenum USING policy_type::policytypeenum")


def downgrade() -> None:
    # Convert back to text/varchar
    op.execute("ALTER TABLE policies ALTER COLUMN policy_type TYPE VARCHAR")
    op.execute("ALTER TABLE rounds ALTER COLUMN status TYPE VARCHAR")
    op.execute("ALTER TABLE campaigns ALTER COLUMN status TYPE VARCHAR")
