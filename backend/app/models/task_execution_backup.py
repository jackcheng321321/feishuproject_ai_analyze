from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime, timedelta

from app.core.database import Base


class ExecutionStatus(str, enum.Enum):
    """执行状态枚举"""
    PENDING = "pending"          # 等待中
    RUNNING = "running"          # 运行中
    SUCCESS = "success"          # 成功
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消
    TIMEOUT = "timeout"          # 超时
    RETRY = "retry"              # 重试中


class ExecutionStep(str, enum.Enum):
    """执行步骤枚举"""
    INIT = "init"                    # 初始化
    PARSE_DATA = "parse_data"        # 解析数据
    DOWNLOAD_FILE = "download_file"  # 下载文件
    AI_ANALYSIS = "ai_analysis"      # AI分析
    WRITE_RESULT = "write_result"    # 写入结果
    NOTIFICATION = "notification"    # 发送通知
    CLEANUP = "cleanup"              # 清理


class TaskExecution(Base):
    """任务执行模型"""
    
    __tablename__ = "task_executions"
    
    id = Column(Integer, primary_key=True, index=True, comment="执行ID")
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"), nullable=False, comment="任务ID")
    
    # 执行标识
    execution_id = Column(String(50), unique=True, nullable=False, comment="执行唯一标识")
    batch_id = Column(String(50), comment="批次ID")
    parent_execution_id = Column(Integer, ForeignKey("task_executions.id"), comment="父执行ID")
    
    # 执行状态
    status = Column(
        SQLEnum(ExecutionStatus), 
        default=ExecutionStatus.PENDING, 
        comment="执行状态"
    )
    current_step = Column(
        SQLEnum(ExecutionStep), 
        default=ExecutionStep.INIT, 
        comment="当前步骤"
    )
    
    # 触发信息
    trigger_type = Column(String(20), comment="触发类型")
    trigger_source = Column(String(100), comment="触发源")
    trigger_data = Column(JSON, comment="触发数据")
    webhook_request_id = Column(String(50), comment="Webhook请求ID")
    
    # 执行配置快照
    task_config_snapshot = Column(JSON, comment="任务配置快照")
    ai_model_config = Column(JSON, comment="AI模型配置")
    storage_config = Column(JSON, comment="存储配置")
    
    # 数据解析结果
    parsed_data = Column(JSON, comment="解析后的数据")
    extracted_fields = Column(JSON, comment="提取的字段")
    validation_results = Column(JSON, comment="验证结果")
    
    # 文件处理信息
    file_path = Column(String(500), comment="文件路径")
    file_size = Column(Integer, comment="文件大小（字节）")
    file_type = Column(String(50), comment="文件类型")
    file_hash = Column(String(64), comment="文件哈希")
    download_url = Column(String(500), comment="下载URL")
    local_file_path = Column(String(500), comment="本地文件路径")
    
    # AI分析信息
    ai_request_data = Column(JSON, comment="AI请求数据")
    ai_response_data = Column(JSON, comment="AI响应数据")
    ai_model_name = Column(String(100), comment="AI模型名称")
    prompt_tokens = Column(Integer, default=0, comment="提示词token数")
    completion_tokens = Column(Integer, default=0, comment="完成token数")
    total_tokens = Column(Integer, default=0, comment="总token数")
    ai_cost = Column(String(20), default="0.00", comment="AI成本")
    
    # 结果信息
    analysis_result = Column(JSON, comment="分析结果")
    formatted_result = Column(JSON, comment="格式化结果")
    result_summary = Column(Text, comment="结果摘要")
    confidence_score = Column(String(10), comment="置信度分数")
    
    # 回写信息
    feishu_response = Column(JSON, comment="飞书响应")
    write_back_status = Column(String(20), comment="回写状态")
    write_back_message = Column(Text, comment="回写消息")
    
    # 执行时间信息
    started_at = Column(DateTime(timezone=True), comment="开始时间")
    completed_at = Column(DateTime(timezone=True), comment="完成时间")
    duration_seconds = Column(String(20), comment="执行时长（秒）")
    
    # 步骤时间记录
    step_timings = Column(JSON, comment="步骤时间记录")
    
    # 错误信息
    error_code = Column(String(50), comment="错误代码")
    error_message = Column(Text, comment="错误消息")
    error_details = Column(JSON, comment="错误详情")
    stack_trace = Column(Text, comment="堆栈跟踪")
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment="重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    next_retry_at = Column(DateTime(timezone=True), comment="下次重试时间")
    retry_reason = Column(Text, comment="重试原因")
    
    # 资源使用情况
    memory_usage_mb = Column(Integer, comment="内存使用（MB）")
    cpu_usage_percent = Column(String(10), comment="CPU使用率")
    disk_usage_mb = Column(Integer, comment="磁盘使用（MB）")
    network_bytes = Column(Integer, comment="网络传输字节数")
    
    # 日志信息
    log_level = Column(String(20), default="INFO", comment="日志级别")
    log_entries = Column(JSON, comment="日志条目")
    debug_info = Column(JSON, comment="调试信息")
    
    # 通知信息
    notifications_sent = Column(JSON, comment="已发送通知")
    notification_status = Column(String(20), comment="通知状态")
    
    # 执行环境信息
    worker_id = Column(String(50), comment="工作节点ID")
    worker_hostname = Column(String(100), comment="工作节点主机名")
    execution_environment = Column(JSON, comment="执行环境信息")
    
    # 优先级和队列信息
    priority = Column(Integer, default=0, comment="优先级")
    queue_name = Column(String(50), comment="队列名称")
    queue_wait_time = Column(String(20), comment="队列等待时间（秒）")
    
    # 标签和分类
    tags = Column(JSON, comment="标签")
    labels = Column(JSON, comment="标签")
    
    # 备注信息
    notes = Column(Text, comment="备注")
    user_feedback = Column(Text, comment="用户反馈")
    
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
    task = relationship("AnalysisTask", back_populates="task_executions")
    parent_execution = relationship("TaskExecution", remote_side=[id])
    child_executions = relationship("TaskExecution", back_populates="parent_execution")
    
    def __repr__(self):
        return f"<TaskExecution(id={self.id}, execution_id='{self.execution_id}', status='{self.status}')>"
    
    def to_dict(self, include_details=True):
        """转换为字典"""
        data = {
            "id": self.id,
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "batch_id": self.batch_id,
            "parent_execution_id": self.parent_execution_id,
            "status": self.status.value if self.status else None,
            "current_step": self.current_step.value if self.current_step else None,
            "trigger_type": self.trigger_type,
            "trigger_source": self.trigger_source,
            "webhook_request_id": self.webhook_request_id,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "ai_model_name": self.ai_model_name,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "ai_cost": self.ai_cost,
            "result_summary": self.result_summary,
            "confidence_score": self.confidence_score,
            "write_back_status": self.write_back_status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "worker_id": self.worker_id,
            "worker_hostname": self.worker_hostname,
            "priority": self.priority,
            "queue_name": self.queue_name,
            "queue_wait_time": self.queue_wait_time,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 详细信息只在需要时包含
        if include_details:
            data.update({
                "trigger_data": self.trigger_data,
                "task_config_snapshot": self.task_config_snapshot,
                "ai_model_config": self.ai_model_config,
                "storage_config": self.storage_config,
                "parsed_data": self.parsed_data,
                "extracted_fields": self.extracted_fields,
                "validation_results": self.validation_results,
                "ai_request_data": self.ai_request_data,
                "ai_response_data": self.ai_response_data,
                "analysis_result": self.analysis_result,
                "formatted_result": self.formatted_result,
                "feishu_response": self.feishu_response,
                "error_details": self.error_details,
                "stack_trace": self.stack_trace,
                "step_timings": self.step_timings,
                "log_entries": self.log_entries,
                "debug_info": self.debug_info,
                "notifications_sent": self.notifications_sent,
                "execution_environment": self.execution_environment,
                "labels": self.labels,
            })
        
        return data
    
    def start_execution(self):
        """开始执行"""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.current_step = ExecutionStep.INIT
        
        # 初始化步骤时间记录
        if not self.step_timings:
            self.step_timings = {}
        self.step_timings["started_at"] = self.started_at.isoformat()
    
    def complete_execution(self, success: bool = True, error_message: str = None):
        """完成执行"""
        self.completed_at = datetime.utcnow()
        
        if success:
            self.status = ExecutionStatus.SUCCESS
        else:
            self.status = ExecutionStatus.FAILED
            if error_message:
                self.error_message = error_message
        
        # 计算执行时长
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = f"{duration.total_seconds():.3f}"
        
        # 记录完成时间
        if not self.step_timings:
            self.step_timings = {}
        self.step_timings["completed_at"] = self.completed_at.isoformat()
    
    def update_step(self, step: ExecutionStep, data: dict = None):
        """更新执行步骤"""
        self.current_step = step
        
        # 记录步骤时间
        if not self.step_timings:
            self.step_timings = {}
        
        step_key = f"{step.value}_at"
        self.step_timings[step_key] = datetime.utcnow().isoformat()
        
        # 记录步骤数据
        if data:
            step_data_key = f"{step.value}_data"
            self.step_timings[step_data_key] = data
    
    def add_log_entry(self, level: str, message: str, details: dict = None):
        """添加日志条目"""
        if not self.log_entries:
            self.log_entries = []
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            "step": self.current_step.value if self.current_step else None,
        }
        
        if details:
            log_entry["details"] = details
        
        self.log_entries.append(log_entry)
        
        # 限制日志条目数量
        if len(self.log_entries) > 1000:
            self.log_entries = self.log_entries[-1000:]
    
    def set_error(self, error_code: str, error_message: str, error_details: dict = None, stack_trace: str = None):
        """设置错误信息"""
        self.error_code = error_code
        self.error_message = error_message
        self.error_details = error_details
        self.stack_trace = stack_trace
        
        # 添加错误日志
        self.add_log_entry("ERROR", error_message, error_details)
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return (
            self.status in [ExecutionStatus.FAILED, ExecutionStatus.TIMEOUT] and
            self.retry_count < self.max_retries
        )
    
    def schedule_retry(self, delay_seconds: int = None):
        """安排重试"""
        if not self.can_retry():
            return False
        
        self.retry_count += 1
        self.status = ExecutionStatus.RETRY
        
        # 计算下次重试时间
        if delay_seconds is None:
            # 指数退避策略
            delay_seconds = min(60 * (2 ** (self.retry_count - 1)), 3600)  # 最大1小时
        
        self.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        # 添加重试日志
        self.add_log_entry(
            "INFO", 
            f"安排第{self.retry_count}次重试，将在{self.next_retry_at}执行",
            {"retry_count": self.retry_count, "delay_seconds": delay_seconds}
        )
        
        return True
    
    def cancel_execution(self, reason: str = None):
        """取消执行"""
        self.status = ExecutionStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        if reason:
            self.error_message = f"执行已取消: {reason}"
        
        # 计算执行时长
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = f"{duration.total_seconds():.3f}"
        
        # 添加取消日志
        self.add_log_entry("WARNING", f"执行已取消: {reason or '未知原因'}")
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.status == ExecutionStatus.RUNNING
    
    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED, ExecutionStatus.TIMEOUT]
    
    def is_successful(self) -> bool:
        """检查是否成功"""
        return self.status == ExecutionStatus.SUCCESS
    
    def get_execution_summary(self) -> dict:
        """获取执行摘要"""
        return {
            "execution_id": self.execution_id,
            "status": self.status.value if self.status else None,
            "current_step": self.current_step.value if self.current_step else None,
            "duration_seconds": self.duration_seconds,
            "total_tokens": self.total_tokens,
            "ai_cost": self.ai_cost,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "result_summary": self.result_summary,
            "confidence_score": self.confidence_score,
        }
    
    def get_performance_metrics(self) -> dict:
        """获取性能指标"""
        metrics = {
            "duration_seconds": self.duration_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "disk_usage_mb": self.disk_usage_mb,
            "network_bytes": self.network_bytes,
            "queue_wait_time": self.queue_wait_time,
        }
        
        # 添加步骤时间分析
        if self.step_timings:
            step_durations = {}
            steps = list(ExecutionStep)
            
            for i, step in enumerate(steps):
                step_start_key = f"{step.value}_at"
                if step_start_key in self.step_timings:
                    if i + 1 < len(steps):
                        next_step_key = f"{steps[i + 1].value}_at"
                        if next_step_key in self.step_timings:
                            start_time = datetime.fromisoformat(self.step_timings[step_start_key].replace('Z', '+00:00'))
                            end_time = datetime.fromisoformat(self.step_timings[next_step_key].replace('Z', '+00:00'))
                            duration = (end_time - start_time).total_seconds()
                            step_durations[step.value] = duration
            
            metrics["step_durations"] = step_durations
        
        return metrics