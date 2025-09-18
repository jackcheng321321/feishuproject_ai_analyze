# Docker完整部署指南

## 🎯 部署目标

将整个AI综合分析管理平台迁移到Docker环境，实现：
- ✅ 保留所有现有数据和配置
- ✅ 统一的容器化部署
- ✅ 代码热重载开发体验
- ✅ Webhook地址保持不变

## 📋 部署前检查清单

### 系统要求
- [x] Windows 10/11 或 Linux
- [x] Docker Desktop 或 Docker Engine
- [x] 至少 4GB 可用内存
- [x] 至少 10GB 可用磁盘空间

### 端口占用检查
```bash
# 检查关键端口是否被占用
netstat -ano | findstr ":8000\|:3000\|:5433\|:6380"
```

### 数据备份（可选但推荐）
```bash
# 备份PostgreSQL数据
docker-compose -f docker-compose.dev.yml exec postgres-dev pg_dump -U postgres ai_analysis_dev > backup.sql

# 备份Redis数据（如果有重要数据）
docker-compose -f docker-compose.dev.yml exec redis-dev redis-cli BGSAVE
```

## 🚀 快速部署

### 方式1: 使用自动部署脚本（推荐）
```bash
# Windows用户
.\deploy-to-docker.bat

# Linux/Mac用户（需要先创建对应的shell脚本）
chmod +x deploy-to-docker.sh
./deploy-to-docker.sh
```

### 方式2: 手动分步部署

#### 步骤1: 停止现有本机服务
```bash
# 停止本机后端和前端服务
# 通过任务管理器或命令行终止Python和Node.js进程
taskkill /f /im python.exe
taskkill /f /im node.exe
```

#### 步骤2: 准备环境配置
```bash
# 复制环境配置模板
copy .env.docker .env

# 根据需要编辑 .env 文件
# 一般情况下默认配置即可使用
```

#### 步骤3: 构建Docker镜像
```bash
# 构建后端开发镜像
docker-compose -f docker-compose.dev.yml build backend-dev

# 构建前端开发镜像  
docker-compose -f docker-compose.dev.yml build frontend-dev
```

#### 步骤4: 启动完整环境
```bash
# 启动包含前端的完整开发环境
docker-compose -f docker-compose.dev.yml --profile frontend up -d

# 查看服务状态
docker-compose -f docker-compose.dev.yml ps
```

#### 步骤5: 验证部署
```bash
# 检查后端健康状态
curl http://localhost:8000/health

# 检查前端服务
curl http://localhost:3000

# 检查API文档
curl http://localhost:8000/docs
```

## 🌐 部署后访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端应用 | http://localhost:3000 | Vue3应用界面 |
| 后端API | http://localhost:8000 | FastAPI后端 |
| API文档 | http://localhost:8000/docs | Swagger文档 |
| PostgreSQL | localhost:5433 | 数据库（外部访问） |
| Redis | localhost:6380 | 缓存（外部访问） |

## 📞 Webhook配置说明

### 🔄 地址不变承诺
- **Webhook URL**: `http://localhost:8000/api/v1/webhooks`
- **访问方式**: 外部系统仍通过localhost:8000访问
- **内部通信**: 容器间通过Docker网络通信

### 🛠 如需修改Webhook地址
1. 编辑 `.env` 文件中的 `WEBHOOK_BASE_URL`
2. 重启服务: `docker-compose -f docker-compose.dev.yml restart backend-dev`
3. 更新飞书应用中的webhook配置

## 💾 数据持久化说明

### 数据保存位置
- **PostgreSQL数据**: Docker卷 `feishuprojectai_postgres_dev_data`
- **Redis数据**: Docker卷 `feishuprojectai_redis_dev_data`  
- **应用日志**: `./backend/logs` 目录

### 数据迁移确认
由于PostgreSQL和Redis已在Docker中运行，数据会自动保留：
- ✅ AI模型配置
- ✅ Webhook配置
- ✅ 任务执行历史
- ✅ 系统配置

## 🛡️ 网络和安全

### Docker网络配置
- **网络名称**: `ai-analysis-dev-network`
- **子网**: `172.21.0.0/16`
- **类型**: Bridge网络

### 端口映射
```yaml
后端: 8000:8000 (主机:容器)
前端: 3000:3000 (主机:容器)
PostgreSQL: 5433:5432 (主机:容器)
Redis: 6380:6379 (主机:容器)
```

### 安全配置
- CORS: 开发环境允许所有来源 (*)
- API密钥: 现有配置保持不变
- 数据库密码: 开发环境使用 `dev_password`

## 🔧 常用管理命令

### 基础操作
```bash
# 查看所有服务状态
docker-compose -f docker-compose.dev.yml ps

# 查看实时日志
docker-compose -f docker-compose.dev.yml logs -f

# 查看特定服务日志
docker-compose -f docker-compose.dev.yml logs -f backend-dev
docker-compose -f docker-compose.dev.yml logs -f frontend-dev

# 重启服务
docker-compose -f docker-compose.dev.yml restart backend-dev
docker-compose -f docker-compose.dev.yml restart frontend-dev

# 停止所有服务
docker-compose -f docker-compose.dev.yml down

# 完全清理（删除数据）
docker-compose -f docker-compose.dev.yml down -v --remove-orphans
```

### 调试操作
```bash
# 进入后端容器
docker-compose -f docker-compose.dev.yml exec backend-dev bash

# 进入前端容器
docker-compose -f docker-compose.dev.yml exec frontend-dev sh

# 进入数据库
docker-compose -f docker-compose.dev.yml exec postgres-dev psql -U postgres -d ai_analysis_dev

# 进入Redis
docker-compose -f docker-compose.dev.yml exec redis-dev redis-cli
```

### 开发调试
```bash
# 重新构建镜像（代码有重大更改时）
docker-compose -f docker-compose.dev.yml build --no-cache

# 仅重启后端（不重构建）
docker-compose -f docker-compose.dev.yml restart backend-dev

# 查看容器资源使用
docker stats
```

## 🚨 故障排除

### 常见问题

#### 1. 端口冲突
**症状**: 启动时报错端口已被占用
```bash
# 解决方案: 检查并终止占用进程
netstat -ano | findstr ":8000"
taskkill /f /PID [进程ID]
```

#### 2. 镜像构建失败
**症状**: build时出现网络超时或依赖安装失败
```bash
# 解决方案: 重新构建并使用本地缓存
docker-compose -f docker-compose.dev.yml build --no-cache backend-dev
```

#### 3. 数据库连接失败
**症状**: 后端日志显示数据库连接错误
```bash
# 解决方案: 检查数据库健康状态
docker-compose -f docker-compose.dev.yml exec postgres-dev pg_isready -U postgres
```

#### 4. 前端访问404
**症状**: http://localhost:3000 无法访问
```bash
# 解决方案: 检查前端容器状态和日志
docker-compose -f docker-compose.dev.yml logs frontend-dev
```

#### 5. Webhook无法访问
**症状**: 外部系统无法调用webhook
```bash
# 解决方案: 确认端口映射和防火墙设置
curl -X POST http://localhost:8000/api/v1/webhooks/test
```

### 性能优化

#### 资源限制配置
在 `docker-compose.dev.yml` 中添加资源限制：
```yaml
services:
  backend-dev:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

#### 卷挂载优化
使用缓存优化的挂载方式：
```yaml
volumes:
  - ./backend:/app:cached  # 已配置
  - /app/node_modules      # 避免挂载node_modules
```

## 📈 监控和维护

### 健康检查
所有服务都配置了健康检查，可通过以下方式查看：
```bash
# 查看容器健康状态
docker ps

# 查看详细健康信息
docker inspect ai-analysis-backend-dev | grep Health -A 10
```

### 日志管理
```bash
# 查看最近100行日志
docker-compose -f docker-compose.dev.yml logs --tail=100 backend-dev

# 按时间过滤日志
docker-compose -f docker-compose.dev.yml logs --since="2025-09-12T10:00:00" backend-dev
```

### 备份和恢复
```bash
# 定期备份数据库
docker-compose -f docker-compose.dev.yml exec postgres-dev pg_dump -U postgres ai_analysis_dev > "backup-$(date +%Y%m%d).sql"

# 恢复数据库
docker-compose -f docker-compose.dev.yml exec -T postgres-dev psql -U postgres -d ai_analysis_dev < backup.sql
```

## 🎓 后续扩展

### 生产环境部署
```bash
# 使用生产环境配置
docker-compose --profile nginx --profile monitoring up -d

# 包含Nginx反向代理和监控服务
```

### 添加更多服务
```bash
# 启动Celery异步任务处理
docker-compose -f docker-compose.dev.yml --profile celery up -d

# 启动管理工具
docker-compose -f docker-compose.dev.yml --profile tools up -d
```

---

## 📞 技术支持

如遇到问题，请按以下顺序排查：
1. 查看容器日志 (`docker-compose logs`)
2. 检查端口占用 (`netstat -ano`)
3. 验证Docker网络 (`docker network ls`)
4. 检查磁盘空间 (`docker system df`)

部署成功后，你的AI综合分析管理平台将运行在完全容器化的环境中，同时保持所有原有功能和数据完整性。