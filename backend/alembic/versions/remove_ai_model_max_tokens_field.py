"""Remove max_tokens field from ai_models table

Revision ID: remove_ai_model_max_tokens_field
Revises: 5b44b3614445
Create Date: 2025-09-09 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_ai_model_max_tokens_field'
down_revision = '5b44b3614445'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 移除AI模型表的max_tokens字段"""
    # 检查max_tokens字段是否存在，如果存在则删除
    op.drop_column('ai_models', 'max_tokens')


def downgrade() -> None:
    """降级数据库结构 - 恢复AI模型表的max_tokens字段"""
    # 恢复max_tokens字段
    op.add_column('ai_models', 
                  sa.Column('max_tokens', sa.INTEGER(), 
                           server_default=sa.text('4000'), 
                           nullable=True, 
                           comment='最大token数'))