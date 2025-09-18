"""merge multiple heads

Revision ID: f1a2b3c4d5e6
Revises: e3a7c9b5d4f2, a38ce9f06d57
Create Date: 2025-09-12 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = ('e3a7c9b5d4f2', 'a38ce9f06d57')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration - no changes needed
    pass


def downgrade() -> None:
    # This is a merge migration - no changes needed
    pass