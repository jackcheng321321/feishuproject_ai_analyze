"""add_multi_field_analysis_support

Revision ID: 023bb44c7005
Revises: 9affec5f69cd
Create Date: 2025-09-18 08:30:33.324514

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '023bb44c7005'
down_revision = '9affec5f69cd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 添加多字段分析支持"""
    # 添加多字段分析字段到 analysis_tasks 表
    op.add_column('analysis_tasks', sa.Column('enable_multi_field_analysis', sa.Boolean(), default=False, nullable=False, comment='是否启用多字段综合分析'))
    op.add_column('analysis_tasks', sa.Column('multi_field_config', sa.JSON(), nullable=True, comment='多字段分析配置'))


def downgrade() -> None:
    """降级数据库结构 - 移除多字段分析支持"""
    # 移除多字段分析字段
    op.drop_column('analysis_tasks', 'multi_field_config')
    op.drop_column('analysis_tasks', 'enable_multi_field_analysis')