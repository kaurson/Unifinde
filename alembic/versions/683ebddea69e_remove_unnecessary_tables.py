"""remove_unnecessary_tables

Revision ID: 683ebddea69e
Revises: fd1877ccfd89
Create Date: 2025-08-07 01:15:30.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '683ebddea69e'
down_revision: Union[str, None] = 'fd1877ccfd89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unnecessary tables
    op.drop_table('llm_analysis_results')
    op.drop_table('university_search_tasks')
    op.drop_table('university_data_collections')
    op.drop_table('university_matches')
    op.drop_table('user_matches')
    op.drop_table('facilities')
    op.drop_table('programs')
    op.drop_table('universities')
    op.drop_table('schools')


def downgrade() -> None:
    # Recreate the dropped tables (simplified versions)
    
    # Create schools table
    op.create_table('schools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('student_population', sa.Integer(), nullable=True),
        sa.Column('teacher_count', sa.Integer(), nullable=True),
        sa.Column('graduation_rate', sa.Float(), nullable=True),
        sa.Column('college_acceptance_rate', sa.Float(), nullable=True),
        sa.Column('average_sat_score', sa.Integer(), nullable=True),
        sa.Column('average_act_score', sa.Integer(), nullable=True),
        sa.Column('ap_courses_offered', sa.Integer(), nullable=True),
        sa.Column('test_scores', sa.JSON(), nullable=True),
        sa.Column('rankings', sa.JSON(), nullable=True),
        sa.Column('awards', sa.JSON(), nullable=True),
        sa.Column('programs_offered', sa.JSON(), nullable=True),
        sa.Column('extracurricular_activities', sa.JSON(), nullable=True),
        sa.Column('sports_teams', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mission_statement', sa.Text(), nullable=True),
        sa.Column('facilities', sa.JSON(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schools_name'), 'schools', ['name'], unique=False)
    
    # Create universities table
    op.create_table('universities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=20), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=100), nullable=True),
        sa.Column('accreditation', sa.Text(), nullable=True),
        sa.Column('student_population', sa.Integer(), nullable=True),
        sa.Column('faculty_count', sa.Integer(), nullable=True),
        sa.Column('acceptance_rate', sa.Float(), nullable=True),
        sa.Column('tuition_domestic', sa.Float(), nullable=True),
        sa.Column('tuition_international', sa.Float(), nullable=True),
        sa.Column('world_ranking', sa.Integer(), nullable=True),
        sa.Column('national_ranking', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mission_statement', sa.Text(), nullable=True),
        sa.Column('vision_statement', sa.Text(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_universities_name'), 'universities', ['name'], unique=False)
    
    # Create programs table
    op.create_table('programs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('university_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('level', sa.String(length=50), nullable=True),
        sa.Column('field', sa.String(length=100), nullable=True),
        sa.Column('duration', sa.String(length=50), nullable=True),
        sa.Column('tuition', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create facilities table
    op.create_table('facilities',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('university_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_matches table
    op.create_table('user_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('university_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('academic_fit_score', sa.Float(), nullable=True),
        sa.Column('financial_fit_score', sa.Float(), nullable=True),
        sa.Column('location_fit_score', sa.Float(), nullable=True),
        sa.Column('personality_fit_score', sa.Float(), nullable=True),
        sa.Column('user_preferences', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('is_favorite', sa.Boolean(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id'], ),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create university_matches table
    op.create_table('university_matches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('university_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('academic_potential_score', sa.Float(), nullable=True),
        sa.Column('financial_stability_score', sa.Float(), nullable=True),
        sa.Column('cultural_fit_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create university_data_collections table
    op.create_table('university_data_collections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('university_name', sa.String(length=200), nullable=False),
        sa.Column('search_query', sa.String(length=500), nullable=True),
        sa.Column('target_urls', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('llm_analysis', sa.JSON(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('browser_session_id', sa.String(length=100), nullable=True),
        sa.Column('scraped_content', sa.JSON(), nullable=True),
        sa.Column('search_results', sa.JSON(), nullable=True),
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
        sa.Column('search_queries', sa.JSON(), nullable=True),
        sa.Column('max_results', sa.Integer(), nullable=True),
        sa.Column('search_engines', sa.JSON(), nullable=True),
        sa.Column('include_news', sa.Boolean(), nullable=True),
        sa.Column('include_social_media', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('search_results', sa.JSON(), nullable=True),
        sa.Column('processed_results', sa.JSON(), nullable=True),
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
        sa.Column('structured_data', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('data_completeness', sa.Float(), nullable=True),
        sa.Column('data_accuracy', sa.Float(), nullable=True),
        sa.Column('source_citations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['data_collection_id'], ['university_data_collections.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
