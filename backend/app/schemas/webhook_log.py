"""Webhook日志相关Pydantic模式

定义Webhook日志的创建、更新、响应等数据验证模式。
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class LogStatus(str, Enum):
    """日志状态枚举"""
    RECEIVED = "received"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class HttpMethod(str, Enum):
    """HTTP方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class SecurityLevel(str, Enum):
    """安全级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WebhookLogBase(BaseModel):
    """Webhook日志基础模式"""
    
    webhook_id: int = Field(..., description="Webhook ID")
    
    # 请求信息
    method: HttpMethod = Field(..., description="HTTP方法")
    url: str = Field(..., max_length=2000, description="请求URL")
    headers: Dict[str, str] = Field({}, description="请求头")
    query_params: Optional[Dict[str, str]] = Field(None, description="查询参数")
    body: Optional[str] = Field(None, description="请求体")
    content_type: Optional[str] = Field(None, max_length=200, description="内容类型")
    content_length: Optional[int] = Field(None, ge=0, description="内容长度")
    
    # 客户端信息
    client_ip: str = Field(..., max_length=45, description="客户端IP")
    user_agent: Optional[str] = Field(None, max_length=1000, description="用户代理")
    referer: Optional[str] = Field(None, max_length=2000, description="引用页")
    
    # 地理位置信息
    country: Optional[str] = Field(None, max_length=100, description="国家")
    region: Optional[str] = Field(None, max_length=100, description="地区")
    city: Optional[str] = Field(None, max_length=100, description="城市")
    
    # 设备信息
    device_type: Optional[str] = Field(None, max_length=50, description="设备类型")
    browser: Optional[str] = Field(None, max_length=100, description="浏览器")
    os: Optional[str] = Field(None, max_length=100, description="操作系统")
    
    @validator('url')
    def validate_url(cls, v):
        if not v or not v.strip():
            raise ValueError('URL不能为空')
        return v.strip()
    
    @validator('headers')
    def validate_headers(cls, v):
        if not isinstance(v, dict):
            raise ValueError('请求头必须是字典格式')
        return v
    
    @validator('query_params')
    def validate_query_params(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('查询参数必须是字典格式')
        return v
    
    @validator('client_ip')
    def validate_client_ip(cls, v):
        if not v or not v.strip():
            raise ValueError('客户端IP不能为空')
        return v.strip()


class WebhookLogCreate(WebhookLogBase):
    """Webhook日志创建模式"""
    
    # 请求ID（用于追踪）
    request_id: Optional[str] = Field(None, max_length=100, description="请求ID")
    
    # 安全信息
    signature: Optional[str] = Field(None, max_length=500, description="签名")
    signature_valid: Optional[bool] = Field(None, description="签名是否有效")
    
    # 处理配置
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300, description="超时时间（秒）")
    
    @validator('request_id')
    def validate_request_id(cls, v):
        if v is not None and not v.strip():
            raise ValueError('请求ID不能为空字符串')
        return v.strip() if v else None


class WebhookLogUpdate(BaseModel):
    """Webhook日志更新模式"""
    
    status: Optional[LogStatus] = Field(None, description="处理状态")
    
    # 响应信息
    response_status_code: Optional[int] = Field(None, ge=100, le=599, description="响应状态码")
    response_headers: Optional[Dict[str, str]] = Field(None, description="响应头")
    response_body: Optional[str] = Field(None, description="响应体")
    response_time_ms: Optional[float] = Field(None, ge=0, description="响应时间（毫秒）")
    
    # 处理信息
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    processing_time_ms: Optional[float] = Field(None, ge=0, description="处理时间（毫秒）")
    
    # 错误信息
    error_message: Optional[str] = Field(None, max_length=2000, description="错误信息")
    error_code: Optional[str] = Field(None, max_length=100, description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    # 安全警告
    security_warnings: Optional[List[str]] = Field(None, description="安全警告")
    security_level: Optional[SecurityLevel] = Field(None, description="安全级别")
    
    # 性能指标
    memory_usage_mb: Optional[float] = Field(None, ge=0, description="内存使用（MB）")
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100, description="CPU使用率（%）")
    
    # 任务执行信息
    task_execution_id: Optional[str] = Field(None, description="任务执行ID")
    tasks_triggered: Optional[int] = Field(None, ge=0, description="触发任务数")
    
    # 归档信息
    archived: Optional[bool] = Field(None, description="是否已归档")
    archived_at: Optional[datetime] = Field(None, description="归档时间")
    
    @validator('response_headers')
    def validate_response_headers(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('响应头必须是字典格式')
        return v
    
    @validator('error_details')
    def validate_error_details(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('错误详情必须是字典格式')
        return v
    
    @validator('security_warnings')
    def validate_security_warnings(cls, v):
        if v is not None and not isinstance(v, list):
            raise ValueError('安全警告必须是列表格式')
        return v


class WebhookLogResponse(WebhookLogBase):
    """Webhook日志响应模式"""
    
    id: int = Field(..., description="日志ID")
    request_id: Optional[str] = Field(None, description="请求ID")
    status: LogStatus = Field(..., description="处理状态")
    
    # 签名信息
    signature: Optional[str] = Field(None, description="签名")
    signature_valid: Optional[bool] = Field(None, description="签名是否有效")
    
    # 响应信息
    response_status_code: Optional[int] = Field(None, description="响应状态码")
    response_headers: Optional[Dict[str, str]] = Field(None, description="响应头")
    response_body: Optional[str] = Field(None, description="响应体")
    response_time_ms: Optional[float] = Field(None, description="响应时间（毫秒）")
    
    # 处理信息
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    processing_time_ms: Optional[float] = Field(None, description="处理时间（毫秒）")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    # 安全信息
    security_warnings: Optional[List[str]] = Field(None, description="安全警告")
    security_level: Optional[SecurityLevel] = Field(None, description="安全级别")
    
    # 性能指标
    memory_usage_mb: Optional[float] = Field(None, description="内存使用（MB）")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU使用率（%）")
    
    # 任务执行信息
    task_execution_id: Optional[str] = Field(None, description="任务执行ID")
    tasks_triggered: Optional[int] = Field(None, description="触发任务数")
    
    # 超时配置
    timeout_seconds: Optional[int] = Field(None, description="超时时间（秒）")
    
    # 归档信息
    archived: bool = Field(False, description="是否已归档")
    archived_at: Optional[datetime] = Field(None, description="归档时间")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookLogSummary(BaseModel):
    """Webhook日志摘要模式"""
    
    id: int = Field(..., description="日志ID")
    webhook_id: int = Field(..., description="Webhook ID")
    webhook_name: str = Field(..., description="Webhook名称")
    method: HttpMethod = Field(..., description="HTTP方法")
    status: LogStatus = Field(..., description="处理状态")
    client_ip: str = Field(..., description="客户端IP")
    
    # 响应信息
    response_status_code: Optional[int] = Field(None, description="响应状态码")
    response_time_ms: Optional[float] = Field(None, description="响应时间（毫秒）")
    processing_time_ms: Optional[float] = Field(None, description="处理时间（毫秒）")
    
    # 任务信息
    tasks_triggered: Optional[int] = Field(None, description="触发任务数")
    
    # 错误信息（仅在失败时）
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 安全级别
    security_level: Optional[SecurityLevel] = Field(None, description="安全级别")
    
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookLogStats(BaseModel):
    """Webhook日志统计模式"""
    
    total_requests: int = Field(0, description="总请求数")
    successful_requests: int = Field(0, description="成功请求数")
    failed_requests: int = Field(0, description="失败请求数")
    timeout_requests: int = Field(0, description="超时请求数")
    rejected_requests: int = Field(0, description="拒绝请求数")
    
    # 成功率
    success_rate: float = Field(0.0, description="成功率")
    
    # 响应时间统计
    average_response_time: Optional[float] = Field(None, description="平均响应时间")
    min_response_time: Optional[float] = Field(None, description="最小响应时间")
    max_response_time: Optional[float] = Field(None, description="最大响应时间")
    
    # 处理时间统计
    average_processing_time: Optional[float] = Field(None, description="平均处理时间")
    min_processing_time: Optional[float] = Field(None, description="最小处理时间")
    max_processing_time: Optional[float] = Field(None, description="最大处理时间")
    
    # 任务统计
    total_tasks_triggered: int = Field(0, description="触发任务总数")
    average_tasks_per_request: float = Field(0.0, description="每请求平均任务数")
    
    # 安全统计
    security_warnings_count: int = Field(0, description="安全警告数")
    high_security_incidents: int = Field(0, description="高安全级别事件数")
    
    # 地理统计
    unique_countries: int = Field(0, description="唯一国家数")
    unique_ips: int = Field(0, description="唯一IP数")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookLogClientSummary(BaseModel):
    """Webhook日志客户端摘要模式"""
    
    client_ip: str = Field(..., description="客户端IP")
    request_count: int = Field(..., description="请求数量")
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    success_rate: float = Field(..., description="成功率")
    
    # 地理信息
    country: Optional[str] = Field(None, description="国家")
    region: Optional[str] = Field(None, description="地区")
    city: Optional[str] = Field(None, description="城市")
    
    # 设备信息
    device_type: Optional[str] = Field(None, description="设备类型")
    browser: Optional[str] = Field(None, description="浏览器")
    os: Optional[str] = Field(None, description="操作系统")
    
    # 时间信息
    first_request_at: datetime = Field(..., description="首次请求时间")
    last_request_at: datetime = Field(..., description="最后请求时间")
    
    # 安全信息
    security_warnings: int = Field(0, description="安全警告数")
    highest_security_level: Optional[SecurityLevel] = Field(None, description="最高安全级别")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookLogPerformanceMetrics(BaseModel):
    """Webhook日志性能指标模式"""
    
    webhook_id: int = Field(..., description="Webhook ID")
    
    # 请求量指标
    requests_per_hour: float = Field(0.0, description="每小时请求数")
    requests_per_day: float = Field(0.0, description="每天请求数")
    peak_requests_per_minute: float = Field(0.0, description="每分钟峰值请求数")
    
    # 响应时间指标
    p50_response_time: Optional[float] = Field(None, description="50%响应时间")
    p90_response_time: Optional[float] = Field(None, description="90%响应时间")
    p95_response_time: Optional[float] = Field(None, description="95%响应时间")
    p99_response_time: Optional[float] = Field(None, description="99%响应时间")
    
    # 处理时间指标
    p50_processing_time: Optional[float] = Field(None, description="50%处理时间")
    p90_processing_time: Optional[float] = Field(None, description="90%处理时间")
    p95_processing_time: Optional[float] = Field(None, description="95%处理时间")
    p99_processing_time: Optional[float] = Field(None, description="99%处理时间")
    
    # 资源使用指标
    average_memory_usage: Optional[float] = Field(None, description="平均内存使用")
    peak_memory_usage: Optional[float] = Field(None, description="峰值内存使用")
    average_cpu_usage: Optional[float] = Field(None, description="平均CPU使用")
    peak_cpu_usage: Optional[float] = Field(None, description="峰值CPU使用")
    
    # 错误率指标
    error_rate: float = Field(0.0, description="错误率")
    timeout_rate: float = Field(0.0, description="超时率")
    rejection_rate: float = Field(0.0, description="拒绝率")
    
    # 时间范围
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookLogSecuritySummary(BaseModel):
    """Webhook日志安全摘要模式"""
    
    webhook_id: int = Field(..., description="Webhook ID")
    
    # 安全事件统计
    total_security_warnings: int = Field(0, description="安全警告总数")
    low_level_warnings: int = Field(0, description="低级别警告数")
    medium_level_warnings: int = Field(0, description="中级别警告数")
    high_level_warnings: int = Field(0, description="高级别警告数")
    critical_level_warnings: int = Field(0, description="严重级别警告数")
    
    # 签名验证统计
    total_signed_requests: int = Field(0, description="签名请求总数")
    valid_signatures: int = Field(0, description="有效签名数")
    invalid_signatures: int = Field(0, description="无效签名数")
    signature_validation_rate: float = Field(0.0, description="签名验证率")
    
    # IP统计
    unique_ips: int = Field(0, description="唯一IP数")
    suspicious_ips: List[str] = Field([], description="可疑IP列表")
    blocked_ips: List[str] = Field([], description="被阻止IP列表")
    
    # 攻击模式
    potential_attacks: List[Dict[str, Any]] = Field([], description="潜在攻击")
    
    # 时间范围
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookLogArchive(BaseModel):
    """Webhook日志归档模式"""
    
    log_ids: List[int] = Field(..., min_items=1, description="日志ID列表")
    archive_reason: Optional[str] = Field(None, max_length=500, description="归档原因")
    
    @validator('log_ids')
    def validate_log_ids(cls, v):
        if not v:
            raise ValueError('日志ID列表不能为空')
        if len(set(v)) != len(v):
            raise ValueError('日志ID列表不能包含重复项')
        return v


class WebhookLogArchiveResponse(BaseModel):
    """Webhook日志归档响应模式"""
    
    total_logs: int = Field(..., description="日志总数")
    archived_logs: int = Field(..., description="已归档日志数")
    failed_logs: int = Field(..., description="归档失败日志数")
    archive_reason: Optional[str] = Field(None, description="归档原因")
    archived_at: datetime = Field(..., description="归档时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookLogFilter(BaseModel):
    """Webhook日志过滤器模式"""
    
    webhook_id: Optional[int] = Field(None, description="Webhook ID过滤")
    status: Optional[LogStatus] = Field(None, description="状态过滤")
    method: Optional[HttpMethod] = Field(None, description="HTTP方法过滤")
    client_ip: Optional[str] = Field(None, description="客户端IP过滤")
    
    # 响应状态码过滤
    response_status_code: Optional[int] = Field(None, description="响应状态码过滤")
    response_status_code_range: Optional[List[int]] = Field(None, description="响应状态码范围")
    
    # 时间过滤
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    processed_after: Optional[datetime] = Field(None, description="处理时间之后")
    processed_before: Optional[datetime] = Field(None, description="处理时间之前")
    
    # 性能过滤
    min_response_time: Optional[float] = Field(None, ge=0, description="最小响应时间")
    max_response_time: Optional[float] = Field(None, ge=0, description="最大响应时间")
    min_processing_time: Optional[float] = Field(None, ge=0, description="最小处理时间")
    max_processing_time: Optional[float] = Field(None, ge=0, description="最大处理时间")
    
    # 安全过滤
    security_level: Optional[SecurityLevel] = Field(None, description="安全级别过滤")
    has_security_warnings: Optional[bool] = Field(None, description="是否有安全警告")
    signature_valid: Optional[bool] = Field(None, description="签名是否有效")
    
    # 地理过滤
    country: Optional[str] = Field(None, description="国家过滤")
    region: Optional[str] = Field(None, description="地区过滤")
    city: Optional[str] = Field(None, description="城市过滤")
    
    # 设备过滤
    device_type: Optional[str] = Field(None, description="设备类型过滤")
    browser: Optional[str] = Field(None, description="浏览器过滤")
    os: Optional[str] = Field(None, description="操作系统过滤")
    
    # 任务过滤
    has_task_execution: Optional[bool] = Field(None, description="是否有任务执行")
    min_tasks_triggered: Optional[int] = Field(None, ge=0, description="最小触发任务数")
    max_tasks_triggered: Optional[int] = Field(None, ge=0, description="最大触发任务数")
    
    # 归档过滤
    archived: Optional[bool] = Field(None, description="是否已归档")
    
    @validator('response_status_code_range')
    def validate_response_status_code_range(cls, v):
        if v is not None:
            if len(v) != 2:
                raise ValueError('响应状态码范围必须包含两个值')
            if v[0] > v[1]:
                raise ValueError('响应状态码范围的第一个值必须小于等于第二个值')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookLogSort(BaseModel):
    """Webhook日志排序模式"""
    
    field: str = Field("created_at", description="排序字段")
    order: str = Field("desc", description="排序顺序")
    
    @validator('field')
    def validate_field(cls, v):
        allowed_fields = [
            'id', 'webhook_id', 'status', 'method', 'created_at', 'processed_at',
            'response_status_code', 'response_time_ms', 'processing_time_ms',
            'client_ip', 'tasks_triggered', 'security_level'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是以下之一: {", ".join(allowed_fields)}')
        return v
    
    @validator('order')
    def validate_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序顺序必须是asc或desc')
        return v.lower()