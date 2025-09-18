"""Add method column to webhooks table

Revision ID: f5058417ed01
Revises: 5ede1e810562
Create Date: 2025-09-08 11:54:02.699586

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5058417ed01'
down_revision = '5ede1e810562'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """添加method字段到webhooks表"""
    # 创建HTTP方法枚举类型
    request_method_enum = sa.Enum('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', name='request_method_enum')
    request_method_enum.create(op.get_bind())
    
    # 添加method字段到webhooks表
    op.add_column('webhooks', sa.Column('method', request_method_enum, nullable=False, server_default='POST', comment='HTTP请求方法'))


def downgrade() -> None:
    """移除method字段"""
    # 删除method字段
    op.drop_column('webhooks', 'method')
    
    # 删除枚举类型
    sa.Enum(name='request_method_enum').drop(op.get_bind())