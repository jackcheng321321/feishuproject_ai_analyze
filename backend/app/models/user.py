from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(100), comment="全名")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级用户")
    is_verified = Column(Boolean, default=False, comment="是否已验证邮箱")
    
    # 权限字段
    can_manage_config = Column(Boolean, default=False, comment="是否可以管理配置")
    can_manage_webhooks = Column(Boolean, default=False, comment="是否可以管理Webhook")
    can_manage_tasks = Column(Boolean, default=True, comment="是否可以管理任务")
    can_view_logs = Column(Boolean, default=True, comment="是否可以查看日志")
    
    # 个人设置
    avatar_url = Column(String(500), comment="头像URL")
    timezone = Column(String(50), default="Asia/Shanghai", comment="时区")
    language = Column(String(10), default="zh-CN", comment="语言")
    theme = Column(String(20), default="light", comment="主题")
    
    # 安全字段
    last_login_at = Column(DateTime(timezone=True), comment="最后登录时间")
    last_login_ip = Column(String(45), comment="最后登录IP")
    failed_login_attempts = Column(Integer, default=0, comment="失败登录次数")
    locked_until = Column(DateTime(timezone=True), comment="锁定到期时间")
    
    # 通知设置
    email_notifications = Column(Boolean, default=True, comment="是否接收邮件通知")
    task_notifications = Column(Boolean, default=True, comment="是否接收任务通知")
    error_notifications = Column(Boolean, default=True, comment="是否接收错误通知")
    
    # 备注信息
    notes = Column(Text, comment="备注")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        comment="更新时间"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "is_verified": self.is_verified,
            "can_manage_config": self.can_manage_config,
            "can_manage_webhooks": self.can_manage_webhooks,
            "can_manage_tasks": self.can_manage_tasks,
            "can_view_logs": self.can_view_logs,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "language": self.language,
            "theme": self.theme,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "email_notifications": self.email_notifications,
            "task_notifications": self.task_notifications,
            "error_notifications": self.error_notifications,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def has_permission(self, permission: str) -> bool:
        """检查用户是否有指定权限"""
        if self.is_superuser:
            return True
        
        permission_map = {
            "manage_config": self.can_manage_config,
            "manage_webhooks": self.can_manage_webhooks,
            "manage_tasks": self.can_manage_tasks,
            "view_logs": self.can_view_logs,
        }
        
        return permission_map.get(permission, False)
    
    def is_locked(self) -> bool:
        """检查用户是否被锁定"""
        if not self.locked_until:
            return False
        
        from datetime import datetime
        return datetime.utcnow() < self.locked_until
    
    def can_login(self) -> bool:
        """检查用户是否可以登录"""
        return self.is_active and not self.is_locked()