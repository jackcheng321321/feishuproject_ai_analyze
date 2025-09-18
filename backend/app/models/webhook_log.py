from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

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


class LogLevel(str, enum.Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class WebhookLog(Base):
    """Webhook日志模型"""
    
    __tablename__ = "webhook_logs"
    
    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False, comment="Webhook ID")
    
    # 请求标识
    request_id = Column(String(50), unique=True, nullable=False, comment="请求唯一标识")
    trace_id = Column(String(50), comment="追踪ID")
    correlation_id = Column(String(50), comment="关联ID")
    
    # 请求信息
    method = Column(
        SQLEnum(RequestMethod), 
        default=RequestMethod.POST, 
        comment="HTTP方法"
    )
    url = Column(String(500), comment="请求URL")
    path = Column(String(200), comment="请求路径")
    query_params = Column(JSON, comment="查询参数")
    
    # 请求头信息
    headers = Column(JSON, comment="请求头")
    user_agent = Column(String(500), comment="用户代理")
    content_type = Column(String(100), comment="内容类型")
    content_length = Column(Integer, comment="内容长度")
    
    # 客户端信息
    client_ip = Column(String(45), comment="客户端IP")
    client_port = Column(Integer, comment="客户端端口")
    forwarded_for = Column(String(200), comment="X-Forwarded-For")
    real_ip = Column(String(45), comment="真实IP")
    
    # 请求体信息
    request_body = Column(Text, comment="请求体")
    request_body_size = Column(Integer, comment="请求体大小")
    request_body_hash = Column(String(64), comment="请求体哈希")
    
    # 签名验证
    signature_header = Column(String(200), comment="签名头")
    signature_valid = Column(Boolean, comment="签名是否有效")
    signature_algorithm = Column(String(20), comment="签名算法")
    
    # 响应信息
    status_code = Column(Integer, comment="响应状态码")
    response_headers = Column(JSON, comment="响应头")
    response_body = Column(Text, comment="响应体")
    response_size = Column(Integer, comment="响应大小")
    
    # 处理信息
    processed = Column(Boolean, default=False, comment="是否已处理")
    processing_status = Column(String(20), comment="处理状态")
    processing_message = Column(Text, comment="处理消息")
    task_execution_id = Column(Integer, ForeignKey("task_executions.id"), comment="关联的任务执行ID")
    
    # 时间信息
    request_time = Column(DateTime(timezone=True), comment="请求时间")
    response_time = Column(DateTime(timezone=True), comment="响应时间")
    processing_time = Column(DateTime(timezone=True), comment="处理时间")
    duration_ms = Column(Integer, comment="处理时长（毫秒）")
    
    # 错误信息
    error_code = Column(String(50), comment="错误代码")
    error_message = Column(Text, comment="错误消息")
    error_details = Column(JSON, comment="错误详情")
    stack_trace = Column(Text, comment="堆栈跟踪")
    
    # 日志级别和分类
    log_level = Column(
        SQLEnum(LogLevel), 
        default=LogLevel.INFO, 
        comment="日志级别"
    )
    category = Column(String(50), comment="日志分类")
    event_type = Column(String(50), comment="事件类型")
    
    # 业务数据
    business_data = Column(JSON, comment="业务数据")
    extracted_fields = Column(JSON, comment="提取的字段")
    validation_results = Column(JSON, comment="验证结果")
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment="重试次数")
    is_retry = Column(Boolean, default=False, comment="是否为重试请求")
    original_request_id = Column(String(50), comment="原始请求ID")
    
    # 限流信息
    rate_limit_key = Column(String(100), comment="限流键")
    rate_limit_remaining = Column(Integer, comment="剩余请求数")
    rate_limit_reset = Column(DateTime(timezone=True), comment="限流重置时间")
    rate_limited = Column(Boolean, default=False, comment="是否被限流")
    
    # 安全信息
    security_check_passed = Column(Boolean, default=True, comment="安全检查是否通过")
    security_warnings = Column(JSON, comment="安全警告")
    blocked_reason = Column(String(200), comment="阻止原因")
    
    # 性能指标
    memory_usage_mb = Column(Integer, comment="内存使用（MB）")
    cpu_usage_percent = Column(String(10), comment="CPU使用率")
    db_query_count = Column(Integer, comment="数据库查询次数")
    db_query_time_ms = Column(Integer, comment="数据库查询时间（毫秒）")
    
    # 地理位置信息
    country = Column(String(50), comment="国家")
    region = Column(String(50), comment="地区")
    city = Column(String(50), comment="城市")
    timezone = Column(String(50), comment="时区")
    
    # 设备信息
    device_type = Column(String(50), comment="设备类型")
    browser = Column(String(100), comment="浏览器")
    os = Column(String(100), comment="操作系统")
    
    # 标签和元数据
    tags = Column(JSON, comment="标签")
    meta_data = Column(JSON, comment="元数据")
    custom_fields = Column(JSON, comment="自定义字段")
    
    # 归档信息
    archived = Column(Boolean, default=False, comment="是否已归档")
    archived_at = Column(DateTime(timezone=True), comment="归档时间")
    retention_until = Column(DateTime(timezone=True), comment="保留到期时间")
    
    # 备注信息
    notes = Column(Text, comment="备注")
    admin_notes = Column(Text, comment="管理员备注")
    
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
    webhook = relationship("Webhook", back_populates="webhook_logs")
    task_execution = relationship("TaskExecution")
    
    def __repr__(self):
        return f"<WebhookLog(id={self.id}, request_id='{self.request_id}', status_code={self.status_code})>"
    
    def to_dict(self, include_sensitive=False, include_body=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "webhook_id": self.webhook_id,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "method": self.method.value if self.method else None,
            "url": self.url,
            "path": self.path,
            "query_params": self.query_params,
            "user_agent": self.user_agent,
            "content_type": self.content_type,
            "content_length": self.content_length,
            "client_ip": self.client_ip,
            "client_port": self.client_port,
            "forwarded_for": self.forwarded_for,
            "real_ip": self.real_ip,
            "request_body_size": self.request_body_size,
            "request_body_hash": self.request_body_hash,
            "signature_valid": self.signature_valid,
            "signature_algorithm": self.signature_algorithm,
            "status_code": self.status_code,
            "response_size": self.response_size,
            "processed": self.processed,
            "processing_status": self.processing_status,
            "processing_message": self.processing_message,
            "task_execution_id": self.task_execution_id,
            "request_time": self.request_time.isoformat() if self.request_time else None,
            "response_time": self.response_time.isoformat() if self.response_time else None,
            "processing_time": self.processing_time.isoformat() if self.processing_time else None,
            "duration_ms": self.duration_ms,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "log_level": self.log_level.value if self.log_level else None,
            "category": self.category,
            "event_type": self.event_type,
            "retry_count": self.retry_count,
            "is_retry": self.is_retry,
            "original_request_id": self.original_request_id,
            "rate_limit_remaining": self.rate_limit_remaining,
            "rate_limit_reset": self.rate_limit_reset.isoformat() if self.rate_limit_reset else None,
            "rate_limited": self.rate_limited,
            "security_check_passed": self.security_check_passed,
            "blocked_reason": self.blocked_reason,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "db_query_count": self.db_query_count,
            "db_query_time_ms": self.db_query_time_ms,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "timezone": self.timezone,
            "device_type": self.device_type,
            "browser": self.browser,
            "os": self.os,
            "tags": self.tags,
            "archived": self.archived,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "retention_until": self.retention_until.isoformat() if self.retention_until else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 敏感信息只在需要时包含
        if include_sensitive:
            data.update({
                "headers": self.headers,
                "response_headers": self.response_headers,
                "signature_header": self.signature_header,
                "business_data": self.business_data,
                "extracted_fields": self.extracted_fields,
                "validation_results": self.validation_results,
                "error_details": self.error_details,
                "stack_trace": self.stack_trace,
                "security_warnings": self.security_warnings,
                "meta_data": self.meta_data,
                "custom_fields": self.custom_fields,
                "admin_notes": self.admin_notes,
            })
        
        # 请求/响应体只在需要时包含
        if include_body:
            data.update({
                "request_body": self.request_body,
                "response_body": self.response_body,
            })
        
        return data
    
    def start_processing(self):
        """开始处理"""
        self.processing_time = datetime.utcnow()
        self.processing_status = "processing"
    
    def complete_processing(self, success: bool = True, message: str = None, task_execution_id: int = None):
        """完成处理"""
        self.processed = True
        self.processing_status = "completed" if success else "failed"
        
        if message:
            self.processing_message = message
        
        if task_execution_id:
            self.task_execution_id = task_execution_id
        
        # 计算处理时长
        if self.request_time:
            duration = datetime.utcnow() - self.request_time
            self.duration_ms = int(duration.total_seconds() * 1000)
    
    def set_response(self, status_code: int, headers: dict = None, body: str = None):
        """设置响应信息"""
        self.status_code = status_code
        self.response_time = datetime.utcnow()
        
        if headers:
            self.response_headers = headers
        
        if body:
            self.response_body = body
            self.response_size = len(body.encode('utf-8'))
    
    def set_error(self, error_code: str, error_message: str, error_details: dict = None, stack_trace: str = None):
        """设置错误信息"""
        self.error_code = error_code
        self.error_message = error_message
        self.error_details = error_details
        self.stack_trace = stack_trace
        self.log_level = LogLevel.ERROR
        self.processing_status = "error"
    
    def add_security_warning(self, warning_type: str, message: str, details: dict = None):
        """添加安全警告"""
        if not self.security_warnings:
            self.security_warnings = []
        
        warning = {
            "type": warning_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if details:
            warning["details"] = details
        
        self.security_warnings.append(warning)
        
        # 如果有安全警告，标记安全检查未通过
        if warning_type in ["malicious_payload", "suspicious_ip", "invalid_signature"]:
            self.security_check_passed = False
    
    def is_successful(self) -> bool:
        """检查请求是否成功"""
        return self.status_code and 200 <= self.status_code < 300
    
    def is_client_error(self) -> bool:
        """检查是否为客户端错误"""
        return self.status_code and 400 <= self.status_code < 500
    
    def is_server_error(self) -> bool:
        """检查是否为服务器错误"""
        return self.status_code and 500 <= self.status_code < 600
    
    def get_client_info(self) -> dict:
        """获取客户端信息"""
        return {
            "ip": self.client_ip,
            "port": self.client_port,
            "forwarded_for": self.forwarded_for,
            "real_ip": self.real_ip,
            "user_agent": self.user_agent,
            "device_type": self.device_type,
            "browser": self.browser,
            "os": self.os,
            "country": self.country,
            "region": self.region,
            "city": self.city,
            "timezone": self.timezone,
        }
    
    def get_performance_metrics(self) -> dict:
        """获取性能指标"""
        return {
            "duration_ms": self.duration_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "db_query_count": self.db_query_count,
            "db_query_time_ms": self.db_query_time_ms,
            "request_body_size": self.request_body_size,
            "response_size": self.response_size,
        }
    
    def get_security_summary(self) -> dict:
        """获取安全摘要"""
        return {
            "signature_valid": self.signature_valid,
            "security_check_passed": self.security_check_passed,
            "rate_limited": self.rate_limited,
            "blocked_reason": self.blocked_reason,
            "security_warnings_count": len(self.security_warnings) if self.security_warnings else 0,
            "retry_count": self.retry_count,
        }
    
    def should_be_archived(self, retention_days: int = 30) -> bool:
        """检查是否应该归档"""
        if self.archived:
            return False
        
        if self.retention_until:
            return datetime.utcnow() > self.retention_until
        
        # 基于创建时间判断
        if self.created_at:
            retention_date = self.created_at + timedelta(days=retention_days)
            return datetime.utcnow() > retention_date
        
        return False
    
    def archive(self):
        """归档日志"""
        self.archived = True
        self.archived_at = datetime.utcnow()
        
        # 清理敏感数据
        self.request_body = None
        self.response_body = None
        self.headers = None
        self.response_headers = None
        self.stack_trace = None
        self.business_data = None
    
    @classmethod
    def create_from_request(cls, webhook_id: int, request_id: str, method: str, url: str, 
                          headers: dict, body: str = None, client_ip: str = None) -> 'WebhookLog':
        """从请求创建日志记录"""
        log = cls(
            webhook_id=webhook_id,
            request_id=request_id,
            method=RequestMethod(method.upper()),
            url=url,
            headers=headers,
            request_body=body,
            client_ip=client_ip,
            request_time=datetime.utcnow(),
        )
        
        # 解析请求信息
        if headers:
            log.user_agent = headers.get('User-Agent')
            log.content_type = headers.get('Content-Type')
            log.content_length = headers.get('Content-Length')
            log.forwarded_for = headers.get('X-Forwarded-For')
            log.real_ip = headers.get('X-Real-IP')
            log.signature_header = headers.get('X-Signature') or headers.get('X-Hub-Signature-256')
        
        if body:
            log.request_body_size = len(body.encode('utf-8'))
            # 这里可以添加哈希计算
        
        return log