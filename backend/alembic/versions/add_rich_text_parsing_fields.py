"""add rich text parsing fields

Revision ID: add_rich_text_parsing_fields
Revises: remove_ai_model_max_tokens_field
Create Date: 2025-09-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_rich_text_parsing_fields'
down_revision = 'remove_ai_model_max_tokens_field'
branch_labels = None
depends_on = None


def upgrade():
    """添加富文本解析相关字段"""
    # 添加enable_rich_text_parsing字段
    op.add_column('analysis_tasks', sa.Column('enable_rich_text_parsing', sa.Boolean(), nullable=True, comment='是否启用富文本字段解析'))
    
    # 添加rich_text_config字段
    op.add_column('analysis_tasks', sa.Column('rich_text_config', sa.JSON(), nullable=True, comment='富文本解析配置'))
    
    # 设置默认值
    op.execute("UPDATE analysis_tasks SET enable_rich_text_parsing = FALSE WHERE enable_rich_text_parsing IS NULL")
    
    # 将字段设为NOT NULL
    op.alter_column('analysis_tasks', 'enable_rich_text_parsing', nullable=False)


def downgrade():
    """移除富文本解析相关字段"""
    op.drop_column('analysis_tasks', 'rich_text_config')
    op.drop_column('analysis_tasks', 'enable_rich_text_parsing')