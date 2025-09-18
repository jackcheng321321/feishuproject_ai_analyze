<template>
  <div class="dashboard">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">仪表板</h1>
      <div class="header-actions">
        <el-button 
          type="primary" 
          :icon="Refresh" 
          @click="refreshData"
          :loading="appStore.isLoading"
        >
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon tasks">
            <el-icon><Operation /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats?.total_tasks || 0 }}</div>
            <div class="stat-label">总任务数</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon active">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats?.active_tasks || 0 }}</div>
            <div class="stat-label">活跃任务</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon executions">
            <el-icon><DataAnalysis /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ stats?.total_executions || 0 }}</div>
            <div class="stat-label">总执行次数</div>
          </div>
        </div>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-icon success-rate">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-number">{{ formatPercentage(stats?.success_rate) }}</div>
            <div class="stat-label">成功率</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 详细信息卡片 -->
    <el-row :gutter="20" class="detail-row">
      <el-col :xs="24" :md="12">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <span>性能指标</span>
              <el-icon><Monitor /></el-icon>
            </div>
          </template>
          <div class="metric-list">
            <div class="metric-item">
              <span class="metric-label">平均执行时间</span>
              <span class="metric-value">{{ formatExecutionTime(stats?.avg_duration) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">Token总消耗</span>
              <span class="metric-value">{{ formatNumber(stats?.total_tokens) }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">系统状态</span>
              <el-tag :type="systemStatus.type" size="small">{{ systemStatus.text }}</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :md="12">
        <el-card class="detail-card">
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
              <el-icon><Tools /></el-icon>
            </div>
          </template>
          <div class="quick-actions">
            <div class="action-btn-wrapper">
              <el-button
                type="primary"
                size="default"
                :icon="Plus"
                @click="$router.push('/task/create')"
                class="action-btn"
              >
                创建新任务
              </el-button>
            </div>
            <div class="action-btn-wrapper">
              <el-button
                type="success"
                size="default"
                :icon="Setting"
                @click="$router.push('/config/models')"
                class="action-btn"
              >
                配置AI模型
              </el-button>
            </div>
            <div class="action-btn-wrapper">
              <el-button
                type="info"
                size="default"
                :icon="Connection"
                @click="$router.push('/webhook/list')"
                class="action-btn"
              >
                管理Webhook
              </el-button>
            </div>
            <div class="action-btn-wrapper">
              <el-button
                type="warning"
                size="default"
                :icon="View"
                @click="$router.push('/monitoring/executions')"
                class="action-btn"
              >
                查看执行记录
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-card class="recent-activity">
      <template #header>
        <div class="card-header">
          <span>最近活动</span>
          <el-icon><Clock /></el-icon>
        </div>
      </template>
      <div v-if="appStore.isLoading" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="recentExecutions.length === 0" class="empty-state">
        <el-empty description="暂无最近活动" />
      </div>
      <div v-else class="activity-list">
        <div 
          v-for="execution in recentExecutions" 
          :key="execution.id" 
          class="activity-item"
        >
          <div class="activity-icon">
            <el-icon
              :class="getExecutionStatusClass(execution.status || execution.execution_status)"
            >
              <component :is="getExecutionStatusIcon(execution.status || execution.execution_status)" />
            </el-icon>
          </div>
          <div class="activity-content">
            <div class="activity-title">
              任务 "{{ execution.task_name || execution.task?.name || '未知任务' }}" {{ getExecutionStatusText(execution.status || execution.execution_status) }}
            </div>
            <div class="activity-time">
              {{ formatTime(execution.started_at) }}
            </div>
          </div>
          <div class="activity-actions">
            <el-button 
              type="text" 
              size="small" 
              @click="viewExecutionDetail(execution.id)"
            >
              查看详情
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 数据更新时间 -->
    <div v-if="appStore.lastUpdated" class="last-updated">
      数据更新时间: {{ formatTime(appStore.lastUpdated) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Refresh, 
  Operation, 
  CircleCheck, 
  DataAnalysis, 
  TrendCharts, 
  Monitor, 
  Tools, 
  Plus, 
  Setting, 
  Connection, 
  View, 
  Clock,
  SuccessFilled,
  WarningFilled,
  CircleCloseFilled,
  Loading
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores'
import { executionApi } from '@/api'
import type { TaskExecution } from '@/types/api'

const router = useRouter()
const appStore = useAppStore()

// 响应式数据
const recentExecutions = ref<TaskExecution[]>([])

// 计算属性
const stats = computed(() => appStore.dashboardStats)

const systemStatus = computed(() => {
  const successRate = stats.value?.success_rate || 0
  if (successRate >= 0.9) {
    return { type: 'success', text: '运行良好' }
  } else if (successRate >= 0.7) {
    return { type: 'warning', text: '需要关注' }
  } else {
    return { type: 'danger', text: '需要处理' }
  }
})

// 方法
const refreshData = async () => {
  await Promise.all([
    appStore.fetchDashboardStats(),
    fetchRecentExecutions()
  ])
}

const fetchRecentExecutions = async () => {
  try {
    const response = await executionApi.getList({ page: 1, size: 5 })
    recentExecutions.value = response.items
  } catch (error) {
    console.error('获取最近执行记录失败:', error)
  }
}

const formatPercentage = (value?: number) => {
  if (value === undefined || value === null) return '0%'
  return `${(value * 100).toFixed(1)}%`
}

const formatExecutionTime = (value?: number) => {
  if (!value) return '0ms'
  if (value < 1000) return `${value}ms`
  return `${(value / 1000).toFixed(1)}s`
}

const formatNumber = (value?: number) => {
  if (!value) return '0'
  return value.toLocaleString()
}

const formatTime = (time: string | Date) => {
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

const getExecutionStatusClass = (status: string) => {
  const classMap: Record<string, string> = {
    success: 'status-success',
    failed: 'status-error',
    processing: 'status-processing',
    pending: 'status-pending'
  }
  return classMap[status] || 'status-pending'
}

const getExecutionStatusIcon = (status: string) => {
  const iconMap: Record<string, any> = {
    success: SuccessFilled,
    failed: CircleCloseFilled,
    processing: Loading,
    pending: WarningFilled
  }
  return iconMap[status] || WarningFilled
}

const getExecutionStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    success: '执行成功',
    failed: '执行失败',
    processing: '正在执行',
    pending: '等待执行'
  }
  return textMap[status] || '未知状态'
}

const viewExecutionDetail = (id: number) => {
  router.push(`/monitoring/executions?execution_id=${id}`)
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 15px;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-icon.tasks {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.executions {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.success-rate {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 5px;
}

.detail-row {
  margin-bottom: 20px;
}

.detail-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.metric-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.metric-item:last-child {
  border-bottom: none;
}

.metric-label {
  color: #606266;
  font-size: 14px;
}

.metric-value {
  font-weight: 600;
  color: #303133;
}

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  align-items: stretch;
}

.action-btn-wrapper {
  height: 48px;
  display: flex;
  align-items: stretch;
}

/* 重置所有按钮样式 */
.action-btn {
  width: 100% !important;
  height: 100% !important;
  min-height: 100% !important;
  max-height: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 12px 16px !important;
  box-sizing: border-box !important;
  line-height: 1 !important;
  border-radius: 6px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  border: 1px solid transparent !important;
}

/* 重置按钮内部元素 */
.action-btn * {
  line-height: 1 !important;
}

.action-btn > span,
.action-btn .el-button__text {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  height: 100% !important;
  width: 100% !important;
  line-height: 1 !important;
}

.action-btn .el-icon {
  margin-right: 6px !important;
  font-size: 16px !important;
  line-height: 1 !important;
  vertical-align: middle !important;
}

/* 确保Grid项目高度一致 */
.quick-actions > .action-btn {
  grid-row: span 1 !important;
  align-self: stretch !important;
}

/* 使用深度选择器强制覆盖Element Plus内部样式 */
:deep(.action-btn) {
  height: 48px !important;
  min-height: 48px !important;
  max-height: 48px !important;
}

:deep(.action-btn .el-button__text) {
  line-height: 1 !important;
}

/* 额外的兜底方案 - 直接重置所有可能的Element Plus类名 */
.el-button.action-btn {
  height: 48px !important;
  min-height: 48px !important;
  max-height: 48px !important;
  line-height: 1 !important;
}

.el-button--primary.action-btn,
.el-button--success.action-btn,
.el-button--info.action-btn,
.el-button--warning.action-btn {
  height: 48px !important;
  min-height: 48px !important;
  max-height: 48px !important;
  line-height: 1 !important;
}

.recent-activity {
  margin-bottom: 20px;
}

.loading-container {
  padding: 20px 0;
}

.empty-state {
  padding: 40px 0;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.activity-item:hover {
  background: #e9ecef;
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.status-success {
  color: #67c23a;
  background: #f0f9ff;
}

.status-error {
  color: #f56c6c;
  background: #fef0f0;
}

.status-processing {
  color: #409eff;
  background: #ecf5ff;
}

.status-pending {
  color: #e6a23c;
  background: #fdf6ec;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
}

.activity-time {
  font-size: 12px;
  color: #909399;
}

.last-updated {
  text-align: center;
  color: #909399;
  font-size: 12px;
  padding: 10px 0;
}

@media (max-width: 768px) {
  .quick-actions {
    grid-template-columns: 1fr;
  }
  
  .activity-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .activity-actions {
    align-self: flex-end;
  }
}
</style>