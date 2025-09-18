from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class RequestMethod(str, enum.Enum):
    """HTTP请求方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class Webhook(Base):
    """Webhook模型"""
    
    __tablename__ = "webhooks"
    
    id = Column(Integer, primary_key=True, index=True, comment="Webhook ID")
    name = Column(String(100), nullable=False, comment="Webhook名称")
    description = Column(Text, comment="描述")
    
    # Webhook配置
    webhook_id = Column(String(50), unique=True, nullable=False, index=True, comment="Webhook唯一标识")
    webhook_url = Column(String(500), nullable=False, comment="Webhook URL")
    method = Column(
        SQLEnum(RequestMethod), 
        default=RequestMethod.POST, 
        nullable=False,
        comment="HTTP请求方法"
    )
    secret_key = Column(String(100), nullable=False, comment="密钥")
    
    # 安全配置
    verify_signature = Column(Boolean, default=True, comment="是否验证签名")
    allowed_ips = Column(JSON, comment="允许的IP地址列表")
    rate_limit_per_minute = Column(Integer, default=60, comment="每分钟请求限制")
    
    # 请求配置
    timeout_seconds = Column(Integer, default=30, comment="超时时间（秒）")
    max_payload_size = Column(Integer, default=1048576, comment="最大载荷大小（字节）")
    
    # 重试配置
    enable_retry = Column(Boolean, default=True, comment="是否启用重试")
    max_retry_attempts = Column(Integer, default=3, comment="最大重试次数")
    retry_delay_seconds = Column(Integer, default=60, comment="重试延迟（秒）")
    
    # 过滤配置
    event_filters = Column(JSON, comment="事件过滤器")
    content_type_filters = Column(JSON, comment="内容类型过滤器")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_public = Column(Boolean, default=False, comment="是否公开")
    
    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建者ID")
    
    # 统计信息
    total_requests = Column(Integer, default=0, comment="总请求次数")
    successful_requests = Column(Integer, default=0, comment="成功请求次数")
    failed_requests = Column(Integer, default=0, comment="失败请求次数")
    last_request_at = Column(DateTime(timezone=True), comment="最后请求时间")
    last_success_at = Column(DateTime(timezone=True), comment="最后成功时间")
    last_failure_at = Column(DateTime(timezone=True), comment="最后失败时间")
    
    # 性能统计
    avg_response_time = Column(String(20), default="0.0", comment="平均响应时间（秒）")
    min_response_time = Column(String(20), default="0.0", comment="最小响应时间（秒）")
    max_response_time = Column(String(20), default="0.0", comment="最大响应时间（秒）")
    
    # 健康检查
    health_check_enabled = Column(Boolean, default=True, comment="是否启用健康检查")
    health_check_interval = Column(Integer, default=300, comment="健康检查间隔（秒）")
    last_health_check = Column(DateTime(timezone=True), comment="最后健康检查时间")
    health_status = Column(String(20), default="unknown", comment="健康状态")
    health_message = Column(Text, comment="健康检查消息")
    
    # 通知配置
    notification_enabled = Column(Boolean, default=True, comment="是否启用通知")
    notification_on_failure = Column(Boolean, default=True, comment="失败时通知")
    notification_on_success = Column(Boolean, default=False, comment="成功时通知")
    notification_emails = Column(JSON, comment="通知邮箱列表")
    
    # 日志配置
    log_requests = Column(Boolean, default=True, comment="是否记录请求日志")
    log_responses = Column(Boolean, default=False, comment="是否记录响应日志")
    log_retention_days = Column(Integer, default=30, comment="日志保留天数")
    
    # 标签和分类
    tags = Column(JSON, comment="标签")
    category = Column(String(50), comment="分类")
    
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
    
    # 关系
    creator = relationship("User", back_populates=None)
    webhook_logs = relationship("WebhookLog", back_populates="webhook", cascade="all, delete-orphan")
    analysis_tasks = relationship("AnalysisTask", back_populates="webhook")
    
    def __repr__(self):
        return f"<Webhook(id={self.id}, name='{self.name}', webhook_id='{self.webhook_id}')>"
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "webhook_id": self.webhook_id,
            "webhook_url": self.webhook_url,
            "method": self.method.value if self.method else "POST",
            "verify_signature": self.verify_signature,
            "allowed_ips": self.allowed_ips,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "timeout_seconds": self.timeout_seconds,
            "max_payload_size": self.max_payload_size,
            "enable_retry": self.enable_retry,
            "max_retry_attempts": self.max_retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "event_filters": self.event_filters,
            "content_type_filters": self.content_type_filters,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "created_by": self.created_by,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "last_request_at": self.last_request_at.isoformat() if self.last_request_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "avg_response_time": self.avg_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "health_check_enabled": self.health_check_enabled,
            "health_check_interval": self.health_check_interval,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_status": self.health_status,
            "health_message": self.health_message,
            "notification_enabled": self.notification_enabled,
            "notification_on_failure": self.notification_on_failure,
            "notification_on_success": self.notification_on_success,
            "notification_emails": self.notification_emails,
            "log_requests": self.log_requests,
            "log_responses": self.log_responses,
            "log_retention_days": self.log_retention_days,
            "tags": self.tags,
            "category": self.category,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 敏感信息只在需要时包含
        if include_sensitive:
            data["secret_key"] = self.secret_key
        else:
            data["has_secret_key"] = bool(self.secret_key)
        
        return data
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_failure_rate(self) -> float:
        """获取失败率"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100
    
    def update_request_stats(self, success: bool, response_time: float = 0.0):
        """更新请求统计"""
        from datetime import datetime
        
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
            self.last_success_at = datetime.utcnow()
        else:
            self.failed_requests += 1
            self.last_failure_at = datetime.utcnow()
        
        self.last_request_at = datetime.utcnow()
        
        # 更新响应时间统计
        if response_time > 0:
            try:
                current_avg = float(self.avg_response_time) if self.avg_response_time else 0.0
                current_min = float(self.min_response_time) if self.min_response_time else float('inf')
                current_max = float(self.max_response_time) if self.max_response_time else 0.0
                
                # 计算新的平均值
                new_avg = ((current_avg * (self.total_requests - 1)) + response_time) / self.total_requests
                self.avg_response_time = f"{new_avg:.3f}"
                
                # 更新最小值和最大值
                self.min_response_time = f"{min(current_min, response_time):.3f}"
                self.max_response_time = f"{max(current_max, response_time):.3f}"
                
            except (ValueError, TypeError):
                self.avg_response_time = f"{response_time:.3f}"
                self.min_response_time = f"{response_time:.3f}"
                self.max_response_time = f"{response_time:.3f}"
    
    def is_healthy(self) -> bool:
        """检查Webhook是否健康"""
        return self.health_status == "healthy"
    
    def can_receive_request(self, client_ip: str = None) -> bool:
        """检查是否可以接收请求"""
        if not self.is_active:
            return False
        
        # 检查IP白名单
        if self.allowed_ips and client_ip:
            if client_ip not in self.allowed_ips:
                return False
        
        return True
    
    def should_retry_on_failure(self) -> bool:
        """检查失败时是否应该重试"""
        return self.enable_retry and self.max_retry_attempts > 0
    
    def matches_event_filter(self, event_data: dict) -> bool:
        """检查事件是否匹配过滤器"""
        if not self.event_filters:
            return True
        
        # 简单的过滤器匹配逻辑
        for filter_key, filter_value in self.event_filters.items():
            if filter_key in event_data:
                if event_data[filter_key] != filter_value:
                    return False
        
        return True
    
    def get_webhook_stats(self) -> dict:
        """获取Webhook统计信息"""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate(),
            "avg_response_time": self.avg_response_time,
            "min_response_time": self.min_response_time,
            "max_response_time": self.max_response_time,
            "last_request_at": self.last_request_at.isoformat() if self.last_request_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "health_status": self.health_status,
            "is_active": self.is_active,
        }