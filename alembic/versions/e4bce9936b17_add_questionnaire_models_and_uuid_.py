"""add_questionnaire_models_and_uuid_support

Revision ID: e4bce9936b17
Revises: 683ebddea69e
Create Date: 2025-08-07 11:49:27.502357

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4bce9936b17'
down_revision: Union[str, None] = '683ebddea69e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create questions table
    op.create_table('questions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_question_text'), 'questions', ['question_text'], unique=True)
    
    # Create user_answers table
    op.create_table('user_answers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('question_id', sa.String(length=36), nullable=False),
        sa.Column('answer_text', sa.Text(), nullable=False),
        sa.Column('answer_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create universities table (if it doesn't exist)
    op.create_table('universities',
        sa.Column('id', sa.String(length=36), nullable=False),
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
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('university_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('level', sa.String(length=50), nullable=True),
        sa.Column('field', sa.String(length=100), nullable=True),
        sa.Column('duration', sa.String(length=50), nullable=True),
        sa.Column('tuition', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create facilities table
    op.create_table('facilities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('university_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('facilities')
    op.drop_table('programs')
    op.drop_index(op.f('ix_universities_name'), table_name='universities')
    op.drop_table('universities')
    op.drop_table('user_answers')
    op.drop_index(op.f('ix_questions_question_text'), table_name='questions')
    op.drop_table('questions')
