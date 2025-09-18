"""SQLAlchemy数据库模型包

定义数据库表结构和关系。
"""

# 导入基础模型
from .base import Base

# 导入所有模型
from .user import User
from .ai_model import AIModel
from .storage_credential import StorageCredential
from .webhook import Webhook
from .analysis_task import AnalysisTask
from .task_execution_simple import TaskExecution
from .webhook_log_simple import WebhookLog
from .system_config import SystemConfig

# 导出所有模型
__all__ = [
    "Base",
    "User",
    "AIModel",
    "StorageCredential",
    "Webhook",
    "AnalysisTask",
    "TaskExecution",
    "WebhookLog",
    "SystemConfig",
]

# 版本信息
__version__ = "1.0.0"
__author__ = "飞书项目AI团队"