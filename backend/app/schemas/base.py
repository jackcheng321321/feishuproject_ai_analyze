"""基础Pydantic模式

定义通用的响应格式、分页结构和错误处理模式。
"""

from typing import Any, Dict, List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

# 泛型类型变量
T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模式"""
    
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """错误响应模式"""
    
    success: bool = Field(False, description="请求是否成功")
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginationInfo(BaseModel):
    """分页信息模式"""
    
    page: int = Field(1, ge=1, description="当前页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")
    total: int = Field(0, ge=0, description="总记录数")
    total_pages: int = Field(0, ge=0, description="总页数")
    has_next: bool = Field(False, description="是否有下一页")
    has_prev: bool = Field(False, description="是否有上一页")
    
    @classmethod
    def create(cls, page: int, page_size: int, total: int) -> 'PaginationInfo':
        """创建分页信息"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模式"""
    
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("", description="响应消息")
    data: List[T] = Field([], description="数据列表")
    pagination: PaginationInfo = Field(..., description="分页信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationError(BaseModel):
    """验证错误模式"""
    
    field: str = Field(..., description="字段名")
    message: str = Field(..., description="错误消息")
    value: Optional[Any] = Field(None, description="错误值")
    code: Optional[str] = Field(None, description="错误代码")


class ValidationErrorResponse(BaseModel):
    """验证错误响应模式"""
    
    success: bool = Field(False, description="请求是否成功")
    error_code: str = Field("VALIDATION_ERROR", description="错误代码")
    error_message: str = Field("数据验证失败", description="错误消息")
    validation_errors: List[ValidationError] = Field([], description="验证错误列表")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间戳")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """健康检查响应模式"""
    
    status: str = Field(..., description="健康状态")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="检查时间")
    version: Optional[str] = Field(None, description="版本信息")
    uptime: Optional[str] = Field(None, description="运行时间")
    checks: Dict[str, Any] = Field({}, description="各组件检查结果")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricsResponse(BaseModel):
    """指标响应模式"""
    
    metrics: Dict[str, Any] = Field({}, description="指标数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="指标时间")
    period: Optional[str] = Field(None, description="统计周期")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BulkOperationRequest(BaseModel):
    """批量操作请求模式"""
    
    ids: List[int] = Field(..., min_items=1, description="ID列表")
    operation: str = Field(..., description="操作类型")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")


class BulkOperationResponse(BaseModel):
    """批量操作响应模式"""
    
    success: bool = Field(True, description="操作是否成功")
    total: int = Field(..., description="总数量")
    successful: int = Field(..., description="成功数量")
    failed: int = Field(..., description="失败数量")
    results: List[Dict[str, Any]] = Field([], description="详细结果")
    errors: List[Dict[str, Any]] = Field([], description="错误信息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="操作时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SearchRequest(BaseModel):
    """搜索请求模式"""
    
    query: Optional[str] = Field(None, description="搜索关键词")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="排序方向")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")


class ExportRequest(BaseModel):
    """导出请求模式"""
    
    format: str = Field("csv", pattern="^(csv|xlsx|json)$", description="导出格式")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    fields: Optional[List[str]] = Field(None, description="导出字段")
    filename: Optional[str] = Field(None, description="文件名")


class ImportRequest(BaseModel):
    """导入请求模式"""
    
    file_path: str = Field(..., description="文件路径")
    format: str = Field("csv", pattern="^(csv|xlsx|json)$", description="文件格式")
    mapping: Optional[Dict[str, str]] = Field(None, description="字段映射")
    options: Optional[Dict[str, Any]] = Field(None, description="导入选项")


class TaskRequest(BaseModel):
    """任务请求模式"""
    
    task_type: str = Field(..., description="任务类型")
    parameters: Dict[str, Any] = Field({}, description="任务参数")
    priority: int = Field(0, description="优先级")
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskResponse(BaseModel):
    """任务响应模式"""
    
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConfigItem(BaseModel):
    """配置项模式"""
    
    key: str = Field(..., description="配置键")
    value: Any = Field(..., description="配置值")
    type: str = Field(..., description="配置类型")
    description: Optional[str] = Field(None, description="配置描述")
    required: bool = Field(False, description="是否必需")
    sensitive: bool = Field(False, description="是否敏感")


class LogEntry(BaseModel):
    """日志条目模式"""
    
    timestamp: datetime = Field(..., description="时间戳")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    module: Optional[str] = Field(None, description="模块名")
    function: Optional[str] = Field(None, description="函数名")
    line: Optional[int] = Field(None, description="行号")
    extra: Optional[Dict[str, Any]] = Field(None, description="额外信息")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StatisticsResponse(BaseModel):
    """统计响应模式"""
    
    period: str = Field(..., description="统计周期")
    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")
    data: Dict[str, Any] = Field({}, description="统计数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }