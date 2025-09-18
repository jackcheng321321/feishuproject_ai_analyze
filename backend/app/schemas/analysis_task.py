"""分析任务相关Pydantic模式

定义分析任务的创建、更新、响应等数据验证模式。
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    ARCHIVED = "archived"


class TriggerType(str, Enum):
    """触发类型枚举"""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    MANUAL = "manual"
    API = "api"
    FILE_WATCH = "file_watch"


class TaskPriority(str, Enum):
    """任务优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class FieldConfig(BaseModel):
    """单个字段配置"""
    field_key: str = Field(..., description="字段标识符")
    field_name: str = Field(..., description="字段显示名称")
    placeholder: str = Field(..., description="在提示词中的占位符名称")
    required: bool = Field(True, description="是否为必需字段")

    @validator('field_key', 'field_name', 'placeholder')
    def validate_non_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('字段不能为空')
        return v.strip()

    @validator('placeholder')
    def validate_placeholder_format(cls, v):
        # 确保占位符是有效的标识符格式
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('占位符只能包含字母、数字、下划线和连字符')
        return v


class MultiFieldConfig(BaseModel):
    """多字段配置模式"""
    fields: List[FieldConfig] = Field(..., description="字段配置列表", min_items=1)

    @validator('fields')
    def validate_unique_placeholders(cls, v):
        placeholders = [field.placeholder for field in v]
        if len(placeholders) != len(set(placeholders)):
            raise ValueError('占位符名称必须唯一')
        return v


class AnalysisTaskBase(BaseModel):
    """分析任务基础模式"""
    
    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    description: Optional[str] = Field(None, max_length=500, description="任务描述")
    trigger_type: TriggerType = Field(..., description="触发类型")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="任务优先级")
    
    # 触发配置
    trigger_config: Dict[str, Any] = Field({}, description="触发配置")
    
    # 数据解析配置
    data_parsing_config: Dict[str, Any] = Field({}, description="数据解析配置")
    
    # 文件获取配置
    file_acquisition_config: Optional[Dict[str, Any]] = Field(None, description="文件获取配置")
    
    # AI分析配置
    ai_analysis_config: Dict[str, Any] = Field({}, description="AI分析配置")
    
    # 结果写入配置
    result_writing_config: Dict[str, Any] = Field({}, description="结果写入配置")
    
    # 飞书集成配置
    feishu_config: Optional[Dict[str, Any]] = Field(None, description="飞书配置")
    
    # 执行参数
    timeout: int = Field(300, ge=30, le=3600, description="超时时间（秒）")
    max_retries: int = Field(3, ge=0, le=10, description="最大重试次数")
    retry_delay: int = Field(60, ge=1, le=3600, description="重试延迟（秒）")
    max_concurrency: int = Field(1, ge=1, le=10, description="最大并发数")
    
    # 资源限制
    max_memory_mb: Optional[int] = Field(None, ge=128, le=8192, description="最大内存（MB）")
    max_cpu_percent: Optional[int] = Field(None, ge=10, le=100, description="最大CPU使用率（%）")
    max_execution_time: Optional[int] = Field(None, ge=60, le=7200, description="最大执行时间（秒）")
    
    # 通知设置
    notify_on_success: bool = Field(False, description="成功时通知")
    notify_on_failure: bool = Field(True, description="失败时通知")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="通知配置")
    
    # 日志设置
    log_level: str = Field("INFO", description="日志级别")
    log_retention_days: int = Field(30, ge=1, le=365, description="日志保留天数")
    enable_detailed_logging: bool = Field(True, description="启用详细日志")
    
    # 其他设置
    tags: Optional[List[str]] = Field(None, description="标签")
    category: Optional[str] = Field(None, description="分类")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('任务名称不能为空')
        return v.strip()
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'日志级别必须是以下之一: {", ".join(allowed_levels)}')
        return v.upper()
    
    @validator('trigger_config')
    def validate_trigger_config(cls, v, values):
        trigger_type = values.get('trigger_type')
        if trigger_type == TriggerType.WEBHOOK:
            if 'webhook_id' not in v:
                raise ValueError('Webhook触发需要指定webhook_id')
        elif trigger_type == TriggerType.SCHEDULE:
            if 'cron_expression' not in v and 'interval_seconds' not in v:
                raise ValueError('定时触发需要指定cron_expression或interval_seconds')
        return v
    
    @validator('ai_analysis_config')
    def validate_ai_analysis_config(cls, v):
        if 'ai_model_id' not in v:
            raise ValueError('AI分析配置需要指定ai_model_id')
        if 'prompt_template' not in v:
            raise ValueError('AI分析配置需要指定prompt_template')
        return v


class AnalysisTaskCreate(BaseModel):
    """分析任务创建模式 - 简化版本"""
    
    # 基本信息
    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    display_name: Optional[str] = Field(None, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, max_length=500, description="任务描述")
    is_active: bool = Field(True, description="是否启用")
    
    # 核心配置
    ai_model_id: int = Field(..., description="AI模型ID")
    webhook_id: int = Field(..., description="Webhook ID")
    
    # 存储配置（可选）
    enable_storage_credential: bool = Field(False, description="是否启用存储凭证")
    storage_credential_id: Optional[int] = Field(None, description="存储凭证ID")
    
    # 富文本字段解析配置
    enable_rich_text_parsing: bool = Field(False, description="是否启用富文本字段解析")
    rich_text_config: Optional[Dict[str, Any]] = Field(None, description="富文本解析配置")

    # 多字段综合分析配置
    enable_multi_field_analysis: bool = Field(False, description="是否启用多字段综合分析")
    multi_field_config: Optional[Dict[str, Any]] = Field(None, description="多字段分析配置")

    # 分析配置
    analysis_prompt: str = Field(..., min_length=10, max_length=2000, description="分析提示词")
    temperature: float = Field(1.0, ge=0.0, le=2.0, description="AI温度参数")
    max_tokens: int = Field(10000, ge=100, le=32000, description="最大token数")
    
    # 数据写入配置
    feishu_write_config: Optional[Dict[str, Any]] = Field(None, description="飞书写入配置")
    
    # 系统字段
    trigger_type: TriggerType = Field(TriggerType.WEBHOOK, description="触发类型")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="任务优先级")
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('任务名称不能为空')
        return v.strip()
    
    @validator('storage_credential_id')
    def validate_storage_credential(cls, v, values):
        enable_storage = values.get('enable_storage_credential', False)
        if enable_storage and not v:
            raise ValueError('启用存储凭证时必须指定存储凭证ID')
        return v

    @validator('multi_field_config')
    def validate_multi_field_config(cls, v, values):
        enable_multi_field = values.get('enable_multi_field_analysis', False)
        if enable_multi_field and not v:
            raise ValueError('启用多字段分析时必须配置字段列表')
        if enable_multi_field and v:
            # 验证配置格式
            if not isinstance(v, dict) or 'fields' not in v:
                raise ValueError('多字段配置必须包含fields字段')
            if not isinstance(v['fields'], list) or len(v['fields']) == 0:
                raise ValueError('多字段配置必须包含至少一个字段')
            # 验证每个字段配置
            for field in v['fields']:
                if not isinstance(field, dict):
                    raise ValueError('字段配置必须是字典格式')
                required_keys = ['field_key', 'field_name', 'placeholder']
                for key in required_keys:
                    if key not in field or not field[key]:
                        raise ValueError(f'字段配置缺少必需的{key}字段')
        return v


class AnalysisTaskUpdate(BaseModel):
    """分析任务更新模式"""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="任务名称")
    description: Optional[str] = Field(None, max_length=500, description="任务描述")
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    priority: Optional[TaskPriority] = Field(None, description="任务优先级")
    
    # 触发配置
    trigger_config: Optional[Dict[str, Any]] = Field(None, description="触发配置")
    
    # 数据解析配置
    data_parsing_config: Optional[Dict[str, Any]] = Field(None, description="数据解析配置")
    
    # 文件获取配置
    file_acquisition_config: Optional[Dict[str, Any]] = Field(None, description="文件获取配置")
    
    # AI分析配置
    ai_analysis_config: Optional[Dict[str, Any]] = Field(None, description="AI分析配置")
    
    # 结果写入配置
    result_writing_config: Optional[Dict[str, Any]] = Field(None, description="结果写入配置")
    
    # 飞书集成配置
    feishu_config: Optional[Dict[str, Any]] = Field(None, description="飞书配置")
    
    # 执行参数
    timeout: Optional[int] = Field(None, ge=30, le=3600, description="超时时间（秒）")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    retry_delay: Optional[int] = Field(None, ge=1, le=3600, description="重试延迟（秒）")
    max_concurrency: Optional[int] = Field(None, ge=1, le=10, description="最大并发数")
    
    # 资源限制
    max_memory_mb: Optional[int] = Field(None, ge=128, le=8192, description="最大内存（MB）")
    max_cpu_percent: Optional[int] = Field(None, ge=10, le=100, description="最大CPU使用率（%）")
    max_execution_time: Optional[int] = Field(None, ge=60, le=7200, description="最大执行时间（秒）")
    
    # 通知设置
    notify_on_success: Optional[bool] = Field(None, description="成功时通知")
    notify_on_failure: Optional[bool] = Field(None, description="失败时通知")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="通知配置")
    
    # 日志设置
    log_level: Optional[str] = Field(None, description="日志级别")
    log_retention_days: Optional[int] = Field(None, ge=1, le=365, description="日志保留天数")
    enable_detailed_logging: Optional[bool] = Field(None, description="启用详细日志")
    
    # 共享设置
    is_shared: Optional[bool] = Field(None, description="是否共享")
    shared_users: Optional[List[int]] = Field(None, description="共享用户ID列表")
    
    # 其他设置
    tags: Optional[List[str]] = Field(None, description="标签")
    category: Optional[str] = Field(None, description="分类")
    notes: Optional[str] = Field(None, max_length=1000, description="备注")
    
    # 版本控制
    version_notes: Optional[str] = Field(None, max_length=500, description="版本说明")
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('任务名称不能为空')
        return v.strip() if v else v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        if v is not None:
            allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if v.upper() not in allowed_levels:
                raise ValueError(f'日志级别必须是以下之一: {", ".join(allowed_levels)}')
            return v.upper()
        return v


class AnalysisTaskResponse(AnalysisTaskBase):
    """分析任务响应模式"""
    
    id: int = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    creator_id: int = Field(..., description="创建者ID")
    is_shared: bool = Field(..., description="是否共享")
    shared_users: Optional[List[int]] = Field(None, description="共享用户ID列表")
    
    # 版本信息
    version: int = Field(..., description="版本号")
    version_notes: Optional[str] = Field(None, description="版本说明")
    
    # 统计信息
    total_executions: int = Field(0, description="总执行次数")
    successful_executions: int = Field(0, description="成功执行次数")
    failed_executions: int = Field(0, description="失败执行次数")
    average_execution_time: Optional[float] = Field(None, description="平均执行时间（秒）")
    total_tokens_used: int = Field(0, description="使用令牌总数")
    total_cost: float = Field(0.0, description="总成本")
    last_execution_at: Optional[datetime] = Field(None, description="最后执行时间")
    last_success_at: Optional[datetime] = Field(None, description="最后成功时间")
    last_failure_at: Optional[datetime] = Field(None, description="最后失败时间")
    
    # 健康状态
    health_status: Optional[str] = Field(None, description="健康状态")
    last_health_check_at: Optional[datetime] = Field(None, description="最后健康检查时间")
    health_check_error: Optional[str] = Field(None, description="健康检查错误")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisTaskTest(BaseModel):
    """分析任务测试模式"""

    test_data: Dict[str, Any] = Field({}, description="测试数据")
    dry_run: bool = Field(True, description="试运行模式")
    skip_file_acquisition: bool = Field(False, description="跳过文件获取")
    skip_result_writing: bool = Field(True, description="跳过结果写入")


class MultiFieldTestRequest(BaseModel):
    """多字段查询测试请求"""
    multi_field_config: MultiFieldConfig = Field(..., description="多字段配置")
    webhook_data: Dict[str, Any] = Field(..., description="Webhook数据（包含项目和工作项信息）")
    plugin_id: str = Field("", description="插件ID（从环境变量获取）")
    plugin_secret: str = Field("", description="插件密钥（从环境变量获取）")
    user_key: str = Field("", description="用户标识（从环境变量获取）")

    @validator('webhook_data')
    def validate_webhook_data(cls, v):
        """验证webhook数据包含必要字段"""
        required_fields = ['project_key', 'work_item_type_key', 'id']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'webhook数据缺少必需字段: {field}')
        return v


class MultiFieldTestResponse(BaseModel):
    """多字段查询测试响应"""
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    project_key: Optional[str] = Field(None, description="项目标识")
    work_item_id: Optional[str] = Field(None, description="工作项ID")
    work_item_type_key: Optional[str] = Field(None, description="工作项类型标识")
    field_data: Optional[Dict[str, Any]] = Field(None, description="查询到的字段数据")
    field_count: Optional[int] = Field(None, description="成功查询的字段数量")
    failed_fields: Optional[List[str]] = Field(None, description="查询失败的字段列表")
    query_details: Optional[List[Dict[str, Any]]] = Field(None, description="每个字段的查询详情")
    timestamp: Optional[str] = Field(None, description="查询时间戳")
    execution_time_ms: Optional[int] = Field(None, description="执行时间（毫秒）")
    error: Optional[str] = Field(None, description="错误信息")


class MultiFieldAnalysisTestRequest(BaseModel):
    """多字段综合分析测试请求"""
    task_id: int = Field(..., description="分析任务ID")
    webhook_data: Dict[str, Any] = Field(..., description="Webhook数据")
    override_prompt: Optional[str] = Field(None, description="覆盖分析提示词（可选）")
    dry_run: bool = Field(True, description="试运行模式（不写入结果）")

    @validator('webhook_data')
    def validate_webhook_data(cls, v):
        """验证webhook数据包含必要字段"""
        required_fields = ['project_key', 'work_item_type_key', 'id']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'webhook数据缺少必需字段: {field}')
        return v


class MultiFieldAnalysisTestResponse(BaseModel):
    """多字段综合分析测试响应"""
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    task_id: Optional[int] = Field(None, description="任务ID")
    task_name: Optional[str] = Field(None, description="任务名称")

    # 查询阶段结果
    field_query_success: Optional[bool] = Field(None, description="字段查询是否成功")
    field_data: Optional[Dict[str, Any]] = Field(None, description="查询到的字段数据")
    field_count: Optional[int] = Field(None, description="成功查询的字段数量")

    # 分析阶段结果
    ai_analysis_success: Optional[bool] = Field(None, description="AI分析是否成功")
    analysis_result: Optional[str] = Field(None, description="AI分析结果")
    rendered_prompt: Optional[str] = Field(None, description="渲染后的提示词")

    # 模型使用信息
    model_name: Optional[str] = Field(None, description="使用的AI模型")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token使用情况")

    # 执行统计
    total_execution_time_ms: Optional[int] = Field(None, description="总执行时间（毫秒）")
    field_query_time_ms: Optional[int] = Field(None, description="字段查询时间（毫秒）")
    ai_analysis_time_ms: Optional[int] = Field(None, description="AI分析时间（毫秒）")

    timestamp: Optional[str] = Field(None, description="执行时间戳")
    error: Optional[str] = Field(None, description="错误信息")
    details: Optional[str] = Field(None, description="详细信息")


class AnalysisTaskTestResponse(BaseModel):
    """分析任务测试响应模式"""
    
    success: bool = Field(..., description="是否成功")
    execution_id: Optional[str] = Field(None, description="执行ID")
    execution_time: Optional[float] = Field(None, description="执行时间（秒）")
    parsed_data: Optional[Dict[str, Any]] = Field(None, description="解析数据")
    ai_analysis_result: Optional[Dict[str, Any]] = Field(None, description="AI分析结果")
    tokens_used: Optional[int] = Field(None, description="使用令牌数")
    cost: Optional[float] = Field(None, description="成本")
    error_message: Optional[str] = Field(None, description="错误信息")
    logs: Optional[List[str]] = Field(None, description="日志")
    tested_at: datetime = Field(..., description="测试时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisTaskHealthCheck(BaseModel):
    """分析任务健康检查模式"""
    
    task_id: int = Field(..., description="任务ID")
    status: str = Field(..., description="状态")
    dependencies_status: Dict[str, str] = Field({}, description="依赖状态")
    configuration_valid: bool = Field(..., description="配置是否有效")
    error_message: Optional[str] = Field(None, description="错误信息")
    checked_at: datetime = Field(..., description="检查时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisTaskUsage(BaseModel):
    """分析任务使用情况模式"""
    
    task_id: int = Field(..., description="任务ID")
    task_name: str = Field(..., description="任务名称")
    executions_count: int = Field(0, description="执行次数")
    successful_executions: int = Field(0, description="成功执行次数")
    failed_executions: int = Field(0, description="失败执行次数")
    success_rate: float = Field(0.0, description="成功率")
    average_execution_time: Optional[float] = Field(None, description="平均执行时间")
    total_tokens_used: int = Field(0, description="使用令牌总数")
    total_cost: float = Field(0.0, description="总成本")
    last_execution_at: Optional[datetime] = Field(None, description="最后执行时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisTaskStats(BaseModel):
    """分析任务统计模式"""
    
    total_tasks: int = Field(0, description="总任务数")
    active_tasks: int = Field(0, description="活跃任务数")
    total_executions: int = Field(0, description="总执行次数")
    successful_executions: int = Field(0, description="成功执行次数")
    failed_executions: int = Field(0, description="失败执行次数")
    average_success_rate: float = Field(0.0, description="平均成功率")
    total_tokens_used: int = Field(0, description="使用令牌总数")
    total_cost: float = Field(0.0, description="总成本")
    average_execution_time: Optional[float] = Field(None, description="平均执行时间")
    most_active_task: Optional[str] = Field(None, description="最活跃任务")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisTaskVersion(BaseModel):
    """分析任务版本模式"""
    
    id: int = Field(..., description="版本ID")
    task_id: int = Field(..., description="任务ID")
    version: int = Field(..., description="版本号")
    version_notes: Optional[str] = Field(None, description="版本说明")
    config_snapshot: Dict[str, Any] = Field(..., description="配置快照")
    created_by: int = Field(..., description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisTaskClone(BaseModel):
    """分析任务克隆模式"""
    
    new_name: str = Field(..., min_length=1, max_length=100, description="新任务名称")
    clone_executions: bool = Field(False, description="克隆执行记录")
    clone_logs: bool = Field(False, description="克隆日志")
    reset_statistics: bool = Field(True, description="重置统计信息")
    
    @validator('new_name')
    def validate_new_name(cls, v):
        if not v.strip():
            raise ValueError('新任务名称不能为空')
        return v.strip()


class AnalysisTaskBatchOperation(BaseModel):
    """分析任务批量操作模式"""
    
    task_ids: List[int] = Field(..., min_items=1, description="任务ID列表")
    operation: str = Field(..., description="操作类型")
    parameters: Dict[str, Any] = Field({}, description="操作参数")
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = [
            'activate', 'deactivate', 'pause', 'archive', 'delete',
            'test', 'health_check', 'update_config', 'clone'
        ]
        if v not in allowed_operations:
            raise ValueError(f'操作类型必须是以下之一: {", ".join(allowed_operations)}')
        return v


class AnalysisTaskBatchOperationResponse(BaseModel):
    """分析任务批量操作响应模式"""
    
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


class AnalysisTaskMetrics(BaseModel):
    """分析任务指标模式"""
    
    task_id: int = Field(..., description="任务ID")
    date: datetime = Field(..., description="日期")
    executions_count: int = Field(0, description="执行次数")
    successful_executions: int = Field(0, description="成功执行次数")
    failed_executions: int = Field(0, description="失败执行次数")
    average_execution_time: float = Field(0.0, description="平均执行时间")
    total_tokens_used: int = Field(0, description="使用令牌总数")
    total_cost: float = Field(0.0, description="总成本")
    success_rate: float = Field(0.0, description="成功率")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisTaskFilter(BaseModel):
    """分析任务过滤器模式"""
    
    name: Optional[str] = Field(None, description="名称过滤")
    status: Optional[TaskStatus] = Field(None, description="状态过滤")
    trigger_type: Optional[TriggerType] = Field(None, description="触发类型过滤")
    priority: Optional[TaskPriority] = Field(None, description="优先级过滤")
    creator_id: Optional[int] = Field(None, description="创建者ID过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    category: Optional[str] = Field(None, description="分类过滤")
    is_shared: Optional[bool] = Field(None, description="共享状态过滤")
    created_after: Optional[datetime] = Field(None, description="创建时间之后")
    created_before: Optional[datetime] = Field(None, description="创建时间之前")
    last_execution_after: Optional[datetime] = Field(None, description="最后执行时间之后")
    last_execution_before: Optional[datetime] = Field(None, description="最后执行时间之前")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisTaskSort(BaseModel):
    """分析任务排序模式"""
    
    field: str = Field("created_at", description="排序字段")
    order: str = Field("desc", description="排序顺序")
    
    @validator('field')
    def validate_field(cls, v):
        allowed_fields = [
            'id', 'name', 'status', 'priority', 'created_at', 'updated_at',
            'last_execution_at', 'total_executions', 'successful_executions',
            'failed_executions', 'success_rate', 'average_execution_time',
            'total_cost', 'total_tokens_used'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是以下之一: {", ".join(allowed_fields)}')
        return v
    
    @validator('order')
    def validate_order(cls, v):
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('排序顺序必须是asc或desc')
        return v.lower()


class TaskConfigurationWizard(BaseModel):
    """任务配置向导"""
    
    name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    webhook_id: int = Field(..., description="关联的Webhook ID")
    ai_model_id: int = Field(..., description="关联的AI模型ID")
    storage_credential_id: Optional[int] = Field(None, description="关联的存储凭证ID（可选）")
    trigger_type: TriggerType = Field(TriggerType.MANUAL, description="触发类型")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="任务优先级")
    data_extraction_config: Dict[str, Any] = Field(default_factory=dict, description="数据提取配置")
    ai_analysis_config: Dict[str, Any] = Field(default_factory=dict, description="AI分析配置")
    result_output_config: Dict[str, Any] = Field(default_factory=dict, description="结果输出配置")


class TaskValidationResult(BaseModel):
    """任务验证结果"""
    
    is_valid: bool = Field(..., description="是否验证通过")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    errors: List[str] = Field(default_factory=list, description="错误信息")
    suggestions: List[str] = Field(default_factory=list, description="建议")
    estimated_cost: Optional[float] = Field(None, description="预估成本")
    estimated_execution_time: Optional[int] = Field(None, description="预估执行时间(秒)")
    configuration_summary: Dict[str, Any] = Field(default_factory=dict, description="配置摘要")


class FeishuWriteConfig(BaseModel):
    """飞书数据写入配置"""
    
    # API配置
    api_url: str = Field(..., description="飞书API地址")
    api_method: str = Field("POST", description="请求方法")
    
    # 认证配置
    auth_type: str = Field("bearer", description="认证类型")
    auth_token: Optional[str] = Field(None, description="认证令牌")
    app_id: Optional[str] = Field(None, description="应用ID")
    app_secret: Optional[str] = Field(None, description="应用密钥")
    
    # 数据映射配置
    field_id: str = Field(..., description="要更新的字段ID")
    record_id_field: str = Field("payload.id", description="记录ID字段路径")
    analysis_result_field: str = Field("analysis_result", description="分析结果字段名")
    
    # 请求模板
    request_template: Dict[str, Any] = Field(default_factory=dict, description="请求模板")
    headers: Dict[str, str] = Field(default_factory=dict, description="请求头")
    
    # 错误处理
    retry_times: int = Field(3, ge=0, le=10, description="重试次数")
    retry_delay: int = Field(5, ge=1, le=300, description="重试延迟(秒)")
    
    @validator('api_method')
    def validate_api_method(cls, v):
        allowed_methods = ['GET', 'POST', 'PUT', 'PATCH']
        if v.upper() not in allowed_methods:
            raise ValueError(f'请求方法必须是以下之一: {", ".join(allowed_methods)}')
        return v.upper()
    
    @validator('auth_type')
    def validate_auth_type(cls, v):
        allowed_types = ['bearer', 'basic', 'api_key', 'oauth2']
        if v.lower() not in allowed_types:
            raise ValueError(f'认证类型必须是以下之一: {", ".join(allowed_types)}')
        return v.lower()


class WebhookDataExtract(BaseModel):
    """Webhook数据提取配置"""
    
    field_value_path: str = Field("payload.changed_fields.pre_field_value", description="字段值提取路径")
    record_id_path: str = Field("payload.id", description="记录ID提取路径")
    
    # 数据处理选项
    trim_whitespace: bool = Field(True, description="是否去除首尾空格")
    max_field_length: Optional[int] = Field(None, ge=1, description="字段值最大长度")
    
    @validator('field_value_path', 'record_id_path')
    def validate_path(cls, v):
        if not v or not v.startswith(('payload.', '$.')):
            raise ValueError('路径必须以payload.或$.开头')
        return v


class TaskLogConfig(BaseModel):
    """任务日志配置"""
    
    # 日志级别
    log_level: str = Field("INFO", description="日志级别")
    
    # 记录内容
    log_webhook_data: bool = Field(True, description="记录Webhook原始数据")
    log_extracted_fields: bool = Field(True, description="记录提取的字段")
    log_ai_request: bool = Field(True, description="记录AI请求")
    log_ai_response: bool = Field(True, description="记录AI响应")
    log_write_result: bool = Field(True, description="记录写入结果")
    
    # 日志保留
    retention_days: int = Field(30, ge=1, le=365, description="日志保留天数")
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'日志级别必须是以下之一: {", ".join(allowed_levels)}')
        return v.upper()


class MultiFieldQueryRequest(BaseModel):
    """多字段查询请求模式"""
    webhook_data: Dict[str, Any] = Field(..., description="webhook数据")
    additional_fields: List[str] = Field(..., description="要查询的额外字段列表")
    plugin_id: str = Field("", description="插件ID")
    plugin_secret: str = Field("", description="插件密钥")
    user_key: str = Field("", description="用户密钥")


class MultiFieldAiAnalysisRequest(BaseModel):
    """多字段AI分析请求模式"""
    ai_model_id: int = Field(..., description="AI模型ID")
    prompt_template: str = Field(..., description="提示词模板")
    field_data: Dict[str, Any] = Field(..., description="字段数据")
    temperature: float = Field(1.0, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(10000, ge=100, le=32000, description="最大Token数")


class MultiFieldQueryResponse(BaseModel):
    """多字段查询响应模式"""
    success: bool = Field(..., description="是否成功")
    field_data: Dict[str, Any] = Field(..., description="查询到的字段数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    query_time: Optional[float] = Field(None, description="查询耗时（秒）")


class MultiFieldAiAnalysisResponse(BaseModel):
    """多字段AI分析响应模式"""
    success: bool = Field(..., description="是否成功")
    analysis_result: Optional[str] = Field(None, description="分析结果")
    rendered_prompt: Optional[str] = Field(None, description="渲染后的提示词")
    tokens_used: Optional[int] = Field(None, description="使用的Token数")
    cost: Optional[float] = Field(None, description="成本")
    error_message: Optional[str] = Field(None, description="错误信息")
    analysis_time: Optional[float] = Field(None, description="分析耗时（秒）")


class AnalysisTaskSimpleResponse(BaseModel):
    """分析任务简化响应模式 - 与数据库字段完全匹配"""
    
    # 基本信息
    id: int = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="任务描述")
    
    # 状态信息
    status: str = Field(..., description="任务状态")
    trigger_type: str = Field(..., description="触发类型")
    is_active: bool = Field(True, description="是否启用")
    
    # 关联信息
    webhook_id: Optional[int] = Field(None, description="Webhook ID")
    ai_model_id: Optional[int] = Field(None, description="AI模型ID")
    storage_credential_id: Optional[int] = Field(None, description="存储凭证ID")
    
    # 关联对象信息（用于前端显示）
    webhook: Optional[Dict[str, Any]] = Field(None, description="关联的Webhook信息")
    ai_model: Optional[Dict[str, Any]] = Field(None, description="关联的AI模型信息")
    storage_credential: Optional[Dict[str, Any]] = Field(None, description="关联的存储凭证信息")
    
    # 配置信息
    temperature: Optional[float] = Field(None, description="AI温度参数")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    enable_rich_text_parsing: bool = Field(False, description="是否启用富文本解析")
    enable_multi_field_analysis: bool = Field(False, description="是否启用多字段综合分析")
    multi_field_config: Optional[Dict[str, Any]] = Field(None, description="多字段分析配置")
    
    # 分析配置字段 - 添加缺失的字段
    analysis_prompt: str = Field("", description="分析提示词")
    data_extraction_config: Dict[str, Any] = Field(default_factory=dict, description="数据提取配置")
    prompt_template: str = Field("", description="提示词模板")
    feishu_config: Dict[str, Any] = Field(default_factory=dict, description="飞书配置")
    field_mapping: Dict[str, Any] = Field(default_factory=dict, description="字段映射")
    feishu_write_config: Dict[str, Any] = Field(default_factory=dict, description="飞书写入配置")
    
    # 统计信息
    total_executions: int = Field(0, description="总执行次数")
    successful_executions: int = Field(0, description="成功执行次数")  
    failed_executions: int = Field(0, description="失败执行次数")
    last_executed_at: Optional[datetime] = Field(None, description="最后执行时间")
    
    # 系统字段
    created_by: Optional[int] = Field(None, description="创建者ID")
    priority: int = Field(0, description="优先级")
    tags: Optional[str] = Field(None, description="标签")
    version: int = Field(1, description="版本号")
    
    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }