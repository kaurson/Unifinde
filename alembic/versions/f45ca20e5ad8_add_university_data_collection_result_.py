"""add_university_data_collection_result_model

Revision ID: f45ca20e5ad8
Revises: 003
Create Date: 2025-08-07 00:55:17.476645

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f45ca20e5ad8'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create university_data_collection_results table
    op.create_table('university_data_collection_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('total_universities', sa.Integer(), nullable=True),
        sa.Column('successful_collections', sa.Integer(), nullable=True),
        sa.Column('failed_collections', sa.Integer(), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('script_version', sa.String(length=50), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('data_collection_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('founded_year', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=100), nullable=True),
        sa.Column('student_population', sa.Integer(), nullable=True),
        sa.Column('undergraduate_population', sa.Integer(), nullable=True),
        sa.Column('graduate_population', sa.Integer(), nullable=True),
        sa.Column('international_students_percentage', sa.Float(), nullable=True),
        sa.Column('faculty_count', sa.Integer(), nullable=True),
        sa.Column('student_faculty_ratio', sa.Float(), nullable=True),
        sa.Column('acceptance_rate', sa.Float(), nullable=True),
        sa.Column('tuition_domestic', sa.Float(), nullable=True),
        sa.Column('tuition_international', sa.Float(), nullable=True),
        sa.Column('room_and_board', sa.Float(), nullable=True),
        sa.Column('total_cost_of_attendance', sa.Float(), nullable=True),
        sa.Column('financial_aid_available', sa.Boolean(), nullable=True),
        sa.Column('average_financial_aid_package', sa.Float(), nullable=True),
        sa.Column('scholarships_available', sa.Boolean(), nullable=True),
        sa.Column('world_ranking', sa.Integer(), nullable=True),
        sa.Column('national_ranking', sa.Integer(), nullable=True),
        sa.Column('regional_ranking', sa.Integer(), nullable=True),
        sa.Column('subject_rankings', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mission_statement', sa.Text(), nullable=True),
        sa.Column('vision_statement', sa.Text(), nullable=True),
        sa.Column('campus_size', sa.String(length=100), nullable=True),
        sa.Column('campus_type', sa.String(length=100), nullable=True),
        sa.Column('climate', sa.String(length=100), nullable=True),
        sa.Column('timezone', sa.String(length=100), nullable=True),
        sa.Column('programs', sa.JSON(), nullable=True),
        sa.Column('student_life', sa.JSON(), nullable=True),
        sa.Column('financial_aid', sa.JSON(), nullable=True),
        sa.Column('international_students', sa.JSON(), nullable=True),
        sa.Column('alumni', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('source_urls', sa.JSON(), nullable=True),
        sa.Column('last_updated', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop university_data_collection_results table
    op.drop_table('university_data_collection_results')
