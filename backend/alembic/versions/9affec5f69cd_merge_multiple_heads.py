"""merge_multiple_heads

Revision ID: 9affec5f69cd
Revises: add_proxy_config_to_ai_models, f1a2b3c4d5e6
Create Date: 2025-09-18 08:29:47.015210

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9affec5f69cd'
down_revision = ('add_proxy_config_to_ai_models', 'f1a2b3c4d5e6')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""
    pass


def downgrade() -> None:
    """降级数据库结构"""
    pass