"""Add university data collection models

Revision ID: 003
Revises: 002
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create university_data_collections table
    op.create_table('university_data_collections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('university_name', sa.String(length=200), nullable=False),
        sa.Column('search_query', sa.String(length=500), nullable=True),
        sa.Column('target_urls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('llm_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('extracted_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('browser_session_id', sa.String(length=100), nullable=True),
        sa.Column('scraped_content', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('search_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('university_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_university_data_collections_university_name'), 'university_data_collections', ['university_name'], unique=False)

    # Create university_search_tasks table
    op.create_table('university_search_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('university_name', sa.String(length=200), nullable=False),
        sa.Column('search_queries', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('max_results', sa.Integer(), nullable=True),
        sa.Column('search_engines', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('include_news', sa.Boolean(), nullable=True),
        sa.Column('include_social_media', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('search_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('processed_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('data_collection_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['data_collection_id'], ['university_data_collections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_university_search_tasks_university_name'), 'university_search_tasks', ['university_name'], unique=False)

    # Create llm_analysis_results table
    op.create_table('llm_analysis_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data_collection_id', sa.Integer(), nullable=False),
        sa.Column('analysis_type', sa.String(length=100), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('prompt_used', sa.Text(), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('structured_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('data_completeness', sa.Float(), nullable=True),
        sa.Column('data_accuracy', sa.Float(), nullable=True),
        sa.Column('source_citations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['data_collection_id'], ['university_data_collections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('llm_analysis_results')
    op.drop_index(op.f('ix_university_search_tasks_university_name'), table_name='university_search_tasks')
    op.drop_table('university_search_tasks')
    op.drop_index(op.f('ix_university_data_collections_university_name'), table_name='university_data_collections')
    op.drop_table('university_data_collections') 