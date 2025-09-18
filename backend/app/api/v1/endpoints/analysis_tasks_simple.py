from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from pydantic import BaseModel, Field
from datetime import datetime
import secrets

from app.core.database import get_db
from app.models.analysis_task import AnalysisTask, TaskStatus, TriggerType
from app.models.webhook import Webhook
from app.models.ai_model import AIModel
from app.models.storage_credential import StorageCredential
from app.models.task_execution_simple import TaskExecution, ExecutionStatus
from app.schemas.analysis_task import (
    AnalysisTaskCreate, AnalysisTaskUpdate, AnalysisTaskResponse, AnalysisTaskSimpleResponse,
    TaskConfigurationWizard, TaskValidationResult
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


@router.get("/", response_model=List[AnalysisTaskSimpleResponse])
async def get_analysis_tasks(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    webhook_id: Optional[int] = None,
    ai_model_id: Optional[int] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取分析任务列表"""
    query = db.query(AnalysisTask)
    
    # 状态过滤
    if status:
        try:
            status_enum = TaskStatus(status)
            query = query.filter(AnalysisTask.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的任务状态: {status}")
    
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
    
    # 排序和分页
    tasks = query.order_by(desc(AnalysisTask.updated_at)).offset(skip).limit(limit).all()
    
    return [AnalysisTaskSimpleResponse.from_orm(task) for task in tasks]


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
    
    # 创建任务
    task = AnalysisTask(
        name=task_data.name,
        display_name=task_data.display_name,
        description=task_data.description,
        status=TaskStatus(task_data.status) if task_data.status else TaskStatus.DRAFT,
        trigger_type=TriggerType(task_data.trigger_type) if task_data.trigger_type else TriggerType.WEBHOOK,
        webhook_id=task_data.webhook_id,
        schedule_config=task_data.schedule_config,
        data_parsing_config=task_data.data_parsing_config,
        jsonpath_rules=task_data.jsonpath_rules,
        data_validation_rules=task_data.data_validation_rules,
        storage_credential_id=task_data.storage_credential_id,
        file_path_template=task_data.file_path_template,
        file_filters=task_data.file_filters,
        download_config=task_data.download_config,
        ai_model_id=task_data.ai_model_id,
        system_prompt=task_data.system_prompt,
        user_prompt_template=task_data.user_prompt_template,
        analysis_config=task_data.analysis_config,
        result_config=task_data.result_config,
        feishu_config=task_data.feishu_config,
        field_mapping=task_data.field_mapping,
        timeout_seconds=task_data.timeout_seconds,
        max_retry_attempts=task_data.max_retry_attempts,
        retry_delay_seconds=task_data.retry_delay_seconds,
        max_concurrent_executions=task_data.max_concurrent_executions,
        queue_priority=task_data.queue_priority,
        max_file_size=task_data.max_file_size,
        max_processing_time=task_data.max_processing_time,
        max_memory_usage=task_data.max_memory_usage,
        notification_config=task_data.notification_config,
        success_notification=task_data.success_notification,
        failure_notification=task_data.failure_notification,
        notification_emails=task_data.notification_emails,
        log_level=task_data.log_level,
        log_retention_days=task_data.log_retention_days,
        detailed_logging=task_data.detailed_logging,
        version=1,
        parent_task_id=task_data.parent_task_id,
        is_template=task_data.is_template,
        created_by=1,  # 默认用户ID，系统无需登录
        shared_with_users=task_data.shared_with_users,
        is_public=task_data.is_public,
        tags=task_data.tags,
        category=task_data.category,
        priority=task_data.priority,
        notes=task_data.notes,
    )
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    logger.info(f"创建分析任务成功: {task.name} (ID: {task.id})")
    return AnalysisTaskSimpleResponse.from_orm(task)


@router.get("/{task_id}", response_model=AnalysisTaskSimpleResponse)
async def get_analysis_task(
    task_id: int,
    include_config: bool = True,
    db: Session = Depends(get_db)
):
    """获取分析任务详情"""
    
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    
    return AnalysisTaskSimpleResponse.from_orm(task)


@router.put("/{task_id}", response_model=AnalysisTaskSimpleResponse)
async def update_analysis_task(
    task_id: int,
    task_data: AnalysisTaskUpdate,
    db: Session = Depends(get_db)
):
    """更新分析任务"""
    
    task = db.query(AnalysisTask).filter(
        AnalysisTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="分析任务不存在")
    
    # 更新字段
    update_data = task_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(task, field):
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
    return AnalysisTaskSimpleResponse.from_orm(task)


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
    
    # 检查是否有正在执行的任务
    running_executions = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id,
        TaskExecution.status == ExecutionStatus.RUNNING
    ).count()
    
    if running_executions > 0:
        raise HTTPException(
            status_code=400,
            detail="无法删除任务，还有正在执行的任务实例"
        )
    
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


@router.post("/test-feishu-config", response_model=Dict[str, Any])
async def test_feishu_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """测试飞书写入配置"""
    try:
        from app.services.feishu_writer import FeishuWriteServiceFactory
        
        # 测试配置
        result = await FeishuWriteServiceFactory.test_service(config)
        
        logger.info(f"飞书配置测试: {result}")
        return result
        
    except Exception as e:
        logger.error(f"飞书配置测试失败: {e}")
        return {
            "success": False,
            "message": f"配置测试失败: {str(e)}"
        }