# API功能完整总结

本文档总结了AI综合分析管理平台后端API的所有已实现功能。

## 核心架构

### 技术栈
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL + SQLAlchemy 2.0 + Alembic
- **认证**: JWT + OAuth2
- **异步任务**: Celery + Redis
- **AI集成**: OpenAI、Anthropic等多种模型
- **文件处理**: 支持多种存储协议(SMB、NFS、FTP、HTTP)

### 核心业务流程
1. **Webhook接收** - 接收飞书项目事件
2. **数据解析** - 使用JSONPath提取关键信息
3. **文件获取** - 通过配置的存储凭证获取文件
4. **AI分析** - 调用配置的AI模型进行分析
5. **结果回写** - 将分析结果写回飞书项目

## API模块详细说明

### 1. 认证模块 (`/api/v1/auth`)

#### 功能概述
提供用户认证、授权和会话管理功能。

#### 主要端点
- `POST /login` - 用户登录，返回JWT令牌
- `POST /logout` - 用户登出
- `POST /refresh` - 刷新访问令牌
- `GET /me` - 获取当前用户信息
- `POST /change-password` - 修改密码

#### 安全特性
- JWT双令牌机制（访问令牌 + 刷新令牌）
- 密码bcrypt加密
- 登录失败限制
- IP白名单支持
- API密钥认证

---

### 2. 用户管理模块 (`/api/v1/users`)

#### 功能概述
提供完整的用户生命周期管理功能。

#### 主要端点
- `GET /` - 获取用户列表（支持分页、搜索、过滤）
- `POST /` - 创建新用户
- `GET /{user_id}` - 获取用户详情
- `PUT /{user_id}` - 更新用户信息
- `DELETE /{user_id}` - 删除用户
- `GET /{user_id}/activity` - 获取用户活动日志

#### 特殊功能
- 用户角色管理（管理员、普通用户）
- 用户状态管理（激活、禁用、锁定）
- 用户权限控制
- 活动日志追踪

---

### 3. AI模型管理模块 (`/api/v1/ai-models`)

#### 功能概述
集中管理多种AI模型配置和调用。

#### 主要端点
- `GET /` - 获取AI模型列表
- `POST /` - 添加新AI模型配置
- `GET /{model_id}` - 获取模型详情
- `PUT /{model_id}` - 更新模型配置
- `DELETE /{model_id}` - 删除模型配置
- `POST /{model_id}/test` - 测试模型连通性
- `GET /providers` - 获取支持的AI服务商
- `GET /stats` - 获取模型使用统计

#### 支持的AI服务商
- OpenAI (GPT系列)
- Anthropic (Claude系列)
- Google (Gemini系列)
- 百度 (文心一言)
- 阿里 (通义千问)
- 腾讯 (混元)

#### 特殊功能
- 模型成本计算
- 使用统计分析
- 健康检查
- 配置模板

---

### 4. 存储凭证管理模块 (`/api/v1/storage-credentials`)

#### 功能概述
管理多种文件存储协议的连接凭证。

#### 主要端点
- `GET /` - 获取存储凭证列表
- `POST /` - 创建存储凭证
- `GET /{credential_id}` - 获取凭证详情
- `PUT /{credential_id}` - 更新凭证
- `DELETE /{credential_id}` - 删除凭证
- `POST /{credential_id}/test` - 测试存储连接
- `GET /protocols` - 获取支持的协议类型
- `GET /stats` - 获取使用统计

#### 支持的存储协议
- **SMB/CIFS** - Windows网络共享
- **NFS** - 网络文件系统
- **FTP/SFTP** - 文件传输协议
- **HTTP/HTTPS** - Web文件访问
- **WebDAV** - Web分布式文件系统
- **Local** - 本地文件系统

#### 安全特性
- 敏感信息加密存储
- 连接测试功能
- 访问权限控制
- 使用情况监控

---

### 5. Webhook管理模块 (`/api/v1/webhooks`)

#### 功能概述
动态创建和管理Webhook端点，接收外部系统事件。

#### 主要端点
- `GET /` - 获取Webhook列表
- `POST /` - 创建新Webhook
- `GET /{webhook_id}` - 获取Webhook详情
- `PUT /{webhook_id}` - 更新Webhook配置
- `DELETE /{webhook_id}` - 删除Webhook
- `POST /receive/{webhook_id}` - 接收Webhook事件（公开端点）
- `GET /{webhook_id}/logs` - 获取Webhook日志
- `GET /stats` - 获取统计信息
- `GET /health` - 健康检查

#### 安全特性
- Webhook签名验证
- IP白名单限制
- 速率限制
- 请求日志记录

#### 特殊功能
- 动态URL生成
- 事件过滤配置
- 重试机制
- 失败通知

---

### 6. 分析任务管理模块 (`/api/v1/analysis-tasks`)

#### 功能概述
配置和管理AI分析任务的完整生命周期。

#### 主要端点
- `GET /` - 获取分析任务列表
- `POST /` - 创建分析任务
- `GET /{task_id}` - 获取任务详情
- `PUT /{task_id}` - 更新任务配置
- `DELETE /{task_id}` - 删除任务
- `POST /{task_id}/start` - 启动任务
- `POST /{task_id}/stop` - 停止任务
- `POST /{task_id}/trigger` - 手动触发任务
- `GET /templates` - 获取任务模板
- `POST /validate` - 验证任务配置

#### 核心功能
- **数据解析配置**: 使用JSONPath提取Webhook数据
- **文件获取配置**: 配置文件存储凭证和路径模板
- **AI分析配置**: 选择AI模型和设置提示词
- **结果回写配置**: 配置飞书项目集成
- **执行统计**: 成功率、执行时间、成本统计

#### 配置模板
- 代码审查任务
- 文档分析任务
- 数据处理任务
- 安全扫描任务

---

### 7. 任务执行管理模块 (`/api/v1/task-executions`)

#### 功能概述
监控和管理所有任务执行实例，提供详细的执行历史和性能分析。

#### 主要端点
- `GET /` - 获取执行历史列表
- `GET /{execution_id}` - 获取执行详情
- `POST /{execution_id}/retry` - 重试失败的执行
- `POST /{execution_id}/cancel` - 取消执行
- `GET /stats` - 获取执行统计
- `GET /timeline` - 获取执行时间线
- `GET /performance` - 获取性能分析
- `GET /logs` - 获取聚合日志

#### 监控功能
- 实时执行状态
- 性能指标统计
- 错误率分析
- 成本统计
- 执行时间趋势

#### 执行状态
- `PENDING` - 等待执行
- `RUNNING` - 执行中
- `SUCCESS` - 执行成功
- `FAILED` - 执行失败
- `CANCELLED` - 已取消
- `TIMEOUT` - 执行超时

---

### 8. Webhook日志模块 (`/api/v1/webhook-logs`)

#### 功能概述
提供Webhook事件的详细日志记录和分析功能。

#### 主要端点
- `GET /` - 获取Webhook日志列表
- `GET /{log_id}` - 获取日志详情
- `GET /stats` - 获取日志统计
- `DELETE /cleanup` - 清理过期日志

#### 日志内容
- 请求详情（IP、User-Agent、Headers）
- 请求体和响应体
- 处理时间和状态
- 错误信息和堆栈跟踪
- 关联的任务执行信息

---

### 9. 系统配置模块 (`/api/v1/system-configs`)

#### 功能概述
提供强大的系统配置管理功能，支持多种配置类型和格式。

#### 主要端点
- `GET /` - 获取系统配置列表（支持丰富过滤）
- `POST /` - 创建系统配置
- `GET /{config_key}` - 获取配置详情
- `PUT /{config_key}` - 更新配置
- `DELETE /{config_key}` - 删除配置
- `GET /{config_key}/value` - 获取类型化配置值
- `GET /public` - 获取公开配置（无需认证）
- `POST /validate` - 验证配置值
- `POST /reset` - 重置配置值
- `POST /export` - 导出配置
- `POST /import` - 导入配置
- `GET /stats` - 获取配置统计
- `GET /health` - 配置健康检查

#### 配置类型支持
- `STRING` - 字符串
- `INTEGER` - 整数
- `FLOAT` - 浮点数
- `BOOLEAN` - 布尔值
- `JSON` - JSON对象
- `TEXT` - 长文本
- `PASSWORD` - 密码（加密存储）
- `URL` - URL地址
- `EMAIL` - 邮箱地址
- `FILE_PATH` - 文件路径

#### 配置分类
- `SYSTEM` - 系统配置
- `DATABASE` - 数据库配置
- `AI_MODEL` - AI模型配置
- `WEBHOOK` - Webhook配置
- `SECURITY` - 安全配置
- `LOGGING` - 日志配置
- `MONITORING` - 监控配置
- `FEISHU` - 飞书配置

#### 高级功能
- **验证规则**: 支持正则表达式、值范围、允许值列表
- **依赖关系**: 配置项之间的依赖管理
- **环境配置**: 支持不同环境的配置
- **版本控制**: 配置变更历史追踪
- **导入导出**: 支持JSON、YAML、ENV、INI格式
- **敏感数据**: 自动加密敏感配置
- **公开配置**: 支持前端直接访问的配置
- **健康检查**: 配置完整性和有效性检查

---

### 10. 文件处理模块 (`/api/v1/files`)

#### 功能概述
提供统一的文件上传、下载和处理功能。

#### 主要端点
- `POST /upload` - 上传文件
- `GET /{file_id}` - 下载文件
- `DELETE /{file_id}` - 删除文件
- `GET /{file_id}/info` - 获取文件信息
- `GET /` - 获取文件列表

#### 文件处理特性
- 安全文件名生成
- 文件类型验证
- 大小限制检查
- 病毒扫描（可配置）
- 文件缩略图生成

## 核心服务组件

### 1. 数据解析服务 (`app.services.data_parser`)

#### 功能概述
使用JSONPath表达式从Webhook数据中提取所需字段。

#### 主要特性
- JSONPath语法支持
- 数据类型转换
- 默认值处理
- 模板渲染
- 嵌套数据提取

### 2. 文件服务 (`app.services.file_service`)

#### 功能概述
提供统一的文件访问接口，支持多种存储协议。

#### 主要特性
- 多协议支持
- 连接池管理
- 错误重试机制
- 文件缓存
- 安全访问控制

### 3. AI服务 (`app.services.ai_service`)

#### 功能概述
统一的AI模型调用接口，支持多种AI服务商。

#### 主要特性
- 多服务商适配
- 请求重试机制
- 成本计算
- 使用统计
- 错误处理

### 4. 飞书服务 (`app.services.feishu_service`)

#### 功能概述
与飞书项目系统集成，支持工作项更新和评论。

#### 主要特性
- OAuth2认证
- 自动令牌刷新
- API限流处理
- 批量操作支持
- 错误重试

### 5. Webhook处理器 (`app.tasks.webhook_processor`)

#### 功能概述
异步处理Webhook事件的完整工作流。

#### 处理流程
1. 接收Webhook事件
2. 数据解析和验证
3. 获取关联的分析任务
4. 执行数据提取
5. 文件内容获取
6. AI模型分析
7. 结果回写到飞书
8. 记录执行日志和统计

## 数据库模型

### 核心实体关系
```
User (用户)
├── AIModel (AI模型)
├── StorageCredential (存储凭证)
├── Webhook (Webhook配置)
└── AnalysisTask (分析任务)
    ├── TaskExecution (任务执行)
    └── WebhookLog (Webhook日志)

SystemConfig (系统配置)
```

### 主要模型特性
- **用户模型**: 支持角色权限、状态管理、活动追踪
- **AI模型**: 多服务商支持、成本计算、使用统计
- **存储凭证**: 加密存储、多协议支持、连接测试
- **Webhook模型**: 动态URL、签名验证、事件过滤
- **分析任务**: 完整配置、状态管理、执行统计
- **任务执行**: 详细日志、性能统计、错误追踪
- **系统配置**: 类型化配置、验证规则、版本控制

## API使用示例

### 1. 创建完整的AI分析工作流

```python
# 1. 创建AI模型配置
ai_model_config = {
    "name": "GPT-4代码审查",
    "provider": "openai",
    "model_name": "gpt-4",
    "api_key": "your-api-key",
    "api_base": "https://api.openai.com/v1",
    "config": {
        "temperature": 0.3,
        "max_tokens": 2000
    }
}
ai_model = await client.post("/api/v1/ai-models", json=ai_model_config)

# 2. 创建存储凭证
storage_config = {
    "name": "代码仓库SMB",
    "protocol": "smb", 
    "host": "fileserver.company.com",
    "username": "service-account",
    "password": "encrypted-password",
    "share_path": "/code-repos"
}
storage = await client.post("/api/v1/storage-credentials", json=storage_config)

# 3. 创建Webhook
webhook_config = {
    "name": "代码提交Webhook",
    "description": "监听代码提交事件",
    "is_active": True,
    "allowed_ips": ["192.168.1.0/24"],
    "secret_key": "webhook-secret"
}
webhook = await client.post("/api/v1/webhooks", json=webhook_config)

# 4. 创建分析任务
task_config = {
    "name": "代码审查任务",
    "description": "自动审查提交的代码变更",
    "webhook_id": webhook["id"],
    "ai_model_id": ai_model["id"],
    "storage_credential_id": storage["id"],
    
    # 数据解析配置
    "data_parsing_config": {
        "commit_id": "$.payload.head_commit.id",
        "repository": "$.repository.name", 
        "author": "$.payload.head_commit.author.name",
        "files_changed": "$.payload.head_commit.modified[*]"
    },
    
    # 文件路径模板
    "file_path_template": "/{{repository}}/{{commit_id}}/",
    
    # AI分析提示词
    "system_prompt": "你是一个专业的代码审查师，请仔细审查提交的代码变更。",
    "user_prompt_template": """
    请审查以下代码变更：
    仓库: {{repository}}
    提交者: {{author}}
    变更文件: {{files_changed}}
    
    代码内容：
    {{file_content}}
    
    请关注：
    1. 代码质量和最佳实践
    2. 潜在的安全问题
    3. 性能优化建议
    4. 代码规范性
    """,
    
    # 飞书回写配置
    "feishu_config": {
        "app_id": "your-feishu-app-id",
        "app_secret": "your-feishu-secret",
        "base_url": "https://open.feishu.cn"
    },
    "field_mapping": {
        "review_result": "custom_field_review",
        "score": "custom_field_score"
    }
}
task = await client.post("/api/v1/analysis-tasks", json=task_config)
```

### 2. 监控任务执行

```python
# 获取任务执行统计
stats = await client.get(f"/api/v1/task-executions/stats?task_id={task['id']}")

# 获取最近的执行记录
executions = await client.get(f"/api/v1/task-executions?task_id={task['id']}&limit=10")

# 获取执行详情
execution_detail = await client.get(f"/api/v1/task-executions/{execution_id}")
```

### 3. 配置管理

```python
# 创建系统配置
config = {
    "key": "ai.default_timeout",
    "name": "AI请求默认超时",
    "display_name": "AI请求超时时间",
    "value": "120",
    "config_type": "integer",
    "category": "ai_model",
    "required": True,
    "min_value": 30,
    "max_value": 600,
    "description": "AI模型请求的默认超时时间（秒）"
}
await client.post("/api/v1/system-configs", json=config)

# 批量导出配置
export_data = {
    "categories": ["ai_model", "webhook"],
    "format": "json",
    "include_sensitive": False
}
config_export = await client.post("/api/v1/system-configs/export", json=export_data)
```

## 部署和运维

### Docker部署

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ai_analysis
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_analysis
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7-alpine
```

### 环境配置

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_analysis
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# AI服务配置
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# 飞书配置
FEISHU_APP_ID=your-app-id
FEISHU_APP_SECRET=your-app-secret
```

### 监控和日志

```python
# Prometheus指标
from prometheus_client import Counter, Histogram, Gauge

webhook_requests = Counter('webhook_requests_total', 'Webhook请求总数', ['webhook_id', 'status'])
task_execution_time = Histogram('task_execution_seconds', '任务执行时间', ['task_id'])
active_connections = Gauge('database_connections_active', '活跃数据库连接数')
```

## 扩展和自定义

### 1. 添加新的AI服务商

```python
# app/services/ai_providers/custom_provider.py
class CustomAIProvider(BaseAIProvider):
    async def generate_completion(self, prompt: str, **kwargs) -> AIResponse:
        # 实现自定义AI服务商接口
        pass
```

### 2. 添加新的存储协议

```python
# app/services/storage_adapters/custom_adapter.py  
class CustomStorageAdapter(BaseStorageAdapter):
    async def get_file(self, path: str) -> FileContent:
        # 实现自定义存储协议
        pass
```

### 3. 自定义Webhook处理器

```python
# app/tasks/custom_processor.py
class CustomWebhookProcessor(WebhookTaskProcessor):
    async def process_custom_event(self, event_data: dict) -> dict:
        # 实现自定义事件处理逻辑
        pass
```

## 总结

该AI综合分析管理平台提供了完整的企业级功能：

### 核心优势
1. **模块化架构**: 各功能模块独立，易于维护和扩展
2. **异步处理**: 基于FastAPI和Celery的高性能异步架构
3. **多AI支持**: 统一接口支持多种AI服务商
4. **安全可靠**: 完善的认证授权和数据加密
5. **监控完善**: 详细的执行日志和性能统计
6. **配置灵活**: 强大的配置管理和模板系统

### 适用场景
- 企业代码审查自动化
- 文档智能分析处理
- 数据质量自动检查
- 安全漏洞扫描分析
- 项目管理自动化
- 知识库智能整理

### 技术特性
- RESTful API设计
- OpenAPI文档自动生成
- 数据库迁移管理
- 容器化部署支持
- 微服务架构就绪
- 生产环境优化

该平台为企业提供了一个强大、灵活、可扩展的AI分析处理解决方案。