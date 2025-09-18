"""SQLAlchemy基础模型

定义所有数据库模型的基类和通用字段。
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, Integer, DateTime, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

# 创建基础模型类
Base = declarative_base()


class TimestampMixin:
    """时间戳混入类
    
    为模型添加创建时间和更新时间字段。
    """
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间"
    )


class UUIDMixin:
    """UUID混入类
    
    为模型添加UUID主键。
    """
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="主键ID"
    )


class SoftDeleteMixin:
    """软删除混入类
    
    为模型添加软删除功能。
    """
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除"
    )
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="删除时间"
    )


class UserTrackingMixin:
    """用户跟踪混入类
    
    为模型添加创建者和更新者字段。
    """
    
    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="创建者ID"
    )
    
    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="更新者ID"
    )


class MetadataMixin:
    """元数据混入类
    
    为模型添加元数据字段。
    """
    
    metadata_json = Column(
        JSONB,
        nullable=True,
        comment="元数据JSON"
    )
    
    tags = Column(
        JSONB,
        nullable=True,
        comment="标签列表"
    )
    
    version = Column(
        Integer,
        default=1,
        nullable=False,
        comment="版本号"
    )


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, UserTrackingMixin):
    """基础模型类
    
    包含所有通用字段的基础模型。
    """
    
    __abstract__ = True
    
    @declared_attr
    def __tablename__(cls) -> str:
        """自动生成表名"""
        return cls.__name__.lower()
    
    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """转换为字典
        
        Args:
            exclude: 要排除的字段列表
            
        Returns:
            模型的字典表示
        """
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    result[column.name] = value.isoformat()
                elif isinstance(value, uuid.UUID):
                    result[column.name] = str(value)
                else:
                    result[column.name] = value
                    
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[list] = None) -> None:
        """从字典更新模型
        
        Args:
            data: 要更新的数据字典
            exclude: 要排除的字段列表
        """
        exclude = exclude or ['id', 'created_at', 'created_by']
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    def soft_delete(self, deleted_by: Optional[uuid.UUID] = None) -> None:
        """软删除
        
        Args:
            deleted_by: 删除者ID
        """
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if deleted_by:
            self.updated_by = deleted_by
    
    def restore(self, restored_by: Optional[uuid.UUID] = None) -> None:
        """恢复删除
        
        Args:
            restored_by: 恢复者ID
        """
        self.is_deleted = False
        self.deleted_at = None
        if restored_by:
            self.updated_by = restored_by
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"


class AuditLogMixin:
    """审计日志混入类
    
    为模型添加审计日志字段。
    """
    
    operation_type = Column(
        String(50),
        nullable=True,
        comment="操作类型"
    )
    
    operation_details = Column(
        JSONB,
        nullable=True,
        comment="操作详情"
    )
    
    ip_address = Column(
        String(45),
        nullable=True,
        comment="IP地址"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="用户代理"
    )


class StatusMixin:
    """状态混入类
    
    为模型添加状态字段。
    """
    
    status = Column(
        String(50),
        nullable=False,
        default="active",
        comment="状态"
    )
    
    status_reason = Column(
        Text,
        nullable=True,
        comment="状态原因"
    )
    
    status_changed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="状态变更时间"
    )
    
    status_changed_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="状态变更者ID"
    )


class ConfigMixin:
    """配置混入类
    
    为模型添加配置字段。
    """
    
    config = Column(
        JSONB,
        nullable=True,
        comment="配置JSON"
    )
    
    config_schema = Column(
        JSONB,
        nullable=True,
        comment="配置模式JSON"
    )
    
    config_version = Column(
        String(20),
        nullable=True,
        comment="配置版本"
    )