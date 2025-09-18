import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { DashboardStats } from '@/types/api'
import { monitoringApi } from '@/api'

// 主应用状态store
export const useAppStore = defineStore('app', () => {
  // 状态
  const loading = ref(false)
  const sidebarCollapsed = ref(false)
  const dashboardStats = ref<DashboardStats | null>(null)
  const lastUpdated = ref<Date | null>(null)

  // 计算属性
  const isLoading = computed(() => loading.value)
  const isSidebarCollapsed = computed(() => sidebarCollapsed.value)

  // 方法
  const setLoading = (value: boolean) => {
    loading.value = value
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setSidebarCollapsed = (value: boolean) => {
    sidebarCollapsed.value = value
  }

  const fetchDashboardStats = async () => {
    try {
      setLoading(true)
      const stats = await monitoringApi.getDashboardStats()
      dashboardStats.value = stats
      lastUpdated.value = new Date()
    } catch (error) {
      console.error('获取仪表板统计数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const resetDashboardStats = () => {
    dashboardStats.value = null
    lastUpdated.value = null
  }

  return {
    // 状态
    loading,
    sidebarCollapsed,
    dashboardStats,
    lastUpdated,
    // 计算属性
    isLoading,
    isSidebarCollapsed,
    // 方法
    setLoading,
    toggleSidebar,
    setSidebarCollapsed,
    fetchDashboardStats,
    resetDashboardStats
  }
})

// 配置管理store
export const useConfigStore = defineStore('config', () => {
  const aiModels = ref([])
  const storageCredentials = ref([])
  const webhooks = ref([])
  
  const refreshAIModels = async () => {
    // 刷新AI模型列表的逻辑
  }
  
  const refreshStorageCredentials = async () => {
    // 刷新存储凭证列表的逻辑
  }
  
  const refreshWebhooks = async () => {
    // 刷新Webhook列表的逻辑
  }
  
  return {
    aiModels,
    storageCredentials,
    webhooks,
    refreshAIModels,
    refreshStorageCredentials,
    refreshWebhooks
  }
})

// 任务管理store
export const useTaskStore = defineStore('task', () => {
  const tasks = ref([])
  const currentTask = ref(null)
  const executions = ref([])
  
  const refreshTasks = async () => {
    // 刷新任务列表的逻辑
  }
  
  const setCurrentTask = (task: any) => {
    currentTask.value = task
  }
  
  const clearCurrentTask = () => {
    currentTask.value = null
  }
  
  const refreshExecutions = async () => {
    // 刷新执行记录的逻辑
  }
  
  return {
    tasks,
    currentTask,
    executions,
    refreshTasks,
    setCurrentTask,
    clearCurrentTask,
    refreshExecutions
  }
})