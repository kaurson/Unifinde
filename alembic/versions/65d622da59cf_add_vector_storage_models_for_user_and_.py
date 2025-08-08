"""Add vector storage models for user and university embeddings

Revision ID: 65d622da59cf
Revises: 88418add5469
Create Date: 2025-08-07 16:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65d622da59cf'
down_revision: Union[str, None] = '88418add5469'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_vectors table
    op.create_table('user_vectors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('embedding', sa.LargeBinary(), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # Create university_vectors table
    op.create_table('university_vectors',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('university_id', sa.String(length=36), nullable=False),
        sa.Column('embedding', sa.LargeBinary(), nullable=False),
        sa.Column('embedding_dimension', sa.Integer(), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['university_id'], ['universities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('university_id')
    )

    # Create vector_search_cache table
    op.create_table('vector_search_cache',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('search_type', sa.String(length=50), nullable=False),
        sa.Column('embedding_model', sa.String(length=100), nullable=False),
        sa.Column('results', sa.JSON(), nullable=False),
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cache_key')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('vector_search_cache')
    op.drop_table('university_vectors')
    op.drop_table('user_vectors')
