"""Initial database schema with all tables

Revision ID: 001
Revises:
Create Date: 2026-01-02 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create campaigns table
    op.create_table('campaigns',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_campaigns_name', 'campaigns', ['name'], unique=False)
    op.create_index('idx_campaigns_status', 'campaigns', ['status', 'deleted_at'], unique=False)

    # Create rounds table
    op.create_table('rounds',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('round_number', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('plan', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rounds_campaign', 'rounds', ['campaign_id', 'round_number'], unique=False)

    # Create variants table
    op.create_table('variants',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('round_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('generation', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('content_hash', sa.String(length=64), nullable=False),
    sa.Column('mutation_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('is_selected', sa.Boolean(), nullable=False),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['variants.id'], ),
    sa.ForeignKeyConstraint(['round_id'], ['rounds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_variants_round', 'variants', ['round_id'], unique=False)
    op.create_index('idx_variants_hash', 'variants', ['content_hash'], unique=False)
    op.create_index('idx_variants_lineage', 'variants', ['parent_id', 'generation'], unique=False)

    # Create evaluations table
    op.create_table('evaluations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('evaluator_type', sa.String(), nullable=False),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('feedback', sa.Text(), nullable=True),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['variant_id'], ['variants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_evaluations_variant', 'evaluations', ['variant_id'], unique=False)

    # Create policies table
    op.create_table('policies',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('policy_type', sa.String(), nullable=False),
    sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_policies_type', 'policies', ['policy_type', 'is_active'], unique=False)

    # Create agent_decisions table
    op.create_table('agent_decisions',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('trace_id', sa.String(length=255), nullable=False),
    sa.Column('agent_type', sa.String(), nullable=False),
    sa.Column('decision_type', sa.String(), nullable=False),
    sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('reasoning', sa.Text(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agent_decisions_trace', 'agent_decisions', ['trace_id'], unique=False)

    # Create reports table
    op.create_table('reports',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('round_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('report_type', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('storage_path', sa.String(), nullable=True),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
    sa.ForeignKeyConstraint(['round_id'], ['rounds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reports_campaign', 'reports', ['campaign_id'], unique=False)

    # Create mcp_access_logs table
    op.create_table('mcp_access_logs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('trace_id', sa.String(length=255), nullable=False),
    sa.Column('server_name', sa.String(), nullable=False),
    sa.Column('tool_name', sa.String(), nullable=False),
    sa.Column('tool_version', sa.String(), nullable=False),
    sa.Column('arguments', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('meta_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mcp_logs_trace', 'mcp_access_logs', ['trace_id'], unique=False)
    op.create_index('idx_mcp_logs_tool', 'mcp_access_logs', ['server_name', 'tool_name'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_mcp_logs_tool', table_name='mcp_access_logs')
    op.drop_index('idx_mcp_logs_trace', table_name='mcp_access_logs')
    op.drop_table('mcp_access_logs')
    op.drop_index('idx_reports_campaign', table_name='reports')
    op.drop_table('reports')
    op.drop_index('idx_agent_decisions_trace', table_name='agent_decisions')
    op.drop_table('agent_decisions')
    op.drop_index('idx_policies_type', table_name='policies')
    op.drop_table('policies')
    op.drop_index('idx_evaluations_variant', table_name='evaluations')
    op.drop_table('evaluations')
    op.drop_index('idx_variants_lineage', table_name='variants')
    op.drop_index('idx_variants_hash', table_name='variants')
    op.drop_index('idx_variants_round', table_name='variants')
    op.drop_table('variants')
    op.drop_index('idx_rounds_campaign', table_name='rounds')
    op.drop_table('rounds')
    op.drop_index('idx_campaigns_status', table_name='campaigns')
    op.drop_index('idx_campaigns_name', table_name='campaigns')
    op.drop_table('campaigns')
