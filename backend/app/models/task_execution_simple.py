from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum, BIGINT, NUMERIC
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timedelta

from app.core.database import Base


class ExecutionStatus(str, enum.Enum):
    """执行状态枚举（匹配数据库中的execution_status_enum）"""
    PENDING = "pending"
    PROCESSING = "processing"  # 数据库中使用processing，不是running
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskExecution(Base):
    """任务执行模型 - 匹配现有数据库结构"""
    
    __tablename__ = "task_executions"
    __table_args__ = {'extend_existing': True}
    
    # 基本字段（匹配现有数据库）
    id = Column(Integer, primary_key=True, index=True, comment="执行ID")
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"), nullable=True, comment="任务ID")
    execution_id = Column(String(50), unique=True, nullable=False, comment="执行唯一标识")
    
    # Webhook和数据字段（匹配现有数据库）
    webhook_payload = Column(JSON, comment="Webhook载荷")
    extracted_data = Column(JSON, comment="提取的数据")
    
    # 文件字段（匹配现有数据库）
    file_url = Column(Text, comment="文件URL")
    file_size_bytes = Column(BIGINT, comment="文件大小（字节）")
    file_type = Column(String(20), comment="文件类型")
    file_content_preview = Column(Text, comment="文件内容预览")
    
    # AI处理字段（匹配现有数据库）
    prompt_sent = Column(Text, comment="发送的提示词")
    ai_response = Column(Text, comment="AI响应")
    ai_response_metadata = Column(JSON, comment="AI响应元数据")
    tokens_used = Column(Integer, comment="使用的token数")
    cost = Column(NUMERIC(precision=10, scale=6), comment="成本")
    
    # 飞书字段（匹配现有数据库）
    feishu_task_id = Column(String(100), comment="飞书任务ID")
    feishu_response = Column(JSON, comment="飞书响应")
    fields_updated = Column(JSON, comment="更新的字段")
    
    # 状态字段（使用数据库中的enum名称）
    execution_status = Column(
        SQLEnum(ExecutionStatus, name="execution_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=ExecutionStatus.PENDING,
        comment="执行状态"
    )
    error_message = Column(Text, comment="错误消息")
    error_code = Column(String(50), comment="错误代码")
    retry_count = Column(Integer, default=0, comment="重试次数")
    
    # 执行日志字段
    execution_log = Column(JSON, comment="执行步骤日志")
    
    # 时间字段（匹配现有数据库）
    started_at = Column(DateTime(timezone=True), server_default=func.now(), comment="开始时间")
    file_fetched_at = Column(DateTime(timezone=True), comment="文件获取时间")
    ai_called_at = Column(DateTime(timezone=True), comment="AI调用时间")
    ai_responded_at = Column(DateTime(timezone=True), comment="AI响应时间")
    feishu_updated_at = Column(DateTime(timezone=True), comment="飞书更新时间")
    completed_at = Column(DateTime(timezone=True), comment="完成时间")
    execution_time_ms = Column(Integer, comment="执行时间（毫秒）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系（简化）
    task = relationship("AnalysisTask", back_populates="task_executions")
    
    def __repr__(self):
        return f"<TaskExecution(id={self.id}, execution_id='{self.execution_id}', status='{self.execution_status}')>"
    
    def to_dict(self, include_details=True):
        """转换为字典"""
        data = {
            "id": str(self.id),  # 转换为字符串以匹配API响应验证
            "task_id": self.task_id,
            "task_name": self.task.name if self.task else None,  # 添加任务名称
            "execution_id": self.execution_id,
            "status": self.execution_status.value if self.execution_status else None,
            "trigger_type": "webhook",  # 修正字段名：trigger_source -> trigger_type
            "trigger_source": "webhook",  # 保留原字段以兼容
            "current_step": "ai_analysis" if self.execution_status in [ExecutionStatus.PROCESSING] else "complete",  # 补充缺失字段
            "file_path": self.file_url,  # 添加file_path字段，前端期望这个字段名
            "file_url": self.file_url,
            "file_size_bytes": self.file_size_bytes,
            "file_type": self.file_type,
            "tokens_used": self.tokens_used,
            "duration": int(self.execution_time_ms / 1000) if self.execution_time_ms else None,  # 添加duration字段（秒）
            "cost": str(self.cost) if self.cost else None,
            "feishu_task_id": self.feishu_task_id,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.completed_at.isoformat() if self.completed_at else (self.created_at.isoformat() if self.created_at else None),  # 补充缺失字段
        }
        
        # 执行日志总是包含（前端需要显示）
        data["execution_log"] = self.execution_log or []
        
        # 详细信息只在需要时包含
        if include_details:
            data.update({
                "webhook_payload": self.webhook_payload,
                "extracted_data": self.extracted_data,
                "file_content_preview": self.file_content_preview,
                "prompt_sent": self.prompt_sent,
                "ai_response": self.ai_response,
                "ai_response_metadata": self.ai_response_metadata,
                "feishu_response": self.feishu_response,
                "fields_updated": self.fields_updated,
                "file_fetched_at": self.file_fetched_at.isoformat() if self.file_fetched_at else None,
                "ai_called_at": self.ai_called_at.isoformat() if self.ai_called_at else None,
                "ai_responded_at": self.ai_responded_at.isoformat() if self.ai_responded_at else None,
                "feishu_updated_at": self.feishu_updated_at.isoformat() if self.feishu_updated_at else None,
            })
        
        return data
    
    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.execution_status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]
    
    def is_successful(self) -> bool:
        """检查是否成功"""
        return self.execution_status == ExecutionStatus.SUCCESS
    
    def update_webhook_data(self, payload_data: dict, extracted_data: dict = None):
        """更新Webhook数据"""
        self.webhook_payload = payload_data
        if extracted_data:
            self.extracted_data = extracted_data
        self.started_at = func.now()
    
    def update_file_info(self, file_url: str = None, file_size: int = None, 
                        file_type: str = None, content_preview: str = None):
        """更新文件信息"""
        if file_url:
            self.file_url = file_url
        if file_size:
            self.file_size_bytes = file_size
        if file_type:
            self.file_type = file_type
        if content_preview:
            self.file_content_preview = content_preview
        self.file_fetched_at = func.now()
    
    def update_ai_request(self, prompt: str):
        """更新AI请求信息"""
        self.prompt_sent = prompt
        self.ai_called_at = func.now()
    
    def update_ai_response(self, response: str, metadata: dict = None, 
                          tokens_used: int = None, cost: float = None):
        """更新AI响应信息"""
        self.ai_response = response
        if metadata:
            self.ai_response_metadata = metadata
        if tokens_used:
            self.tokens_used = tokens_used
        if cost:
            self.cost = cost
        self.ai_responded_at = func.now()
    
    def update_feishu_result(self, feishu_task_id: str = None, 
                           feishu_response: dict = None, fields_updated: dict = None):
        """更新飞书写入结果"""
        if feishu_task_id:
            self.feishu_task_id = feishu_task_id
        if feishu_response:
            self.feishu_response = feishu_response
        if fields_updated:
            self.fields_updated = fields_updated
        self.feishu_updated_at = func.now()
    
    def mark_completed(self, status: ExecutionStatus = ExecutionStatus.SUCCESS, 
                      error_message: str = None, error_code: str = None):
        """标记执行完成"""
        self.execution_status = status
        if error_message:
            self.error_message = error_message
        if error_code:
            self.error_code = error_code
        
        # 设置完成时间并计算执行时间
        from datetime import datetime, timezone
        completed_time = datetime.now(timezone.utc)
        self.completed_at = completed_time
        
        # 计算执行时间 - 如果有开始时间的话
        if self.started_at is not None:
            try:
                # 如果started_at是datetime对象，确保时区兼容性
                if isinstance(self.started_at, datetime):
                    # 如果started_at没有时区信息，添加UTC时区
                    if self.started_at.tzinfo is None:
                        started_time_utc = self.started_at.replace(tzinfo=timezone.utc)
                    else:
                        started_time_utc = self.started_at
                    
                    # 计算时间差
                    delta = completed_time - started_time_utc
                    self.execution_time_ms = int(delta.total_seconds() * 1000)
            except Exception as e:
                # 如果时间计算失败，不影响主流程，只记录错误
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"执行时间计算失败: {e}")
                self.execution_time_ms = None
    
    def increment_retry(self):
        """增加重试次数"""
        self.retry_count = (self.retry_count or 0) + 1
    
    def update_execution_log(self, log_entries: list):
        """更新执行日志"""
        self.execution_log = log_entries
    
    def get_execution_summary(self) -> dict:
        """获取执行摘要"""
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "status": self.execution_status.value if self.execution_status else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_ms": self.execution_time_ms,
            "tokens_used": self.tokens_used,
            "cost": str(self.cost) if self.cost else None,
            "retry_count": self.retry_count,
            "has_error": bool(self.error_message),
            "file_processed": bool(self.file_url),
            "ai_called": bool(self.ai_called_at),
            "feishu_updated": bool(self.feishu_updated_at)
        }
    
    def get_detailed_log(self) -> dict:
        """获取详细日志"""
        log_data = {
            "basic_info": {
                "execution_id": self.execution_id,
                "task_id": self.task_id,
                "status": self.execution_status.value if self.execution_status else None,
                "retry_count": self.retry_count
            },
            "webhook_data": {
                "payload": self.webhook_payload,
                "extracted_data": self.extracted_data
            },
            "file_processing": {
                "url": self.file_url,
                "size_bytes": self.file_size_bytes,
                "type": self.file_type,
                "content_preview": self.file_content_preview,
                "fetched_at": self.file_fetched_at.isoformat() if self.file_fetched_at else None
            },
            "ai_processing": {
                "prompt_sent": self.prompt_sent,
                "response": self.ai_response,
                "metadata": self.ai_response_metadata,
                "tokens_used": self.tokens_used,
                "cost": str(self.cost) if self.cost else None,
                "called_at": self.ai_called_at.isoformat() if self.ai_called_at else None,
                "responded_at": self.ai_responded_at.isoformat() if self.ai_responded_at else None
            },
            "feishu_result": {
                "task_id": self.feishu_task_id,
                "response": self.feishu_response,
                "fields_updated": self.fields_updated,
                "updated_at": self.feishu_updated_at.isoformat() if self.feishu_updated_at else None
            },
            "timing": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "execution_time_ms": self.execution_time_ms
            },
            "errors": {
                "error_code": self.error_code,
                "error_message": self.error_message
            } if self.error_message else None
        }
        
        return log_data