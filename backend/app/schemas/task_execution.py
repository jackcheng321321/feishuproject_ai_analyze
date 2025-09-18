"""任务执行相关Pydantic模式

定义任务执行的创建、更新、响应等数据验证模式。
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    RETRY = "retry"


class ExecutionStep(str, Enum):
    """执行步骤枚举"""
    INIT = "init"
    PARSE_DATA = "parse_data"
    ACQUIRE_FILES = "acquire_files"
    AI_ANALYSIS = "ai_analysis"
    WRITE_RESULT = "write_result"
    NOTIFY = "notify"
    CLEANUP = "cleanup"
    COMPLETE = "complete"


class TriggerSource(str, Enum):
    """触发源枚举"""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    API = "api"
    RETRY = "retry"
    SYSTEM = "system"


class TaskExecutionBase(BaseModel):
    """任务执行基础模式"""
    
    task_id: int = Field(..., description="任务ID")
    batch_id: Optional[str] = Field(None, description="批次ID")
    parent_execution_id: Optional[str] = Field(None, description="父执行ID")
    trigger_source: TriggerSource = Field(..., description="触发源")
    trigger_data: Optional[Dict[str, Any]] = Field(None, description="触发数据")
    priority: int = Field(0, ge=-10, le=10, description="优先级")
    
    # 执行环境
    execution_environment: Optional[Dict[str, Any]] = Field(None, description="执行环境")
    queue_name: Optional[str] = Field(None, description="队列名称")
    worker_id: Optional[str] = Field(None, description="工作器ID")
    
    # 标签和元数据
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    @validator('trigger_data')
    def validate_trigger_data(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('触发数据必须是字典格式')
        return v
    
    @validator('execution_environment')
    def validate_execution_environment(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('执行环境必须是字典格式')
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('元数据必须是字典格式')
        return v


class TaskExecutionCreate(TaskExecutionBase):
    """任务执行创建模式"""
    
    # 执行配置快照
    task_config_snapshot: Dict[str, Any] = Field({}, description="任务配置快照")
    
    # 调度信息
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")
    
    @validator('task_config_snapshot')
    def validate_task_config_snapshot(cls, v):
        if not isinstance(v, dict):
            raise ValueError('任务配置快照必须是字典格式')
        return v


class TaskExecutionUpdate(BaseModel):
    """任务执行更新模式"""
    
    status: Optional[ExecutionStatus] = Field(None, description="执行状态")
    current_step: Optional[ExecutionStep] = Field(None, description="当前步骤")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100, description="进度百分比")
    
    # 解析数据
    parsed_data: Optional[Dict[str, Any]] = Field(None, description="解析数据")
    
    # 文件处理信息
    files_info: Optional[List[Dict[str, Any]]] = Field(None, description="文件信息")
    
    # AI分析信息
    ai_model_used: Optional[str] = Field(None, description="使用的AI模型")
    input_tokens: Optional[int] = Field(None, ge=0, description="输入令牌数")
    output_tokens: Optional[int] = Field(None, ge=0, description="输出令牌数")
    total_tokens: Optional[int] = Field(None, ge=0, description="总令牌数")
    ai_cost: Optional[float] = Field(None, ge=0, description="AI成本")
    
    # 分析结果
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="分析结果")
    
    # 写入状态
    write_status: Optional[str] = Field(None, description="写入状态")
    write_details: Optional[Dict[str, Any]] = Field(None, description="写入详情")
    
    # 时间信息
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    # 重试信息
    retry_count: Optional[int] = Field(None, ge=0, description="重试次数")
    max_retries: Optional[int] = Field(None, ge=0, description="最大重试次数")
    next_retry_at: Optional[datetime] = Field(None, description="下次重试时间")
    
    # 资源使用
    memory_usage_mb: Optional[float] = Field(None, ge=0, description="内存使用（MB）")
    cpu_usage_percent: Optional[float] = Field(None, ge=0, le=100, description="CPU使用率（%）")
    execution_time_seconds: Optional[float] = Field(None, ge=0, description="执行时间（秒）")
    
    # 通知状态
    notification_sent: Optional[bool] = Field(None, description="是否已发送通知")
    notification_details: Optional[Dict[str, Any]] = Field(None, description="通知详情")
    
    @validator('parsed_data')
    def validate_parsed_data(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('解析数据必须是字典格式')
        return v
    
    @validator('analysis_result')
    def validate_analysis_result(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('分析结果必须是字典格式')
        return v
    
    @validator('error_details')
    def validate_error_details(cls, v):
        if v is not None and not isinstance(v, dict):
            raise ValueError('错误详情必须是字典格式')
        return v


class TaskExecutionResponse(TaskExecutionBase):
    """任务执行响应模式"""
    
    id: str = Field(..., description="执行ID")
    status: ExecutionStatus = Field(..., description="执行状态")
    current_step: ExecutionStep = Field(..., description="当前步骤")
    progress_percentage: int = Field(0, description="进度百分比")
    
    # 任务配置快照
    task_config_snapshot: Dict[str, Any] = Field({}, description="任务配置快照")
    
    # 解析数据
    parsed_data: Optional[Dict[str, Any]] = Field(None, description="解析数据")
    
    # 文件处理信息
    files_info: Optional[List[Dict[str, Any]]] = Field(None, description="文件信息")
    
    # AI分析信息
    ai_model_used: Optional[str] = Field(None, description="使用的AI模型")
    input_tokens: Optional[int] = Field(None, description="输入令牌数")
    output_tokens: Optional[int] = Field(None, description="输出令牌数")
    total_tokens: Optional[int] = Field(None, description="总令牌数")
    ai_cost: Optional[float] = Field(None, description="AI成本")
    
    # 分析结果
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="分析结果")
    
    # 写入状态
    write_status: Optional[str] = Field(None, description="写入状态")
    write_details: Optional[Dict[str, Any]] = Field(None, description="写入详情")
    
    # 时间信息
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    # 重试信息
    retry_count: int = Field(0, description="重试次数")
    max_retries: int = Field(0, description="最大重试次数")
    next_retry_at: Optional[datetime] = Field(None, description="下次重试时间")
    
    # 资源使用
    memory_usage_mb: Optional[float] = Field(None, description="内存使用（MB）")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU使用率（%）")
    execution_time_seconds: Optional[float] = Field(None, description="执行时间（秒）")
    
    # 日志条目
    log_entries: Optional[List[Dict[str, Any]]] = Field(None, description="日志条目")
    
    # 通知状态
    notification_sent: bool = Field(False, description="是否已发送通知")
    notification_details: Optional[Dict[str, Any]] = Field(None, description="通知详情")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskExecutionSummary(BaseModel):
    """任务执行摘要模式"""
    
    id: str = Field(..., description="执行ID")
    task_id: int = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    status: ExecutionStatus = Field(..., description="执行状态")
    current_step: ExecutionStep = Field(..., description="当前步骤")
    progress_percentage: int = Field(0, description="进度百分比")
    trigger_source: TriggerSource = Field(..., description="触发源")
    
    # 时间信息
    scheduled_at: Optional[datetime] = Field(None, description="计划执行时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    execution_time_seconds: Optional[float] = Field(None, description="执行时间（秒）")
    
    # 基本统计
    total_tokens: Optional[int] = Field(None, description="总令牌数")
    ai_cost: Optional[float] = Field(None, description="AI成本")
    retry_count: int = Field(0, description="重试次数")
    
    # 错误信息（仅在失败时）
    error_message: Optional[str] = Field(None, description="错误信息")
    
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskExecutionCancel(BaseModel):
    """任务执行取消模式"""
    
    reason: Optional[str] = Field(None, max_length=500, description="取消原因")
    force: bool = Field(False, description="强制取消")


class TaskExecutionRetry(BaseModel):
    """任务执行重试模式"""
    
    reason: Optional[str] = Field(None, max_length=500, description="重试原因")
    reset_retry_count: bool = Field(False, description="重置重试计数")
    delay_seconds: Optional[int] = Field(None, ge=0, le=3600, description="延迟秒数")


class TaskExecutionLog(BaseModel):
    """任务执行日志模式"""
    
    execution_id: str = Field(..., description="执行ID")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    step: Optional[ExecutionStep] = Field(None, description="执行步骤")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    timestamp: datetime = Field(..., description="时间戳")
    
    @validator('level')
    def validate_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'日志级别必须是以下之一: {", ".join(allowed_levels)}')
        return v.upper()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskExecutionMetrics(BaseModel):
    """任务执行指标模式"""
    
    execution_id: str = Field(..., description="执行ID")
    task_id: int = Field(..., description="任务ID")
    
    # 性能指标
    execution_time_seconds: float = Field(..., description="执行时间（秒）")
    memory_usage_mb: Optional[float] = Field(None, description="内存使用（MB）")
    cpu_usage_percent: Optional[float] = Field(None, description="CPU使用率（%）")
    
    # AI指标
    input_tokens: Optional[int] = Field(None, description="输入令牌数")
    output_tokens: Optional[int] = Field(None, description="输出令牌数")
    total_tokens: Optional[int] = Field(None, description="总令牌数")
    ai_cost: Optional[float] = Field(None, description="AI成本")
    
    # 文件处理指标
    files_processed: Optional[int] = Field(None, description="处理文件数")
    bytes_processed: Optional[int] = Field(None, description="处理字节数")
    
    # 状态指标
    success: bool = Field(..., description="是否成功")
    retry_count: int = Field(0, description="重试次数")
    
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskExecutionStats(BaseModel):
    """任务执行统计模式"""
    
    total_executions: int = Field(0, description="总执行次数")
    successful_executions: int = Field(0, description="成功执行次数")
    failed_executions: int = Field(0, description="失败执行次数")
    cancelled_executions: int = Field(0, description="取消执行次数")
    running_executions: int = Field(0, description="运行中执行次数")
    pending_executions: int = Field(0, description="待执行次数")
    
    # 成功率
    success_rate: float = Field(0.0, description="成功率")
    
    # 时间统计
    average_execution_time: Optional[float] = Field(None, description="平均执行时间")
    min_execution_time: Optional[float] = Field(None, description="最小执行时间")
    max_execution_time: Optional[float] = Field(None, description="最大执行时间")
    
    # 资源统计
    total_tokens_used: int = Field(0, description="使用令牌总数")
    total_cost: float = Field(0.0, description="总成本")
    average_memory_usage: Optional[float] = Field(None, description="平均内存使用")
    average_cpu_usage: Optional[float] = Field(None, description="平均CPU使用")
    
    # 重试统计
    total_retries: int = Field(0, description="总重试次数")
    average_retries: float = Field(0.0, description="平均重试次数")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskExecutionBatchOperation(BaseModel):
    """任务执行批量操作模式"""
    
    execution_ids: List[str] = Field(..., min_items=1, description="执行ID列表")
    operation: str = Field(..., description="操作类型")
    parameters: Dict[str, Any] = Field({}, description="操作参数")
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['cancel', 'retry', 'delete', 'archive']
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(allowed_operations)}')
        return v


class TaskExecutionBatchOperationResponse(BaseModel):
    """任务执行批量操作响应模式"""
    
    operation: str = Field(..., description="操作类型")
    total_processed: int = Field(..., description="处理总数")
    successful_operations: int = Field(..., description="成功操作数")
    failed_operations: int = Field(..., description="失败操作数")
    results: List[Dict[str, Any]] = Field(..., description="结果列表")
    executed_at: datetime = Field(..., description="执行时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskExecutionFilter(BaseModel):
    """任务执行过滤器模式"""
    
    task_id: Optional[int] = Field(None, description="任务ID过滤")
    status: Optional[ExecutionStatus] = Field(None, description="状态过滤")
    trigger_source: Optional[TriggerSource] = Field(None, description="触发源过滤")
    batch_id: Optional[str] = Field(None, description="批次ID过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    
    # 时间过滤
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    started_after: Optional[datetime] = Field(None, description="开始时间之后")
    started_before: Optional[datetime] = Field(None, description="开始时间之前")
    completed_after: Optional[datetime] = Field(None, description="完成时间之后")
    completed_before: Optional[datetime] = Field(None, description="完成时间之前")
    
    # 性能过滤
    min_execution_time: Optional[float] = Field(None, ge=0, description="最小执行时间")
    max_execution_time: Optional[float] = Field(None, ge=0, description="最大执行时间")
    min_tokens: Optional[int] = Field(None, ge=0, description="最小令牌数")
    max_tokens: Optional[int] = Field(None, ge=0, description="最大令牌数")
    min_cost: Optional[float] = Field(None, ge=0, description="最小成本")
    max_cost: Optional[float] = Field(None, ge=0, description="最大成本")
    
    # 错误过滤
    has_error: Optional[bool] = Field(None, description="是否有错误")
    error_code: Optional[str] = Field(None, description="错误代码过滤")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskExecutionSort(BaseModel):
    """任务执行排序模式"""
    
    field: str = Field("created_at", description="排序字段")
    order: str = Field("desc", description="排序顺序")
    
    @validator('field')
    def validate_field(cls, v):
        allowed_fields = [
            'id', 'task_id', 'status', 'created_at', 'started_at', 'completed_at',
            'execution_time_seconds', 'total_tokens', 'ai_cost', 'retry_count',
            'progress_percentage', 'priority'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是以下之一: {", ".join(allowed_fields)}')
        return v
    
    @validator('order')
    def validate_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序顺序必须是asc或desc')
        return v.lower()


class ExecutionDetailResponse(BaseModel):
    """任务执行详情响应"""
    
    execution: TaskExecutionResponse = Field(..., description="任务执行基本信息")
    logs: List[TaskExecutionLog] = Field(default_factory=list, description="执行日志")
    metrics: TaskExecutionMetrics = Field(..., description="执行指标")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    performance_stats: Optional[Dict[str, Any]] = Field(None, description="性能统计")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")