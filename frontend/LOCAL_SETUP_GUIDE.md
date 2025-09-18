# 前端本地运行指南

## 概述

由于Docker前端服务存在依赖损坏问题，现已改为本地运行方案，提供更稳定的开发体验。

## 系统要求

- Windows 10/11
- Node.js 18+ (推荐 18.x 或 20.x)
- npm 8+

## 快速开始

### 1. 初始化环境（仅首次运行）

```batch
# 进入前端目录
cd frontend

# 运行环境设置脚本
setup-local.bat
```

此脚本会：
- 清理旧的依赖
- 设置淘宝npm镜像源
- 安装所有依赖包
- 验证关键组件

### 2. 启动前端服务

#### 方式1：前台运行（推荐调试时使用）
```batch
cd frontend
start-frontend.bat
```
- 在当前终端窗口运行
- 可以看到实时日志
- 按 Ctrl+C 停止

#### 方式2：后台运行（推荐日常使用）
```batch
cd frontend
start-frontend-background.bat
```
- 在后台运行，关闭窗口不影响服务
- 日志保存到 `logs/` 目录
- 适合长期运行

### 3. 停止前端服务

```batch
cd frontend
stop-frontend.bat
```

## 一键系统管理

### 启动整个系统
```batch
# 在项目根目录运行
start-system.bat
```
自动启动：
1. 后端Docker服务（数据库、Redis、API）
2. 前端本地服务

### 停止整个系统
```batch
# 在项目根目录运行
stop-system.bat
```

## 服务地址

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 故障排除

### 端口占用问题
```batch
# 检查端口占用
netstat -ano | findstr ":3000"

# 手动终止占用进程
taskkill /f /pid <进程ID>
```

### 依赖安装失败
```batch
# 清理缓存重新安装
npm cache clean --force
rmdir /s /q node_modules
del package-lock.json
npm install
```

### 网络问题
```batch
# 切换npm镜像源
npm config set registry https://registry.npmmirror.com
# 或者
npm config set registry https://registry.npmjs.org
```

### Node.js版本问题
确保使用Node.js 18+版本：
```batch
node --version
npm --version
```

## 日志查看

### 前端日志
- 前台运行：直接在终端查看
- 后台运行：查看 `frontend/logs/` 目录下的日志文件

### 后端日志
```batch
# 查看Docker服务日志
docker-compose -f docker-compose.noproxy.yml logs -f backend-dev
```

## 开发建议

1. **代码热重载**: 修改前端代码会自动刷新浏览器
2. **API开发**: 后端API更改需要重启Docker容器
3. **调试模式**: 使用前台运行方式便于查看错误信息
4. **生产模式**: 使用后台运行方式进行长期开发

## 文件结构

```
frontend/
├── setup-local.bat              # 环境初始化脚本
├── start-frontend.bat           # 前台启动脚本
├── start-frontend-background.bat # 后台启动脚本
├── stop-frontend.bat            # 停止脚本
├── logs/                        # 日志目录
└── LOCAL_SETUP_GUIDE.md         # 本说明文档

项目根目录/
├── start-system.bat             # 一键启动系统
├── stop-system.bat              # 一键停止系统
└── docker-compose.noproxy.yml   # 后端Docker配置（前端已禁用）
```

## 注意事项

1. **Docker配置**: `docker-compose.noproxy.yml` 中的前端服务已被注释禁用
2. **端口管理**: 确保3000端口未被其他程序占用
3. **依赖更新**: 如需更新依赖，重新运行 `setup-local.bat`
4. **系统重启**: Windows重启后需要重新运行启动脚本

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 首次安装 | `frontend\setup-local.bat` |
| 启动前端 | `frontend\start-frontend.bat` |
| 后台启动前端 | `frontend\start-frontend-background.bat` |
| 停止前端 | `frontend\stop-frontend.bat` |
| 启动整个系统 | `start-system.bat` |
| 停止整个系统 | `stop-system.bat` |
| 查看后端日志 | `docker logs ai-analysis-backend-dev` |