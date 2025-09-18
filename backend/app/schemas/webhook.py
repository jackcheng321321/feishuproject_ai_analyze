"""Webhook相关Pydantic模式

定义Webhook的创建、更新、响应等数据验证模式。
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
from enum import Enum


class WebhookStatus(str, Enum):
    """Webhook状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PAUSED = "paused"
    ERROR = "error"


class WebhookEventType(str, Enum):
    """Webhook事件类型枚举"""
    ALL = "*"
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_DELETED = "task.deleted"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    SYSTEM_ERROR = "system.error"
    CUSTOM = "custom"


class WebhookBase(BaseModel):
    """Webhook基础模式"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Webhook名称")
    url: HttpUrl = Field(..., description="Webhook URL")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    
    # 安全设置
    secret_key: Optional[str] = Field(None, description="密钥")
    verify_signature: bool = Field(True, description="验证签名")
    allowed_ips: Optional[List[str]] = Field(None, description="允许的IP地址")
    
    # 请求设置
    timeout: int = Field(30, ge=1, le=300, description="超时时间（秒）")
    max_payload_size: int = Field(1048576, ge=1024, le=10485760, description="最大负载大小（字节）")
    
    # 重试设置
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")
    retry_delay: int = Field(60, ge=1, le=3600, description="重试延迟（秒）")
    retry_backoff: float = Field(2.0, ge=1.0, le=10.0, description="重试退避倍数")
    
    # 速率限制
    rate_limit: Optional[int] = Field(None, ge=1, description="速率限制（请求/分钟）")
    
    # 过滤设置
    event_filters: Optional[List[WebhookEventType]] = Field(None, description="事件过滤器")
    content_type_filters: Optional[List[str]] = Field(None, description="内容类型过滤器")
    
    # 其他设置
    tags: Optional[List[str]] = Field(None, description="标签")
    category: Optional[str] = Field(None, description="分类")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Webhook名称不能为空')
        return v.strip()
    
    @validator('allowed_ips')
    def validate_allowed_ips(cls, v):
        if v:
            import ipaddress
            for ip in v:
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    try:
                        ipaddress.ip_network(ip, strict=False)
                    except ValueError:
                        raise ValueError(f'无效的IP地址或网络: {ip}')
        return v
    
    @validator('content_type_filters')
    def validate_content_type_filters(cls, v):
        if v:
            allowed_types = [
                'application/json', 'application/xml', 'text/plain',
                'text/html', 'application/x-www-form-urlencoded'
            ]
            for content_type in v:
                if content_type not in allowed_types:
                    raise ValueError(f'不支持的内容类型: {content_type}')
        return v


# 简化版Webhook创建模式，按照用户需求只需要名称，其他字段自动生成或使用默认值
class WebhookCreateSimple(BaseModel):
    """简化版Webhook创建模式 - 只需要名称，其他自动生成"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Webhook名称")
    description: Optional[str] = Field(None, max_length=500, description="描述（可选）")
    is_active: bool = Field(True, description="是否激活")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Webhook名称不能为空')
        return v.strip()


class WebhookCreate(WebhookBase):
    """完整版Webhook创建模式"""
    
    is_active: bool = Field(True, description="是否激活")
    is_public: bool = Field(False, description="是否公开")
    
    # 健康检查设置
    enable_health_check: bool = Field(True, description="启用健康检查")
    health_check_interval: int = Field(300, ge=60, le=3600, description="健康检查间隔（秒）")
    health_check_timeout: int = Field(10, ge=1, le=60, description="健康检查超时（秒）")
    
    # 通知设置
    notify_on_failure: bool = Field(True, description="失败时通知")
    notify_on_recovery: bool = Field(True, description="恢复时通知")
    failure_threshold: int = Field(3, ge=1, le=10, description="失败阈值")
    
    # 日志设置
    log_requests: bool = Field(True, description="记录请求")
    log_responses: bool = Field(True, description="记录响应")
    log_errors: bool = Field(True, description="记录错误")
    log_retention_days: int = Field(30, ge=1, le=365, description="日志保留天数")


class WebhookUpdate(BaseModel):
    """Webhook更新模式"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Webhook名称")
    url: Optional[HttpUrl] = Field(None, description="Webhook URL")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    
    # 安全设置
    secret_key: Optional[str] = Field(None, description="密钥")
    verify_signature: Optional[bool] = Field(None, description="验证签名")
    allowed_ips: Optional[List[str]] = Field(None, description="允许的IP地址")
    
    # 请求设置
    timeout: Optional[int] = Field(None, ge=1, le=300, description="超时时间（秒）")
    max_payload_size: Optional[int] = Field(None, ge=1024, le=10485760, description="最大负载大小（字节）")
    
    # 重试设置
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    retry_delay: Optional[int] = Field(None, ge=1, le=3600, description="重试延迟（秒）")
    retry_backoff: Optional[float] = Field(None, ge=1.0, le=10.0, description="重试退避倍数")
    
    # 速率限制
    rate_limit: Optional[int] = Field(None, ge=1, description="速率限制（请求/分钟）")
    
    # 过滤设置
    event_filters: Optional[List[WebhookEventType]] = Field(None, description="事件过滤器")
    content_type_filters: Optional[List[str]] = Field(None, description="内容类型过滤器")
    
    # 状态
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_public: Optional[bool] = Field(None, description="是否公开")
    
    # 健康检查设置
    enable_health_check: Optional[bool] = Field(None, description="启用健康检查")
    health_check_interval: Optional[int] = Field(None, ge=60, le=3600, description="健康检查间隔（秒）")
    health_check_timeout: Optional[int] = Field(None, ge=1, le=60, description="健康检查超时（秒）")
    
    # 通知设置
    notify_on_failure: Optional[bool] = Field(None, description="失败时通知")
    notify_on_recovery: Optional[bool] = Field(None, description="恢复时通知")
    failure_threshold: Optional[int] = Field(None, ge=1, le=10, description="失败阈值")
    
    # 日志设置
    log_requests: Optional[bool] = Field(None, description="记录请求")
    log_responses: Optional[bool] = Field(None, description="记录响应")
    log_errors: Optional[bool] = Field(None, description="记录错误")
    log_retention_days: Optional[int] = Field(None, ge=1, le=365, description="日志保留天数")
    
    # 其他设置
    tags: Optional[List[str]] = Field(None, description="标签")
    category: Optional[str] = Field(None, description="分类")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Webhook名称不能为空')
        return v.strip() if v else v
    
    @validator('allowed_ips')
    def validate_allowed_ips(cls, v):
        if v:
            import ipaddress
            for ip in v:
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    try:
                        ipaddress.ip_network(ip, strict=False)
                    except ValueError:
                        raise ValueError(f'无效的IP地址或网络: {ip}')
        return v


class WebhookResponse(WebhookBase):
    """Webhook响应模式"""
    
    id: int = Field(..., description="Webhook ID")
    is_active: bool = Field(..., description="是否激活")
    is_public: bool = Field(..., description="是否公开")
    creator_id: int = Field(..., description="创建者ID")
    
    # 健康检查设置
    enable_health_check: bool = Field(..., description="启用健康检查")
    health_check_interval: int = Field(..., description="健康检查间隔（秒）")
    health_check_timeout: int = Field(..., description="健康检查超时（秒）")
    
    # 通知设置
    notify_on_failure: bool = Field(..., description="失败时通知")
    notify_on_recovery: bool = Field(..., description="恢复时通知")
    failure_threshold: int = Field(..., description="失败阈值")
    
    # 日志设置
    log_requests: bool = Field(..., description="记录请求")
    log_responses: bool = Field(..., description="记录响应")
    log_errors: bool = Field(..., description="记录错误")
    log_retention_days: int = Field(..., description="日志保留天数")
    
    # 统计信息
    total_requests: int = Field(0, description="总请求数")
    successful_requests: int = Field(0, description="成功请求数")
    failed_requests: int = Field(0, description="失败请求数")
    average_response_time: Optional[float] = Field(None, description="平均响应时间（毫秒）")
    last_request_at: Optional[datetime] = Field(None, description="最后请求时间")
    last_success_at: Optional[datetime] = Field(None, description="最后成功时间")
    last_failure_at: Optional[datetime] = Field(None, description="最后失败时间")
    
    # 健康状态
    health_status: Optional[str] = Field(None, description="健康状态")
    last_health_check_at: Optional[datetime] = Field(None, description="最后健康检查时间")
    health_check_error: Optional[str] = Field(None, description="健康检查错误")
    consecutive_failures: int = Field(0, description="连续失败次数")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookTest(BaseModel):
    """Webhook测试模式"""
    
    event_type: WebhookEventType = Field(WebhookEventType.CUSTOM, description="事件类型")
    payload: Dict[str, Any] = Field({}, description="测试负载")
    headers: Optional[Dict[str, str]] = Field(None, description="自定义头部")
    
    @validator('payload')
    def validate_payload(cls, v):
        if not isinstance(v, dict):
            raise ValueError('负载必须是字典格式')
        return v


class WebhookTestResponse(BaseModel):
    """Webhook测试响应模式"""
    
    success: bool = Field(..., description="是否成功")
    status_code: Optional[int] = Field(None, description="HTTP状态码")
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）")
    response_headers: Optional[Dict[str, str]] = Field(None, description="响应头部")
    response_body: Optional[str] = Field(None, description="响应体")
    error_message: Optional[str] = Field(None, description="错误信息")
    tested_at: datetime = Field(..., description="测试时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookHealthCheck(BaseModel):
    """Webhook健康检查模式"""
    
    webhook_id: int = Field(..., description="Webhook ID")
    status: str = Field(..., description="状态")
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）")
    status_code: Optional[int] = Field(None, description="HTTP状态码")
    error_message: Optional[str] = Field(None, description="错误信息")
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookUsage(BaseModel):
    """Webhook使用情况模式"""
    
    webhook_id: int = Field(..., description="Webhook ID")
    webhook_name: str = Field(..., description="Webhook名称")
    requests_count: int = Field(0, description="请求数量")
    successful_requests: int = Field(0, description="成功请求数")
    failed_requests: int = Field(0, description="失败请求数")
    success_rate: float = Field(0.0, description="成功率")
    average_response_time: Optional[float] = Field(None, description="平均响应时间")
    last_request_at: Optional[datetime] = Field(None, description="最后请求时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookStats(BaseModel):
    """Webhook统计模式"""
    
    total_webhooks: int = Field(0, description="总Webhook数")
    active_webhooks: int = Field(0, description="活跃Webhook数")
    total_requests: int = Field(0, description="总请求数")
    successful_requests: int = Field(0, description="成功请求数")
    failed_requests: int = Field(0, description="失败请求数")
    average_success_rate: float = Field(0.0, description="平均成功率")
    average_response_time: Optional[float] = Field(None, description="平均响应时间")
    most_active_webhook: Optional[str] = Field(None, description="最活跃Webhook")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookEvent(BaseModel):
    """Webhook事件模式"""
    
    id: str = Field(..., description="事件ID")
    webhook_id: int = Field(..., description="Webhook ID")
    event_type: WebhookEventType = Field(..., description="事件类型")
    payload: Dict[str, Any] = Field(..., description="事件负载")
    headers: Dict[str, str] = Field({}, description="请求头部")
    source_ip: Optional[str] = Field(None, description="源IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookDelivery(BaseModel):
    """Webhook投递模式"""
    
    id: str = Field(..., description="投递ID")
    webhook_id: int = Field(..., description="Webhook ID")
    event_id: str = Field(..., description="事件ID")
    status: str = Field(..., description="投递状态")
    attempt: int = Field(..., description="尝试次数")
    max_attempts: int = Field(..., description="最大尝试次数")
    
    # 请求信息
    request_url: str = Field(..., description="请求URL")
    request_method: str = Field("POST", description="请求方法")
    request_headers: Dict[str, str] = Field({}, description="请求头部")
    request_body: Optional[str] = Field(None, description="请求体")
    
    # 响应信息
    response_status_code: Optional[int] = Field(None, description="响应状态码")
    response_headers: Optional[Dict[str, str]] = Field(None, description="响应头部")
    response_body: Optional[str] = Field(None, description="响应体")
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    
    # 时间信息
    scheduled_at: datetime = Field(..., description="计划时间")
    delivered_at: Optional[datetime] = Field(None, description="投递时间")
    next_retry_at: Optional[datetime] = Field(None, description="下次重试时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookBatchTest(BaseModel):
    """Webhook批量测试模式"""
    
    webhook_ids: List[int] = Field(..., min_items=1, description="Webhook ID列表")
    event_type: WebhookEventType = Field(WebhookEventType.CUSTOM, description="事件类型")
    payload: Dict[str, Any] = Field({}, description="测试负载")
    
    @validator('payload')
    def validate_payload(cls, v):
        if not isinstance(v, dict):
            raise ValueError('负载必须是字典格式')
        return v


class WebhookBatchTestResponse(BaseModel):
    """Webhook批量测试响应模式"""
    
    results: List[WebhookTestResponse] = Field(..., description="测试结果列表")
    total_tested: int = Field(..., description="测试总数")
    successful_tests: int = Field(..., description="成功测试数")
    failed_tests: int = Field(..., description="失败测试数")
    average_response_time: Optional[float] = Field(None, description="平均响应时间")
    tested_at: datetime = Field(..., description="测试时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookMetrics(BaseModel):
    """Webhook指标模式"""
    
    webhook_id: int = Field(..., description="Webhook ID")
    date: datetime = Field(..., description="日期")
    requests_count: int = Field(0, description="请求数量")
    successful_requests: int = Field(0, description="成功请求数")
    failed_requests: int = Field(0, description="失败请求数")
    average_response_time: float = Field(0.0, description="平均响应时间")
    max_response_time: float = Field(0.0, description="最大响应时间")
    min_response_time: float = Field(0.0, description="最小响应时间")
    error_rate: float = Field(0.0, description="错误率")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookFilter(BaseModel):
    """Webhook过滤器模式"""
    
    name: Optional[str] = Field(None, description="名称过滤")
    status: Optional[WebhookStatus] = Field(None, description="状态过滤")
    event_types: Optional[List[WebhookEventType]] = Field(None, description="事件类型过滤")
    creator_id: Optional[int] = Field(None, description="创建者ID过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    category: Optional[str] = Field(None, description="分类过滤")
    is_active: Optional[bool] = Field(None, description="激活状态过滤")
    is_public: Optional[bool] = Field(None, description="公开状态过滤")
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookSort(BaseModel):
    """Webhook排序模式"""
    
    field: str = Field("created_at", description="排序字段")
    order: str = Field("desc", description="排序顺序")
    
    @validator('field')
    def validate_field(cls, v):
        allowed_fields = [
            'id', 'name', 'created_at', 'updated_at', 'last_request_at',
            'total_requests', 'successful_requests', 'failed_requests',
            'average_response_time', 'success_rate'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是以下之一: {", ".join(allowed_fields)}')
        return v
    
    @validator('order')
    def validate_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序顺序必须是asc或desc')
        return v.lower()


class WebhookSimpleResponse(BaseModel):
    """简化版Webhook响应模式 - 直接映射数据库字段"""

    id: int = Field(..., description="Webhook ID")
    name: str = Field(..., description="Webhook名称")
    description: Optional[str] = Field(None, description="描述")
    webhook_id: str = Field(..., description="Webhook唯一标识")
    webhook_url: str = Field(..., description="Webhook URL")
    url: Optional[str] = Field(None, description="前端兼容的URL字段")  # 前端期待的字段
    method: str = Field("POST", description="HTTP请求方法")
    secret_key: str = Field(..., description="密钥")

    # 状态字段
    is_active: bool = Field(..., description="是否启用")
    is_public: bool = Field(..., description="是否公开")

    # 统计信息
    total_requests: int = Field(0, description="总请求次数")
    successful_requests: int = Field(0, description="成功请求次数")
    failed_requests: int = Field(0, description="失败请求次数")

    # 时间信息
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    last_triggered_at: Optional[datetime] = Field(None, description="最后触发时间")  # 前端期待的字段

    @classmethod
    def from_webhook(cls, webhook):
        """从Webhook模型创建响应对象"""
        return cls(
            id=webhook.id,
            name=webhook.name,
            description=webhook.description,
            webhook_id=webhook.webhook_id,
            webhook_url=webhook.webhook_url,
            url=webhook.webhook_url,  # 映射到前端期待的url字段
            method=webhook.method.value if webhook.method else "POST",  # 获取HTTP方法
            secret_key=webhook.secret_key,
            is_active=webhook.is_active,
            is_public=webhook.is_public,
            total_requests=webhook.total_requests,
            successful_requests=webhook.successful_requests,
            failed_requests=webhook.failed_requests,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            last_triggered_at=webhook.last_request_at,  # 映射最后请求时间到前端期待的字段
        )
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }