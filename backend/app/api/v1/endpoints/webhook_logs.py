from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.webhook_log_simple import WebhookLog
from app.models.webhook import Webhook
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class WebhookLogResponse(BaseModel):
    id: int
    webhook_id: int
    webhook_name: Optional[str] = None
    request_id: Optional[str] = None
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_headers: Optional[Dict[str, Any]] = None
    request_payload: Optional[Dict[str, Any]] = None
    request_size_bytes: Optional[int] = None
    response_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    is_valid: bool = True
    validation_errors: Optional[List[str]] = None
    task_execution_id: Optional[int] = None
    created_at: str
    
    class Config:
        from_attributes = True


class WebhookLogSummary(BaseModel):
    id: int
    webhook_id: int
    webhook_name: Optional[str] = None
    method: str = "POST"
    status: str
    source_ip: Optional[str] = None
    response_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    created_at: str
    
    class Config:
        from_attributes = True


class WebhookLogPaginatedResponse(BaseModel):
    items: List[Dict[str, Any]]  # 改为通用字典类型以支持完整数据
    total: int
    page: int
    size: int

@router.get("/", response_model=WebhookLogPaginatedResponse)
async def get_webhook_logs(
    webhook_id: Optional[int] = Query(None, description="过滤特定Webhook的日志"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=200, description="限制记录数"),
    db: Session = Depends(get_db)
):
    """获取Webhook日志列表"""
    try:
        query = db.query(WebhookLog).join(Webhook, WebhookLog.webhook_id == Webhook.id)
        
        if webhook_id:
            query = query.filter(WebhookLog.webhook_id == webhook_id)
        
        # 获取总数
        total = query.count()
        
        # 获取分页数据
        logs = query.order_by(desc(WebhookLog.created_at)).offset(skip).limit(limit).all()
        
        result = []
        for log in logs:
            webhook_name = log.webhook.name if log.webhook else f"Webhook-{log.webhook_id}"
            status = "成功" if log.is_successful() else "失败" if log.response_status else "处理中"
            
            # 返回完整的详细数据而不是简化版
            result.append({
                "id": log.id,
                "webhook_id": log.webhook_id,
                "webhook_name": webhook_name,
                "method": "POST",
                "status": status,
                "source_ip": str(log.source_ip) if log.source_ip else None,
                "response_status": log.response_status,
                "response_time_ms": log.response_time_ms,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "request_payload": log.request_payload,
                "request_headers": log.request_headers,
                "validation_errors": log.validation_errors,
                "is_valid": log.is_valid,
                "user_agent": log.user_agent
            })
        
        logger.info(f"返回{len(result)}条Webhook日志记录，总计{total}条")
        
        return WebhookLogPaginatedResponse(
            items=result,
            total=total,
            page=(skip // limit) + 1,
            size=limit
        )
        
    except Exception as e:
        logger.error(f"获取Webhook日志失败: {e}")
        raise HTTPException(status_code=500, detail="获取日志失败")


@router.get("/{log_id}", response_model=WebhookLogResponse)
async def get_webhook_log(
    log_id: int,
    db: Session = Depends(get_db)
):
    """获取Webhook日志详情"""
    try:
        log = db.query(WebhookLog).join(Webhook, WebhookLog.webhook_id == Webhook.id).filter(
            WebhookLog.id == log_id
        ).first()
        
        if not log:
            raise HTTPException(status_code=404, detail="Webhook日志不存在")
        
        webhook_name = log.webhook.name if log.webhook else f"Webhook-{log.webhook_id}"
        
        return WebhookLogResponse(
            id=log.id,
            webhook_id=log.webhook_id,
            webhook_name=webhook_name,
            request_id=log.request_id,
            source_ip=str(log.source_ip) if log.source_ip else None,
            user_agent=log.user_agent,
            request_headers=log.request_headers,
            request_payload=log.request_payload,
            request_size_bytes=log.request_size_bytes,
            response_status=log.response_status,
            response_time_ms=log.response_time_ms,
            is_valid=log.is_valid,
            validation_errors=log.validation_errors,
            task_execution_id=log.task_execution_id,
            created_at=log.created_at.isoformat() if log.created_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Webhook日志详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取日志详情失败")


@router.get("/stats/summary")
async def get_webhook_logs_stats(
    webhook_id: Optional[int] = Query(None, description="特定Webhook的统计"),
    db: Session = Depends(get_db)
):
    """获取Webhook日志统计信息"""
    try:
        query = db.query(WebhookLog)
        
        if webhook_id:
            query = query.filter(WebhookLog.webhook_id == webhook_id)
        
        total_logs = query.count()
        success_logs = query.filter(WebhookLog.response_status >= 200, WebhookLog.response_status < 300).count()
        failed_logs = query.filter(WebhookLog.response_status >= 400).count()
        pending_logs = query.filter(WebhookLog.response_status.is_(None)).count()
        
        return {
            "total": total_logs,
            "success": success_logs,
            "failed": failed_logs,
            "pending": pending_logs,
            "success_rate": (success_logs / total_logs * 100) if total_logs > 0 else 0.0
        }
        
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")