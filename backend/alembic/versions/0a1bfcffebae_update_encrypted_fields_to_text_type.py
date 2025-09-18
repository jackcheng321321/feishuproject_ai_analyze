"""Update encrypted fields to TEXT type

Revision ID: 0a1bfcffebae
Revises: 863b2f4592af
Create Date: 2025-09-09 11:55:17.204418

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a1bfcffebae'
down_revision = '863b2f4592af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 将加密字段改为TEXT类型"""
    # 修改username_encrypted字段类型
    op.alter_column('storage_credentials', 'username_encrypted',
                    existing_type=sa.VARCHAR(100),
                    type_=sa.Text(),
                    nullable=True)
    
    # 修改access_key_encrypted字段类型
    op.alter_column('storage_credentials', 'access_key_encrypted',
                    existing_type=sa.VARCHAR(500),
                    type_=sa.Text(),
                    nullable=True)
    
    # 修改secret_key_encrypted字段类型
    op.alter_column('storage_credentials', 'secret_key_encrypted',
                    existing_type=sa.VARCHAR(500),
                    type_=sa.Text(),
                    nullable=True)
    
    # 修改token_encrypted字段类型
    op.alter_column('storage_credentials', 'token_encrypted',
                    existing_type=sa.VARCHAR(500),
                    type_=sa.Text(),
                    nullable=True)


def downgrade() -> None:
    """降级数据库结构 - 恢复原有字段类型"""
    # 恢复username_encrypted字段类型
    op.alter_column('storage_credentials', 'username_encrypted',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(100),
                    nullable=False)
    
    # 恢复access_key_encrypted字段类型
    op.alter_column('storage_credentials', 'access_key_encrypted',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(500),
                    nullable=True)
    
    # 恢复secret_key_encrypted字段类型
    op.alter_column('storage_credentials', 'secret_key_encrypted',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(500),
                    nullable=True)
    
    # 恢复token_encrypted字段类型
    op.alter_column('storage_credentials', 'token_encrypted',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(500),
                    nullable=True)