from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    DRAFT = "draft"          # 草稿
    ACTIVE = "active"        # 激活
    PAUSED = "paused"        # 暂停
    DISABLED = "disabled"    # 禁用
    ARCHIVED = "archived"    # 归档


class TriggerType(str, enum.Enum):
    """触发器类型枚举"""
    WEBHOOK = "webhook"      # Webhook触发
    SCHEDULE = "schedule"    # 定时触发
    MANUAL = "manual"        # 手动触发
    API = "api"              # API触发


class AnalysisTask(Base):
    """分析任务模型"""
    
    __tablename__ = "analysis_tasks"
    
    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    name = Column(String(100), nullable=False, comment="任务名称")
    display_name = Column(String(200), comment="显示名称")
    description = Column(Text, comment="任务描述")
    
    # 任务状态
    status = Column(
        SQLEnum(TaskStatus), 
        default=TaskStatus.DRAFT, 
        comment="任务状态"
    )
    
    # 触发器配置
    trigger_type = Column(
        SQLEnum(TriggerType), 
        default=TriggerType.WEBHOOK, 
        comment="触发器类型"
    )
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), comment="关联的Webhook ID")
    schedule_config = Column(JSON, comment="定时任务配置")
    
    # 数据解析配置
    data_parsing_config = Column(JSON, comment="数据解析配置")
    jsonpath_rules = Column(JSON, comment="JSONPath提取规则")
    data_validation_rules = Column(JSON, comment="数据验证规则")
    
    # 数据库必需字段（与实际schema匹配）
    data_extraction_config = Column(JSON, nullable=False, default={}, comment="数据提取配置")
    prompt_template = Column(Text, nullable=False, comment="提示词模板")
    
    # 文件获取配置（可选）
    enable_storage_credential = Column(Boolean, default=False, comment="是否启用存储凭证")
    storage_credential_id = Column(Integer, ForeignKey("storage_credentials.id"), comment="存储凭证ID")
    file_path_template = Column(String(500), comment="文件路径模板")
    file_filters = Column(JSON, comment="文件过滤器")
    download_config = Column(JSON, comment="下载配置")
    
    # AI分析配置
    ai_model_id = Column(Integer, ForeignKey("ai_models.id"), comment="AI模型ID")
    system_prompt = Column(Text, comment="系统提示词")
    user_prompt_template = Column(Text, comment="用户提示词模板")
    analysis_config = Column(JSON, comment="分析配置")
    temperature = Column(Numeric(3, 2), default=0.7, comment="AI温度参数")
    max_tokens = Column(Integer, default=4000, comment="最大token数")
    
    # 结果回写配置
    result_config = Column(JSON, comment="结果配置")
    feishu_config = Column(JSON, comment="飞书配置")
    feishu_write_config = Column(JSON, comment="飞书写入配置")
    field_mapping = Column(JSON, comment="字段映射")
    
    # Webhook数据提取配置
    webhook_data_extract = Column(JSON, comment="Webhook数据提取配置")
    
    # 富文本字段解析配置
    enable_rich_text_parsing = Column(Boolean, default=False, comment="是否启用富文本字段解析")
    rich_text_config = Column(JSON, comment="富文本解析配置")

    # 多字段综合分析配置
    enable_multi_field_analysis = Column(Boolean, default=False, comment="是否启用多字段综合分析")
    multi_field_config = Column(JSON, comment="多字段分析配置")
    
    # 执行配置
    timeout_seconds = Column(Integer, default=3600, comment="超时时间（秒）")
    max_retry_attempts = Column(Integer, default=3, comment="最大重试次数")
    retry_delay_seconds = Column(Integer, default=60, comment="重试延迟（秒）")
    
    # 并发控制
    max_concurrent_executions = Column(Integer, default=1, comment="最大并发执行数")
    queue_priority = Column(Integer, default=0, comment="队列优先级")
    
    # 资源限制
    max_file_size = Column(Integer, comment="最大文件大小（字节）")
    max_processing_time = Column(Integer, comment="最大处理时间（秒）")
    max_memory_usage = Column(Integer, comment="最大内存使用（MB）")
    
    # 通知配置
    notification_config = Column(JSON, comment="通知配置")
    success_notification = Column(Boolean, default=False, comment="成功时通知")
    failure_notification = Column(Boolean, default=True, comment="失败时通知")
    notification_emails = Column(JSON, comment="通知邮箱列表")
    
    # 日志配置
    log_level = Column(String(20), default="INFO", comment="日志级别")
    log_retention_days = Column(Integer, default=30, comment="日志保留天数")
    detailed_logging = Column(Boolean, default=False, comment="是否详细日志")
    
    # 版本控制
    version = Column(Integer, default=1, comment="版本号")
    parent_task_id = Column(Integer, ForeignKey("analysis_tasks.id"), comment="父任务ID")
    is_template = Column(Boolean, default=False, comment="是否为模板")
    
    # 创建者和权限
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建者ID（可空，支持无用户认证模式）")
    shared_with_users = Column(JSON, comment="共享用户列表")
    is_public = Column(Boolean, default=False, comment="是否公开")
    
    # 统计信息
    total_executions = Column(Integer, default=0, comment="总执行次数")
    successful_executions = Column(Integer, default=0, comment="成功执行次数")
    failed_executions = Column(Integer, default=0, comment="失败执行次数")
    avg_execution_time = Column(Integer, default=0, comment="平均执行时间（秒）")
    total_tokens_used = Column(Integer, default=0, comment="总使用token数")
    total_cost = Column(Numeric(10, 2), default=0.0, comment="总成本")
    
    # 最后执行信息
    last_execution_at = Column(DateTime(timezone=True), comment="最后执行时间")
    last_success_at = Column(DateTime(timezone=True), comment="最后成功时间")
    last_failure_at = Column(DateTime(timezone=True), comment="最后失败时间")
    last_execution_status = Column(String(20), comment="最后执行状态")
    last_execution_message = Column(Text, comment="最后执行消息")
    
    # 健康检查
    health_check_enabled = Column(Boolean, default=True, comment="是否启用健康检查")
    health_status = Column(String(20), default="unknown", comment="健康状态")
    health_message = Column(Text, comment="健康检查消息")
    
    # 标签和分类
    tags = Column(JSON, comment="标签")
    category = Column(String(50), comment="分类")
    priority = Column(Integer, default=0, comment="优先级")  # 0=normal, 1=high, 2=urgent
    
    # 备注信息
    notes = Column(Text, comment="备注")
    changelog = Column(JSON, comment="变更日志")
    
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
    webhook = relationship("Webhook", back_populates="analysis_tasks")
    storage_credential = relationship("StorageCredential")
    ai_model = relationship("AIModel")
    creator = relationship("User")
    parent_task = relationship("AnalysisTask", remote_side=[id])
    child_tasks = relationship("AnalysisTask", back_populates="parent_task")
    task_executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    def to_dict(self, include_config=True):
        """转换为字典"""
        data = {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "trigger_type": self.trigger_type.value if self.trigger_type else None,
            "webhook_id": self.webhook_id,
            "enable_storage_credential": self.enable_storage_credential,
            "storage_credential_id": self.storage_credential_id,
            "ai_model_id": self.ai_model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "max_retry_attempts": self.max_retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "max_concurrent_executions": self.max_concurrent_executions,
            "queue_priority": self.queue_priority,
            "max_file_size": self.max_file_size,
            "max_processing_time": self.max_processing_time,
            "max_memory_usage": self.max_memory_usage,
            "success_notification": self.success_notification,
            "failure_notification": self.failure_notification,
            "notification_emails": self.notification_emails,
            "log_level": self.log_level,
            "log_retention_days": self.log_retention_days,
            "detailed_logging": self.detailed_logging,
            "version": self.version,
            "parent_task_id": self.parent_task_id,
            "is_template": self.is_template,
            "created_by": self.created_by,
            "shared_with_users": self.shared_with_users,
            "is_public": self.is_public,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "avg_execution_time": self.avg_execution_time,
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "last_execution_at": self.last_execution_at.isoformat() if self.last_execution_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "last_execution_status": self.last_execution_status,
            "last_execution_message": self.last_execution_message,
            "health_check_enabled": self.health_check_enabled,
            "health_status": self.health_status,
            "health_message": self.health_message,
            "tags": self.tags,
            "category": self.category,
            "priority": self.priority,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 配置信息只在需要时包含
        if include_config:
            data.update({
                "schedule_config": self.schedule_config,
                "data_parsing_config": self.data_parsing_config,
                "jsonpath_rules": self.jsonpath_rules,
                "data_validation_rules": self.data_validation_rules,
                "data_extraction_config": self.data_extraction_config,
                "prompt_template": self.prompt_template,
                "file_path_template": self.file_path_template,
                "file_filters": self.file_filters,
                "download_config": self.download_config,
                "system_prompt": self.system_prompt,
                "user_prompt_template": self.user_prompt_template,
                "analysis_config": self.analysis_config,
                "result_config": self.result_config,
                "feishu_config": self.feishu_config,
                "feishu_write_config": self.feishu_write_config,
                "field_mapping": self.field_mapping,
                "webhook_data_extract": self.webhook_data_extract,
                "enable_rich_text_parsing": self.enable_rich_text_parsing,
                "rich_text_config": self.rich_text_config,
                "enable_multi_field_analysis": self.enable_multi_field_analysis,
                "multi_field_config": self.multi_field_config,
                "notification_config": self.notification_config,
                "changelog": self.changelog,
            })
        
        return data
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100
    
    def get_failure_rate(self) -> float:
        """获取失败率"""
        if self.total_executions == 0:
            return 0.0
        return (self.failed_executions / self.total_executions) * 100
    
    def update_execution_stats(self, success: bool, execution_time: float = 0.0, tokens_used: int = 0, cost: float = 0.0):
        """更新执行统计"""
        from datetime import datetime
        
        self.total_executions += 1
        
        if success:
            self.successful_executions += 1
            self.last_success_at = datetime.utcnow()
            self.last_execution_status = "success"
        else:
            self.failed_executions += 1
            self.last_failure_at = datetime.utcnow()
            self.last_execution_status = "failed"
        
        self.last_execution_at = datetime.utcnow()
        
        # 更新平均执行时间
        if execution_time > 0:
            current_avg = float(self.avg_execution_time) if self.avg_execution_time else 0.0
            new_avg = ((current_avg * (self.total_executions - 1)) + execution_time) / self.total_executions
            self.avg_execution_time = int(new_avg)  # 转换为整数秒
        
        # 更新token使用统计
        if tokens_used > 0:
            self.total_tokens_used += tokens_used
        
        # 更新成本统计
        if cost > 0:
            current_cost = float(self.total_cost) if self.total_cost else 0.0
            self.total_cost = current_cost + cost
    
    def is_active(self) -> bool:
        """检查任务是否激活"""
        return self.status == TaskStatus.ACTIVE
    
    def can_execute(self) -> bool:
        """检查任务是否可以执行"""
        # 基本检查
        base_checks = (
            self.status == TaskStatus.ACTIVE and
            self.webhook_id is not None and
            self.ai_model_id is not None
        )
        
        # 存储凭证检查（只有启用时才检查）
        storage_check = (
            not self.enable_storage_credential or 
            (self.enable_storage_credential and self.storage_credential_id is not None)
        )
        
        return base_checks and storage_check
    
    def is_healthy(self) -> bool:
        """检查任务是否健康"""
        return self.health_status == "healthy"
    
    def get_execution_summary(self) -> dict:
        """获取执行摘要"""
        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.get_success_rate(),
            "failure_rate": self.get_failure_rate(),
            "avg_execution_time": self.avg_execution_time,
            "total_tokens_used": self.total_tokens_used,
            "total_cost": self.total_cost,
            "last_execution_at": self.last_execution_at.isoformat() if self.last_execution_at else None,
            "last_execution_status": self.last_execution_status,
            "health_status": self.health_status,
        }
    
    def create_version(self) -> 'AnalysisTask':
        """创建新版本"""
        # 这里应该实现版本创建逻辑
        # 返回新的任务实例
        pass
    
    def validate_config(self) -> dict:
        """验证任务配置"""
        errors = []
        warnings = []
        
        # 基础验证
        if not self.name:
            errors.append("任务名称不能为空")
        
        if not self.webhook_id and self.trigger_type == TriggerType.WEBHOOK:
            errors.append("Webhook触发器需要指定Webhook")
        
        if not self.ai_model_id:
            errors.append("需要指定AI模型")
        
        # 存储凭证验证（只有启用时才检查）
        if self.enable_storage_credential and not self.storage_credential_id:
            errors.append("启用存储凭证时需要指定存储凭证")
        
        # 配置验证
        if not self.system_prompt and not self.user_prompt_template:
            warnings.append("建议设置系统提示词或用户提示词模板")
        
        if self.timeout_seconds and self.timeout_seconds < 60:
            warnings.append("超时时间建议不少于60秒")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }