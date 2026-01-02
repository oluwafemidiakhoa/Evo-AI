"""Fix schema mismatches across all tables

Revision ID: 002
Revises: 001
Create Date: 2026-01-02 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix rounds table
    op.add_column('rounds', sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.add_column('rounds', sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('rounds', sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.drop_index('idx_rounds_campaign', table_name='rounds')
    op.create_index('idx_rounds_campaign_status', 'rounds', ['campaign_id', 'status', 'deleted_at'], unique=False)
    op.create_index('idx_rounds_status', 'rounds', ['status'], unique=False)
    op.create_unique_constraint('uq_campaign_round_number', 'rounds', ['campaign_id', 'round_number'])

    # Fix variants table
    op.add_column('variants', sa.Column('mutation_type', sa.String(length=50), nullable=True))
    op.drop_index('idx_variants_round', table_name='variants')
    op.drop_index('idx_variants_hash', table_name='variants')
    op.drop_index('idx_variants_lineage', table_name='variants')
    op.create_index('idx_variants_round', 'variants', ['round_id', 'deleted_at'], unique=False)
    op.create_index('idx_variants_parent', 'variants', ['parent_id', 'deleted_at'], unique=False)
    op.create_index('idx_variants_lineage', 'variants', ['generation', 'is_selected'], unique=False)
    op.create_index('idx_variants_content_hash', 'variants', ['content_hash'], unique=False)
    op.create_index('idx_variants_selected', 'variants', ['round_id', 'is_selected'], unique=False)

    # Fix evaluations table - drop old columns and add new ones
    op.drop_column('evaluations', 'evaluator_type')
    op.drop_column('evaluations', 'feedback')
    op.add_column('evaluations', sa.Column('round_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.add_column('evaluations', sa.Column('evaluator_config', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.add_column('evaluations', sa.Column('execution_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'))
    op.create_foreign_key('fk_evaluations_round_id', 'evaluations', 'rounds', ['round_id'], ['id'])
    op.drop_column('evaluations', 'deleted_at')
    op.drop_column('evaluations', 'updated_at')
    op.create_index('idx_evaluations_round', 'evaluations', ['round_id'], unique=False)
    op.create_index('idx_evaluations_score', 'evaluations', ['round_id', 'score'], unique=False)

    # Fix policies table
    op.add_column('policies', sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.create_foreign_key('fk_policies_campaign_id', 'policies', 'campaigns', ['campaign_id'], ['id'])
    op.drop_index('idx_policies_type', table_name='policies')
    op.create_index('idx_policies_campaign_active', 'policies', ['campaign_id', 'is_active', 'deleted_at'], unique=False)
    op.create_index('idx_policies_type', 'policies', ['policy_type'], unique=False)
    op.create_unique_constraint('uq_campaign_policy_type_version', 'policies', ['campaign_id', 'policy_type', 'version'])

    # Fix agent_decisions table - complete rebuild
    op.drop_index('idx_agent_decisions_trace', table_name='agent_decisions')
    op.drop_table('agent_decisions')
    op.create_table('agent_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('span_id', sa.String(length=16), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('round_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('variant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('decision', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('input_context', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('llm_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('token_usage', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id']),
        sa.ForeignKeyConstraint(['round_id'], ['rounds.id']),
        sa.ForeignKeyConstraint(['variant_id'], ['variants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agent_decisions_trace', 'agent_decisions', ['trace_id'], unique=False)
    op.create_index('idx_agent_decisions_agent', 'agent_decisions', ['agent_type', 'created_at'], unique=False)
    op.create_index('idx_agent_decisions_round', 'agent_decisions', ['round_id', 'agent_type'], unique=False)
    op.create_index('idx_agent_decisions_campaign', 'agent_decisions', ['campaign_id', 'created_at'], unique=False)

    # Fix mcp_access_logs table - complete rebuild
    op.drop_index('idx_mcp_logs_tool', table_name='mcp_access_logs')
    op.drop_index('idx_mcp_logs_trace', table_name='mcp_access_logs')
    op.drop_table('mcp_access_logs')
    op.create_table('mcp_access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mcp_server_name', sa.String(length=100), nullable=False),
        sa.Column('mcp_server_version', sa.String(length=20), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('input_params', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_mcp_logs_trace', 'mcp_access_logs', ['trace_id'], unique=False)
    op.create_index('idx_mcp_logs_server', 'mcp_access_logs', ['mcp_server_name', 'created_at'], unique=False)
    op.create_index('idx_mcp_logs_status', 'mcp_access_logs', ['status', 'created_at'], unique=False)

    # Fix reports table
    op.add_column('reports', sa.Column('format', sa.String(length=20), nullable=False, server_default='markdown'))
    op.drop_constraint('reports_campaign_id_fkey', 'reports', type_='foreignkey')
    op.drop_column('reports', 'campaign_id')
    op.drop_column('reports', 'deleted_at')
    op.alter_column('reports', 'content', nullable=True)
    op.alter_column('reports', 'round_id', nullable=False)
    op.drop_index('idx_reports_campaign', table_name='reports')
    op.create_index('idx_reports_round', 'reports', ['round_id', 'report_type'], unique=False)
    op.create_index('idx_reports_created', 'reports', ['created_at'], unique=False)


def downgrade() -> None:
    # Reverse reports fixes
    op.drop_index('idx_reports_created', table_name='reports')
    op.drop_index('idx_reports_round', table_name='reports')
    op.create_index('idx_reports_campaign', 'reports', ['campaign_id'], unique=False)
    op.alter_column('reports', 'round_id', nullable=True)
    op.alter_column('reports', 'content', nullable=False)
    op.add_column('reports', sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('reports', sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.create_foreign_key('reports_campaign_id_fkey', 'reports', 'campaigns', ['campaign_id'], ['id'])
    op.drop_column('reports', 'format')

    # Reverse mcp_access_logs fixes
    op.drop_index('idx_mcp_logs_status', table_name='mcp_access_logs')
    op.drop_index('idx_mcp_logs_server', table_name='mcp_access_logs')
    op.drop_index('idx_mcp_logs_trace', table_name='mcp_access_logs')
    op.drop_table('mcp_access_logs')
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

    # Reverse agent_decisions fixes
    op.drop_index('idx_agent_decisions_campaign', table_name='agent_decisions')
    op.drop_index('idx_agent_decisions_round', table_name='agent_decisions')
    op.drop_index('idx_agent_decisions_agent', table_name='agent_decisions')
    op.drop_index('idx_agent_decisions_trace', table_name='agent_decisions')
    op.drop_table('agent_decisions')
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

    # Reverse policies fixes
    op.drop_constraint('uq_campaign_policy_type_version', 'policies', type_='unique')
    op.drop_index('idx_policies_type', table_name='policies')
    op.create_index('idx_policies_type', 'policies', ['policy_type', 'is_active'], unique=False)
    op.drop_index('idx_policies_campaign_active', table_name='policies')
    op.drop_constraint('fk_policies_campaign_id', 'policies', type_='foreignkey')
    op.drop_column('policies', 'campaign_id')

    # Reverse evaluations fixes
    op.drop_index('idx_evaluations_score', table_name='evaluations')
    op.drop_index('idx_evaluations_round', table_name='evaluations')
    op.add_column('evaluations', sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False))
    op.add_column('evaluations', sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.drop_constraint('fk_evaluations_round_id', 'evaluations', type_='foreignkey')
    op.drop_column('evaluations', 'execution_metadata')
    op.drop_column('evaluations', 'evaluator_config')
    op.drop_column('evaluations', 'round_id')
    op.add_column('evaluations', sa.Column('feedback', sa.Text(), nullable=True))
    op.add_column('evaluations', sa.Column('evaluator_type', sa.String(), nullable=False))

    # Reverse variants fixes
    op.drop_index('idx_variants_selected', table_name='variants')
    op.drop_index('idx_variants_content_hash', table_name='variants')
    op.drop_index('idx_variants_lineage', table_name='variants')
    op.drop_index('idx_variants_parent', table_name='variants')
    op.drop_index('idx_variants_round', table_name='variants')
    op.create_index('idx_variants_lineage', 'variants', ['parent_id', 'generation'], unique=False)
    op.create_index('idx_variants_hash', 'variants', ['content_hash'], unique=False)
    op.create_index('idx_variants_round', 'variants', ['round_id'], unique=False)
    op.drop_column('variants', 'mutation_type')

    # Reverse rounds fixes
    op.drop_constraint('uq_campaign_round_number', 'rounds', type_='unique')
    op.drop_index('idx_rounds_status', table_name='rounds')
    op.drop_index('idx_rounds_campaign_status', table_name='rounds')
    op.create_index('idx_rounds_campaign', 'rounds', ['campaign_id', 'round_number'], unique=False)
    op.drop_column('rounds', 'completed_at')
    op.drop_column('rounds', 'started_at')
    op.drop_column('rounds', 'metrics')
