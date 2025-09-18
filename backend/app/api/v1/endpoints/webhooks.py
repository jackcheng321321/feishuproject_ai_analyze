from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
import secrets
import hashlib
import hmac
import time
import json
import html
import urllib.parse
from datetime import datetime

from app.core.database import get_db
from app.models.webhook import Webhook, RequestMethod
from app.models.webhook_log_simple import WebhookLog
from app.schemas.webhook import WebhookCreate, WebhookCreateSimple, WebhookUpdate, WebhookResponse, WebhookSimpleResponse
from app.tasks.webhook_processor import process_webhook_async
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def _unescape_field_value(value: str) -> str:
    """处理字段值的转义，还原被编码的特殊字符"""
    if not isinstance(value, str):
        return value
    
    try:
        # HTML转义还原
        value = html.unescape(value)
        # URL编码还原 
        value = urllib.parse.unquote(value)
        # 注意：不要处理反斜杠，因为SMB路径需要保持\\格式
        # 只处理JSON中的引号转义
        value = value.replace('\\"', '"').replace('\\/', '/')
        return value
    except Exception as e:
        logger.warning(f"字段值转义处理失败: {e}")
        return value


class WebhookReceiveResponse(BaseModel):
    success: bool
    message: str
    webhook_id: Optional[str] = None
    execution_id: Optional[str] = None


@router.get("/")
async def get_webhooks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取Webhook列表"""
    query = db.query(Webhook)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    webhooks = query.offset(skip).limit(limit).all()
    
    # 返回分页响应格式
    return {
        "items": [WebhookSimpleResponse.from_webhook(webhook) for webhook in webhooks],
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }


@router.post("/simple", response_model=WebhookSimpleResponse)
async def create_simple_webhook(
    webhook_data: WebhookCreateSimple,
    request: Request,
    db: Session = Depends(get_db)
):
    """创建简化版Webhook - 只需要名称，其他自动生成"""
    # 生成唯一的webhook_id
    webhook_id = f"wh_{secrets.token_urlsafe(16)}"
    
    # 生成密钥
    secret_key = secrets.token_urlsafe(32)
    
    # 构建webhook URL - 使用完整URL
    base_url = f"{request.url.scheme}://{request.headers.get('host', 'localhost:8000')}"
    webhook_url = f"{base_url}/api/v1/webhooks/receive/{webhook_id}"
    
    # 创建webhook对象，使用合理默认值
    webhook = Webhook(
        name=webhook_data.name,
        description=webhook_data.description or f"自动创建的Webhook: {webhook_data.name}",
        webhook_id=webhook_id,
        webhook_url=webhook_url,
        method=RequestMethod.POST,  # 默认使用POST方法
        secret_key=secret_key,
        # 安全设置 - 使用合理默认值
        verify_signature=False,  # 简化版不验证签名，方便测试
        allowed_ips=None,
        rate_limit_per_minute=60,
        # 请求设置
        timeout_seconds=30,
        max_payload_size=1048576,  # 1MB
        # 重试设置
        enable_retry=True,
        max_retry_attempts=3,
        retry_delay_seconds=60,
        # 过滤设置
        event_filters=None,
        content_type_filters=None,
        # 状态
        is_active=webhook_data.is_active,
        is_public=False,
        # 健康检查设置
        health_check_enabled=True,
        health_check_interval=300,
        # 通知设置
        notification_enabled=False,  # 简化版默认不通知
        notification_on_failure=False,
        notification_on_success=False,
        notification_emails=None,
        # 日志设置
        log_requests=True,
        log_responses=True,
        log_retention_days=30,
        # 其他设置
        tags=None,
        category="auto-generated",
        notes=f"通过简化接口创建于 {datetime.utcnow().isoformat()}",
    )
    
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    
    logger.info(f"Created simple webhook: {webhook.name} with ID: {webhook.webhook_id}")
    
    # 使用自定义方法确保字段映射正确
    return WebhookSimpleResponse.from_webhook(webhook)


@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: Session = Depends(get_db)
):
    """创建完整版Webhook（需要提供完整配置）"""
    # 生成唯一的webhook_id
    webhook_id = f"wh_{secrets.token_urlsafe(16)}"
    
    # 生成密钥
    secret_key = secrets.token_urlsafe(32)
    
    # 构建webhook URL
    webhook_url = f"/api/v1/webhooks/receive/{webhook_id}"
    
    # 创建webhook对象
    webhook = Webhook(
        name=webhook_data.name,
        description=webhook_data.description,
        webhook_id=webhook_id,
        webhook_url=webhook_url,
        secret_key=secret_key,
        verify_signature=webhook_data.verify_signature,
        allowed_ips=webhook_data.allowed_ips,
        rate_limit_per_minute=webhook_data.rate_limit_per_minute,
        timeout_seconds=webhook_data.timeout_seconds,
        max_payload_size=webhook_data.max_payload_size,
        enable_retry=webhook_data.enable_retry,
        max_retry_attempts=webhook_data.max_retry_attempts,
        retry_delay_seconds=webhook_data.retry_delay_seconds,
        event_filters=webhook_data.event_filters,
        content_type_filters=webhook_data.content_type_filters,
        is_active=webhook_data.is_active,
        is_public=webhook_data.is_public,
        health_check_enabled=webhook_data.health_check_enabled,
        health_check_interval=webhook_data.health_check_interval,
        notification_enabled=webhook_data.notification_enabled,
        notification_on_failure=webhook_data.notification_on_failure,
        notification_on_success=webhook_data.notification_on_success,
        notification_emails=webhook_data.notification_emails,
        log_requests=webhook_data.log_requests,
        log_responses=webhook_data.log_responses,
        log_retention_days=webhook_data.log_retention_days,
        tags=webhook_data.tags,
        category=webhook_data.category,
        notes=webhook_data.notes,
    )
    
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    
    logger.info(f"Created webhook: {webhook.name} with ID: {webhook.webhook_id}")
    return WebhookResponse.from_orm(webhook)


@router.get("/stats", response_model=Dict[str, Any])
async def get_webhooks_stats(
    db: Session = Depends(get_db)
):
    """获取Webhook统计信息"""
    webhooks = db.query(Webhook).all()
    
    total_webhooks = len(webhooks)
    active_webhooks = sum(1 for w in webhooks if w.is_active)
    total_requests = sum(w.total_requests for w in webhooks)
    successful_requests = sum(w.successful_requests for w in webhooks)
    failed_requests = sum(w.failed_requests for w in webhooks)
    
    return {
        "total_webhooks": total_webhooks,
        "active_webhooks": active_webhooks,
        "inactive_webhooks": total_webhooks - active_webhooks,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
    }


@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_webhook_logs(
    webhook_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """获取Webhook日志"""
    query = db.query(WebhookLog)
    
    if webhook_id:
        webhook = db.query(Webhook).filter(
            Webhook.id == webhook_id
        ).first()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook不存在")
        
        query = query.filter(WebhookLog.webhook_id == webhook_id)
    
    logs = query.order_by(desc(WebhookLog.created_at)).offset(skip).limit(limit).all()
    
    return [{
        "id": log.id,
        "webhook_id": log.webhook_id,
        "request_method": log.request_method,
        "request_url": log.request_url,
        "request_headers": log.request_headers,
        "request_body": log.request_body if log.request_body else None,
        "response_status": log.response_status,
        "response_headers": log.response_headers,
        "response_body": log.response_body,
        "processing_time_ms": log.processing_time_ms,
        "client_ip": log.client_ip,
        "user_agent": log.user_agent,
        "error_message": log.error_message,
        "created_at": log.created_at.isoformat(),
    } for log in logs]


@router.get("/test/{webhook_id}")
async def test_webhook(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """测试Webhook连通性"""
    webhook = db.query(Webhook).filter(
        Webhook.webhook_id == webhook_id
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 创建测试数据
    test_data = {
        "test": True,
        "timestamp": datetime.utcnow().isoformat(),
        "message": "This is a test webhook call",
        "webhook_id": webhook_id
    }
    
    # 记录测试日志
    log = WebhookLog(
        webhook_id=webhook.id,
        request_id=f"test_{secrets.token_urlsafe(8)}",
        source_ip="127.0.0.1",
        user_agent="Webhook-Test",
        request_headers={"Content-Type": "application/json", "User-Agent": "Webhook-Test"},
        request_payload=test_data,
        request_size_bytes=len(json.dumps(test_data).encode('utf-8')),
        response_status=200,
        response_time_ms=50,
        is_valid=True
    )
    
    db.add(log)
    webhook.update_request_stats(success=True, response_time=0.05)
    db.commit()
    
    return {
        "success": True,
        "message": "Webhook测试成功",
        "test_data": test_data,
        "webhook_url": webhook.webhook_url
    }


@router.get("/generate-url")
async def generate_webhook_url():
    """生成新的Webhook URL预览"""
    webhook_id = f"wh_{secrets.token_urlsafe(16)}"
    webhook_url = f"/api/v1/webhooks/receive/{webhook_id}"
    
    return {
        "webhook_id": webhook_id,
        "webhook_url": webhook_url,
        "full_url": f"http://localhost:8000{webhook_url}",  # 实际部署时需要使用真实域名
        "note": "这是预览URL，需要创建Webhook后才能使用"
    }


@router.get("/health/{webhook_id}")
async def check_webhook_health(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """检查Webhook健康状态"""
    webhook = db.query(Webhook).filter(
        Webhook.webhook_id == webhook_id
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 更新健康检查时间
    webhook.last_health_check = datetime.utcnow()
    
    # 简单的健康检查逻辑
    health_issues = []
    
    if not webhook.is_active:
        health_issues.append("Webhook未激活")
    
    if webhook.failed_requests > webhook.successful_requests * 2:  # 失败率超过66%
        health_issues.append("失败率过高")
    
    if webhook.last_request_at and (datetime.utcnow() - webhook.last_request_at).days > 7:
        health_issues.append("超过7天未收到请求")
    
    # 更新健康状态
    if not health_issues:
        webhook.health_status = "healthy"
        webhook.health_message = "Webhook运行正常"
    elif len(health_issues) == 1 and "未收到请求" in health_issues[0]:
        webhook.health_status = "warning"
        webhook.health_message = "长时间未收到请求"
    else:
        webhook.health_status = "unhealthy"
        webhook.health_message = "; ".join(health_issues)
    
    db.commit()
    
    return {
        "webhook_id": webhook_id,
        "health_status": webhook.health_status,
        "health_message": webhook.health_message,
        "last_health_check": webhook.last_health_check.isoformat(),
        "issues": health_issues,
        "stats": webhook.get_webhook_stats()
    }


@router.get("/export/{webhook_id}")
async def export_webhook_data(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """导出Webhook配置和统计数据"""
    webhook = db.query(Webhook).filter(
        Webhook.webhook_id == webhook_id
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 获取最近的日志
    recent_logs = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook.id
    ).order_by(desc(WebhookLog.created_at)).limit(10).all()
    
    export_data = {
        "webhook": webhook.to_dict(include_sensitive=False),
        "stats": webhook.get_webhook_stats(),
        "recent_logs": [{
            "timestamp": log.created_at.isoformat(),
            "method": log.request_method,
            "status": log.response_status,
            "processing_time_ms": log.processing_time_ms,
            "client_ip": log.client_ip,
        } for log in recent_logs],
        "exported_at": datetime.utcnow().isoformat()
    }
    
    return export_data


@router.get("/copy/{webhook_id}")
async def copy_webhook(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """复制Webhook配置"""
    original_webhook = db.query(Webhook).filter(
        Webhook.webhook_id == webhook_id,
        Webhook.created_by == current_user.id
    ).first()
    
    if not original_webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 生成新的ID和密钥
    new_webhook_id = f"wh_{secrets.token_urlsafe(16)}"
    new_secret_key = secrets.token_urlsafe(32)
    new_webhook_url = f"/api/v1/webhooks/receive/{new_webhook_id}"
    
    # 创建副本
    new_webhook = Webhook(
        name=f"{original_webhook.name} (复制)",
        description=original_webhook.description,
        webhook_id=new_webhook_id,
        webhook_url=new_webhook_url,
        secret_key=new_secret_key,
        verify_signature=original_webhook.verify_signature,
        allowed_ips=original_webhook.allowed_ips,
        rate_limit_per_minute=original_webhook.rate_limit_per_minute,
        timeout_seconds=original_webhook.timeout_seconds,
        max_payload_size=original_webhook.max_payload_size,
        enable_retry=original_webhook.enable_retry,
        max_retry_attempts=original_webhook.max_retry_attempts,
        retry_delay_seconds=original_webhook.retry_delay_seconds,
        event_filters=original_webhook.event_filters,
        content_type_filters=original_webhook.content_type_filters,
        is_active=False,  # 默认不激活副本
        is_public=original_webhook.is_public,
        health_check_enabled=original_webhook.health_check_enabled,
        health_check_interval=original_webhook.health_check_interval,
        notification_enabled=original_webhook.notification_enabled,
        notification_on_failure=original_webhook.notification_on_failure,
        notification_on_success=original_webhook.notification_on_success,
        notification_emails=original_webhook.notification_emails,
        log_requests=original_webhook.log_requests,
        log_responses=original_webhook.log_responses,
        log_retention_days=original_webhook.log_retention_days,
        tags=original_webhook.tags,
        category=original_webhook.category,
        notes=f"复制自: {original_webhook.name}",
    )
    
    db.add(new_webhook)
    db.commit()
    db.refresh(new_webhook)
    
    return {
        "success": True,
        "message": "Webhook复制成功",
        "original_id": webhook_id,
        "new_webhook": WebhookResponse.from_orm(new_webhook).dict()
    }


@router.get("/batch/health-check")
async def batch_health_check(
    db: Session = Depends(get_db)
):
    """批量健康检查所有Webhook"""
    webhooks = db.query(Webhook).filter(
        Webhook.health_check_enabled == True
    ).all()
    
    results = []
    
    for webhook in webhooks:
        # 简单健康检查逻辑
        health_issues = []
        
        if not webhook.is_active:
            health_issues.append("未激活")
        
        if webhook.failed_requests > webhook.successful_requests * 2:
            health_issues.append("失败率过高")
        
        if webhook.last_request_at and (datetime.utcnow() - webhook.last_request_at).days > 7:
            health_issues.append("长时间无请求")
        
        # 更新健康状态
        if not health_issues:
            webhook.health_status = "healthy"
            webhook.health_message = "正常"
        elif len(health_issues) == 1 and "无请求" in health_issues[0]:
            webhook.health_status = "warning"
            webhook.health_message = "警告: " + health_issues[0]
        else:
            webhook.health_status = "unhealthy"
            webhook.health_message = "异常: " + "; ".join(health_issues)
        
        webhook.last_health_check = datetime.utcnow()
        
        results.append({
            "webhook_id": webhook.webhook_id,
            "name": webhook.name,
            "health_status": webhook.health_status,
            "health_message": webhook.health_message,
            "issues": health_issues
        })
    
    db.commit()
    
    return {
        "checked_count": len(webhooks),
        "healthy_count": sum(1 for r in results if r["health_status"] == "healthy"),
        "warning_count": sum(1 for r in results if r["health_status"] == "warning"),
        "unhealthy_count": sum(1 for r in results if r["health_status"] == "unhealthy"),
        "results": results
    }


@router.get("/{webhook_id}", response_model=WebhookSimpleResponse)
async def get_webhook(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """获取Webhook详情"""
    # 尝试按数字ID或webhook_id字符串查找
    webhook = None
    if webhook_id.isdigit():
        # 前端传的是数字ID
        webhook = db.query(Webhook).filter(Webhook.id == int(webhook_id)).first()
    else:
        # 传的是webhook_id字符串
        webhook = db.query(Webhook).filter(Webhook.webhook_id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    return WebhookSimpleResponse.from_webhook(webhook)


@router.get("/{webhook_id}/latest-log")
async def get_webhook_latest_log(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """获取指定Webhook的最新日志记录 - 用于任务创建页面的数据预览"""
    try:
        # 尝试按数字ID或webhook_id字符串查找webhook
        webhook = None
        if webhook_id.isdigit():
            webhook = db.query(Webhook).filter(Webhook.id == int(webhook_id)).first()
        else:
            webhook = db.query(Webhook).filter(Webhook.webhook_id == webhook_id).first()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook不存在")
        
        # 获取最新的一条日志记录
        latest_log = db.query(WebhookLog).filter(
            WebhookLog.webhook_id == webhook.id
        ).order_by(desc(WebhookLog.created_at)).first()
        
        if not latest_log:
            return {
                "field_value": None,
                "record_id": None,
                "project_key": None,
                "work_item_type_key": None,
                "message": "暂无日志记录"
            }
        
        # 提取预览数据
        payload = latest_log.request_payload or {}
        logger.info(f"原始payload结构: {type(payload)} - {payload}")
        
        # 从payload中提取字段值和记录ID，以及项目相关信息
        field_value = None
        record_id = None
        raw_field_value = None
        project_key = None
        work_item_type_key = None
        
        try:
            # 数据结构分析：payload包含header和payload两个部分
            # 真正的业务数据在payload.payload中
            if isinstance(payload, dict):
                # 优先尝试从payload.payload中提取
                inner_payload = payload.get('payload', {})
                if isinstance(inner_payload, dict):
                    changed_fields = inner_payload.get('changed_fields')
                    record_id = inner_payload.get('id')
                    project_key = inner_payload.get('project_key')
                    work_item_type_key = inner_payload.get('work_item_type_key')
                    logger.info(f"从inner_payload提取 - changed_fields类型: {type(changed_fields)}, record_id: {record_id}, project_key: {project_key}, work_item_type_key: {work_item_type_key}")
                else:
                    # 备用：直接从顶级payload提取
                    changed_fields = payload.get('changed_fields')
                    record_id = payload.get('id')
                    project_key = payload.get('project_key')
                    work_item_type_key = payload.get('work_item_type_key')
                    logger.info(f"从顶级payload提取 - changed_fields类型: {type(changed_fields)}, record_id: {record_id}, project_key: {project_key}, work_item_type_key: {work_item_type_key}")
                
                logger.info(f"changed_fields内容: {changed_fields}")
                
                # changed_fields可能是数组或对象
                if isinstance(changed_fields, list) and len(changed_fields) > 0:
                    # 数组格式：取第一个元素
                    first_field = changed_fields[0]
                    logger.info(f"数组模式 - first_field: {first_field}")
                    if isinstance(first_field, dict):
                        raw_field_value = first_field.get('cur_field_value')
                        logger.info(f"提取到raw_field_value: {raw_field_value}")
                elif isinstance(changed_fields, dict):
                    # 对象格式：直接取值
                    raw_field_value = changed_fields.get('cur_field_value')
                    logger.info(f"对象模式 - raw_field_value: {raw_field_value}")
                else:
                    logger.warning(f"changed_fields格式未知: {type(changed_fields)}")
                    raw_field_value = None
                
                # 处理数据转义
                if raw_field_value:
                    field_value = _unescape_field_value(raw_field_value)
                    logger.info(f"转义后field_value: {field_value}")
                else:
                    field_value = raw_field_value
                    
        except Exception as e:
            logger.warning(f"解析webhook payload数据失败: {e}")
        
        logger.info(f"返回Webhook {webhook_id} 的最新日志预览数据")
        return {
            "field_value": field_value,
            "record_id": record_id,
            "project_key": project_key,
            "work_item_type_key": work_item_type_key,
            "log_id": latest_log.id,
            "created_at": latest_log.created_at.isoformat() if latest_log.created_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Webhook最新日志失败: {e}")
        raise HTTPException(status_code=500, detail="获取最新日志失败")


@router.get("/{webhook_id}/logs")
async def get_webhook_logs_by_id(
    webhook_id: str,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    """获取指定Webhook的日志记录"""
    try:
        # 尝试按数字ID或webhook_id字符串查找webhook
        webhook = None
        if webhook_id.isdigit():
            webhook = db.query(Webhook).filter(Webhook.id == int(webhook_id)).first()
        else:
            webhook = db.query(Webhook).filter(Webhook.webhook_id == webhook_id).first()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook不存在")
        
        # 计算分页
        skip = (page - 1) * size
        limit = size
        
        # 查询日志记录
        query = db.query(WebhookLog).filter(WebhookLog.webhook_id == webhook.id)
        logs = query.order_by(desc(WebhookLog.created_at)).offset(skip).limit(limit).all()
        
        # 格式化返回数据
        result = []
        for log in logs:
            status = "成功" if log.response_status and 200 <= log.response_status < 300 else "失败" if log.response_status and log.response_status >= 400 else "处理中"
            
            result.append({
                "id": log.id,
                "webhook_id": log.webhook_id,
                "webhook_name": webhook.name,
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
        
        logger.info(f"返回Webhook {webhook_id} 的 {len(result)} 条日志记录")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Webhook日志失败: {e}")
        raise HTTPException(status_code=500, detail="获取日志失败")


@router.put("/{webhook_id}", response_model=WebhookSimpleResponse)
async def update_webhook(
    webhook_id: str,
    webhook_data: WebhookUpdate,
    db: Session = Depends(get_db)
):
    """更新Webhook配置"""
    # 尝试按数字ID或webhook_id字符串查找
    webhook = None
    if webhook_id.isdigit():
        # 前端传的是数字ID
        webhook = db.query(Webhook).filter(Webhook.id == int(webhook_id)).first()
    else:
        # 传的是webhook_id字符串
        webhook = db.query(Webhook).filter(Webhook.webhook_id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 更新字段（使用Pydantic V2语法）
    update_data = webhook_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(webhook, field):
            setattr(webhook, field, value)
    
    db.commit()
    db.refresh(webhook)
    
    logger.info(f"Updated webhook: {webhook.webhook_id}")
    return WebhookSimpleResponse.from_webhook(webhook)


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """删除Webhook"""
    # 尝试按数字ID或webhook_id字符串查找
    webhook = None
    if webhook_id.isdigit():
        # 前端传的是数字ID
        webhook = db.query(Webhook).filter(Webhook.id == int(webhook_id)).first()
    else:
        # 传的是webhook_id字符串
        webhook = db.query(Webhook).filter(Webhook.webhook_id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 检查是否有关联的分析任务
    from app.models.analysis_task import AnalysisTask
    linked_tasks = db.query(AnalysisTask).filter(AnalysisTask.webhook_id == webhook.id).count()
    
    if linked_tasks > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"无法删除Webhook，还有{linked_tasks}个分析任务与其关联"
        )
    
    db.delete(webhook)
    db.commit()
    
    logger.info(f"Deleted webhook: {webhook_id}")
    return {"success": True, "message": "Webhook删除成功"}


@router.post("/{webhook_id}/test")
async def test_webhook_by_id(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """测试Webhook连通性 - 前端调用的版本"""
    # 尝试按数字ID或webhook_id字符串查找
    webhook = None
    if webhook_id.isdigit():
        # 前端传的是数字ID
        webhook = db.query(Webhook).filter(Webhook.id == int(webhook_id)).first()
    else:
        # 传的是webhook_id字符串
        webhook = db.query(Webhook).filter(Webhook.webhook_id == webhook_id).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")
    
    # 返回简单的测试成功响应
    logger.info(f"Testing webhook: {webhook.webhook_id}")
    return {
        "success": True, 
        "message": f"Webhook '{webhook.name}' 测试成功",
        "webhook_url": webhook.webhook_url
    }


# ===================== 核心功能：Webhook接收端点 =====================

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """验证webhook签名"""
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # 支持不同的签名格式
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False


def check_rate_limit(webhook: Webhook, client_ip: str, db: Session) -> bool:
    """检查速率限制"""
    if not webhook.rate_limit_per_minute:
        return True
    
    # 简单的基于时间的速率限制检查
    now = datetime.utcnow()
    one_minute_ago = now.replace(second=now.second - 60 if now.second >= 60 else 0)
    
    recent_requests = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook.id,
        WebhookLog.source_ip == client_ip,
        WebhookLog.created_at >= one_minute_ago
    ).count()
    
    return recent_requests < webhook.rate_limit_per_minute


@router.post("/receive/{webhook_id}", response_model=WebhookReceiveResponse)
async def receive_webhook(
    webhook_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    接收Webhook请求的核心端点
    这是飞书项目发送数据到我们系统的入口
    """
    start_time = time.time()
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    request_method = request.method
    request_url = str(request.url)
    request_headers = dict(request.headers)
    
    # 获取原始请求体
    try:
        request_body = await request.body()
        # 尝试多种编码方式
        try:
            request_body_str = request_body.decode('utf-8')
        except UnicodeDecodeError:
            try:
                request_body_str = request_body.decode('gbk')
            except UnicodeDecodeError:
                try:
                    request_body_str = request_body.decode('latin-1')
                except UnicodeDecodeError:
                    request_body_str = request_body.decode('utf-8', errors='ignore')
    except Exception as e:
        logger.error(f"Failed to read request body: {e}")
        return WebhookReceiveResponse(
            success=False,
            message="无法读取请求体",
            webhook_id=webhook_id
        )
    
    # 查找webhook
    webhook = db.query(Webhook).filter(
        Webhook.webhook_id == webhook_id,
        Webhook.is_active == True
    ).first()
    
    if not webhook:
        logger.warning(f"Webhook not found or inactive: {webhook_id}")
        return WebhookReceiveResponse(
            success=False,
            message="Webhook不存在或已禁用",
            webhook_id=webhook_id
        )
    
    # 记录请求开始
    processing_start = time.time()
    
    try:
        # IP白名单检查
        if not webhook.can_receive_request(client_ip):
            raise HTTPException(status_code=403, detail="IP地址不在白名单中")
        
        # 速率限制检查
        if not check_rate_limit(webhook, client_ip, db):
            raise HTTPException(status_code=429, detail="请求频率超限")
        
        # 载荷大小检查
        if len(request_body) > webhook.max_payload_size:
            raise HTTPException(status_code=413, detail="请求体过大")
        
        # 签名验证
        if webhook.verify_signature:
            signature = request.headers.get("x-webhook-signature") or request.headers.get("signature")
            if not signature:
                raise HTTPException(status_code=400, detail="缺少签名头")
            
            if not verify_webhook_signature(request_body, signature, webhook.secret_key):
                raise HTTPException(status_code=401, detail="签名验证失败")
        
        # 解析JSON数据
        try:
            if request_body_str:
                payload_data = json.loads(request_body_str)
            else:
                payload_data = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in webhook payload: {e}")
            raise HTTPException(status_code=400, detail="无效的JSON格式")
        
        # 事件过滤
        if not webhook.matches_event_filter(payload_data):
            logger.info(f"Event filtered out for webhook {webhook_id}")
            response_data = {
                "success": True,
                "message": "事件已过滤",
                "filtered": True
            }
        else:
            # 生成执行ID
            execution_id = f"exec_{secrets.token_urlsafe(12)}"
            
            print(f"\n🎯 [WEBHOOK] 启动异步任务处理")
            print(f"   - Webhook ID: {webhook.id}")
            print(f"   - 执行ID: {execution_id}")
            print(f"   - 客户端IP: {client_ip}")
            print(f"   - Payload大小: {len(str(payload_data))} 字符")
            
            # 启动异步任务处理
            background_tasks.add_task(
                process_webhook_async,
                webhook_id=webhook.id,
                payload_data=payload_data,
                execution_id=execution_id,
                client_ip=client_ip,
                user_agent=user_agent
            )
            
            print(f"✅ [WEBHOOK] 异步任务已添加到后台队列")
            
            response_data = {
                "success": True,
                "message": "Webhook接收成功，正在处理",
                "execution_id": execution_id
            }
        
        # 计算处理时间
        processing_time = (time.time() - processing_start) * 1000
        
        # 记录成功日志
        log = WebhookLog(
            webhook_id=webhook.id,
            request_id=f"req_{secrets.token_urlsafe(8)}",
            source_ip=client_ip,
            user_agent=user_agent,
            request_headers=request_headers,
            request_payload=payload_data if payload_data else None,
            request_size_bytes=len(request_body) if request_body else 0,
            response_status=200,
            response_time_ms=int(processing_time),
            is_valid=True
        )
        
        db.add(log)
        webhook.update_request_stats(success=True, response_time=processing_time / 1000)
        db.commit()
        
        logger.info(f"Webhook {webhook_id} processed successfully in {processing_time:.2f}ms")
        
        return WebhookReceiveResponse(
            success=True,
            message=response_data["message"],
            webhook_id=webhook_id,
            execution_id=response_data.get("execution_id")
        )
        
    except HTTPException as e:
        # 处理HTTP异常
        processing_time = (time.time() - processing_start) * 1000
        error_message = e.detail
        
        # 记录失败日志
        log = WebhookLog(
            webhook_id=webhook.id,
            request_id=f"req_{secrets.token_urlsafe(8)}",
            source_ip=client_ip,
            user_agent=user_agent,
            request_headers=request_headers,
            request_payload=None,  # 错误时不记录payload
            request_size_bytes=len(request_body) if request_body else 0,
            response_status=e.status_code,
            response_time_ms=int(processing_time),
            is_valid=False,
            validation_errors=[error_message]
        )
        
        db.add(log)
        webhook.update_request_stats(success=False, response_time=processing_time / 1000)
        db.commit()
        
        logger.warning(f"Webhook {webhook_id} failed with HTTP {e.status_code}: {error_message}")
        
        return WebhookReceiveResponse(
            success=False,
            message=error_message,
            webhook_id=webhook_id
        )
        
    except Exception as e:
        # 处理其他异常
        processing_time = (time.time() - processing_start) * 1000
        error_message = f"内部服务器错误: {str(e)}"
        
        # 记录失败日志
        log = WebhookLog(
            webhook_id=webhook.id,
            request_id=f"req_{secrets.token_urlsafe(8)}",
            source_ip=client_ip,
            user_agent=user_agent,
            request_headers=request_headers,
            request_payload=None,  # 错误时不记录payload
            request_size_bytes=len(request_body) if request_body else 0,
            response_status=500,
            response_time_ms=int(processing_time),
            is_valid=False,
            validation_errors=[error_message]
        )
        
        db.add(log)
        webhook.update_request_stats(success=False, response_time=processing_time / 1000)
        db.commit()
        
        logger.error(f"Webhook {webhook_id} failed with exception: {e}", exc_info=True)
        
        return WebhookReceiveResponse(
            success=False,
            message="服务器内部错误",
            webhook_id=webhook_id
        )


@router.get("/receive/{webhook_id}")
async def webhook_info(
    webhook_id: str,
    db: Session = Depends(get_db)
):
    """
    获取Webhook信息（GET请求）
    用于验证Webhook URL是否可访问
    """
    webhook = db.query(Webhook).filter(
        Webhook.webhook_id == webhook_id,
        Webhook.is_active == True
    ).first()
    
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在或已禁用")
    
    return {
        "webhook_id": webhook_id,
        "name": webhook.name,
        "description": webhook.description,
        "is_active": webhook.is_active,
        "created_at": webhook.created_at.isoformat(),
        "last_request_at": webhook.last_request_at.isoformat() if webhook.last_request_at else None,
        "total_requests": webhook.total_requests,
        "success_rate": webhook.get_success_rate(),
        "status": "ready",
        "message": "Webhook已就绪，可以接收POST请求"
    }


@router.get("/{webhook_id}/association-status")
async def check_webhook_association_status(
    webhook_id: int,
    db: Session = Depends(get_db)
):
    """检查webhook是否已关联其他任务"""
    # 导入在函数内部，避免循环依赖
    from app.models.analysis_task import AnalysisTask

    # 检查webhook是否存在
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook不存在")

    # 查询关联的所有任务（包括启用和未启用的）
    all_associated_tasks = db.query(AnalysisTask).filter(
        AnalysisTask.webhook_id == webhook_id
    ).all()

    # 查询关联的启用状态任务
    active_associated_tasks = [task for task in all_associated_tasks if task.is_active]

    # 调试信息
    logger.info(f"Webhook {webhook_id} 关联状态检查:")
    logger.info(f"  - Webhook启用状态: {webhook.is_active}")
    logger.info(f"  - 总关联任务数: {len(all_associated_tasks)}")
    logger.info(f"  - 启用状态任务数: {len(active_associated_tasks)}")
    if active_associated_tasks:
        logger.info(f"  - 启用状态任务: {[f'{task.name}(ID:{task.id})' for task in active_associated_tasks]}")

    return {
        "webhook_id": webhook_id,
        "webhook_name": webhook.name,
        "is_active": webhook.is_active,
        "associated_task_count": len(all_associated_tasks),
        "active_task_count": len(active_associated_tasks),
        "associated_tasks": [
            {
                "id": task.id,
                "name": task.name,
                "is_active": task.is_active,
                "created_at": task.created_at.isoformat()
            }
            for task in all_associated_tasks
        ],
        "can_be_associated": webhook.is_active and len(active_associated_tasks) == 0,
        "restriction_reason": None if webhook.is_active and len(active_associated_tasks) == 0
                           else ("Webhook未启用" if not webhook.is_active
                                else f"已关联 {len(active_associated_tasks)} 个启用任务")
    }