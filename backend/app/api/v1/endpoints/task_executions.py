from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_, func, text
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.models.analysis_task import AnalysisTask
from app.models.task_execution_simple import TaskExecution, ExecutionStatus
from app.models.webhook_log_simple import WebhookLog
from app.schemas.task_execution import TaskExecutionResponse, ExecutionDetailResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class ExecutionFilter(BaseModel):
    status: Optional[str] = None
    task_id: Optional[int] = None
    execution_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_error: Optional[bool] = None


class ExecutionStats(BaseModel):
    total_executions: int
    successful_executions: int
    failed_executions: int
    running_executions: int
    success_rate: float
    avg_execution_time: float
    total_tokens_used: int
    total_cost: float


@router.get("/")
async def get_task_executions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    task_id: Optional[int] = None,
    execution_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    has_error: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取任务执行列表"""
    
    # 构建查询，获取所有任务执行记录，预加载task关联对象
    query = db.query(TaskExecution).options(joinedload(TaskExecution.task))
    
    # 状态过滤
    if status:
        try:
            status_enum = ExecutionStatus(status)
            query = query.filter(TaskExecution.execution_status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的执行状态: {status}")
    
    # 任务ID过滤（使用外键直接过滤，无需join）
    if task_id:
        query = query.filter(TaskExecution.task_id == task_id)
    
    # 执行ID过滤
    if execution_id:
        query = query.filter(TaskExecution.execution_id.ilike(f"%{execution_id}%"))
    
    # 时间范围过滤
    if start_date:
        query = query.filter(TaskExecution.started_at >= start_date)
    
    if end_date:
        query = query.filter(TaskExecution.started_at <= end_date)
    
    # 错误过滤
    if has_error is not None:
        if has_error:
            query = query.filter(TaskExecution.error_message != None)
        else:
            query = query.filter(TaskExecution.error_message == None)
    
    # 获取总数
    total_count = query.count()
    
    # 排序和分页
    executions = query.order_by(desc(TaskExecution.started_at)).offset(skip).limit(limit).all()
    
    # 返回分页响应格式
    return {
        "items": [execution.to_dict() for execution in executions],
        "total": total_count,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total_count + limit - 1) // limit if limit > 0 and total_count > 0 else 0
    }


@router.get("/stats", response_model=ExecutionStats)
async def get_execution_stats(
    days: int = Query(30, description="统计天数", ge=1, le=365),
    task_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取任务执行统计"""
    
    # 时间范围
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 构建查询
    query = db.query(TaskExecution).join(AnalysisTask).filter(
        TaskExecution.started_at >= start_date
    )
    
    if task_id:
        query = query.filter(TaskExecution.task_id == task_id)
    
    executions = query.all()
    
    # 计算统计数据
    total_executions = len(executions)
    successful_executions = sum(1 for e in executions if e.execution_status == ExecutionStatus.SUCCESS)
    failed_executions = sum(1 for e in executions if e.execution_status == ExecutionStatus.FAILED)
    running_executions = sum(1 for e in executions if e.execution_status == ExecutionStatus.PROCESSING)
    
    success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
    
    # 计算平均执行时间（只统计已完成的任务）
    completed_executions = [e for e in executions if e.completed_at and e.started_at]
    if completed_executions:
        total_time = sum((e.completed_at - e.started_at).total_seconds() for e in completed_executions)
        avg_execution_time = total_time / len(completed_executions)
    else:
        avg_execution_time = 0.0
    
    # 计算token和成本（从output_data中提取）
    total_tokens = 0
    total_cost = 0.0
    
    for execution in executions:
        if execution.output_data and isinstance(execution.output_data, dict):
            if 'task_results' in execution.output_data:
                for task_result in execution.output_data['task_results']:
                    if isinstance(task_result, dict):
                        total_tokens += task_result.get('tokens_used', 0)
                        total_cost += float(task_result.get('cost', 0))
    
    return ExecutionStats(
        total_executions=total_executions,
        successful_executions=successful_executions,
        failed_executions=failed_executions,
        running_executions=running_executions,
        success_rate=success_rate,
        avg_execution_time=avg_execution_time,
        total_tokens_used=total_tokens,
        total_cost=total_cost
    )


@router.get("/timeline")
async def get_execution_timeline(
    days: int = Query(7, description="时间线天数", ge=1, le=30),
    task_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取任务执行时间线"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 构建查询
    query = db.query(TaskExecution).join(AnalysisTask).filter(
        TaskExecution.started_at >= start_date
    )
    
    if task_id:
        query = query.filter(TaskExecution.task_id == task_id)
    
    executions = query.order_by(TaskExecution.started_at).all()
    
    # 按天分组统计
    timeline = {}
    for execution in executions:
        date_key = execution.started_at.strftime('%Y-%m-%d')
        
        if date_key not in timeline:
            timeline[date_key] = {
                'date': date_key,
                'total': 0,
                'successful': 0,
                'failed': 0,
                'running': 0,
                'executions': []
            }
        
        timeline[date_key]['total'] += 1
        
        if execution.execution_status == ExecutionStatus.SUCCESS:
            timeline[date_key]['successful'] += 1
        elif execution.execution_status == ExecutionStatus.FAILED:
            timeline[date_key]['failed'] += 1
        elif execution.execution_status == ExecutionStatus.PROCESSING:
            timeline[date_key]['running'] += 1
        
        # 添加执行详情
        timeline[date_key]['executions'].append({
            'id': execution.id,
            'execution_id': execution.execution_id,
            'task_id': execution.task_id,
            'task_name': execution.task.name if execution.task else None,
            'status': execution.execution_status.value,
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'processing_time': (execution.completed_at - execution.started_at).total_seconds() if execution.completed_at and execution.started_at else None,
            'has_error': bool(execution.error_message)
        })
    
    # 转换为列表并按日期排序
    timeline_list = list(timeline.values())
    timeline_list.sort(key=lambda x: x['date'])
    
    return {
        'timeline': timeline_list,
        'summary': {
            'days': days,
            'total_executions': sum(day['total'] for day in timeline_list),
            'total_successful': sum(day['successful'] for day in timeline_list),
            'total_failed': sum(day['failed'] for day in timeline_list),
            'total_running': sum(day['running'] for day in timeline_list),
        }
    }


@router.get("/performance")
async def get_execution_performance(
    days: int = Query(7, description="性能分析天数", ge=1, le=90),
    task_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取任务执行性能分析"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 构建查询
    query = db.query(TaskExecution).join(AnalysisTask).filter(
        TaskExecution.started_at >= start_date,
        TaskExecution.completed_at.isnot(None)
    )
    
    if task_id:
        query = query.filter(TaskExecution.task_id == task_id)
    
    executions = query.all()
    
    if not executions:
        return {
            'execution_times': [],
            'token_usage': [],
            'cost_analysis': [],
            'error_patterns': [],
            'performance_summary': {
                'avg_execution_time': 0,
                'median_execution_time': 0,
                'p95_execution_time': 0,
                'fastest_execution': 0,
                'slowest_execution': 0
            }
        }
    
    # 计算执行时间
    execution_times = []
    token_usage = []
    cost_data = []
    error_patterns = {}
    
    for execution in executions:
        if execution.started_at and execution.completed_at:
            exec_time = (execution.completed_at - execution.started_at).total_seconds()
            execution_times.append({
                'execution_id': execution.execution_id,
                'task_name': execution.task.name if execution.task else None,
                'execution_time': exec_time,
                'started_at': execution.started_at.isoformat(),
                'status': execution.execution_status.value
            })
        
        # 从output_data中提取token和成本数据
        if execution.output_data and isinstance(execution.output_data, dict):
            if 'task_results' in execution.output_data:
                for task_result in execution.output_data['task_results']:
                    if isinstance(task_result, dict):
                        tokens = task_result.get('tokens_used', 0)
                        cost = float(task_result.get('cost', 0))
                        
                        if tokens > 0:
                            token_usage.append({
                                'execution_id': execution.execution_id,
                                'tokens_used': tokens,
                                'cost': cost,
                                'started_at': execution.started_at.isoformat()
                            })
                            
                            cost_data.append(cost)
        
        # 错误模式分析
        if execution.error_message:
            # 简单的错误分类
            error_type = 'unknown'
            error_msg = execution.error_message.lower()
            
            if 'timeout' in error_msg or '超时' in error_msg:
                error_type = 'timeout'
            elif 'connection' in error_msg or 'network' in error_msg or '连接' in error_msg:
                error_type = 'network'
            elif 'auth' in error_msg or 'permission' in error_msg or '权限' in error_msg or '认证' in error_msg:
                error_type = 'auth'
            elif 'file' in error_msg or '文件' in error_msg:
                error_type = 'file_access'
            elif 'parse' in error_msg or 'json' in error_msg or '解析' in error_msg:
                error_type = 'data_parsing'
            elif 'ai' in error_msg or 'model' in error_msg or '模型' in error_msg:
                error_type = 'ai_model'
            
            if error_type not in error_patterns:
                error_patterns[error_type] = {
                    'type': error_type,
                    'count': 0,
                    'examples': []
                }
            
            error_patterns[error_type]['count'] += 1
            if len(error_patterns[error_type]['examples']) < 3:
                error_patterns[error_type]['examples'].append({
                    'execution_id': execution.execution_id,
                    'message': execution.error_message,
                    'started_at': execution.started_at.isoformat()
                })
    
    # 计算性能统计
    times = [item['execution_time'] for item in execution_times]
    performance_summary = {}
    
    if times:
        times.sort()
        n = len(times)
        
        performance_summary = {
            'avg_execution_time': sum(times) / n,
            'median_execution_time': times[n // 2] if n > 0 else 0,
            'p95_execution_time': times[int(n * 0.95)] if n > 0 else 0,
            'fastest_execution': min(times),
            'slowest_execution': max(times)
        }
    
    return {
        'execution_times': sorted(execution_times, key=lambda x: x['started_at']),
        'token_usage': sorted(token_usage, key=lambda x: x['started_at']),
        'cost_analysis': {
            'data': cost_data,
            'total_cost': sum(cost_data),
            'avg_cost_per_execution': sum(cost_data) / len(cost_data) if cost_data else 0,
            'max_cost': max(cost_data) if cost_data else 0,
            'min_cost': min(cost_data) if cost_data else 0
        },
        'error_patterns': list(error_patterns.values()),
        'performance_summary': performance_summary
    }


@router.get("/{execution_id}")
async def get_task_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """获取任务执行详情"""
    
    execution = db.query(TaskExecution).filter(
        TaskExecution.execution_id == execution_id
    ).options(joinedload(TaskExecution.task)).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="任务执行不存在")
    
    return execution.to_dict(include_details=True)


@router.get("/{execution_id}/logs")
async def get_execution_logs(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """获取任务执行日志"""
    
    # 获取执行记录
    execution = db.query(TaskExecution).filter(
        TaskExecution.execution_id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="任务执行不存在")
    
    # 获取相关的webhook日志
    webhook_logs = []
    if execution.task and execution.task.webhook_id:
        webhook_logs = db.query(WebhookLog).filter(
            WebhookLog.webhook_id == execution.task.webhook_id,
            WebhookLog.request_body.ilike(f'%{execution_id}%')
        ).order_by(WebhookLog.created_at).all()
    
    # 构建日志时间线
    logs = []
    
    # 添加webhook接收日志
    for log in webhook_logs:
        logs.append({
            'timestamp': log.created_at.isoformat(),
            'level': 'INFO' if log.response_status == 200 else 'ERROR',
            'source': 'webhook',
            'message': f'Webhook请求: {log.request_method} {log.request_url}',
            'details': {
                'status': log.response_status,
                'processing_time_ms': log.processing_time_ms,
                'client_ip': log.client_ip,
                'user_agent': log.user_agent,
                'error_message': log.error_message
            }
        })
    
    # 添加任务执行日志
    if execution.started_at:
        logs.append({
            'timestamp': execution.started_at.isoformat(),
            'level': 'INFO',
            'source': 'task_execution',
            'message': f'任务执行开始: {execution.task.name if execution.task else "Unknown"}',
            'details': {
                'execution_id': execution.execution_id,
                'task_id': execution.task_id,
                'input_data_size': len(json.dumps(execution.input_data)) if execution.input_data else 0
            }
        })
    
    # 从output_data中提取执行步骤日志
    if execution.output_data and isinstance(execution.output_data, dict):
        if 'execution_log' in execution.output_data:
            for i, log_entry in enumerate(execution.output_data['execution_log']):
                logs.append({
                    'timestamp': execution.started_at.isoformat() if execution.started_at else datetime.utcnow().isoformat(),
                    'level': 'INFO',
                    'source': 'task_processor',
                    'message': log_entry,
                    'details': {'step': i + 1}
                })
        
        if 'task_results' in execution.output_data:
            for task_result in execution.output_data['task_results']:
                if isinstance(task_result, dict) and 'steps' in task_result:
                    for step in task_result['steps']:
                        if isinstance(step, dict):
                            level = 'INFO' if step.get('success', False) else 'ERROR'
                            logs.append({
                                'timestamp': execution.started_at.isoformat() if execution.started_at else datetime.utcnow().isoformat(),
                                'level': level,
                                'source': 'task_step',
                                'message': f'步骤: {step.get("step", "unknown")}',
                                'details': step
                            })
    
    if execution.completed_at:
        level = 'INFO' if execution.execution_status == ExecutionStatus.SUCCESS else 'ERROR'
        logs.append({
            'timestamp': execution.completed_at.isoformat(),
            'level': level,
            'source': 'task_execution',
            'message': f'任务执行结束: {execution.execution_status.value}',
            'details': {
                'execution_id': execution.execution_id,
                'status': execution.execution_status.value,
                'error_message': execution.error_message,
                'processing_time': (execution.completed_at - execution.started_at).total_seconds() if execution.started_at else None
            }
        })
    
    # 按时间排序
    logs.sort(key=lambda x: x['timestamp'])
    
    return {
        'execution_id': execution_id,
        'task_name': execution.task.name if execution.task else None,
        'logs': logs,
        'summary': {
            'total_logs': len(logs),
            'info_count': sum(1 for log in logs if log['level'] == 'INFO'),
            'error_count': sum(1 for log in logs if log['level'] == 'ERROR'),
            'warning_count': sum(1 for log in logs if log['level'] == 'WARNING'),
            'sources': list(set(log['source'] for log in logs)),
            'start_time': execution.started_at.isoformat() if execution.started_at else None,
            'end_time': execution.completed_at.isoformat() if execution.completed_at else None
        }
    }


@router.delete("/{execution_id}")
async def delete_task_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """删除任务执行记录"""
    
    execution = db.query(TaskExecution).filter(
        TaskExecution.execution_id == execution_id
    ).first()
    
    if not execution:
        raise HTTPException(status_code=404, detail="任务执行不存在")
    
    if execution.execution_status == ExecutionStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="无法删除正在运行的任务执行")
    
    db.delete(execution)
    db.commit()
    
    logger.info(f"删除任务执行记录: {execution_id}")
    return {"success": True, "message": "任务执行记录删除成功"}


@router.post("/{execution_id}/retry")
async def retry_task_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """重试任务执行"""

    # 查找原始执行记录
    original_execution = db.query(TaskExecution).filter(
        TaskExecution.execution_id == execution_id
    ).options(joinedload(TaskExecution.task)).first()

    if not original_execution:
        raise HTTPException(status_code=404, detail="任务执行记录不存在")

    # 检查是否有Webhook载荷数据
    if not original_execution.webhook_payload:
        raise HTTPException(status_code=400, detail="任务执行记录缺少Webhook数据，无法重试")

    # 检查任务是否仍然存在且活跃
    if not original_execution.task:
        raise HTTPException(status_code=400, detail="关联的任务不存在，无法重试")

    try:
        # 生成新的执行ID
        import uuid
        new_execution_id = f"retry_{execution_id}_{uuid.uuid4().hex[:8]}"

        # 获取原始Webhook数据
        webhook_payload = original_execution.webhook_payload
        webhook_id = original_execution.task.webhook_id

        if not webhook_id:
            raise HTTPException(status_code=400, detail="任务未关联Webhook，无法重试")

        # 获取客户端信息（使用默认值作为重试标识）
        client_ip = "127.0.0.1"  # 重试标识
        user_agent = f"Retry-Agent/{original_execution.execution_id}"

        logger.info(f"开始重试任务执行: {execution_id} -> {new_execution_id}")

        # 导入Webhook处理器
        from app.tasks.webhook_processor import process_webhook_async
        from fastapi import BackgroundTasks
        import asyncio

        # 创建后台任务来处理重试
        # 注意：这里我们直接调用异步函数，而不是通过BackgroundTasks
        # 因为我们希望能够捕获执行结果并返回给用户
        try:
            # 异步执行重试任务
            retry_result = await process_webhook_async(
                webhook_id=webhook_id,
                payload_data=webhook_payload,
                execution_id=new_execution_id,
                client_ip=client_ip,
                user_agent=user_agent
            )

            # 增加原始执行的重试次数
            original_execution.increment_retry()
            db.commit()

            logger.info(f"重试任务执行完成: {new_execution_id}, 成功: {retry_result.get('success', False)}")

            return {
                "success": True,
                "message": "任务重试已完成",
                "original_execution_id": execution_id,
                "new_execution_id": new_execution_id,
                "retry_result": {
                    "success": retry_result.get("success", False),
                    "task_count": retry_result.get("total_tasks", 0),
                    "successful_tasks": retry_result.get("successful_tasks", 0),
                    "failed_tasks": retry_result.get("failed_tasks", 0),
                    "processing_time": retry_result.get("processing_time_seconds", 0),
                    "error": retry_result.get("error") if not retry_result.get("success", False) else None
                }
            }

        except Exception as processing_error:
            logger.error(f"重试任务处理失败: {processing_error}")

            # 即使处理失败，也要增加重试次数
            original_execution.increment_retry()
            db.commit()

            return {
                "success": False,
                "message": f"任务重试处理失败: {str(processing_error)}",
                "original_execution_id": execution_id,
                "new_execution_id": new_execution_id,
                "error": str(processing_error)
            }

    except Exception as e:
        logger.error(f"重试任务执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"重试任务执行失败: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_executions(
    days: int = Query(30, description="保留天数", ge=7, le=365),
    dry_run: bool = Query(False, description="是否为预览模式"),
    db: Session = Depends(get_db)
):
    """清理旧的任务执行记录"""

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # 查找要删除的执行记录
    old_executions = db.query(TaskExecution).filter(
        TaskExecution.started_at < cutoff_date,
        TaskExecution.execution_status != ExecutionStatus.PROCESSING
    ).all()

    if dry_run:
        # 预览模式，不实际删除
        return {
            "dry_run": True,
            "cutoff_date": cutoff_date.isoformat(),
            "executions_to_delete": len(old_executions),
            "executions": [{
                "execution_id": exec.execution_id,
                "task_name": exec.task.name if exec.task else None,
                "status": exec.execution_status.value,
                "started_at": exec.started_at.isoformat() if exec.started_at else None
            } for exec in old_executions[:10]]  # 只显示前10个
        }

    # 实际删除
    deleted_count = len(old_executions)

    for execution in old_executions:
        db.delete(execution)

    db.commit()

    logger.info(f"清理旧执行记录: 删除了 {deleted_count} 条记录 (保留 {days} 天)")

    return {
        "dry_run": False,
        "cutoff_date": cutoff_date.isoformat(),
        "deleted_count": deleted_count,
        "message": f"成功删除 {deleted_count} 条旧执行记录"
    }