# 飞书项目AI后端服务

基于FastAPI的飞书数据分析后端服务，提供AI驱动的数据处理和分析功能。

## 功能特性

- 🚀 **高性能API**: 基于FastAPI构建，支持异步处理
- 🔐 **安全认证**: JWT令牌认证，支持用户权限管理
- 🗄️ **数据库管理**: PostgreSQL + SQLAlchemy ORM + Alembic迁移
- 🤖 **AI集成**: 支持OpenAI、Anthropic等多种AI模型
- 📊 **数据分析**: 自动化数据处理和分析任务
- 🔗 **Webhook支持**: 实时数据接收和处理
- 📁 **多存储支持**: AWS S3、Azure Blob、Google Cloud Storage
- 📝 **完整日志**: 基于Loguru的结构化日志系统
- 📖 **API文档**: 自动生成的Swagger/OpenAPI文档

## 技术栈

- **Web框架**: FastAPI 0.104+
- **数据库**: PostgreSQL + SQLAlchemy 2.0
- **认证**: JWT + OAuth2
- **数据验证**: Pydantic 2.0
- **异步任务**: Celery + Redis
- **日志**: Loguru
- **测试**: Pytest
- **代码质量**: Black + isort + flake8 + mypy

## 项目结构

```
backend/
├── app/
│   ├── api/                    # API路由
│   │   ├── auth.py            # 认证相关
│   │   ├── users.py           # 用户管理
│   │   ├── ai_models.py       # AI模型管理
│   │   ├── storage_credentials.py  # 存储凭证
│   │   ├── webhooks.py        # Webhook管理
│   │   ├── analysis_tasks.py  # 分析任务
│   │   ├── task_executions.py # 任务执行
│   │   ├── webhook_logs.py    # Webhook日志
│   │   └── system_configs.py  # 系统配置
│   ├── core/                  # 核心模块
│   │   ├── config.py          # 配置管理
│   │   ├── database.py        # 数据库连接
│   │   ├── security.py        # 安全相关
│   │   ├── logger.py          # 日志配置
│   │   └── exceptions.py      # 异常处理
│   ├── models/                # 数据库模型
│   │   ├── base.py            # 基础模型
│   │   ├── user.py            # 用户模型
│   │   ├── ai_model.py        # AI模型
│   │   ├── storage_credential.py  # 存储凭证
│   │   ├── webhook.py         # Webhook模型
│   │   ├── analysis_task.py   # 分析任务
│   │   ├── task_execution.py  # 任务执行
│   │   ├── webhook_log.py     # Webhook日志
│   │   └── system_config.py   # 系统配置
│   ├── schemas/               # Pydantic模式
│   │   ├── base.py            # 基础模式
│   │   ├── user.py            # 用户模式
│   │   ├── ai_model.py        # AI模型模式
│   │   ├── storage_credential.py  # 存储凭证模式
│   │   ├── webhook.py         # Webhook模式
│   │   ├── analysis_task.py   # 分析任务模式
│   │   ├── task_execution.py  # 任务执行模式
│   │   ├── webhook_log.py     # Webhook日志模式
│   │   └── system_config.py   # 系统配置模式
│   └── main.py                # 应用入口
├── alembic/                   # 数据库迁移
│   ├── versions/              # 迁移文件
│   ├── env.py                 # 迁移环境
│   └── script.py.mako         # 迁移模板
├── tests/                     # 测试文件
├── requirements.txt           # 依赖包
├── alembic.ini               # Alembic配置
├── .env.example              # 环境变量模板
└── README.md                 # 项目说明
```

## 快速开始

### 1. 环境准备

确保已安装以下软件：
- Python 3.9+
- PostgreSQL 12+
- Redis 6+

### 2. 克隆项目

```bash
git clone <repository-url>
cd feishuprojectai/backend
```

### 3. 创建虚拟环境

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等信息
```

### 6. 初始化数据库

```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 7. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 8. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量配置

主要环境变量说明：

```bash
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/feishu_ai

# 安全配置
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis配置
REDIS_URL=redis://localhost:6379/0

# AI模型配置
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key

# 飞书配置
FEISHU_APP_ID=your-feishu-app-id
FEISHU_APP_SECRET=your-feishu-app-secret
```

## API接口

### 认证相关
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息

### 用户管理
- `POST /api/v1/users/` - 创建用户
- `GET /api/v1/users/me` - 获取用户资料
- `GET /api/v1/users/{user_id}` - 获取指定用户

### AI模型管理
- `GET /api/v1/ai-models/` - 获取AI模型列表
- `POST /api/v1/ai-models/` - 创建AI模型
- `GET /api/v1/ai-models/{model_id}` - 获取AI模型详情
- `PUT /api/v1/ai-models/{model_id}` - 更新AI模型
- `DELETE /api/v1/ai-models/{model_id}` - 删除AI模型

### 存储凭证管理
- `GET /api/v1/storage-credentials/` - 获取存储凭证列表
- `POST /api/v1/storage-credentials/` - 创建存储凭证
- `GET /api/v1/storage-credentials/{credential_id}` - 获取存储凭证详情
- `PUT /api/v1/storage-credentials/{credential_id}` - 更新存储凭证
- `DELETE /api/v1/storage-credentials/{credential_id}` - 删除存储凭证

### Webhook管理
- `GET /api/v1/webhooks/` - 获取Webhook列表
- `POST /api/v1/webhooks/` - 创建Webhook
- `GET /api/v1/webhooks/{webhook_id}` - 获取Webhook详情
- `PUT /api/v1/webhooks/{webhook_id}` - 更新Webhook
- `DELETE /api/v1/webhooks/{webhook_id}` - 删除Webhook

### 分析任务管理
- `GET /api/v1/analysis-tasks/` - 获取分析任务列表
- `POST /api/v1/analysis-tasks/` - 创建分析任务
- `GET /api/v1/analysis-tasks/{task_id}` - 获取分析任务详情
- `PUT /api/v1/analysis-tasks/{task_id}` - 更新分析任务
- `DELETE /api/v1/analysis-tasks/{task_id}` - 删除分析任务

### 任务执行管理
- `GET /api/v1/task-executions/` - 获取任务执行列表
- `GET /api/v1/task-executions/{execution_id}` - 获取任务执行详情
- `PUT /api/v1/task-executions/{execution_id}` - 更新任务执行状态

### Webhook日志
- `GET /api/v1/webhook-logs/` - 获取Webhook日志列表
- `GET /api/v1/webhook-logs/{log_id}` - 获取Webhook日志详情

### 系统配置
- `GET /api/v1/system-configs/` - 获取系统配置列表
- `GET /api/v1/system-configs/{config_key}` - 获取系统配置
- `PUT /api/v1/system-configs/{config_key}` - 更新系统配置

## 开发指南

### 代码规范

项目使用以下工具确保代码质量：

```bash
# 代码格式化
black .

# 导入排序
isort .

# 代码检查
flake8 .

# 类型检查
mypy .
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 数据库迁移

```bash
# 创建新的迁移文件
alembic revision --autogenerate -m "描述变更内容"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

### 添加新的API端点

1. 在 `app/schemas/` 中定义Pydantic模式
2. 在 `app/models/` 中定义数据库模型
3. 在 `app/api/` 中创建API路由
4. 在 `app/main.py` 中注册路由
5. 创建数据库迁移
6. 编写测试用例

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t feishu-ai-backend .

# 运行容器
docker run -d -p 8000:8000 --env-file .env feishu-ai-backend
```

### 生产环境配置

1. 设置环境变量 `ENVIRONMENT=production`
2. 配置反向代理（Nginx）
3. 设置SSL证书
4. 配置监控和日志收集
5. 设置自动备份

## 监控和日志

### 日志配置

日志文件位置：`logs/app.log`

日志级别：
- `DEBUG`: 调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 健康检查

- 健康检查端点: `GET /health`
- 数据库连接检查: `GET /health/db`
- Redis连接检查: `GET /health/redis`

## 常见问题

### Q: 数据库连接失败
A: 检查数据库服务是否启动，环境变量配置是否正确

### Q: JWT令牌验证失败
A: 检查SECRET_KEY配置，确保客户端发送正确的Authorization头

### Q: AI模型调用失败
A: 检查API密钥配置，确保网络连接正常

### Q: 文件上传失败
A: 检查存储凭证配置，确保有足够的权限

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

- 项目维护者: 飞书项目AI团队
- 邮箱: support@feishu-ai.com
- 文档: https://docs.feishu-ai.com