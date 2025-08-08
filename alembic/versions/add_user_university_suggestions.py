"""Add UserUniversitySuggestion table

Revision ID: add_user_suggestions
Revises: 65d622da59cf
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_user_suggestions'
down_revision = '65d622da59cf'
branch_labels = None
depends_on = None


def upgrade():
    # Create user_university_suggestions table
    op.create_table('user_university_suggestions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('university_id', sa.String(36), nullable=False),
        sa.Column('university_name', sa.String(200), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('matching_method', sa.String(50), nullable=False),
        sa.Column('confidence', sa.String(20), nullable=True),
        sa.Column('match_reasons', sa.JSON(), nullable=True),
        sa.Column('user_preferences', sa.JSON(), nullable=True),
        sa.Column('university_data', sa.JSON(), nullable=True),
        sa.Column('program_id', sa.String(36), nullable=True),
        sa.Column('program_name', sa.String(200), nullable=True),
        sa.Column('program_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on user_id for better performance
    op.create_index(op.f('ix_user_university_suggestions_user_id'), 'user_university_suggestions', ['user_id'], unique=False)


def downgrade():
    # Drop index
    op.drop_index(op.f('ix_user_university_suggestions_user_id'), table_name='user_university_suggestions')
    
    # Drop table
    op.drop_table('user_university_suggestions') 