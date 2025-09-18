"""Remove encryption from AI model api_key field

Revision ID: 5b44b3614445
Revises: a38ce9f06d57
Create Date: 2025-09-09 17:42:56.591406

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b44b3614445'
down_revision = 'a38ce9f06d57'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""
    # 重命名字段：api_key_encrypted -> api_key
    op.alter_column('ai_models', 'api_key_encrypted', 
                   new_column_name='api_key')


def downgrade() -> None:
    """降级数据库结构"""
    # 还原字段名称：api_key -> api_key_encrypted
    op.alter_column('ai_models', 'api_key',
                   new_column_name='api_key_encrypted')