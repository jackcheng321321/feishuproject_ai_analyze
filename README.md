# FeishuProject AI - AI综合分析管理平台

FeishuProject AI 是一个面向飞书项目管理场景的 AI 辅助分析平台，支持自动接收项目事件、智能抓取文件与富文本、调用多种大模型进行分析并将结论回写至飞书。项目采用前后端分离架构，可用于团队知识流转、任务质检、合规审阅等自动化场景。

## 功能亮点

- Webhook 接入飞书项目事件，实现无人工干预的自动触发
- 集成 OpenAI、Gemini、Claude 等主流模型，支持自定义模型参数
- 支持 SMB、NFS、FTP、HTTP 等多种协议的文件拉取与解析
- 通过 Celery 与 Redis 构建异步任务流水线，保障高并发场景下的稳定性
- 提供 AI 运行监控、执行历史查询与详细日志，方便定位问题
- 内置密钥加密与权限校验机制，降低敏感数据泄露风险

## 技术栈

**后端**
- FastAPI、SQLAlchemy、Alembic
- Celery、Redis
- JWT/OAuth2 认证

**前端**
- Vue 3、TypeScript、Vite
- Pinia、Axios、Element Plus

## 目录结构

`	ext
.
├─bbackend/              # FastAPI 服务，包含 API、模型、任务、服务等子模块
│  ├─app/
│  │  ├─api/            # v1 接口定义
│  │  ├─core/           # 配置、安全、日志等核心模块
│  │  ├─models/         # SQLAlchemy 模型
│  │  ├─schemas/        # Pydantic 数据模型
│  │  ├─services/       # 业务服务，如飞书、AI 调度等
│  │  ├─tasks/          # Celery 任务与调度脚本
│  │  └─utils/          # 工具方法
│  ├─alembic/           # 数据库迁移脚本
│  └─tests/             # 后端测试用例
├─ffrontend/             # Vue 单页应用
│  ├─src/
│  │  ├─api/            # 前端接口封装
│  │  ├─views/          # 页面视图（任务、模型、监控、Webhook 等）
│  │  ├─stores/         # Pinia 状态管理
│  │  └─utils/          # 前端工具函数
├─.env.docker           # Docker 环境变量示例（请替换默认值）
├─.env.feishu.example   # 飞书相关环境变量模板
├─DOCKER-DEPLOYMENT.md  # 容器化部署详细文档
└─README.md
`

## 快速上手

### 1. 克隆项目

`ash
git clone <your-github-repo-url>
cd feishuproject-ai-opensourse
`

### 2. 准备运行环境

#### Python 后端
`ash
cd bbackend
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -r requirements.txt

# 启动后端（默认端口 8000）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
`

#### 前端
`ash
cd ../ffrontend
npm install
npm run dev   # 默认端口 3000
`

浏览器访问 http://localhost:3000 即可打开管理界面，后端 OpenAPI 文档访问 http://localhost:8000/docs。

### 3. Docker（可选）

仓库附带容器化说明，若需要一键部署，请先根据 .env.docker 配置变量，再参考 DOCKER-DEPLOYMENT.md 制作/恢复对应的 docker-compose 文件后启动。

## 环境变量速览

| 变量名 | 说明 | 示例/默认值 |
| --- | --- | --- |
| ENVIRONMENT | 运行环境 | development |
| SECRET_KEY | JWT 签名密钥（需至少 32 位） | your_jwt_secret_key_32_chars_minimum |
| ENCRYPTION_KEY | 敏感字段加密密钥 | your_encryption_key_32_chars_long |
| DATABASE_URL | PostgreSQL 连接串 | postgresql://postgres:your_password@localhost:5433/ai_analysis_dev |
| REDIS_URL | Redis 连接地址 | edis://localhost:6380/0 |
| FEISHU_PLUGIN_ID | 飞书应用 ID | cli_xxx |
| FEISHU_PLUGIN_SECRET | 飞书应用密钥 | your_feishu_secret |
| FEISHU_USER_KEY | 飞书用户鉴权密钥 | your_feishu_user_key |
| WEBHOOK_BASE_URL | Webhook 回调基础地址 | http://localhost:8000/api/v1/webhooks |
| MAX_FILE_SIZE_MB | 单个文件最大体积 | 100 |
| FLOWER_PASSWORD | Celery 监控面板密码 | your_flower_password |
| GRAFANA_PASSWORD | Grafana 登录密码 | your_grafana_password |

> ⚠️ 请务必在生产环境中替换所有示例密钥、账号与密码。

## 开发与调试

- **数据库迁移**：在 backend 目录执行 lembic revision --autogenerate -m "message" 生成迁移，再运行 lembic upgrade head 应用。
- **代码格式**：推荐使用 lack、isort、lake8 审核后端代码；前端使用 
pm run lint 与 
pm run type-check。
- **测试**：pytest 可运行后端测试，前端可使用 
pm run test。
- **日志查看**：后端默认输出到控制台，可根据配置写入文件；前端可通过浏览器 DevTools 及应用内日志页面排查问题。

## 安全与合规提示

- 仓库内的 .env.docker、backend/.env.test 等文件仅提供开发示例，切勿在生产环境直接使用默认密码。
- backend/test_basic.db 等测试数据库文件如包含真实数据，请在开源前删除或清洗。
- 请确保所有源代码文件都是可阅读的格式，便于社区审查和贡献。
- 建议补充 .gitignore 以忽略 
node_modules/、.venv/、__pycache__/ 等临时文件，避免误提交敏感内容。

## 贡献指南

1. Fork 仓库并创建特性分支
2. 提交前运行格式化与测试确保通过
3. 提交 Pull Request 并说明改动背景与影响范围

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 相关文档

- DOCKER-DEPLOYMENT.md：容器化部署指南
- frontend/LOCAL_SETUP_GUIDE.md（若存在）：前端本地调试说明
- backend/ 目录内脚本：提供常用测试与演示场景的启动脚本

如需在 GitHub 上发布，请在发布前完成安全自查、清理敏感文件，并确保 README 与实际代码保持一致。
