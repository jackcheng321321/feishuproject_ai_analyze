"""Remove max_tokens field from ai_models table

Revision ID: b7f8e2d5a1c3
Revises: 5b44b3614445
Create Date: 2025-09-09 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7f8e2d5a1c3'
down_revision = '5b44b3614445'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove max_tokens field from ai_models table
    op.drop_column('ai_models', 'max_tokens')


def downgrade() -> None:
    # Add max_tokens field back to ai_models table
    op.add_column('ai_models', sa.Column('max_tokens', sa.Integer(), nullable=True))