# 前端Docker问题解决方案

## 问题分析

经过深入分析，发现前端Docker启动失败的核心原因是：

### 1. 主要问题：Vite二进制文件损坏
- **症状**: `SyntaxError: Invalid or unexpected token`
- **原因**: `/app/node_modules/vite/bin/vite.js` 文件内容被破坏，包含二进制垃圾数据
- **影响**: 无法启动Vite开发服务器

### 2. 次要问题：
- npm依赖安装过程中的网络中断
- Docker缓存导致的依赖不一致
- 文件权限问题

## 解决方案

### 方案1：中国网络优化版（推荐）

使用 `Dockerfile.cn`，已配置淘宝镜像源，构建速度更快：

```bash
# 清理现有镜像和容器
docker-compose -f docker-compose.dev.yml down --rmi all --volumes --remove-orphans

# 重新构建前端镜像（使用国内镜像源）
docker-compose -f docker-compose.dev.yml build --no-cache frontend-dev

# 启动前端服务
docker-compose -f docker-compose.dev.yml --profile frontend up -d
```

### 方案2：完整修复版

如果需要详细验证过程，使用 `Dockerfile.fixed`：

```bash
# 修改docker-compose.dev.yml中的dockerfile行：
# dockerfile: Dockerfile.fixed

# 然后重新构建
docker-compose -f docker-compose.dev.yml build --no-cache frontend-dev
```

### 方案3：最小化Docker方案

如果前两个方案仍有问题，使用 `Dockerfile.minimal`：

```bash
# 修改docker-compose.dev.yml中的dockerfile行：
# dockerfile: Dockerfile.minimal

# 然后重新构建
docker-compose -f docker-compose.dev.yml build --no-cache frontend-dev
```

### 方案3：本地开发方式（备用）

如果Docker问题持续，可以使用本地开发：

```bash
cd frontend
npm install --force
npm run dev
```

## 验证步骤

### 1. 验证容器构建
```bash
docker run --rm frontend-test sh -c "npm --version && node --version && ls -la node_modules/.bin/vite"
```

### 2. 验证Vite文件完整性
```bash
docker run --rm frontend-test sh -c "head -n 3 node_modules/.bin/vite"
```
应该看到正常的JavaScript代码，而不是二进制数据。

### 3. 验证服务启动
```bash
docker run --rm -p 3001:3000 frontend-test timeout 30 npm run dev
```

## 预防措施

### 1. 使用.dockerignore
已创建 `.dockerignore` 文件，排除不必要的文件。

### 2. npm缓存管理
在Dockerfile中加入：
```dockerfile
RUN npm cache clean --force
```

### 3. 版本锁定
使用 `package-lock.json` 锁定依赖版本。

### 4. 网络稳定性
使用官方npm源：
```dockerfile
RUN npm config set registry https://registry.npmjs.org/
```

## 常见问题排查

### Q: 端口冲突
```bash
# 查看端口占用
netstat -ano | findstr ":3000"
# 使用不同端口
docker run -p 3001:3000 ...
```

### Q: 权限问题
```bash
# 在容器内修复权限
RUN chmod +x node_modules/.bin/vite
```

### Q: 网络问题
```bash
# 检查Docker网络
docker network ls
docker network inspect feishuproject-ai_ai-analysis-dev-network
```

## 启动命令汇总

### 完整重建（推荐）
```bash
# 1. 完全清理
docker-compose -f docker-compose.dev.yml down --rmi all --volumes --remove-orphans
docker system prune -f

# 2. 重新构建（使用修复版）
docker-compose -f docker-compose.dev.yml build --no-cache frontend-dev

# 3. 启动服务
docker-compose -f docker-compose.dev.yml --profile frontend up -d

# 4. 查看日志
docker-compose -f docker-compose.dev.yml logs -f frontend-dev
```

### 快速验证
```bash
# 检查服务状态
docker-compose -f docker-compose.dev.yml ps

# 检查前端健康状态
curl http://localhost:3000
```