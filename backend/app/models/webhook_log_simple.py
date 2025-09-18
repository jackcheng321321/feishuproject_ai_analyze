"""简化版WebhookLog模型，匹配实际数据库表结构"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET, ARRAY
from datetime import datetime

from app.core.database import Base


class WebhookLog(Base):
    """WebhookLog模型 - 匹配实际数据库表结构"""
    
    __tablename__ = "webhook_logs"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False, comment="Webhook ID")
    
    # 基本字段（匹配数据库实际结构）
    request_id = Column(String(50), comment="请求ID")
    source_ip = Column(INET, comment="来源IP")
    user_agent = Column(Text, comment="用户代理")
    request_headers = Column(JSON, comment="请求头")
    request_payload = Column(JSON, comment="请求载荷")
    request_size_bytes = Column(Integer, comment="请求大小（字节）")
    response_status = Column(Integer, comment="响应状态码")
    response_time_ms = Column(Integer, comment="响应时间（毫秒）")
    is_valid = Column(Boolean, default=True, comment="是否有效")
    validation_errors = Column(ARRAY(String), comment="验证错误")
    task_execution_id = Column(Integer, ForeignKey("task_executions.id"), comment="任务执行ID")
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        comment="创建时间"
    )
    
    # 关系
    webhook = relationship("Webhook", back_populates="webhook_logs")
    task_execution = relationship("TaskExecution", backref="webhook_logs")
    
    def __repr__(self):
        return f"<WebhookLog(id={self.id}, webhook_id={self.webhook_id}, status={self.response_status})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "request_id": self.request_id,
            "source_ip": str(self.source_ip) if self.source_ip else None,
            "user_agent": self.user_agent,
            "request_headers": self.request_headers,
            "request_payload": self.request_payload,
            "request_size_bytes": self.request_size_bytes,
            "response_status": self.response_status,
            "response_time_ms": self.response_time_ms,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "task_execution_id": self.task_execution_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def is_successful(self):
        """检查是否成功"""
        return self.response_status and 200 <= self.response_status < 300
    
    def is_client_error(self):
        """检查是否客户端错误"""
        return self.response_status and 400 <= self.response_status < 500
    
    def is_server_error(self):
        """检查是否服务器错误"""
        return self.response_status and 500 <= self.response_status < 600
    
    @classmethod
    def create_from_request(cls, webhook_id: int, request_id: str = None, 
                          source_ip: str = None, user_agent: str = None,
                          headers: dict = None, payload: dict = None,
                          request_size: int = None):
        """从请求创建日志"""
        return cls(
            webhook_id=webhook_id,
            request_id=request_id,
            source_ip=source_ip,
            user_agent=user_agent,
            request_headers=headers,
            request_payload=payload,
            request_size_bytes=request_size,
        )
    
    def set_response(self, status_code: int, response_time_ms: int = None):
        """设置响应信息"""
        self.response_status = status_code
        if response_time_ms:
            self.response_time_ms = response_time_ms
    
    def set_validation_errors(self, errors: list):
        """设置验证错误"""
        self.validation_errors = errors
        self.is_valid = False