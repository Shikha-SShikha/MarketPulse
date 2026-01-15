"""add_evaluation_tables

Revision ID: a56385b6e2fb
Revises: 4400986d96ca
Create Date: 2025-12-25 20:45:47.051217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a56385b6e2fb'
down_revision: Union[str, None] = '4400986d96ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create evaluation_runs table
    op.create_table(
        'evaluation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hallucination_score', sa.Float(), nullable=False),
        sa.Column('grounding_score', sa.Float(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('actionability_score', sa.Float(), nullable=False),
        sa.Column('coherence_score', sa.Float(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False, server_default='9.5'),
        sa.Column('evaluator_model', sa.String(100), nullable=True),
        sa.Column('evaluation_method', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes for evaluation_runs
    op.create_index('ix_evaluations_content', 'evaluation_runs', ['content_type', 'content_id', 'created_at'])
    op.create_index('ix_evaluations_passed', 'evaluation_runs', ['passed', 'created_at'])
    op.create_index('ix_evaluations_score', 'evaluation_runs', ['overall_score', 'created_at'])
    op.create_index('ix_evaluation_runs_content_type', 'evaluation_runs', ['content_type'])
    op.create_index('ix_evaluation_runs_content_id', 'evaluation_runs', ['content_id'])
    op.create_index('ix_evaluation_runs_created_at', 'evaluation_runs', ['created_at'])

    # Create evaluation_issues table
    op.create_table(
        'evaluation_issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('evaluation_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issue_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('affected_signal_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('affected_entities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id'], ondelete='CASCADE'),
    )

    # Create indexes for evaluation_issues
    op.create_index('ix_evaluation_issues_type', 'evaluation_issues', ['issue_type', 'severity', 'created_at'])
    op.create_index('ix_evaluation_issues_evaluation_run_id', 'evaluation_issues', ['evaluation_run_id'])


def downgrade() -> None:
    # Drop evaluation_issues table and indexes
    op.drop_index('ix_evaluation_issues_evaluation_run_id', 'evaluation_issues')
    op.drop_index('ix_evaluation_issues_type', 'evaluation_issues')
    op.drop_table('evaluation_issues')

    # Drop evaluation_runs table and indexes
    op.drop_index('ix_evaluation_runs_created_at', 'evaluation_runs')
    op.drop_index('ix_evaluation_runs_content_id', 'evaluation_runs')
    op.drop_index('ix_evaluation_runs_content_type', 'evaluation_runs')
    op.drop_index('ix_evaluations_score', 'evaluation_runs')
    op.drop_index('ix_evaluations_passed', 'evaluation_runs')
    op.drop_index('ix_evaluations_content', 'evaluation_runs')
    op.drop_table('evaluation_runs')
