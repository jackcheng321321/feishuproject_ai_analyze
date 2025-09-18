"""Add fields for feishu integration

Revision ID: 863b2f4592af
Revises: f5058417ed01
Create Date: 2025-09-09 11:29:02.103779

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '863b2f4592af'
down_revision = 'f5058417ed01'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""
    # 添加新字段到 analysis_tasks 表
    op.add_column('analysis_tasks', sa.Column('enable_storage_credential', sa.Boolean(), nullable=True, default=False, comment='是否启用存储凭证'))
    op.add_column('analysis_tasks', sa.Column('feishu_write_config', sa.JSON(), nullable=True, comment='飞书写入配置'))
    op.add_column('analysis_tasks', sa.Column('webhook_data_extract', sa.JSON(), nullable=True, comment='Webhook数据提取配置'))
    op.add_column('analysis_tasks', sa.Column('temperature', sa.Numeric(precision=3, scale=2), nullable=True, default=0.7, comment='AI模型温度参数'))
    op.add_column('analysis_tasks', sa.Column('max_tokens', sa.Integer(), nullable=True, default=1000, comment='AI模型最大token数'))
    
    # 设置默认值
    op.execute("UPDATE analysis_tasks SET enable_storage_credential = FALSE WHERE enable_storage_credential IS NULL")
    op.execute("UPDATE analysis_tasks SET temperature = 0.7 WHERE temperature IS NULL")  
    op.execute("UPDATE analysis_tasks SET max_tokens = 1000 WHERE max_tokens IS NULL")


def downgrade() -> None:
    """降级数据库结构"""
    # 删除添加的字段
    op.drop_column('analysis_tasks', 'max_tokens')
    op.drop_column('analysis_tasks', 'temperature')
    op.drop_column('analysis_tasks', 'webhook_data_extract')
    op.drop_column('analysis_tasks', 'feishu_write_config')
    op.drop_column('analysis_tasks', 'enable_storage_credential')