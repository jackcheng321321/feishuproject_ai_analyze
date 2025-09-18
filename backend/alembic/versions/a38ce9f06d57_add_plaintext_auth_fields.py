"""Add plaintext auth fields to storage credentials

Revision ID: a38ce9f06d57
Revises: 0a1bfcffebae
Create Date: 2025-09-09 16:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a38ce9f06d57'
down_revision = '0a1bfcffebae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 添加明文认证字段"""
    # 添加明文字段到存储凭证表
    op.add_column('storage_credentials', sa.Column('username', sa.String(length=255), nullable=True, comment='用户名'))
    op.add_column('storage_credentials', sa.Column('password', sa.String(length=255), nullable=True, comment='密码'))
    op.add_column('storage_credentials', sa.Column('access_key', sa.String(length=500), nullable=True, comment='访问密钥'))
    op.add_column('storage_credentials', sa.Column('secret_key', sa.String(length=500), nullable=True, comment='密钥'))
    op.add_column('storage_credentials', sa.Column('token', sa.Text(), nullable=True, comment='令牌'))


def downgrade() -> None:
    """降级数据库结构 - 移除明文认证字段"""
    op.drop_column('storage_credentials', 'token')
    op.drop_column('storage_credentials', 'secret_key')
    op.drop_column('storage_credentials', 'access_key')
    op.drop_column('storage_credentials', 'password')
    op.drop_column('storage_credentials', 'username')