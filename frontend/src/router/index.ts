import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '仪表板' }
  },
  {
    path: '/config',
    name: 'Config',
    redirect: '/config/models',
    meta: { title: '配置管理' },
    children: [
      {
        path: 'models',
        name: 'ModelConfig',
        component: () => import('@/views/config/ModelConfig.vue'),
        meta: { title: 'AI模型配置' }
      },
      {
        path: 'storage',
        name: 'StorageConfig',
        component: () => import('@/views/config/StorageConfig.vue'),
        meta: { title: '存储凭证配置' }
      }
    ]
  },
  {
    path: '/webhook',
    name: 'Webhook',
    redirect: '/webhook/list',
    meta: { title: 'Webhook管理' },
    children: [
      {
        path: 'list',
        name: 'WebhookList',
        component: () => import('@/views/webhook/WebhookList.vue'),
        meta: { title: 'Webhook列表' }
      },
      {
        path: 'logs',
        name: 'WebhookLogs',
        component: () => import('@/views/webhook/WebhookLogs.vue'),
        meta: { title: '请求日志' }
      },
      {
        path: 'logs/:id',
        name: 'WebhookLogsById',
        component: () => import('@/views/webhook/WebhookLogs.vue'),
        meta: { title: '请求日志' }
      },
      {
        path: 'detail/:id',
        name: 'WebhookDetail',
        component: () => import('@/views/webhook/WebhookDetail.vue'),
        meta: { title: 'Webhook详情' }
      }
    ]
  },
  {
    path: '/task',
    name: 'Task',
    redirect: '/task/list',
    meta: { title: '任务管理' },
    children: [
      {
        path: 'list',
        name: 'TaskList',
        component: () => import('@/views/task/TaskList.vue'),
        meta: { title: '任务列表' }
      },
      {
        path: 'create',
        name: 'TaskCreate',
        component: () => import('@/views/task/TaskCreate.vue'),
        meta: { title: '创建任务' }
      },
      {
        path: 'detail/:id',
        name: 'TaskDetail',
        component: () => import('@/views/task/TaskDetail.vue'),
        meta: { title: '任务详情' }
      },
      {
        path: 'edit/:id',
        name: 'TaskEdit',
        component: () => import('@/views/task/TaskCreate.vue'),
        meta: { title: '编辑任务' }
      },
      {
        path: 'logs/:id',
        name: 'TaskLogs',
        component: () => import('@/views/task/TaskLogs.vue'),
        meta: { title: '任务日志' }
      }
    ]
  },
  {
    path: '/monitoring',
    name: 'Monitoring',
    redirect: '/monitoring/executions',
    meta: { title: '监控分析' },
    children: [
      {
        path: 'executions',
        name: 'ExecutionHistory',
        component: () => import('@/views/monitoring/ExecutionHistory.vue'),
        meta: { title: '执行历史' }
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/monitoring/Analytics.vue'),
        meta: { title: '统计分析' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - AI综合分析管理平台`
  }
  next()
})

export default router