# 🤖 FeishuProject AI - AI综合分析管理平台

<div align="center">

![GitHub License](https://img.shields.io/github/license/jackcheng321321/feishuproject_ai_analyze)
![GitHub Stars](https://img.shields.io/github/stars/jackcheng321321/feishuproject_ai_analyze)
![GitHub Forks](https://img.shields.io/github/forks/jackcheng321321/feishuproject_ai_analyze)
![GitHub Issues](https://img.shields.io/github/issues/jackcheng321321/feishuproject_ai_analyze)

**一个强大的AI驱动的自动化分析平台，专为飞书项目管理场景设计，通过Webhook接收事件，智能分析内容，并自动回写结果**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [文档](#-文档) • [贡献指南](#-贡献) • [许可证](#-许可证)

</div>

## 🌟 项目亮点

- 🔗 **飞书深度集成**: 专为飞书项目管理场景定制，支持项目事件自动接收和结果回写
- 📁 **多协议文件获取**: 支持SMB、NFS、FTP、HTTP等协议，灵活获取飞书项目中的文件内容
- 🤖 **多AI模型支持**: 集成OpenAI、Anthropic Claude、Google Gemini、月之暗面、智谱AI等主流AI服务
- 🔄 **全自动化流程**: 飞书事件接收→数据解析→文件获取→AI分析→结果回写的完整自动化
- 📊 **监控与分析**: 详细的执行日志、Token消耗统计、AI模型性能监控
- 🛡️ **企业级安全**: 敏感信息加密存储、Webhook验证、错误重试机制
- 🐳 **容器化部署**: 完整的Docker支持，一键部署开发/生产环境
- 🎨 **现代化UI**: 基于Vue 3 + TypeScript的响应式管理界面

## 🏗️ 系统架构

```mermaid
graph TD
    A[飞书项目系统] -->|Webhook| B[API网关]
    B --> C[任务调度引擎]
    C --> D[数据解析模块]
    D --> E[文件获取模块]
    E --> F[AI分析模块]
    F --> G[结果回写模块]
    G --> H[飞书项目更新]

    I[配置管理] --> C
    I --> E
    I --> F

    J[监控系统] --> C
    K[日志系统] --> C
    L[PostgreSQL] --> C
    M[Redis缓存] --> C
```

## 🚀 快速开始

### 方式一：Docker一键部署（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/jackcheng321321/feishuproject_ai_analyze.git
cd feishuproject_ai_analyze

# 2. 配置环境变量
cp .env.docker .env
# 编辑 .env 文件，配置数据库密码、AI API密钥等

# 3. 启动完整环境（如果有docker-compose文件）
docker-compose up -d

# 4. 访问服务
echo "🎉 部署完成！"
echo "前端界面: http://localhost:3000"
echo "后端API: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
```

### 方式二：本地开发部署

<details>
<summary>点击展开本地部署步骤</summary>

#### 前置要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

#### 后端设置
```bash
cd backend
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 文件配置数据库、AI API密钥等信息
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 前端设置
```bash
cd frontend
npm install
cp .env.development .env.local
# 编辑环境配置
npm run dev
```
</details>

## 🎯 功能特性

### 核心功能
- ✅ **飞书Webhook接收**: 支持飞书项目事件格式和验证机制
- ✅ **智能数据解析**: 使用JSONPath灵活解析飞书事件数据和富文本内容
- ✅ **多协议文件获取**: SMB/NFS/FTP/HTTP协议支持，获取项目相关文件
- ✅ **AI模型管理**: 支持多种AI服务商，可配置参数和代理
- ✅ **任务执行引擎**: 基于Celery的异步任务处理，支持重试和监控
- ✅ **结果回写**: 自动将AI分析结果写回飞书项目系统

### 管理功能
- 🔧 **配置管理**: Web界面配置AI模型、存储凭证、Webhook
- 📊 **监控面板**: 实时查看任务执行状态、成功率、Token消耗统计
- 📋 **执行日志**: 详细的任务执行日志和错误追踪
- 👥 **多租户支持**: 支持多个独立的飞书应用配置
- 🔐 **权限控制**: 基于JWT的API认证和权限管理

### 技术特性
- 🏗️ **微服务架构**: 后端采用FastAPI，前端Vue 3
- 🗄️ **数据持久化**: PostgreSQL + Redis组合存储
- 📦 **容器化**: Docker + Docker Compose完整支持
- 🔄 **异步处理**: Celery任务队列处理长时间任务
- 📈 **可观测性**: 结构化日志、指标监控
- 🛡️ **安全加固**: API认证、数据加密、输入验证

## 📚 文档

- [🚀 部署指南](DOCKER-DEPLOYMENT.md) - 生产环境部署方案
- [📋 API文档](http://localhost:8000/docs) - 完整的API接口文档
- [🔧 开发文档](backend/README.md) - 后端开发说明
- [🎨 前端文档](frontend/README.md) - 前端开发说明

## 🛠️ 技术栈

### 后端技术
- **框架**: FastAPI 0.104+ (高性能异步Web框架)
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0 + Alembic
- **缓存**: Redis 7 (缓存和消息队列)
- **任务队列**: Celery (异步任务处理)
- **认证**: JWT + OAuth2 (安全认证机制)
- **AI集成**: OpenAI、Anthropic、Google Gemini、月之暗面、智谱AI等
- **文件处理**: 支持SMB、NFS、FTP、HTTP协议

### 前端技术
- **框架**: Vue 3 + TypeScript + Vite
- **UI库**: Element Plus (企业级UI组件)
- **状态管理**: Pinia (Vue生态状态管理)
- **HTTP客户端**: Axios (API请求处理)
- **构建工具**: Vite (极速开发体验)

### 基础设施
- **容器化**: Docker + Docker Compose
- **代理**: Nginx (生产环境)
- **监控**: 支持Prometheus + Grafana集成
- **日志**: 结构化日志输出

## 🌍 使用场景

### 飞书项目管理增强
- 📋 **需求分析**: 自动分析项目需求文档，提取关键信息和风险点
- 📊 **进度报告**: 根据项目数据自动生成进度分析报告
- 🔍 **质量检查**: 智能检查项目交付物质量和合规性
- 📝 **文档归档**: 自动分类和标签项目文档

### 代码质量管理
- 🔍 **代码审查**: 自动分析代码质量和潜在问题
- 📋 **技术文档**: 生成API文档和架构说明
- ✅ **测试报告**: 分析测试覆盖率和质量指标

### 内容智能处理
- 📰 **内容审核**: 自动检测不当内容和合规问题
- 🔍 **信息提取**: 从文档中提取关键业务信息
- 📈 **数据洞察**: 从项目内容中提取业务洞察

## ⚙️ 环境变量配置

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| SECRET_KEY | JWT签名密钥（至少32位） | your_jwt_secret_key_32_chars_minimum |
| ENCRYPTION_KEY | 敏感字段加密密钥 | your_encryption_key_32_chars_long |
| DATABASE_URL | PostgreSQL连接串 | postgresql://postgres:your_password@localhost:5433/ai_analysis_dev |
| REDIS_URL | Redis连接地址 | redis://localhost:6380/0 |
| FEISHU_PLUGIN_ID | 飞书应用ID | cli_xxx |
| FEISHU_PLUGIN_SECRET | 飞书应用密钥 | your_feishu_secret |
| WEBHOOK_BASE_URL | Webhook回调基础地址 | http://localhost:8000/api/v1/webhooks |

> ⚠️ 请务必在生产环境中替换所有示例密钥、账号与密码。

## 🤝 贡献

我们欢迎所有形式的贡献！无论是报告问题、提出功能请求、改进文档还是提交代码。

### 贡献方式
- 🐛 [报告Bug](https://github.com/jackcheng321321/feishuproject_ai_analyze/issues/new)
- 💡 [功能请求](https://github.com/jackcheng321321/feishuproject_ai_analyze/issues/new)
- 📖 改进文档
- 🔧 提交代码

### 开发指南
```bash
# 1. Fork项目
# 2. 创建功能分支
git checkout -b feature/amazing-feature

# 3. 提交更改
git commit -m 'Add some amazing feature'

# 4. 推送到分支
git push origin feature/amazing-feature

# 5. 创建Pull Request
```

## 📈 路线图

### v1.1 (计划中)
- [ ] 更多AI模型支持 (Claude 3.5, GPT-4 Turbo)
- [ ] 批量文件处理能力
- [ ] 高级监控和告警功能
- [ ] 飞书机器人集成

### v1.2 (未来计划)
- [ ] 工作流可视化编辑器
- [ ] 插件系统支持
- [ ] 移动端管理应用
- [ ] 企业级SSO集成

## 🏆 致谢

感谢所有为项目做出贡献的开发者和用户！

特别感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI组件库
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL工具包
- [Docker](https://www.docker.com/) - 容器化平台

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## ☕ 支持项目

如果这个项目对你有帮助，请考虑：

- ⭐ 给项目点个Star
- 🐛 报告问题和建议
- 🤝 提交PR贡献代码
- 📢 分享给其他开发者

---

<div align="center">

**[⬆ 回到顶部](#-feishuproject-ai---ai综合分析管理平台)**

Made with ❤️ by the FeishuProject AI Team

</div>