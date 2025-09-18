"""add rich text parsing fields

Revision ID: d9e6f4c8a2b1
Revises: b7f8e2d5a1c3
Create Date: 2025-09-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd9e6f4c8a2b1'
down_revision = 'b7f8e2d5a1c3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add rich text parsing support to analysis_tasks table
    op.add_column('analysis_tasks', sa.Column('parse_rich_text', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('analysis_tasks', sa.Column('extract_images', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('analysis_tasks', sa.Column('parse_tables', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove rich text parsing fields
    op.drop_column('analysis_tasks', 'parse_tables')
    op.drop_column('analysis_tasks', 'extract_images')
    op.drop_column('analysis_tasks', 'parse_rich_text')