from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai_models,
    storage_credentials,
    webhooks,
    analysis_tasks,
    task_executions,
    webhook_logs,
    system_configs,
    auth,
    users,
    files,
    monitoring,
    image_download
)

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])

# AI模型管理路由
api_router.include_router(ai_models.router, prefix="/ai-models", tags=["AI模型管理"])

# 存储凭证管理路由
api_router.include_router(storage_credentials.router, prefix="/storage-credentials", tags=["存储凭证管理"])

# Webhook管理路由
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhook管理"])

# 分析任务管理路由
api_router.include_router(analysis_tasks.router, prefix="/analysis-tasks", tags=["分析任务管理"])

# Webhook日志路由
api_router.include_router(webhook_logs.router, prefix="/webhook-logs", tags=["Webhook日志"])

# 系统配置路由
api_router.include_router(system_configs.router, prefix="/system-configs", tags=["系统配置"])

# 文件处理路由
api_router.include_router(files.router, prefix="/files", tags=["文件处理"])

# 监控统计路由
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["监控统计"])

# 执行记录路由（供前端直接访问）
api_router.include_router(task_executions.router, prefix="/executions", tags=["执行记录"])

# 附件下载路由
api_router.include_router(image_download.router, prefix="/attachment-download", tags=["附件下载"])