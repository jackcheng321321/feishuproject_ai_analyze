from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from pydantic import BaseModel, Field, validator
from datetime import datetime
import secrets
import logging

# 创建logger实例
logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.models.analysis_task import AnalysisTask, TaskStatus, TriggerType
from app.models.webhook import Webhook
from app.models.ai_model import AIModel
from app.models.storage_credential import StorageCredential
from app.models.task_execution_simple import TaskExecution, ExecutionStatus
from app.schemas.analysis_task import (
    AnalysisTaskCreate, AnalysisTaskUpdate, AnalysisTaskResponse, AnalysisTaskSimpleResponse,
    TaskConfigurationWizard, TaskValidationResult, MultiFieldTestRequest, MultiFieldTestResponse,
    MultiFieldAnalysisTestRequest, MultiFieldAnalysisTestResponse
)
from app.services.data_parser import webhook_data_parser
from app.services.ai_service import ai_service
from app.services.feishu_service import FeishuResultWriter
from app.tasks.webhook_processor import process_webhook_async
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class TaskListFilter(BaseModel):
    status: Optional[str] = None
    webhook_id: Optional[int] = None
    ai_model_id: Optional[int] = None
    category: Optional[str] = None
    search: Optional[str] = None


class TaskExecutionTrigger(BaseModel):
    payload_data: Dict[str, Any] = Field(..., description="测试用的webhook数据")
    execution_id: Optional[str] = Field(None, description="执行ID，不提供则自动生成")


class AiAnalysisTestRequest(BaseModel):
    ai_model_id: int = Field(..., description="AI模型ID")
    prompt: str = Field(..., description="分析提示词")
    temperature: float = Field(default=1.0, description="温度参数")
    max_tokens: int = Field(default=10000, description="最大Token数")
    storage_credential_id: Optional[int] = Field(None, description="存储凭证ID（可选）")
    webhook_data: Dict[str, Any] = Field(..., description="Webhook数据")
    # 富文本字段支持
    rich_text_images: Optional[List[Dict[str, Any]]] = Field(None, description="富文本图片数据")
    content_type: Optional[str] = Field("plain_text", description="内容类型：plain_text, file_content, rich_text_with_images")


class AiAnalysisTestResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    content: str = Field(..., description="AI分析结果内容")
    model_name: str = Field(..., description="使用的模型名称")
    token_usage: Dict[str, int] = Field(..., description="Token使用情况")
    response_time: int = Field(..., description="响应时间（毫秒）")


class RichTextQueryRequest(BaseModel):
    """富文本字段查询请求"""
    webhook_data: Dict[str, Any] = Field(..., description="Webhook数据")
    plugin_id: str = Field("", description="插件ID（从环境变量获取）")
    plugin_secret: str = Field("", description="插件密钥（从环境变量获取）")
    user_key: str = Field("", description="用户标识（从环境变量获取）")


class PluginTokenRequest(BaseModel):
    """获取Plugin Token请求"""
    plugin_id: str = Field("", description="插件ID（从环境变量获取）")
    plugin_secret: str = Field("", description="插件密钥（从环境变量获取）")


class FeishuWriteTestRequest(BaseModel):
    """飞书数据写入测试请求"""
    field_key: str = Field(..., description="要更新的字段标识")
    analysis_result: str = Field(..., description="AI分析结果内容")
    webhook_data: Dict[str, Any] = Field(..., description="Webhook数据")
    project_key: str = Field(..., description="项目标识")
    work_item_type_key: str = Field(..., description="工作项类型标识")
    work_item_id: str = Field(..., description="工作项ID")
    plugin_token: Optional[str] = Field(None, description="插件令牌（可选，自动获取）")
    user_key: str = Field("", description="用户标识（从环境变量获取）")
    
    # 自动类型转换
    @validator('work_item_id', pre=True)
    def convert_work_item_id_to_string(cls, v):
        """确保work_item_id是字符串类型"""
        return str(v) if v is not None else ""
    
    @validator('field_key', 'project_key', 'work_item_type_key', 'user_key', pre=True)
    def ensure_string_fields(cls, v):
        """确保字符串字段都是字符串类型"""
        return str(v) if v is not None else ""


class FeishuWriteTestResponse(BaseModel):
    """飞书数据写入测试响应"""
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    project_key: Optional[str] = Field(None, description="项目标识")
    work_item_id: Optional[str] = Field(None, description="工作项ID")
    work_item_type_key: Optional[str] = Field(None, description="工作项类型标识")
    field_key: Optional[str] = Field(None, description="字段标识")
    write_response: Optional[Dict[str, Any]] = Field(None, description="写入API响应")
    error: Optional[str] = Field(None, description="错误信息")
    details: Optional[str] = Field(None, description="详细信息")


class RichTextQueryResponse(BaseModel):
    """富文本字段查询响应"""
    success: bool = Field(..., description="是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    field_key: Optional[str] = Field(None, description="字段标识")
    doc: Optional[str] = Field(None, description="富文本文档JSON")
    doc_text: Optional[str] = Field(None, description="富文本纯文本内容")
    doc_html: Optional[str] = Field(None, description="富文本HTML内容")
    is_empty: Optional[bool] = Field(None, description="是否为空")
    work_item_id: Optional[str] = Field(None, description="工作项ID")
    work_item_name: Optional[str] = Field(None, description="工作项名称")
    webhook_info: Optional[Dict[str, Any]] = Field(None, description="Webhook信息")
    timestamp: Optional[str] = Field(None, description="查询时间戳")
    error: Optional[str] = Field(None, description="错误信息")
    # 图片相关字段
    has_images: Optional[bool] = Field(None, description="是否包含图片")
    image_uuids: Optional[List[str]] = Field(None, description="图片UUID列表")
    downloaded_images: Optional[List[Dict[str, Any]]] = Field(None, description="下载的图片详情")
    download_count: Optional[int] = Field(None, description="成功下载的图片数量")
    download_failed_count: Optional[int] = Field(None, description="下载失败的图片数量")


@router.get("/")
async def get_analysis_tasks(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    webhook_id: Optional[int] = None,
    ai_model_id: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取分析任务列表"""
    from sqlalchemy.orm import joinedload
    
    # 预加载关联数据
    query = db.query(AnalysisTask).options(
        joinedload(AnalysisTask.webhook),
        joinedload(AnalysisTask.ai_model),
        joinedload(AnalysisTask.storage_credential)
    )
    
    # 状态过滤（支持新旧两种方式）
    if status:
        try:
            status_enum = TaskStatus(status)
            query = query.filter(AnalysisTask.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的任务状态: {status}")
    
    # 活跃状态过滤
    if is_active is not None:
        if is_active:
            query = query.filter(AnalysisTask.status == TaskStatus.ACTIVE)
        else:
            query = query.filter(AnalysisTask.status != TaskStatus.ACTIVE)
    
    # Webhook过滤
    if webhook_id:
        query = query.filter(AnalysisTask.webhook_id == webhook_id)
    
    # AI模型过滤
    if ai_model_id:
        query = query.filter(AnalysisTask.ai_model_id == ai_model_id)
    
    # 分类过滤
    if category:
        query = query.filter(AnalysisTask.category == category)
    
    # 搜索过滤
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                AnalysisTask.name.ilike(search_pattern),
                AnalysisTask.description.ilike(search_pattern),
                AnalysisTask.notes.ilike(search_pattern)
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 排序和分页
    tasks = query.order_by(desc(AnalysisTask.updated_at)).offset(skip).limit(limit).all()
    
    # 构建响应数据，包含关联信息
    items = []
    for task in tasks:
        # 查询该任务最新的执行记录
        latest_execution = db.query(TaskExecution).filter(
            TaskExecution.task_id == task.id
        ).order_by(desc(TaskExecution.started_at)).first()
        
        # 构建关联对象信息
        webhook_info = None
        if task.webhook:
            webhook_info = {
                "id": task.webhook.id,
                "name": task.webhook.name,
                "url": task.webhook.webhook_url
            }
        
        ai_model_info = None
        if task.ai_model:
            ai_model_info = {
                "id": task.ai_model.id,
                "name": task.ai_model.name,
                "model_name": task.ai_model.model_name,
                "model_type": task.ai_model.model_type.value if task.ai_model.model_type else None
            }
        
        storage_credential_info = None
        if task.storage_credential:
            storage_credential_info = {
                "id": task.storage_credential.id,
                "name": task.storage_credential.name,
                "protocol_type": task.storage_credential.protocol_type.value if task.storage_credential.protocol_type else None
            }
        
        # 构建任务数据
        task_data = {
            "id": task.id,
            "name": task.name,
            "display_name": task.display_name,
            "description": task.description,
            "status": task.status.value if task.status else "draft",
            "trigger_type": task.trigger_type.value if task.trigger_type else "manual",
            "is_active": task.status == TaskStatus.ACTIVE if task.status else False,
            
            # 关联ID
            "webhook_id": task.webhook_id,
            "ai_model_id": task.ai_model_id,
            "storage_credential_id": task.storage_credential_id,
            
            # 关联对象信息
            "webhook": webhook_info,
            "ai_model": ai_model_info,
            "storage_credential": storage_credential_info,
            
            # 配置信息
            "temperature": task.temperature,
            "max_tokens": task.max_tokens,
            "enable_rich_text_parsing": task.enable_rich_text_parsing or False,
            
            # 统计信息
            "total_executions": task.total_executions or 0,
            "successful_executions": task.successful_executions or 0,
            "failed_executions": task.failed_executions or 0,
            "last_executed_at": latest_execution.started_at.isoformat() if latest_execution and latest_execution.started_at else None,
            
            # 系统字段
            "created_by": task.created_by,
            "priority": task.priority or 0,
            "tags": task.tags,
            "version": task.version or 1,
            
            # 时间戳
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None
        }
        
        items.append(task_data)
    
    # 返回分页响应格式
    return {
        "items": items,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }


@router.post("/", response_model=AnalysisTaskSimpleResponse)
async def create_analysis_task(
    task_data: AnalysisTaskCreate,
    db: Session = Depends(get_db)
):
    """创建分析任务"""
    
    # 验证关联资源是否存在
    if task_data.webhook_id:
        webhook = db.query(Webhook).filter(
            Webhook.id == task_data.webhook_id
        ).first()
        if not webhook:
            raise HTTPException(status_code=404, detail="关联的Webhook不存在")
    
    if task_data.ai_model_id:
        ai_model = db.query(AIModel).filter(
            AIModel.id == task_data.ai_model_id
        ).first()
        if not ai_model:
            raise HTTPException(status_code=404, detail="关联的AI模型不存在")
    
    if task_data.storage_credential_id:
        storage_credential = db.query(StorageCredential).filter(
            StorageCredential.id == task_data.storage_credential_id
        ).first()
        if not storage_credential:
            raise HTTPException(status_code=404, detail="关联的存储凭证不存在")
    
    # 创建任务 - 使用简化的字段映射
    task = AnalysisTask(
        name=task_data.name,
        display_name=task_data.display_name or task_data.name,
        description=task_data.description,
        status=TaskStatus.ACTIVE if task_data.is_active else TaskStatus.DRAFT,
        trigger_type=task_data.trigger_type,
        webhook_id=task_data.webhook_id,
        ai_model_id=task_data.ai_model_id,
        storage_credential_id=task_data.storage_credential_id if task_data.enable_storage_credential else None,
        
        # AI分析配置 - 安全的类型转换
        system_prompt="分析以下内容",  # 默认系统提示
        user_prompt_template=task_data.analysis_prompt,
        analysis_config={
            "temperature": task_data.temperature,
            "max_tokens": task_data.max_tokens
        },
        temperature=float(task_data.temperature) if task_data.temperature is not None else 1.0,
        max_tokens=int(task_data.max_tokens) if task_data.max_tokens is not None else 10000,
        
        # 飞书配置 - 修复：统一使用feishu_write_config字段
        feishu_write_config=task_data.feishu_write_config,
        feishu_config=task_data.feishu_write_config,  # 保留兼容性
        
        # 富文本配置
        enable_rich_text_parsing=task_data.enable_rich_text_parsing,
        rich_text_config=task_data.rich_text_config if task_data.enable_rich_text_parsing else None,
        
        # 默认配置
        schedule_config={},
        data_parsing_config={},
        jsonpath_rules={},
        data_validation_rules={},
        
        # 数据库必需字段
        data_extraction_config={},
        prompt_template=task_data.analysis_prompt or "分析以下内容并提取重要信息",
        file_path_template="",
        file_filters={},
        download_config={},
        result_config={},
        field_mapping={},
        timeout_seconds=300,
        max_retry_attempts=3,
        retry_delay_seconds=60,
        max_concurrent_executions=1,
        queue_priority=0,
        max_file_size=10485760,  # 10MB
        max_processing_time=1800,  # 30分钟
        max_memory_usage=1073741824,  # 1GB
        # 通知和日志配置 - 使用默认值
        success_notification=False,
        failure_notification=True,
        notification_emails="",
        log_level="INFO",
        log_retention_days=30,
        detailed_logging=True,
        
        # 版本和层次结构
        version=1,
        parent_task_id=None,
        is_template=False,
        created_by=None,  # 无用户认证模式下设置为空
        
        # 共享和权限
        shared_with_users="",
        is_public=False,
        
        # 分类和优先级
        tags="",
        category="",
        priority=0,  # 转换为整数：normal=0, high=1, urgent=2
        notes="",
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # 重新查询以获取关联数据
    from sqlalchemy.orm import joinedload
    task_with_relations = db.query(AnalysisTask).options(
        joinedload(AnalysisTask.webhook),
        joinedload(AnalysisTask.ai_model),
        joinedload(AnalysisTask.storage_credential)
    ).filter(AnalysisTask.id == task.id).first()
    
    # 构建关联对象信息
    webhook_info = None
    if task_with_relations.webhook:
        webhook_info = {
            "id": task_with_relations.webhook.id,
            "name": task_with_relations.webhook.name,
            "url": task_with_relations.webhook.webhook_url
        }
    
    ai_model_info = None
    if task_with_relations.ai_model:
        ai_model_info = {
            "id": task_with_relations.ai_model.id,
            "name": task_with_relations.ai_model.name,
            "model_name": task_with_relations.ai_model.model_name,
            "model_type": task_with_relations.ai_model.model_type.value if task_with_relations.ai_model.model_type else None
        }
    
    storage_credential_info = None
    if task_with_relations.storage_credential:
        storage_credential_info = {
            "id": task_with_relations.storage_credential.id,
            "name": task_with_relations.storage_credential.name,
            "protocol_type": task_with_relations.storage_credential.protocol_type.value if task_with_relations.storage_credential.protocol_type else None
        }
    
    # 构建任务数据
    task_data = {
        "id": task_with_relations.id,
        "name": task_with_relations.name,
        "display_name": task_with_relations.display_name,
        "description": task_with_relations.description,
        "status": task_with_relations.status.value if task_with_relations.status else "draft",
        "trigger_type": task_with_relations.trigger_type.value if task_with_relations.trigger_type else "manual",
        "is_active": task_with_relations.status == TaskStatus.ACTIVE if task_with_relations.status else False,
        
        # 关联ID
        "webhook_id": task_with_relations.webhook_id,
        "ai_model_id": task_with_relations.ai_model_id,
        "storage_credential_id": task_with_relations.storage_credential_id,
        
        # 关联对象信息
        "webhook": webhook_info,
        "ai_model": ai_model_info,
        "storage_credential": storage_credential_info,
        
        # 配置信息
        "temperature": task_with_relations.temperature,
        "max_tokens": task_with_relations.max_tokens,
        "enable_rich_text_parsing": task_with_relations.enable_rich_text_parsing or False,

        # 添加AnalysisTaskSimpleResponse必需的字段
        "analysis_prompt": task_with_relations.user_prompt_template or "",
        "data_extraction_config": task_with_relations.data_extraction_config or {},
        "prompt_template": task_with_relations.prompt_template or "",
        "feishu_config": task_with_relations.feishu_config or {},
        "field_mapping": task_with_relations.field_mapping or {},
        "feishu_write_config": task_with_relations.feishu_write_config or {},
        
        # 统计信息
        "total_executions": task_with_relations.total_executions or 0,
        "successful_executions": task_with_relations.successful_executions or 0,
        "failed_executions": task_with_relations.failed_executions or 0,
        "last_executed_at": task_with_relations.last_execution_at,
        
        # 系统字段
        "created_by": task_with_relations.created_by,
        "priority": task_with_relations.priority or 0,
        "tags": task_with_relations.tags,
        "version": task_with_relations.version or 1,
        
        # 时间戳 - 保持datetime对象类型，Pydantic会自动处理序列化
        "created_at": task_with_relations.created_at,
        "updated_at": task_with_relations.updated_at
    }
    
    logger.info(f"创建分析任务成功: {task.name} (ID: {task.id})")
    return AnalysisTaskSimpleResponse(**task_data)


@router.get("/{task_id}/stats")
async def get_task_stats(
    task_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取单个任务的统计信息"""
    # 验证任务是否存在
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 构建查询条件
    query = db.query(TaskExecution).filter(TaskExecution.task_id == task_id)

    if start_date:
        start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        query = query.filter(TaskExecution.started_at >= start_time)

    if end_date:
        end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        query = query.filter(TaskExecution.started_at <= end_time)

    executions = query.all()

    # 计算统计数据
    total_executions = len(executions)
    success_executions = len([e for e in executions if e.execution_status == ExecutionStatus.SUCCESS])
    failed_executions = len([e for e in executions if e.execution_status == ExecutionStatus.FAILED])
    success_rate = round((success_executions / total_executions) if total_executions > 0 else 0, 4)

    # 计算平均执行时间（毫秒）
    durations = [e.execution_time_ms for e in executions if e.execution_time_ms]
    avg_duration = round(sum(durations) / len(durations), 2) if durations else 0

    # 计算token消耗总量
    total_tokens = sum(e.tokens_used for e in executions if e.tokens_used)

    # 处理文件数量
    total_files = len([e for e in executions if e.file_url])

    # 最后执行时间
    last_execution = max([e.started_at for e in executions], default=None) if executions else None

    return {
        "total_executions": total_executions,
        "success_executions": success_executions,
        "failed_executions": failed_executions,
        "success_rate": success_rate,
        "avg_duration": avg_duration,
        "total_tokens": total_tokens,
        "total_files": total_files,
        "last_execution": last_execution.isoformat() if last_execution else None
    }


@router.get("/{task_id}/executions")
async def get_task_executions(
    task_id: int,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    """获取单个任务的执行记录"""
    # 验证任务是否存在
    task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 计算分页参数
    skip = (page - 1) * size

    # 查询执行记录
    query = db.query(TaskExecution).filter(TaskExecution.task_id == task_id)
    total = query.count()

    executions = query.order_by(desc(TaskExecution.started_at)).offset(skip).limit(size).all()

    # 转换为响应格式
    execution_items = []
    for execution in executions:
        execution_items.append({
            "id": execution.id,
            "task_id": execution.task_id,
            "execution_status": execution.execution_status.value if execution.execution_status else "unknown",
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "execution_time_ms": execution.execution_time_ms,
            "tokens_used": execution.tokens_used,
            "file_url": execution.file_url,
            "ai_response": execution.ai_response,
            "error_message": execution.error_message
        })

    return {
        "items": execution_items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }


@router.get("/{task_id}", response_model=AnalysisTaskSimpleResponse)
async def get_analysis_task(
    task_id: int,
    include_config: bool = True,
    db: Session = Depends(get_db)
):
    """获取分析任务详情"""
    from sqlalchemy.orm import joinedload
    
    task = db.query(AnalysisTask).options(
        joinedload(AnalysisTask.webhook),
        joinedload(AnalysisTask.ai_model),
        joinedload(AnalysisTask.storage_credential)
    ).filter(AnalysisTask.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    
    # 构建关联对象信息
    webhook_info = None
    if task.webhook:
        webhook_info = {
            "id": task.webhook.id,
            "name": task.webhook.name,
            "url": task.webhook.webhook_url
        }
    
    ai_model_info = None
    if task.ai_model:
        ai_model_info = {
            "id": task.ai_model.id,
            "name": task.ai_model.name,
            "model_name": task.ai_model.model_name,
            "model_type": task.ai_model.model_type.value if task.ai_model.model_type else None
        }
    
    storage_credential_info = None
    if task.storage_credential:
        storage_credential_info = {
            "id": task.storage_credential.id,
            "name": task.storage_credential.name,
            "protocol_type": task.storage_credential.protocol_type.value if task.storage_credential.protocol_type else None
        }
    
    # 调试日志：检查数据库中的原始数据
    logger.info(f"=== 获取任务详情 ID: {task_id} ===")
    logger.info(f"user_prompt_template: {task.user_prompt_template}")
    logger.info(f"feishu_write_config: {task.feishu_write_config}")
    logger.info(f"feishu_config: {task.feishu_config}")
    
    # 构建任务数据
    task_data = {
        "id": task.id,
        "name": task.name,
        "display_name": task.display_name,
        "description": task.description,
        "status": task.status.value if task.status else "draft",
        "trigger_type": task.trigger_type.value if task.trigger_type else "manual",
        "is_active": task.status == TaskStatus.ACTIVE if task.status else False,
        
        # 关联ID
        "webhook_id": task.webhook_id,
        "ai_model_id": task.ai_model_id,
        "storage_credential_id": task.storage_credential_id,
        
        # 关联对象信息
        "webhook": webhook_info,
        "ai_model": ai_model_info,
        "storage_credential": storage_credential_info,
        
        # 配置信息
        "temperature": task.temperature,
        "max_tokens": task.max_tokens,
        "enable_rich_text_parsing": task.enable_rich_text_parsing or False,
        
        # 分析配置字段 - 修复缺失的字段
        "analysis_prompt": task.user_prompt_template or "",  # 分析提示词
        "data_extraction_config": task.data_extraction_config or {},
        "prompt_template": task.prompt_template or "",
        "feishu_config": task.feishu_config or {},
        "field_mapping": task.field_mapping or {},
        "feishu_write_config": task.feishu_write_config or {},  # 飞书写入配置
        
        # 统计信息
        "total_executions": task.total_executions or 0,
        "successful_executions": task.successful_executions or 0,
        "failed_executions": task.failed_executions or 0,
        "last_executed_at": task.last_execution_at.isoformat() if task.last_execution_at else None,
        
        # 系统字段
        "created_by": task.created_by,
        "priority": task.priority or 0,
        "tags": task.tags,
        "version": task.version or 1,
        
        # 时间戳
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None
    }
    
    # 调试日志：检查构建的返回数据
    logger.info(f"=== 构建的返回数据 ===")
    logger.info(f"analysis_prompt: {task_data.get('analysis_prompt', 'NOT_FOUND')}")
    logger.info(f"feishu_write_config: {task_data.get('feishu_write_config', 'NOT_FOUND')}")
    
    return AnalysisTaskSimpleResponse(**task_data)


@router.put("/{task_id}")
async def update_analysis_task(
    task_id: int,
    task_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """更新分析任务"""
    from sqlalchemy.orm import joinedload
    
    task = db.query(AnalysisTask).options(
        joinedload(AnalysisTask.webhook),
        joinedload(AnalysisTask.ai_model),
        joinedload(AnalysisTask.storage_credential)
    ).filter(AnalysisTask.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    
    # 处理特殊字段
    if 'is_active' in task_data:
        # 前端传的是布尔值，需要转换为状态枚举
        if task_data['is_active']:
            task.status = TaskStatus.ACTIVE
        else:
            task.status = TaskStatus.DISABLED
        del task_data['is_active']  # 删除处理过的字段
    
    # 处理analysis_prompt字段映射
    if 'analysis_prompt' in task_data:
        task.user_prompt_template = task_data['analysis_prompt']
        del task_data['analysis_prompt']  # 删除处理过的字段
    
    # 处理飞书写入配置字段映射
    if 'feishu_write_config' in task_data:
        # 同时更新两个字段，确保数据一致性
        task.feishu_write_config = task_data['feishu_write_config']
        task.feishu_config = task_data['feishu_write_config']  # 保持兼容性
        del task_data['feishu_write_config']  # 删除处理过的字段

    # 定义允许更新的字段白名单（排除关联对象字段）
    allowed_fields = {
        'name', 'display_name', 'description', 'webhook_id', 'ai_model_id',
        'storage_credential_id', 'data_extraction_config', 'prompt_template',
        'temperature', 'max_tokens', 'enable_rich_text_parsing',
        'feishu_config', 'field_mapping',  # 移除feishu_write_config，因为已经在上面处理
        'enable_storage_credential', 'file_path_template', 'file_filters',
        'download_config', 'system_prompt', 'analysis_config', 'result_config',
        'webhook_data_extract', 'rich_text_config', 'timeout_seconds',
        'max_retry_attempts', 'retry_delay_seconds', 'max_concurrent_executions',
        'queue_priority', 'max_file_size', 'created_by', 'priority', 'tags'
    }
    
    # 更新其他字段
    for field, value in task_data.items():
        if hasattr(task, field) and field in allowed_fields:
            if field in ['status', 'trigger_type'] and value:
                # 处理枚举字段
                if field == 'status':
                    value = TaskStatus(value)
                elif field == 'trigger_type':
                    value = TriggerType(value)
            setattr(task, field, value)
    
    # 更新版本号
    task.version += 1
    
    db.commit()
    db.refresh(task)
    
    logger.info(f"更新分析任务成功: {task.name} (ID: {task.id})")
    
    # 构建响应数据（与列表API保持一致）
    webhook_info = None
    if task.webhook:
        webhook_info = {
            "id": task.webhook.id,
            "name": task.webhook.name,
            "url": task.webhook.webhook_url
        }
    
    ai_model_info = None
    if task.ai_model:
        ai_model_info = {
            "id": task.ai_model.id,
            "name": task.ai_model.name,
            "model_name": task.ai_model.model_name,
            "model_type": task.ai_model.model_type.value if task.ai_model.model_type else None
        }
    
    storage_credential_info = None
    if task.storage_credential:
        storage_credential_info = {
            "id": task.storage_credential.id,
            "name": task.storage_credential.name,
            "protocol_type": task.storage_credential.protocol_type.value if task.storage_credential.protocol_type else None
        }
    
    return {
        "id": task.id,
        "name": task.name,
        "display_name": task.display_name,
        "description": task.description,
        "status": task.status.value if task.status else "draft",
        "trigger_type": task.trigger_type.value if task.trigger_type else "manual",
        "is_active": task.status == TaskStatus.ACTIVE if task.status else False,
        
        # 关联ID
        "webhook_id": task.webhook_id,
        "ai_model_id": task.ai_model_id,
        "storage_credential_id": task.storage_credential_id,
        
        # 关联对象信息
        "webhook": webhook_info,
        "ai_model": ai_model_info,
        "storage_credential": storage_credential_info,
        
        # 配置信息
        "temperature": task.temperature,
        "max_tokens": task.max_tokens,
        "enable_rich_text_parsing": task.enable_rich_text_parsing or False,
        
        # 统计信息
        "total_executions": task.total_executions or 0,
        "successful_executions": task.successful_executions or 0,
        "failed_executions": task.failed_executions or 0,
        "last_executed_at": task.last_execution_at.isoformat() if task.last_execution_at else None,
        
        # 系统字段
        "created_by": task.created_by,
        "priority": task.priority or 0,
        "tags": task.tags,
        "version": task.version or 1,
        
        # 时间戳
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None
    }


@router.delete("/{task_id}")
async def delete_analysis_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """删除分析任务"""
    
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    
    # 检查是否有子任务
    child_tasks = db.query(AnalysisTask).filter(
        AnalysisTask.parent_task_id == task_id
    ).count()
    
    if child_tasks > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"无法删除任务，还有{child_tasks}个子任务依赖此任务"
        )
    
    # 检查是否有正在执行的任务 - 暂时禁用此检查避免枚举问题
    # TODO: 修复枚举查询问题后重新启用
    # running_executions = db.query(TaskExecution).filter(
    #     TaskExecution.task_id == task_id,
    #     TaskExecution.execution_status == "processing"
    # ).count()
    # 
    # if running_executions > 0:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="无法删除任务，还有正在执行的任务实例"
    #     )
    
    db.delete(task)
    db.commit()
    
    logger.info(f"删除分析任务成功: {task.name} (ID: {task_id})")
    return {"success": True, "message": "分析任务删除成功"}


@router.post("/{task_id}/trigger")
async def trigger_analysis_task(
    task_id: int,
    trigger_data: TaskExecutionTrigger,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """手动触发分析任务执行"""
    
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    
    if not task.can_execute():
        raise HTTPException(status_code=400, detail="任务无法执行，请检查配置")
    
    # 生成执行ID
    execution_id = trigger_data.execution_id or f"manual_{secrets.token_urlsafe(12)}"
    
    # 获取关联的webhook
    if not task.webhook_id:
        raise HTTPException(status_code=400, detail="任务没有关联Webhook")
    
    # 启动异步处理
    background_tasks.add_task(
        process_webhook_async,
        webhook_id=task.webhook_id,
        payload_data=trigger_data.payload_data,
        execution_id=execution_id,
        client_ip="127.0.0.1",  # 手动触发
        user_agent="Manual-Trigger"
    )
    
    logger.info(f"手动触发分析任务: {task.name} (ID: {task_id}, 执行ID: {execution_id})")
    return {
        "success": True,
        "message": "分析任务触发成功",
        "task_id": task_id,
        "task_name": task.name,
        "execution_id": execution_id,
        "status": "processing"
    }


@router.post("/test-ai-analysis/", response_model=AiAnalysisTestResponse)
async def test_ai_analysis(
    test_data: AiAnalysisTestRequest,
    db: Session = Depends(get_db)
):
    """AI分析测试接口"""
    import time
    
    start_time = time.time()
    
    try:
        # 验证AI模型是否存在
        ai_model = db.query(AIModel).filter(
            AIModel.id == test_data.ai_model_id
        ).first()
        
        if not ai_model:
            raise HTTPException(status_code=404, detail="指定的AI模型不存在")
        
        if not ai_model.is_active:
            raise HTTPException(status_code=400, detail="指定的AI模型未启用")
        
        # 准备分析数据
        analysis_content = test_data.prompt
        field_value = test_data.webhook_data.get('field_value', '')
        
        # 处理富文本图片数据 - 优先使用已下载的图片数据
        rich_text_images = []
        if test_data.content_type == "rich_text_with_images" and test_data.rich_text_images:
            logger.info(f"检测到富文本图片数据，共 {len(test_data.rich_text_images)} 张图片")

            # 处理每张图片，优先使用已有的base64数据，避免重复下载
            processed_images = []
            for i, img_data in enumerate(test_data.rich_text_images):
                try:
                    logger.info(f"处理图片 {i+1}: {list(img_data.keys())}")

                    # 检查图片数据是否已包含base64内容（来自富文本查询）
                    if img_data.get('base64'):
                        logger.info(f"图片 {i+1} 已包含base64数据，直接使用 (大小: {img_data.get('size', 0)} bytes)")
                        processed_images.append(img_data)
                        continue

                    # 如果没有base64数据但有download_success标记，说明之前下载失败了，跳过
                    if img_data.get('download_success') is False:
                        logger.warning(f"图片 {i+1} 之前下载失败: {img_data.get('error', '未知错误')}")
                        continue

                    # 如果既没有base64数据也没有下载状态标记，但有UUID，尝试重新下载（备用逻辑）
                    img_uuid = img_data.get('uuid')
                    if img_uuid:
                        logger.warning(f"图片 {i+1} 缺少base64数据，尝试重新获取: uuid={img_uuid}")

                        # 从webhook数据中提取项目信息
                        webhook_data = test_data.webhook_data or {}
                        project_key = webhook_data.get('project_key')
                        work_item_type_key = webhook_data.get('work_item_type_key')
                        work_item_id = str(webhook_data.get('id', ''))

                        if not all([project_key, work_item_type_key, work_item_id]):
                            logger.warning(f"图片 {i+1} 缺少必要的项目信息，无法重新下载")
                            continue

                        # 导入图片下载服务
                        from app.services.image_download_service import feishu_image_service
                        import os
                        plugin_id = os.getenv("FEISHU_PLUGIN_ID", "")
                        plugin_secret = os.getenv("FEISHU_PLUGIN_SECRET", "")
                        user_key = os.getenv("FEISHU_USER_KEY", "")

                        if not all([plugin_id, plugin_secret, user_key]):
                            logger.error(f"飞书配置缺失，无法重新下载图片 {i+1}")
                            continue

                        download_result = await feishu_image_service.download_attachment_with_auto_auth(
                            project_key=project_key,
                            work_item_type_key=work_item_type_key,
                            work_item_id=work_item_id,
                            file_uuid=img_uuid,
                            plugin_id=plugin_id,
                            plugin_secret=plugin_secret,
                            user_key=user_key,
                            save_to_file=False  # 不保存文件，直接获取base64数据
                        )

                        if download_result.get('success') and download_result.get('image_data_base64'):
                            # 更新图片数据，添加base64内容
                            updated_img_data = img_data.copy()
                            updated_img_data['base64'] = download_result['image_data_base64']
                            updated_img_data['size'] = download_result.get('actual_size', 0)
                            updated_img_data['type'] = download_result.get('content_type', 'image/png')

                            processed_images.append(updated_img_data)
                            logger.info(f"图片 {i+1} 重新下载成功，大小: {updated_img_data['size']} bytes")
                        else:
                            logger.error(f"图片 {i+1} 重新下载失败: {download_result.get('error', '未知错误')}")
                    else:
                        logger.warning(f"图片 {i+1} 缺少UUID，无法处理")

                except Exception as e:
                    logger.error(f"处理图片 {i+1} 时发生异常: {e}")
                    continue

            rich_text_images = processed_images
            logger.info(f"富文本图片处理完成，成功处理 {len(processed_images)} 张图片，其中复用已下载数据 {len([img for img in processed_images if img.get('source') == 'rich_text_field'])} 张")
        
        # 如果启用了存储凭证，实际获取文件内容
        file_contents = []
        if test_data.storage_credential_id and field_value and test_data.content_type != "rich_text_with_images":
            try:
                storage_credential = db.query(StorageCredential).filter(
                    StorageCredential.id == test_data.storage_credential_id
                ).first()
                
                if storage_credential and storage_credential.is_active:
                    logger.info(f"开始获取存储文件内容，路径: {field_value}")
                    from app.services.file_service import file_service
                    
                    # 检查webhook数据中是否有文件列表
                    webhook_data = test_data.webhook_data or {}
                    files_list = webhook_data.get('files', [])
                    
                    if files_list:
                        # 如果有文件列表，逐个获取文件内容
                        logger.info(f"检测到文件列表，共 {len(files_list)} 个文件")
                        for file_name in files_list:
                            try:
                                # 构建完整文件路径
                                if field_value.endswith('\\') or field_value.endswith('/'):
                                    full_file_path = field_value + file_name
                                else:
                                    full_file_path = field_value + '\\' + file_name
                                
                                logger.info(f"获取文件: {full_file_path}")
                                file_result = await file_service.get_network_file(full_file_path)
                                
                                if file_result.get('success'):
                                    file_contents.append(file_result)
                                    logger.info(f"成功获取文件: {file_result.get('file_name')}, 大小: {file_result.get('file_size')} 字节")
                                else:
                                    logger.warning(f"获取文件失败: {file_name} - {file_result.get('error')}")
                                    
                            except Exception as file_e:
                                logger.error(f"获取文件失败 {file_name}: {str(file_e)}")
                    else:
                        # 如果没有文件列表，先检查路径是否为目录
                        try:
                            # 先判断路径是否为目录
                            import os
                            if os.path.isdir(field_value):
                                # 如果是目录，列出目录内容
                                logger.info(f"检测到目录路径，开始列出目录内容: {field_value}")
                                directory_items = await file_service.list_network_directory(field_value)
                                
                                # 筛选出文件（非目录）
                                files_in_dir = [item for item in directory_items if not item.get('is_directory', False)]
                                logger.info(f"目录中找到 {len(files_in_dir)} 个文件")
                                
                                # 逐个获取文件内容
                                for file_info in files_in_dir:
                                    file_name = file_info.get('name', '')
                                    if file_name:
                                        try:
                                            # 构建完整文件路径
                                            full_file_path = os.path.join(field_value, file_name)
                                            logger.info(f"读取目录文件: {full_file_path}")
                                            
                                            file_result = await file_service.get_network_file(full_file_path)
                                            if file_result and isinstance(file_result, dict):
                                                file_contents.append(file_result)
                                                logger.info(f"成功获取目录文件: {file_name}, 大小: {file_result.get('file_size', 0)} 字节")
                                            else:
                                                logger.warning(f"获取目录文件失败: {file_name}")
                                                
                                        except Exception as file_e:
                                            logger.error(f"获取目录文件失败 {file_name}: {str(file_e)}")
                                            
                            else:
                                # 如果是文件，直接获取内容
                                file_result = await file_service.get_network_file(field_value)
                                if file_result and isinstance(file_result, dict):
                                    file_contents.append(file_result)
                                    logger.info(f"成功获取文件: {file_result.get('file_name', 'unknown')}, 大小: {file_result.get('file_size', 0)} 字节")
                                else:
                                    logger.warning(f"获取文件失败: {field_value}")
                                    
                        except Exception as file_e:
                            logger.error(f"文件服务调用失败: {str(file_e)}")
                            # 如果获取文件失败，保持原始路径信息
                            field_value = f"文件路径: {field_value} (获取文件内容失败: {str(file_e)})"
                        
            except Exception as e:
                logger.warning(f"处理存储文件信息失败，使用原始字段值: {str(e)}")
        
        # 获取API密钥
        api_key = ai_model.api_key or ""
        if not api_key:
            raise HTTPException(status_code=400, detail="AI模型未配置API密钥")
        
        # 推断提供商信息
        provider = "openai"  # 默认值
        if ai_model.model_type:
            model_type_str = ai_model.model_type.value if hasattr(ai_model.model_type, 'value') else str(ai_model.model_type)
            if "gemini" in model_type_str.lower() or "google" in model_type_str.lower():
                provider = "google"
            elif "claude" in model_type_str.lower() or "anthropic" in model_type_str.lower():
                provider = "anthropic"
            elif "openai" in model_type_str.lower() or "gpt" in (ai_model.model_name or "").lower():
                provider = "openai"
            else:
                provider = "openai"  # 兼容性默认值
        
        # 构建AI分析请求
        ai_request = {
            "model_config": {
                "provider": provider,
                "model_name": ai_model.model_name or ai_model.name,
                "api_key": api_key,
                "api_endpoint": ai_model.api_endpoint,
                "temperature": test_data.temperature,
                "max_tokens": test_data.max_tokens
            },
            "prompt": analysis_content,
            "data_content": field_value if not file_contents and not rich_text_images else "",  # 如果有文件内容或图片，就不用文本描述
            "file_contents": file_contents,  # 实际文件内容
            "rich_text_images": rich_text_images,  # 富文本图片数据
            "context": {
                "test_mode": True,
                "webhook_data": test_data.webhook_data,
                "has_files": len(file_contents) > 0,
                "has_rich_text_images": len(rich_text_images) > 0,
                "content_type": test_data.content_type or "plain_text"
            }
        }
        
        # 调用AI分析服务
        ai_result = await ai_service.analyze_content(ai_request)
        
        if not ai_result or not ai_result.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=f"AI分析失败: {ai_result.get('error', '未知错误')}"
            )
        
        # 计算响应时间
        response_time = int((time.time() - start_time) * 1000)
        
        # 构建响应
        response = AiAnalysisTestResponse(
            success=True,
            content=ai_result.get('content', ''),
            model_name=f"{provider}/{ai_model.model_name or ai_model.name}",
            token_usage={
                "prompt_tokens": ai_result.get('usage', {}).get('prompt_tokens', 0),
                "completion_tokens": ai_result.get('usage', {}).get('completion_tokens', 0),
                "total_tokens": ai_result.get('usage', {}).get('total_tokens', 0)
            },
            response_time=response_time
        )
        
        logger.info(f"AI分析测试成功: 模型={ai_model.model_name}, 耗时={response_time}ms")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI分析测试失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"AI分析测试失败: {str(e)}"
        )


@router.post("/test-feishu-config/")
async def test_feishu_config(
    config_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """测试飞书配置"""
    try:
        feishu_writer = FeishuResultWriter(config_data)
        test_result = await feishu_writer.test_connection()
        
        return {
            "success": test_result.get("success", False),
            "message": test_result.get("message", "测试完成")
        }
    except Exception as e:
        logger.error(f"飞书配置测试失败: {str(e)}")
        return {
            "success": False,
            "message": f"测试失败: {str(e)}"
        }


@router.post("/query-rich-text-field/", response_model=RichTextQueryResponse)
async def query_rich_text_field(
    query_data: RichTextQueryRequest,
    db: Session = Depends(get_db)
):
    """查询富文本字段详细信息"""
    try:
        logger.info("收到富文本字段查询请求")

        # 从环境变量获取飞书配置
        import os
        plugin_id = os.getenv("FEISHU_PLUGIN_ID", "")
        plugin_secret = os.getenv("FEISHU_PLUGIN_SECRET", "")
        user_key = os.getenv("FEISHU_USER_KEY", "")

        if not all([plugin_id, plugin_secret, user_key]):
            missing = []
            if not plugin_id: missing.append("FEISHU_PLUGIN_ID")
            if not plugin_secret: missing.append("FEISHU_PLUGIN_SECRET")
            if not user_key: missing.append("FEISHU_USER_KEY")
            raise HTTPException(
                status_code=500,
                detail=f"飞书配置缺失，请检查环境变量: {', '.join(missing)}"
            )

        logger.info(f"从环境变量获取飞书配置 - Plugin ID: {plugin_id[:10]}..., User Key: {user_key}")

        # 创建飞书API客户端实例
        from app.services.feishu_service import FeishuProjectAPI

        # 使用默认主机地址，如果需要可以从配置中读取
        feishu_host = "https://project.feishu.cn"

        # 创建API客户端（使用虚拟的app_id和app_secret，因为我们使用的是plugin token方式）
        async with FeishuProjectAPI(
            host=feishu_host,
            app_id="dummy_app_id",  # plugin token方式不需要真实的app_id
            app_secret="dummy_secret",  # plugin token方式不需要真实的app_secret
            user_id=user_key
        ) as api_client:

            # 调用富文本字段查询方法（使用环境变量中的配置）
            result = await api_client.query_rich_text_field(
                webhook_data=query_data.webhook_data,
                plugin_id=plugin_id,
                plugin_secret=plugin_secret,
                user_key=user_key
            )
            
            logger.info(f"富文本字段查询结果: {result.get('success', False)}")
            
            # 构建响应
            response = RichTextQueryResponse(
                success=result.get("success", False),
                message=result.get("message"),
                field_key=result.get("field_key"),
                doc=result.get("doc"),
                doc_text=result.get("doc_text"),
                doc_html=result.get("doc_html"),
                is_empty=result.get("is_empty"),
                work_item_id=result.get("work_item_id"),
                work_item_name=result.get("work_item_name"),
                webhook_info=result.get("webhook_info"),
                timestamp=result.get("timestamp"),
                error=result.get("error"),
                # 图片相关字段
                has_images=result.get("has_images", False),
                image_uuids=result.get("image_uuids", []),
                downloaded_images=result.get("downloaded_images", []),
                download_count=result.get("download_count", 0),
                download_failed_count=result.get("download_failed_count", 0)
            )
            
            return response
            
    except Exception as e:
        logger.error(f"查询富文本字段失败: {str(e)}", exc_info=True)
        
        return RichTextQueryResponse(
            success=False,
            message=f"查询失败: {str(e)}",
            error=str(e),
            timestamp=datetime.now().isoformat(),
            # 图片相关字段默认值
            has_images=False,
            image_uuids=[],
            downloaded_images=[],
            download_count=0,
            download_failed_count=0
        )


@router.post("/get-plugin-token/")
async def get_plugin_token(
    request: PluginTokenRequest,
    db: Session = Depends(get_db)
):
    """获取飞书Plugin Token（用于图片下载认证）"""
    try:
        logger.info("收到获取Plugin Token请求")
        
        # 创建飞书API客户端实例
        from app.services.feishu_service import FeishuProjectAPI
        
        # 使用默认主机地址
        feishu_host = "https://project.feishu.cn"
        
        # 创建API客户端
        async with FeishuProjectAPI(
            host=feishu_host,
            app_id="dummy_app_id",
            app_secret="dummy_secret",
            user_id=os.getenv("FEISHU_USER_KEY", "")
        ) as api_client:
            
            # 获取plugin token
            plugin_token = await api_client.get_plugin_token(
                plugin_id=request.plugin_id,
                plugin_secret=request.plugin_secret
            )
            
            logger.info("Plugin Token获取成功")
            
            return {
                "success": True,
                "plugin_token": plugin_token,
                "message": "Plugin Token获取成功"
            }
            
    except Exception as e:
        logger.error(f"获取Plugin Token失败: {str(e)}", exc_info=True)
        
        return {
            "success": False,
            "message": f"获取Plugin Token失败: {str(e)}",
            "error": str(e)
        }


@router.post("/test-feishu-write/", response_model=FeishuWriteTestResponse)
async def test_feishu_write(
    request_data: FeishuWriteTestRequest,
    db: Session = Depends(get_db)
):
    """测试飞书项目数据写入功能"""
    try:
        logger.info("收到飞书写入测试请求")
        
        # 创建飞书API客户端实例
        from app.services.feishu_service import FeishuProjectAPI
        
        # 使用默认主机地址
        feishu_host = "https://project.feishu.cn"
        
        # 创建API客户端
        async with FeishuProjectAPI(
            host=feishu_host,
            app_id="dummy_app_id",
            app_secret="dummy_secret",
            user_id=request_data.user_key
        ) as api_client:
            
            # 第一步：获取plugin_token（如果没有提供）
            plugin_token = request_data.plugin_token
            if not plugin_token:
                logger.info("获取plugin_token...")
                # 从环境变量获取飞书API配置
                import os
                plugin_id = os.getenv("FEISHU_PLUGIN_ID", "")
                plugin_secret = os.getenv("FEISHU_PLUGIN_SECRET", "")
                
                if not plugin_id or not plugin_secret:
                    logger.error("飞书API配置缺失，请检查环境变量: FEISHU_PLUGIN_ID, FEISHU_PLUGIN_SECRET")
                    return {"success": False, "message": "飞书API配置缺失"}
                
                plugin_token = await api_client.get_plugin_token(
                    plugin_id=plugin_id,
                    plugin_secret=plugin_secret
                )
                logger.info("plugin_token获取成功")
            
            # 第二步：构建飞书项目数据写入请求
            # 按照文档要求的接口格式：
            # PUT https://project.feishu.cn/open_api/:project_key/work_item/:work_item_type_key/:work_item_id
            update_url = f"https://project.feishu.cn/open_api/{request_data.project_key}/work_item/{request_data.work_item_type_key}/{request_data.work_item_id}"
            
            # 确保user_key不为空，如果为空则从环境变量获取
            user_key = request_data.user_key
            if not user_key:
                import os
                user_key = os.getenv("FEISHU_USER_KEY", "")
                if not user_key:
                    logger.error("飞书用户标识缺失，请检查环境变量: FEISHU_USER_KEY")
                    return FeishuWriteTestResponse(
                        success=False,
                        message="飞书用户标识缺失，请检查环境变量: FEISHU_USER_KEY",
                        error="Missing FEISHU_USER_KEY"
                    )

            logger.info(f"使用用户标识: {user_key[:10]}..." if len(user_key) > 10 else f"使用用户标识: {user_key}")

            headers = {
                "Content-Type": "application/json",
                "X-PLUGIN-TOKEN": plugin_token,
                "X-USER-KEY": user_key
            }
            
            # 第三步：将AI分析结果转换为富文本格式
            logger.info("转换AI分析结果为飞书富文本格式...")
            
            try:
                from app.utils.markdown_converter import convert_markdown_to_feishu
                rich_text_content = convert_markdown_to_feishu(request_data.analysis_result)
                logger.info(f"成功转换为富文本，包含 {len(rich_text_content)} 个内容块")
                
                # 使用富文本格式作为字段值
                field_value = rich_text_content
                
            except Exception as convert_error:
                logger.warning(f"富文本转换失败，使用纯文本格式: {convert_error}")
                # 降级处理：使用纯文本
                field_value = request_data.analysis_result
            
            # 按照文档要求的请求体格式
            request_body = {
                "update_fields": [{
                    "field_key": request_data.field_key,
                    "field_value": field_value,
                    "target_state": {
                        "state_key": "",
                        "transition_id": 0
                    },
                    "field_type_key": "",
                    "field_alias": "",
                    "help_description": ""
                }]
            }
            
            logger.info(f"发送飞书写入请求到: {update_url}")
            logger.info(f"请求体: {request_body}")
            
            # 第三步：发送PUT请求到飞书项目API
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.put(update_url, headers=headers, json=request_body) as response:
                    response_text = await response.text()
                    logger.info(f"飞书API响应状态: {response.status}")
                    logger.info(f"飞书API响应内容: {response_text}")
                    
                    try:
                        response_json = await response.json() if response.status != 204 else {}
                    except:
                        response_json = {"raw_response": response_text}
                    
                    if response.status in [200, 204]:
                        # 写入成功
                        return FeishuWriteTestResponse(
                            success=True,
                            message="飞书数据写入成功",
                            project_key=request_data.project_key,
                            work_item_id=request_data.work_item_id,
                            work_item_type_key=request_data.work_item_type_key,
                            field_key=request_data.field_key,
                            write_response=response_json
                        )
                    else:
                        # 写入失败
                        error_msg = response_json.get("error", {}).get("msg", "未知错误") if isinstance(response_json, dict) else str(response_json)
                        
                        return FeishuWriteTestResponse(
                            success=False,
                            message=f"飞书数据写入失败: HTTP {response.status}",
                            project_key=request_data.project_key,
                            work_item_id=request_data.work_item_id,
                            work_item_type_key=request_data.work_item_type_key,
                            field_key=request_data.field_key,
                            error=error_msg,
                            details=response_text
                        )
            
    except Exception as e:
        logger.error(f"飞书写入测试失败: {str(e)}", exc_info=True)
        
        return FeishuWriteTestResponse(
            success=False,
            message=f"测试失败: {str(e)}",
            error=str(e),
            details=f"异常信息: {str(e)}"
        )


@router.post("/test-multi-field-query/", response_model=MultiFieldTestResponse)
async def test_multi_field_query(
    request_data: MultiFieldTestRequest,
    db: Session = Depends(get_db)
):
    """测试多字段查询功能"""
    import time
    from datetime import datetime

    start_time = time.time()

    try:
        logger.info("收到多字段查询测试请求")

        # 从环境变量获取飞书配置
        import os
        plugin_id = os.getenv("FEISHU_PLUGIN_ID", "")
        plugin_secret = os.getenv("FEISHU_PLUGIN_SECRET", "")
        user_key = os.getenv("FEISHU_USER_KEY", "")

        if not all([plugin_id, plugin_secret, user_key]):
            missing = []
            if not plugin_id: missing.append("FEISHU_PLUGIN_ID")
            if not plugin_secret: missing.append("FEISHU_PLUGIN_SECRET")
            if not user_key: missing.append("FEISHU_USER_KEY")
            raise HTTPException(
                status_code=500,
                detail=f"飞书配置缺失，请检查环境变量: {', '.join(missing)}"
            )

        # 提取必要的项目信息
        webhook_data = request_data.webhook_data
        project_key = webhook_data.get('project_key')
        work_item_type_key = webhook_data.get('work_item_type_key')
        work_item_id = str(webhook_data.get('id', ''))

        if not all([project_key, work_item_type_key, work_item_id]):
            raise HTTPException(
                status_code=400,
                detail="Webhook数据缺少必需字段: project_key, work_item_type_key, id"
            )

        logger.info(f"开始测试多字段查询: 项目={project_key}, 工作项类型={work_item_type_key}, 工作项ID={work_item_id}")
        logger.info(f"配置的字段数量: {len(request_data.multi_field_config.fields)}")

        # 创建飞书API客户端
        from app.services.feishu_service import FeishuProjectAPI
        feishu_host = "https://project.feishu.cn"

        async with FeishuProjectAPI(
            host=feishu_host,
            app_id="dummy_app_id",
            app_secret="dummy_secret",
            user_id=user_key
        ) as api_client:

            # 获取plugin token
            plugin_token = await api_client.get_plugin_token(
                plugin_id=plugin_id,
                plugin_secret=plugin_secret
            )

            # 提取字段标识符列表
            field_keys = [field.field_key for field in request_data.multi_field_config.fields]
            logger.info(f"查询字段: {field_keys}")

            # 调用多字段查询方法
            result = await api_client.query_multiple_fields(
                project_key=project_key,
                work_item_type_key=work_item_type_key,
                work_item_id=work_item_id,
                field_keys=field_keys,
                plugin_token=plugin_token,
                user_key=user_key
            )

            # 计算执行时间
            execution_time_ms = int((time.time() - start_time) * 1000)

            # 分析查询结果
            field_data = result.get('field_data', {})
            failed_fields = []
            query_details = []

            for field_config in request_data.multi_field_config.fields:
                field_key = field_config.field_key
                field_name = field_config.field_name

                if field_key in field_data:
                    # 查询成功
                    field_value = field_data[field_key]
                    query_details.append({
                        "field_key": field_key,
                        "field_name": field_name,
                        "success": True,
                        "value": field_value,
                        "value_type": type(field_value).__name__,
                        "has_value": field_value is not None and field_value != ""
                    })
                else:
                    # 查询失败
                    failed_fields.append(field_key)
                    query_details.append({
                        "field_key": field_key,
                        "field_name": field_name,
                        "success": False,
                        "error": "字段查询失败或不存在"
                    })

            success = len(failed_fields) == 0
            successful_field_count = len(field_data)

            logger.info(f"多字段查询完成: 成功 {successful_field_count}/{len(field_keys)} 个字段")

            return MultiFieldTestResponse(
                success=success,
                message=f"多字段查询完成，成功查询 {successful_field_count}/{len(field_keys)} 个字段",
                project_key=project_key,
                work_item_id=work_item_id,
                work_item_type_key=work_item_type_key,
                field_data=field_data,
                field_count=successful_field_count,
                failed_fields=failed_fields if failed_fields else None,
                query_details=query_details,
                timestamp=datetime.now().isoformat(),
                execution_time_ms=execution_time_ms
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多字段查询测试失败: {str(e)}", exc_info=True)
        execution_time_ms = int((time.time() - start_time) * 1000)

        return MultiFieldTestResponse(
            success=False,
            message=f"多字段查询测试失败: {str(e)}",
            timestamp=datetime.now().isoformat(),
            execution_time_ms=execution_time_ms,
            error=str(e)
        )


@router.post("/test-multi-field-analysis/", response_model=MultiFieldAnalysisTestResponse)
async def test_multi_field_analysis(
    request_data: MultiFieldAnalysisTestRequest,
    db: Session = Depends(get_db)
):
    """测试多字段综合分析功能"""
    import time
    from datetime import datetime

    start_time = time.time()
    field_query_start = None
    ai_analysis_start = None

    try:
        logger.info(f"收到多字段综合分析测试请求 - 任务ID: {request_data.task_id}")

        # 验证任务是否存在并启用了多字段分析
        task = db.query(AnalysisTask).filter(AnalysisTask.id == request_data.task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="指定的分析任务不存在")

        if not task.enable_multi_field_analysis:
            raise HTTPException(status_code=400, detail="指定的任务未启用多字段分析功能")

        if not task.multi_field_config:
            raise HTTPException(status_code=400, detail="指定的任务缺少多字段配置")

        # 验证AI模型
        if not task.ai_model_id:
            raise HTTPException(status_code=400, detail="任务未配置AI模型")

        ai_model = db.query(AIModel).filter(AIModel.id == task.ai_model_id).first()
        if not ai_model or not ai_model.is_active:
            raise HTTPException(status_code=400, detail="任务配置的AI模型不存在或未启用")

        # 从环境变量获取飞书配置
        import os
        plugin_id = os.getenv("FEISHU_PLUGIN_ID", "")
        plugin_secret = os.getenv("FEISHU_PLUGIN_SECRET", "")
        user_key = os.getenv("FEISHU_USER_KEY", "")

        if not all([plugin_id, plugin_secret, user_key]):
            raise HTTPException(status_code=500, detail="飞书配置缺失")

        # 提取项目信息
        webhook_data = request_data.webhook_data
        project_key = webhook_data.get('project_key')
        work_item_type_key = webhook_data.get('work_item_type_key')
        work_item_id = str(webhook_data.get('id', ''))

        logger.info(f"开始多字段综合分析测试: 任务={task.name}, 项目={project_key}, 工作项={work_item_id}")

        # 第一阶段：多字段查询
        field_query_start = time.time()
        logger.info("=== 第一阶段：多字段查询 ===")

        from app.services.feishu_service import FeishuProjectAPI
        feishu_host = "https://project.feishu.cn"

        field_data = {}
        field_query_success = False

        async with FeishuProjectAPI(
            host=feishu_host,
            app_id="dummy_app_id",
            app_secret="dummy_secret",
            user_id=user_key
        ) as api_client:

            # 获取plugin token
            plugin_token = await api_client.get_plugin_token(
                plugin_id=plugin_id,
                plugin_secret=plugin_secret
            )

            # 解析多字段配置
            multi_field_config = task.multi_field_config
            field_keys = [field['field_key'] for field in multi_field_config['fields']]

            # 调用多字段查询
            query_result = await api_client.query_multiple_fields(
                project_key=project_key,
                work_item_type_key=work_item_type_key,
                work_item_id=work_item_id,
                field_keys=field_keys,
                plugin_token=plugin_token,
                user_key=user_key
            )

            field_data = query_result.get('field_data', {})
            field_query_success = len(field_data) > 0

        field_query_time_ms = int((time.time() - field_query_start) * 1000)
        logger.info(f"字段查询完成，耗时 {field_query_time_ms}ms，获取到 {len(field_data)} 个字段")

        if not field_query_success:
            raise Exception("多字段查询失败，未获取到任何字段数据")

        # 第二阶段：AI分析
        ai_analysis_start = time.time()
        logger.info("=== 第二阶段：AI综合分析 ===")

        # 使用任务的提示词模板或请求中的覆盖提示词
        prompt_template = request_data.override_prompt or task.user_prompt_template or "请分析以下数据："

        # 模板渲染：将字段数据插入提示词模板
        rendered_prompt = prompt_template
        for field_config in multi_field_config['fields']:
            placeholder = field_config['placeholder']
            field_key = field_config['field_key']
            field_value = field_data.get(field_key, "")

            # 安全的字符串转换
            safe_value = str(field_value) if field_value is not None else ""
            rendered_prompt = rendered_prompt.replace(f'{{{placeholder}}}', safe_value)

        logger.info(f"渲染后的提示词长度: {len(rendered_prompt)} 字符")

        # 推断AI模型提供商
        provider = "openai"  # 默认值
        if ai_model.model_type:
            model_type_str = ai_model.model_type.value if hasattr(ai_model.model_type, 'value') else str(ai_model.model_type)
            if "gemini" in model_type_str.lower():
                provider = "google"
            elif "claude" in model_type_str.lower():
                provider = "anthropic"

        # 构建AI分析请求
        ai_request = {
            "model_config": {
                "provider": provider,
                "model_name": ai_model.model_name or ai_model.name,
                "api_key": ai_model.api_key,
                "api_endpoint": ai_model.api_endpoint,
                "temperature": task.temperature or 1.0,
                "max_tokens": task.max_tokens or 10000
            },
            "prompt": rendered_prompt,
            "data_content": "",  # 多字段模式下数据已嵌入提示词
            "file_contents": [],
            "rich_text_images": [],
            "context": {
                "test_mode": True,
                "multi_field_analysis": True,
                "field_count": len(field_data),
                "webhook_data": webhook_data
            }
        }

        # 调用AI分析服务
        ai_result = await ai_service.analyze_content(ai_request)
        ai_analysis_time_ms = int((time.time() - ai_analysis_start) * 1000)

        ai_analysis_success = ai_result and ai_result.get('success', False)
        analysis_result = ai_result.get('content', '') if ai_analysis_success else ""

        logger.info(f"AI分析完成，耗时 {ai_analysis_time_ms}ms，成功: {ai_analysis_success}")

        if not ai_analysis_success:
            raise Exception(f"AI分析失败: {ai_result.get('error', '未知错误')}")

        # 计算总执行时间
        total_execution_time_ms = int((time.time() - start_time) * 1000)

        return MultiFieldAnalysisTestResponse(
            success=True,
            message="多字段综合分析测试完成",
            task_id=task.id,
            task_name=task.name,

            # 查询阶段结果
            field_query_success=field_query_success,
            field_data=field_data,
            field_count=len(field_data),

            # 分析阶段结果
            ai_analysis_success=ai_analysis_success,
            analysis_result=analysis_result,
            rendered_prompt=rendered_prompt if len(rendered_prompt) < 2000 else rendered_prompt[:1997] + "...",

            # 模型使用信息
            model_name=f"{provider}/{ai_model.model_name or ai_model.name}",
            token_usage={
                "prompt_tokens": ai_result.get('usage', {}).get('prompt_tokens', 0),
                "completion_tokens": ai_result.get('usage', {}).get('completion_tokens', 0),
                "total_tokens": ai_result.get('usage', {}).get('total_tokens', 0)
            },

            # 执行统计
            total_execution_time_ms=total_execution_time_ms,
            field_query_time_ms=field_query_time_ms,
            ai_analysis_time_ms=ai_analysis_time_ms,

            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"多字段综合分析测试失败: {str(e)}", exc_info=True)

        # 计算执行时间
        total_execution_time_ms = int((time.time() - start_time) * 1000)
        field_query_time_ms = int((time.time() - field_query_start) * 1000) if field_query_start else 0
        ai_analysis_time_ms = int((time.time() - ai_analysis_start) * 1000) if ai_analysis_start else 0

        return MultiFieldAnalysisTestResponse(
            success=False,
            message=f"多字段综合分析测试失败: {str(e)}",
            task_id=request_data.task_id,
            timestamp=datetime.now().isoformat(),
            total_execution_time_ms=total_execution_time_ms,
            field_query_time_ms=field_query_time_ms,
            ai_analysis_time_ms=ai_analysis_time_ms,
            error=str(e)
        )