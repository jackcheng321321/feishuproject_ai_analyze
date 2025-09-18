# AI综合分析管理平台 - 前端

基于 Vue 3 + TypeScript + Element Plus 构建的现代化管理平台前端应用。

## 🚀 技术栈

- **框架**: Vue 3.3+ (Composition API)
- **语言**: TypeScript 5.1+
- **构建工具**: Vite 4.4+
- **UI组件库**: Element Plus 2.3+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.2+
- **HTTP客户端**: Axios 1.5+
- **图表库**: ECharts 5.4+
- **样式**: CSS3 + Element Plus主题

## 📦 项目结构

```
src/
├── api/                 # API接口封装
│   └── index.ts        # 统一API导出
├── assets/             # 静态资源
│   └── styles/         # 样式文件
│       └── main.css    # 全局样式
├── components/         # 公共组件
├── router/             # 路由配置
│   └── index.ts        # 路由定义
├── stores/             # Pinia状态管理
│   └── index.ts        # 状态store
├── types/              # TypeScript类型定义
│   └── api.ts          # API类型定义
├── utils/              # 工具函数
│   └── request.ts      # HTTP请求封装
├── views/              # 页面组件
│   ├── Dashboard.vue   # 仪表板
│   ├── config/         # 配置管理
│   ├── webhook/        # Webhook管理
│   ├── task/           # 任务管理
│   └── monitor/        # 监控分析
├── App.vue             # 根组件
└── main.ts             # 应用入口
```

## 🛠️ 开发环境设置

### 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 yarn
yarn install
```

### 环境变量配置

复制环境变量模板文件：

```bash
cp .env.example .env.development
```

编辑 `.env.development` 文件，配置开发环境变量：

```env
# 开发环境配置
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=AI综合分析管理平台 (开发)
VITE_APP_VERSION=1.0.0-dev
VITE_DEBUG=true
```

### 启动开发服务器

```bash
# 启动开发服务器
npm run dev

# 或
yarn dev
```

开发服务器将在 `http://localhost:3000` 启动。

## 📋 可用脚本

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 类型检查
npm run type-check

# 代码检查和修复
npm run lint
```

## 🏗️ 构建部署

### 生产构建

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 部署配置

1. **Nginx 配置示例**:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/dist;
    index index.html;

    # 处理 Vue Router 的 history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://backend-server:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

2. **Docker 部署**:

```dockerfile
# 构建阶段
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# 生产阶段
FROM nginx:alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🎨 功能特性

### 核心功能

- **仪表板**: 系统概览和关键指标展示
- **配置管理**: AI模型和存储凭证配置
- **Webhook管理**: Webhook配置和日志监控
- **任务管理**: 分析任务的创建、编辑和执行
- **监控分析**: 执行历史和统计分析

### 技术特性

- **响应式设计**: 支持桌面和移动设备
- **暗色主题**: 支持明暗主题切换
- **国际化**: 支持多语言（当前为中文）
- **类型安全**: 完整的 TypeScript 类型定义
- **模块化**: 清晰的代码组织和模块划分
- **性能优化**: 代码分割和懒加载

## 🔧 开发指南

### 代码规范

项目使用 ESLint + Prettier 进行代码规范检查：

```bash
# 检查代码规范
npm run lint

# 自动修复代码规范问题
npm run lint -- --fix
```

### 组件开发

1. **使用 Composition API**:

```vue
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

// 响应式数据
const loading = ref(false)
const formData = reactive({
  name: '',
  type: ''
})

// 生命周期
onMounted(() => {
  // 初始化逻辑
})
</script>
```

2. **API 调用**:

```typescript
import { taskApi } from '@/api'

const loadTasks = async () => {
  try {
    loading.value = true
    const response = await taskApi.getList({
      page: 1,
      size: 10
    })
    tasks.value = response.items
  } catch (error) {
    console.error('加载任务失败:', error)
  } finally {
    loading.value = false
  }
}
```

3. **状态管理**:

```typescript
import { useTaskStore } from '@/stores'

const taskStore = useTaskStore()

// 使用 store 中的数据和方法
const { tasks, loading } = storeToRefs(taskStore)
const { loadTasks, createTask } = taskStore
```

### 样式开发

1. **使用 CSS 变量**:

```css
.custom-component {
  color: var(--el-text-color-primary);
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
}
```

2. **响应式设计**:

```css
@media (max-width: 768px) {
  .desktop-only {
    display: none;
  }
}
```

## 🐛 常见问题

### 开发环境问题

1. **端口被占用**:
   - 修改 `vite.config.ts` 中的端口配置
   - 或使用 `--port` 参数指定端口

2. **API 请求失败**:
   - 检查后端服务是否启动
   - 确认 `.env.development` 中的 API 地址配置

3. **类型错误**:
   - 运行 `npm run type-check` 检查类型问题
   - 确保 `types/` 目录下的类型定义正确

### 构建问题

1. **内存不足**:
   ```bash
   # 增加 Node.js 内存限制
   NODE_OPTIONS="--max-old-space-size=4096" npm run build
   ```

2. **路径问题**:
   - 检查 `vite.config.ts` 中的路径别名配置
   - 确保导入路径使用正确的别名

## 📚 相关文档

- [Vue 3 官方文档](https://vuejs.org/)
- [Element Plus 组件库](https://element-plus.org/)
- [Vite 构建工具](https://vitejs.dev/)
- [Pinia 状态管理](https://pinia.vuejs.org/)
- [Vue Router 路由](https://router.vuejs.org/)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。