from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import json
import io

from app.core.database import get_db
from app.models.analysis_task import AnalysisTask
from app.models.task_execution_simple import TaskExecution, ExecutionStatus

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats() -> Dict[str, Any]:
    """获取仪表板统计数据"""
    try:
        # 模拟仪表板统计数据，实际应从数据库获取
        return {
            "total_tasks": 0,
            "active_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_executions": 0,
            "success_rate": 0.0,
            "avg_execution_time": 0.0,
            "webhook_count": 0,
            "ai_model_count": 0,
            "storage_credential_count": 0
        }
    except Exception as e:
        logger.error(f"获取仪表板统计数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计数据失败")

@router.get("/execution-stats")
async def get_execution_stats(
    start_date: str = None,
    end_date: str = None,
    task_id: int = None
) -> List[Dict[str, Any]]:
    """获取执行统计数据"""
    try:
        # 模拟执行统计数据
        return []
    except Exception as e:
        logger.error(f"获取执行统计数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取执行统计数据失败")

@router.get("/executions")
async def get_executions(
    page: int = 1,
    size: int = 10,
    status: str = None
) -> Dict[str, Any]:
    """获取执行记录列表"""
    try:
        # 模拟执行记录数据
        executions = []
        for i in range(min(size, 5)):  # 返回少量模拟数据
            executions.append({
                "id": f"exec_{1000 + i}",
                "task_id": f"task_{100 + i}",
                "status": "completed" if i % 2 == 0 else "running",
                "started_at": "2025-09-05T14:30:00Z",
                "completed_at": "2025-09-05T14:35:00Z" if i % 2 == 0 else None,
                "duration": 300 if i % 2 == 0 else None,
                "result": "Success" if i % 2 == 0 else None
            })
        
        return {
            "items": executions,
            "total": 25,
            "page": page,
            "size": size,
            "pages": 3
        }
    except Exception as e:
        logger.error(f"获取执行记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取执行记录失败")

@router.get("/overview-stats")
async def get_overview_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取概览统计数据"""
    try:
        # 获取基本统计
        from app.models.analysis_task import TaskStatus
        total_tasks = db.query(AnalysisTask).count()
        active_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == TaskStatus.ACTIVE).count()
        total_executions = db.query(TaskExecution).count()
        
        # 成功和失败的执行
        success_executions = db.query(TaskExecution).filter(
            TaskExecution.execution_status == ExecutionStatus.SUCCESS
        ).count()
        
        # 计算成功率（返回0-1的小数，前端会自动转换为百分比）
        success_rate = round((success_executions / total_executions) if total_executions > 0 else 0, 4)
        
        # 计算平均执行时间
        avg_duration = 0
        executions_with_time = db.query(TaskExecution).filter(
            TaskExecution.execution_time_ms != None
        ).all()
        
        if executions_with_time:
            total_time = sum(ex.execution_time_ms for ex in executions_with_time if ex.execution_time_ms)
            avg_duration = total_time / len(executions_with_time) / 1000 if total_time > 0 else 0
        
        # 计算token总消耗
        total_tokens = sum(
            ex.tokens_used for ex in db.query(TaskExecution).all()
            if ex.tokens_used
        )
        
        # 处理的文件数（有file_url的执行）
        total_files = db.query(TaskExecution).filter(
            TaskExecution.file_url != None
        ).count()
        
        return {
            "total_tasks": total_tasks,
            "total_executions": total_executions,
            "success_rate": success_rate,
            "avg_duration": round(avg_duration, 2),
            "total_tokens": total_tokens,
            "total_files": total_files,
            "active_tasks": active_tasks,
            "avg_file_size": 0,  # 计算平均文件大小
            "tasks_change": 0,
            "executions_change": 0,
            "success_rate_change": 0,
            "duration_change": 0,
            "tokens_change": 0,
            "files_change": 0,
            "active_tasks_change": 0,
            "file_size_change": 0
        }
    except Exception as e:
        logger.error(f"获取概览统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取概览统计失败")

@router.get("/execution-trend")
async def get_execution_trend(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "day",
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取执行趋势数据"""
    try:
        from sqlalchemy import func, text
        from datetime import timezone

        # 设置默认日期范围为最近7天
        if not end_date:
            end_time = datetime.now()
        else:
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if not start_date:
            start_time = end_time - timedelta(days=7)
        else:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        # 根据时间范围查询真实的执行数据
        trend_data = []
        current_date = start_time.date()
        end_date_obj = end_time.date()

        while current_date <= end_date_obj:
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())

            # 查询当天的执行数据
            total_executions = db.query(TaskExecution).filter(
                TaskExecution.started_at >= day_start,
                TaskExecution.started_at <= day_end
            ).count()

            success_executions = db.query(TaskExecution).filter(
                TaskExecution.started_at >= day_start,
                TaskExecution.started_at <= day_end,
                TaskExecution.execution_status == ExecutionStatus.SUCCESS
            ).count()

            failed_executions = db.query(TaskExecution).filter(
                TaskExecution.started_at >= day_start,
                TaskExecution.started_at <= day_end,
                TaskExecution.execution_status == ExecutionStatus.FAILED
            ).count()

            trend_data.append({
                "time": current_date.strftime("%Y-%m-%d"),
                "total": total_executions,
                "success": success_executions,
                "failed": failed_executions
            })

            current_date += timedelta(days=1)

        return trend_data
    except Exception as e:
        logger.error(f"获取执行趋势失败: {e}")
        # 如果出错，返回空数据而不是假数据
        return []

@router.get("/success-rate-trend")
async def get_success_rate_trend(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "day",
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取成功率趋势"""
    try:
        # 设置默认日期范围为最近7天
        if not end_date:
            end_time = datetime.now()
        else:
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if not start_date:
            start_time = end_time - timedelta(days=7)
        else:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        trend_data = []
        current_date = start_time.date()
        end_date_obj = end_time.date()

        while current_date <= end_date_obj:
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())

            # 查询当天的执行数据
            total_executions = db.query(TaskExecution).filter(
                TaskExecution.started_at >= day_start,
                TaskExecution.started_at <= day_end
            ).count()

            success_executions = db.query(TaskExecution).filter(
                TaskExecution.started_at >= day_start,
                TaskExecution.started_at <= day_end,
                TaskExecution.execution_status == ExecutionStatus.SUCCESS
            ).count()

            # 计算成功率（百分比形式，0-100）
            success_rate = (success_executions / total_executions * 100) if total_executions > 0 else 0

            trend_data.append({
                "time": current_date.strftime("%Y-%m-%d"),
                "success_rate": round(success_rate, 1)
            })

            current_date += timedelta(days=1)

        return trend_data
    except Exception as e:
        logger.error(f"获取成功率趋势失败: {e}")
        return []

@router.get("/task-type-distribution")
async def get_task_type_distribution(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取任务类型分布"""
    try:
        from sqlalchemy import func

        # 设置日期过滤条件
        query = db.query(AnalysisTask)

        if start_date:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(AnalysisTask.created_at >= start_time)

        if end_date:
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(AnalysisTask.created_at <= end_time)

        # 根据任务名称或描述推断任务类型，简化处理
        # 在实际项目中，可能需要为AnalysisTask模型添加task_type字段
        task_distribution = []

        # 获取所有任务并简单分类
        tasks = query.all()
        type_counts = {}

        for task in tasks:
            # 简单的任务类型推断逻辑，可以根据实际需求优化
            task_type = "custom_analysis"  # 默认类型

            if task.name:
                name_lower = task.name.lower()
                if any(keyword in name_lower for keyword in ['文档', 'document', 'doc']):
                    task_type = "document_analysis"
                elif any(keyword in name_lower for keyword in ['数据', 'data', 'extract']):
                    task_type = "data_extraction"
                elif any(keyword in name_lower for keyword in ['总结', 'summary', '摘要']):
                    task_type = "content_summary"
                elif any(keyword in name_lower for keyword in ['情感', 'sentiment']):
                    task_type = "sentiment_analysis"
                elif any(keyword in name_lower for keyword in ['关键词', 'keyword']):
                    task_type = "keyword_extraction"

            type_counts[task_type] = type_counts.get(task_type, 0) + 1

        # 转换为返回格式
        for task_type, count in type_counts.items():
            task_distribution.append({
                "task_type": task_type,
                "count": count
            })

        # 如果没有数据，返回空列表而不是假数据
        return task_distribution

    except Exception as e:
        logger.error(f"获取任务类型分布失败: {e}")
        return []

@router.get("/token-trend")
async def get_token_trend(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: str = "day",
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取Token消耗趋势"""
    try:
        from sqlalchemy import func

        # 设置默认日期范围为最近7天
        if not end_date:
            end_time = datetime.now()
        else:
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        if not start_date:
            start_time = end_time - timedelta(days=7)
        else:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

        trend_data = []
        current_date = start_time.date()
        end_date_obj = end_time.date()

        while current_date <= end_date_obj:
            day_start = datetime.combine(current_date, datetime.min.time())
            day_end = datetime.combine(current_date, datetime.max.time())

            # 查询当天的token消耗
            daily_tokens = db.query(func.sum(TaskExecution.tokens_used)).filter(
                TaskExecution.started_at >= day_start,
                TaskExecution.started_at <= day_end,
                TaskExecution.tokens_used != None
            ).scalar()

            trend_data.append({
                "time": current_date.strftime("%Y-%m-%d"),
                "tokens": daily_tokens or 0
            })

            current_date += timedelta(days=1)

        return trend_data
    except Exception as e:
        logger.error(f"获取Token趋势失败: {e}")
        return []

@router.get("/duration-distribution")
async def get_duration_distribution(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取执行时长分布"""
    try:
        # 设置日期过滤条件
        query = db.query(TaskExecution).filter(TaskExecution.execution_time_ms != None)

        if start_date:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(TaskExecution.started_at >= start_time)

        if end_date:
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(TaskExecution.started_at <= end_time)

        executions = query.all()

        # 初始化时长区间计数
        duration_ranges = {
            "0-30s": 0,
            "30-60s": 0,
            "1-2min": 0,
            "2-5min": 0,
            ">5min": 0
        }

        # 统计各时长区间的执行次数
        for execution in executions:
            if execution.execution_time_ms:
                seconds = execution.execution_time_ms / 1000

                if seconds <= 30:
                    duration_ranges["0-30s"] += 1
                elif seconds <= 60:
                    duration_ranges["30-60s"] += 1
                elif seconds <= 120:
                    duration_ranges["1-2min"] += 1
                elif seconds <= 300:
                    duration_ranges["2-5min"] += 1
                else:
                    duration_ranges[">5min"] += 1

        # 转换为返回格式
        return [
            {"range": range_name, "count": count}
            for range_name, count in duration_ranges.items()
        ]

    except Exception as e:
        logger.error(f"获取时长分布失败: {e}")
        return []

@router.get("/file-type-distribution")
async def get_file_type_distribution(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """获取文件类型分布"""
    try:
        import os

        # 设置日期过滤条件
        query = db.query(TaskExecution).filter(TaskExecution.file_url != None)

        if start_date:
            start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(TaskExecution.started_at >= start_time)

        if end_date:
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(TaskExecution.started_at <= end_time)

        executions = query.all()

        # 统计文件类型
        file_type_counts = {}

        for execution in executions:
            if execution.file_url:
                # 从file_url中提取文件扩展名
                file_ext = os.path.splitext(execution.file_url)[1].lower()

                # 将扩展名映射为文件类型
                if file_ext in ['.pdf']:
                    file_type = 'PDF'
                elif file_ext in ['.docx', '.doc']:
                    file_type = 'DOCX'
                elif file_ext in ['.txt']:
                    file_type = 'TXT'
                elif file_ext in ['.md', '.markdown']:
                    file_type = 'MD'
                elif file_ext in ['.xlsx', '.xls']:
                    file_type = 'Excel'
                elif file_ext in ['.pptx', '.ppt']:
                    file_type = 'PowerPoint'
                elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    file_type = '图片'
                else:
                    file_type = '其他'

                file_type_counts[file_type] = file_type_counts.get(file_type, 0) + 1

        # 转换为返回格式
        return [
            {"file_type": file_type, "count": count}
            for file_type, count in file_type_counts.items()
        ]

    except Exception as e:
        logger.error(f"获取文件类型分布失败: {e}")
        return []

@router.get("/task-stats")
async def get_task_stats(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "total_executions",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取任务统计详情"""
    try:
        tasks = db.query(AnalysisTask).all()
        task_stats = []
        
        for task in tasks:
            executions = db.query(TaskExecution).filter(
                TaskExecution.task_id == task.id
            ).all()
            
            total_executions = len(executions)
            success_executions = len([e for e in executions if e.execution_status == ExecutionStatus.SUCCESS])
            failed_executions = len([e for e in executions if e.execution_status == ExecutionStatus.FAILED])
            success_rate = round((success_executions / total_executions * 100) if total_executions > 0 else 0, 1)
            
            # 计算平均时长
            durations = [e.execution_time_ms for e in executions if e.execution_time_ms]
            avg_duration = round(sum(durations) / len(durations) / 1000, 2) if durations else 0
            
            # 计算token消耗
            total_tokens = sum(e.tokens_used for e in executions if e.tokens_used)
            
            # 处理的文件数
            total_files = len([e for e in executions if e.file_url])
            
            # 最后执行时间
            last_execution = max([e.started_at for e in executions], default=None) if executions else None
            
            task_stats.append({
                "task_id": task.id,
                "task_name": task.name,
                "task_type": "custom_analysis",  # 简化处理
                "total_executions": total_executions,
                "success_executions": success_executions,
                "failed_executions": failed_executions,
                "success_rate": success_rate,
                "avg_duration": avg_duration,
                "total_tokens": total_tokens,
                "total_files": total_files,
                "last_execution": last_execution.isoformat() if last_execution else None
            })
        
        # 简单分页
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated_stats = task_stats[start_idx:end_idx]
        
        return {
            "items": paginated_stats,
            "total": len(task_stats),
            "page": page,
            "size": size,
            "pages": (len(task_stats) + size - 1) // size
        }
        
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        return {"items": [], "total": 0, "page": page, "size": size, "pages": 0}

@router.get("/export-report")
async def export_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """导出统计报告"""
    try:
        # 模拟导出功能，返回简单的JSON文件
        report_data = {
            "report_date": datetime.now().isoformat(),
            "summary": {
                "total_tasks": 10,
                "total_executions": 50,
                "success_rate": 85.0
            }
        }
        
        json_str = json.dumps(report_data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.StringIO(json_str),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=analytics_report.json"}
        )
    except Exception as e:
        logger.error(f"导出报告失败: {e}")
        raise HTTPException(status_code=500, detail="导出报告失败")

@router.get("/export-task-stats")
async def export_task_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """导出任务统计"""
    try:
        # 模拟导出功能
        stats_data = {
            "export_date": datetime.now().isoformat(),
            "task_statistics": []
        }
        
        json_str = json.dumps(stats_data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.StringIO(json_str),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=task_stats.json"}
        )
    except Exception as e:
        logger.error(f"导出任务统计失败: {e}")
        raise HTTPException(status_code=500, detail="导出任务统计失败")