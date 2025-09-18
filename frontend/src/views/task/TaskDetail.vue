<template>
  <div class="task-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack" class="back-btn">
          返回
        </el-button>
        <h1 class="page-title">任务详情</h1>
      </div>
      <div class="header-actions">
        <el-button :icon="Edit" @click="editTask" v-if="task.id">
          编辑
        </el-button>
        <el-button :icon="Refresh" @click="refreshData" :loading="loading">
          刷新
        </el-button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="page-container" v-loading="loading">
      <el-row :gutter="20" v-if="task.id">
        <!-- 基本信息 -->
        <el-col :xs="24" :lg="12">
          <el-card class="info-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">基本信息</span>
                <div class="status-tags">
                  <el-tag :type="task.is_active ? 'success' : 'warning'" size="small">
                    {{ task.is_active ? '活跃' : '停用' }}
                  </el-tag>

                </div>
              </div>
            </template>
            
            <div class="info-list">
              <div class="info-item">
                <label>任务名称:</label>
                <span>{{ task.name }}</span>
              </div>


              <div class="info-item">
                <label>状态:</label>
                <el-tag :type="task.is_active ? 'success' : 'warning'" size="small">
                  {{ task.is_active ? '活跃' : '停用' }}
                </el-tag>
              </div>
              <div class="info-item">
                <label>创建时间:</label>
                <span>{{ formatTime(task.created_at) }}</span>
              </div>
              <div class="info-item">
                <label>更新时间:</label>
                <span>{{ formatTime(task.updated_at) }}</span>
              </div>
              <div class="info-item" v-if="task.description">
                <label>描述:</label>
                <span>{{ task.description }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 配置信息 -->
        <el-col :xs="24" :lg="12">
          <el-card class="info-card" shadow="never">
            <template #header>
              <span class="card-title">配置信息</span>
            </template>
            
            <div class="config-section">
              <h4>AI模型配置</h4>
              <div v-if="task.ai_model">
                <div class="info-item">
                  <label>模型名称:</label>
                  <span>{{ task.ai_model.name }}</span>
                </div>
              </div>
              <el-text v-else type="info">未配置AI模型</el-text>
            </div>
            
            <el-divider />
            
            <div class="config-section">
              <h4>存储配置</h4>
              <div v-if="task.storage_credential">
                <div class="info-item">
                  <label>存储名称:</label>
                  <span>{{ task.storage_credential.name }}</span>
                </div>
                <div class="info-item">
                  <label>协议类型:</label>
                  <span>{{ task.storage_credential.protocol_type }}</span>
                </div>
              </div>
              <el-text v-else type="info">未配置存储凭证</el-text>
            </div>
            
            <el-divider />
            
            <div class="config-section">
              <h4>Webhook配置</h4>
              <div v-if="task.webhook">
                <div class="info-item">
                  <label>Webhook名称:</label>
                  <span>{{ task.webhook.name }}</span>
                </div>
              </div>
              <el-text v-else type="info">未配置Webhook</el-text>
            </div>
            
            <el-divider />
            
            <div class="config-section">
              <h4>执行配置</h4>
              <div v-if="task.feishu_write_config?.field_id">
                <div class="info-item">
                  <label>飞书字段ID:</label>
                  <span class="path-text">{{ task.feishu_write_config.field_id }}</span>
                </div>
              </div>
              <el-text v-else type="info">未配置飞书字段</el-text>
            </div>
          </el-card>
        </el-col>
        
        <!-- 分析配置和执行统计 -->
        <el-col :xs="24" :lg="12">
          <el-card class="analysis-card" shadow="never">
            <template #header>
              <span class="card-title">分析配置</span>
            </template>

            <div class="config-section">
              <h4>分析提示词</h4>
              <div v-if="task.analysis_prompt" class="prompt-content">
                <pre>{{ task.analysis_prompt }}</pre>
              </div>
              <el-text v-else type="info">未配置分析提示词</el-text>
            </div>
          </el-card>
        </el-col>

        <!-- 执行统计 -->
        <el-col :xs="24" :lg="12">
          <el-card class="stats-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">执行统计</span>
                <el-date-picker
                  v-model="statsDateRange"
                  type="datetimerange"
                  range-separator="至"
                  start-placeholder="开始时间"
                  end-placeholder="结束时间"
                  format="YYYY-MM-DD HH:mm:ss"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  @change="loadStats"
                  size="small"
                />
              </div>
            </template>
            
            <el-row :gutter="15" class="stats-row">
              <el-col :xs="12" :sm="6">
                <div class="stat-item">
                  <div class="stat-number">{{ stats.total_executions }}</div>
                  <div class="stat-label">总执行次数</div>
                </div>
              </el-col>
              <el-col :xs="12" :sm="6">
                <div class="stat-item success">
                  <div class="stat-number">{{ stats.success_executions }}</div>
                  <div class="stat-label">成功次数</div>
                </div>
              </el-col>
              <el-col :xs="12" :sm="6">
                <div class="stat-item error">
                  <div class="stat-number">{{ stats.failed_executions }}</div>
                  <div class="stat-label">失败次数</div>
                </div>
              </el-col>
              <el-col :xs="12" :sm="6">
                <div class="stat-item warning">
                  <div class="stat-number">{{ formatSuccessRate(stats.success_rate) }}</div>
                  <div class="stat-label">成功率</div>
                </div>
              </el-col>
            </el-row>
            
            <el-divider />
            
            <div class="additional-stats">
              <div class="info-item">
                <label>平均耗时:</label>
                <span>{{ formatDuration(stats.avg_duration) }}</span>
              </div>
              <div class="info-item">
                <label>Token消耗:</label>
                <span>{{ formatNumber(stats.total_tokens) }}</span>
              </div>
              <div class="info-item">
                <label>处理文件:</label>
                <span>{{ stats.total_files }}个</span>
              </div>
              <div class="info-item">
                <label>最后执行:</label>
                <span v-if="stats.last_execution">
                  {{ formatTime(stats.last_execution) }}
                </span>
                <el-text v-else type="info">从未执行</el-text>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <!-- 最近执行记录 -->
        <el-col :xs="24">
          <el-card class="executions-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">最近执行记录</span>
                <el-button size="small" @click="viewAllExecutions">
                  查看全部
                </el-button>
              </div>
            </template>
            
            <el-table
              :data="recentExecutions"
              stripe
              v-loading="executionsLoading"
              empty-text="暂无执行记录"
            >
              <el-table-column prop="id" label="执行ID" width="150" align="center" />
              <el-table-column prop="execution_status" label="状态" width="150" align="center">
                <template #default="{ row }">
                  <el-tag :type="getExecutionStatusType(row.execution_status)" size="small">
                    {{ getExecutionStatusLabel(row.execution_status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="execution_time_ms" label="耗时" width="150" align="center">
                <template #default="{ row }">
                  <span v-if="row.execution_time_ms">{{ formatDuration(row.execution_time_ms) }}</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="tokens_used" label="Token" width="150" align="center">
                <template #default="{ row }">
                  <span v-if="row.tokens_used">{{ formatNumber(row.tokens_used) }}</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column prop="started_at" label="开始时间" min-width="180">
                <template #default="{ row }">
                  {{ formatTime(row.started_at) }}
                </template>
              </el-table-column>
              <el-table-column prop="completed_at" label="结束时间" min-width="180">
                <template #default="{ row }">
                  <span v-if="row.completed_at">{{ formatTime(row.completed_at) }}</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    size="small"
                    :icon="View"
                    @click="viewExecutionDetail(row.id)"
                  >
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>
      </el-row>
      
      <!-- 数据为空时的提示 -->
      <el-empty v-else description="任务不存在或已被删除" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  Refresh,
  View
} from '@element-plus/icons-vue'
import { taskApi } from '@/api'
import type { AnalysisTask, TaskExecution } from '@/types/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const executionsLoading = ref(false)
const statsDateRange = ref<[string, string] | null>(null)

const task = ref<AnalysisTask>({
  id: 0,
  name: '',
  description: '',
  webhook_id: 0,
  ai_model_id: 0,
  storage_credential_id: 0,
  data_extraction_config: {},
  prompt_template: '',
  analysis_prompt: '',
  feishu_config: {},
  field_mapping: {},
  is_active: true,
  is_scheduled: false,
  cron_expression: '',
  created_at: '',
  updated_at: ''
})

const stats = reactive({
  total_executions: 0,
  success_executions: 0,
  failed_executions: 0,
  success_rate: 0,
  avg_duration: 0,
  total_tokens: 0,
  total_files: 0,
  last_execution: ''
})

const recentExecutions = ref<TaskExecution[]>([])

// 方法
const goBack = () => {
  router.back()
}

const refreshData = async () => {
  await Promise.all([
    loadTask(),
    loadStats(),
    loadRecentExecutions()
  ])
}

const loadTask = async () => {
  const taskId = route.params.id as string
  if (!taskId) return
  
  loading.value = true
  try {
    const response = await taskApi.getById(parseInt(taskId))
    task.value = response
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  const taskId = route.params.id as string
  if (!taskId) return
  
  try {
    const params = {
      task_id: taskId,
      start_date: statsDateRange.value?.[0],
      end_date: statsDateRange.value?.[1]
    }
    const response = await taskApi.getStats(params)
    Object.assign(stats, response)
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

const loadRecentExecutions = async () => {
  const taskId = route.params.id as string
  if (!taskId) return
  
  executionsLoading.value = true
  try {
    const response = await taskApi.getExecutions({
      task_id: taskId,
      page: 1,
      size: 10
    })
    recentExecutions.value = response.items || []
  } catch (error) {
    console.error('获取执行记录失败:', error)
    ElMessage.warning('获取执行记录失败，请检查网络连接')
    recentExecutions.value = []
  } finally {
    executionsLoading.value = false
  }
}

const editTask = () => {
  router.push({ name: 'TaskCreate', params: { id: task.value.id } })
}


const viewAllExecutions = () => {
  router.push({ name: 'TaskExecutions', query: { task_id: task.value.id } })
}

const viewExecutionDetail = (executionId: string) => {
  router.push({ name: 'TaskExecutions', query: { task_id: task.value.id, execution_id: executionId } })
}

// 工具方法
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'active': 'success',
    'inactive': 'warning',
    'error': 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'active': '活跃',
    'inactive': '停用',
    'error': '错误'
  }
  return labelMap[status] || status
}

const getPriorityType = (priority: string) => {
  const typeMap: Record<string, string> = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return typeMap[priority] || 'info'
}

const getPriorityLabel = (priority: string) => {
  const labelMap: Record<string, string> = {
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return labelMap[priority] || priority
}

const getTaskTypeLabel = (taskType: string) => {
  const labelMap: Record<string, string> = {
    'document_analysis': '文档分析',
    'data_extraction': '数据提取',
    'content_summary': '内容总结',
    'sentiment_analysis': '情感分析',
    'keyword_extraction': '关键词提取',
    'custom_analysis': '自定义分析'
  }
  return labelMap[taskType] || taskType
}

const getScheduleTypeLabel = (scheduleType: string) => {
  const labelMap: Record<string, string> = {
    'manual': '手动执行',
    'cron': '定时执行',
    'interval': '间隔执行'
  }
  return labelMap[scheduleType] || scheduleType
}

const getExecutionStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'pending': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return typeMap[status] || 'info'
}

const getExecutionStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'pending': '等待中',
    'running': '运行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return labelMap[status] || status
}

const getTriggerTypeLabel = (triggerType: string) => {
  const labelMap: Record<string, string> = {
    'manual': '手动',
    'scheduled': '定时',
    'webhook': 'Webhook',
    'api': 'API'
  }
  return labelMap[triggerType] || triggerType
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const formatDuration = (milliseconds: number) => {
  if (!milliseconds) return '0秒'
  
  const seconds = Math.floor(milliseconds / 1000)
  
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return remainingSeconds > 0 ? `${minutes}分${remainingSeconds}秒` : `${minutes}分钟`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
  }
}

const formatSuccessRate = (rate?: number) => {
  if (rate === undefined || rate === null || isNaN(rate)) return '0%'
  // 后端返回0-1之间的小数，需要转换为百分比
  const percentage = rate * 100
  return `${percentage.toFixed(1)}%`
}

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return num.toString()
}

const formatInterval = (seconds: number) => {
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}分钟`
  } else if (seconds < 86400) {
    return `${Math.floor(seconds / 3600)}小时`
  } else {
    return `${Math.floor(seconds / 86400)}天`
  }
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.task-detail {
  padding: 0;
}

.back-btn {
  margin-right: 15px;
}

.status-tags {
  display: flex;
  gap: 8px;
}

.info-card,
.analysis-card,
.schedule-card,
.stats-card,
.executions-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 16px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.info-item label {
  font-weight: 500;
  color: var(--el-text-color-regular);
  min-width: 80px;
  flex-shrink: 0;
}

.info-item span {
  flex: 1;
  word-break: break-all;
}

.path-text {
  font-family: 'Courier New', monospace;
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.cron-text {
  font-family: 'Courier New', monospace;
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--el-color-primary);
}

.config-section {
  margin-bottom: 20px;
}

.config-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.file-types {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.prompt-content {
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
}

.prompt-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.stats-row {
  margin-top: 10px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
  border-left: 4px solid var(--el-border-color);
}

.stat-item.success {
  border-left-color: var(--el-color-success);
}

.stat-item.error {
  border-left-color: var(--el-color-danger);
}

.stat-item.warning {
  border-left-color: var(--el-color-warning);
}

.stat-number {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-item.success .stat-number {
  color: var(--el-color-success);
}

.stat-item.error .stat-number {
  color: var(--el-color-danger);
}

.stat-item.warning .stat-number {
  color: var(--el-color-warning);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.additional-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 768px) {
  .info-item {
    flex-direction: column;
    gap: 5px;
  }
  
  .info-item label {
    min-width: auto;
  }
  
  .stat-item {
    padding: 12px;
  }
  
  .stat-number {
    font-size: 18px;
  }
  
  .status-tags {
    flex-direction: column;
    align-items: flex-start;
  }
}

.text-muted {
  color: var(--el-text-color-placeholder);
  font-style: italic;
}
</style>