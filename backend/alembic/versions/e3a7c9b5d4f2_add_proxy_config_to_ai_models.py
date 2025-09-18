"""Add proxy configuration to AI models

Revision ID: e3a7c9b5d4f2
Revises: d9e6f4c8a2b1
Create Date: 2025-09-12 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3a7c9b5d4f2'
down_revision = 'd9e6f4c8a2b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add proxy configuration fields to ai_models table
    op.add_column('ai_models', sa.Column('use_proxy', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('ai_models', sa.Column('proxy_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Remove proxy configuration fields
    op.drop_column('ai_models', 'proxy_url')
    op.drop_column('ai_models', 'use_proxy')