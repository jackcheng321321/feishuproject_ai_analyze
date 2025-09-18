<template>
  <div class="task-executions">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h1 class="page-title">执行记录</h1>
        <el-tag v-if="taskInfo" type="primary" class="ml-10">
          {{ taskInfo.name }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="refreshData" :loading="loading">
          刷新
        </el-button>
        <el-button 
          v-if="taskInfo" 
          type="primary" 
          :icon="VideoPlay" 
          @click="executeTask"
          :loading="executeLoading"
          :disabled="!taskInfo.is_active"
        >
          立即执行
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="page-container">
      <el-row :gutter="20" class="search-row">
        <el-col :xs="24" :sm="12" :md="6">
          <el-select
            v-model="searchForm.status"
            placeholder="选择状态"
            clearable
            @change="handleSearch"
          >
            <el-option label="运行中" value="running" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select
            v-model="searchForm.trigger_type"
            placeholder="选择触发方式"
            clearable
            @change="handleSearch"
          >
            <el-option label="手动执行" value="manual" />
            <el-option label="定时执行" value="scheduled" />
            <el-option label="API调用" value="api" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-date-picker
            v-model="searchForm.start_date"
            type="datetime"
            placeholder="开始时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            @change="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-date-picker
            v-model="searchForm.end_date"
            type="datetime"
            placeholder="结束时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            @change="handleSearch"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 统计信息 -->
    <div class="page-container">
      <el-row :gutter="20" class="stats-row">
        <el-col :xs="12" :sm="6">
          <div class="stat-card running">
            <div class="stat-number">{{ stats.running_count }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card success">
            <div class="stat-number">{{ stats.success_count }}</div>
            <div class="stat-label">成功</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card failed">
            <div class="stat-number">{{ stats.failed_count }}</div>
            <div class="stat-label">失败</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-card total">
            <div class="stat-number">{{ stats.total_count }}</div>
            <div class="stat-label">总计</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 执行记录列表 -->
    <div class="page-container">
      <el-table
        v-loading="loading"
        :data="executionList"
        stripe
        @sort-change="handleSortChange"
        @expand-change="handleExpandChange"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="execution-detail">
              <div class="detail-section">
                <h4>执行信息</h4>
                <div class="detail-content">
                  <div class="detail-item">
                    <label>执行ID:</label>
                    <code>{{ row.id }}</code>
                  </div>
                  <div class="detail-item">
                    <label>文件路径:</label>
                    <code>{{ row.file_path }}</code>
                  </div>
                  <div class="detail-item">
                    <label>文件大小:</label>
                    <span v-if="row.file_size">{{ formatFileSize(row.file_size) }}</span>
                    <el-text v-else type="info">未知</el-text>
                  </div>
                  <div class="detail-item">
                    <label>执行耗时:</label>
                    <span v-if="row.duration">{{ formatDuration(row.duration) }}</span>
                    <el-text v-else type="info">计算中...</el-text>
                  </div>
                  <div class="detail-item">
                    <label>Token消耗:</label>
                    <span v-if="row.tokens_used">{{ row.tokens_used.toLocaleString() }}</span>
                    <el-text v-else type="info">0</el-text>
                  </div>
                </div>
              </div>
              
              <div class="detail-section">
                <h4>分析提示词</h4>
                <div class="detail-content">
                  <pre class="prompt-content">{{ row.analysis_prompt }}</pre>
                </div>
              </div>
              
              <div v-if="row.result" class="detail-section">
                <h4>分析结果</h4>
                <div class="detail-content">
                  <div class="result-content">
                    {{ row.result }}
                  </div>
                </div>
              </div>
              
              <div v-if="row.error_message" class="detail-section">
                <h4>错误信息</h4>
                <div class="detail-content">
                  <div class="error-message">
                    {{ row.error_message }}
                  </div>
                </div>
              </div>
              
              <div v-if="row.metadata" class="detail-section">
                <h4>元数据</h4>
                <div class="detail-content">
                  <pre class="json-content">{{ formatJson(row.metadata) }}</pre>
                </div>
              </div>

              <!-- 重试按钮 -->
              <div class="detail-section">
                <h4>操作</h4>
                <div class="detail-content">
                  <el-button
                    type="primary"
                    size="small"
                    :icon="Refresh"
                    @click="showRetryConfirmDialog(row)"
                    :loading="row.retryLoading"
                  >
                    重试执行
                  </el-button>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="trigger_type" label="触发方式" width="100">
          <template #default="{ row }">
            <el-tag :type="getTriggerTagType(row.trigger_type)" size="small">
              {{ getTriggerTypeLabel(row.trigger_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="file_path" label="文件路径" min-width="200">
          <template #default="{ row }">
            <el-text class="file-path" truncated>
              {{ row.file_path }}
            </el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="file_size" label="文件大小" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.file_size">
              {{ formatFileSize(row.file_size) }}
            </span>
            <el-text v-else type="info">未知</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.duration">
              {{ formatDuration(row.duration) }}
            </span>
            <el-text v-else type="info">计算中</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="tokens_used" label="Token消耗" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.tokens_used">
              {{ row.tokens_used.toLocaleString() }}
            </span>
            <el-text v-else type="info">0</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="started_at" label="开始时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.started_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            <span v-if="row.completed_at">
              {{ formatTime(row.completed_at) }}
            </span>
            <el-text v-else type="info">未完成</el-text>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'running'"
              type="warning"
              size="small"
              :icon="VideoPause"
              @click="cancelExecution(row)"
              :loading="row.cancelLoading"
            >
              取消
            </el-button>
            <el-button
              v-if="row.status === 'failed'"
              type="primary"
              size="small"
              :icon="Refresh"
              @click="retryExecution(row)"
              :loading="row.retryLoading"
            >
              重试
            </el-button>
            <el-button
              v-if="row.result"
              type="success"
              size="small"
              :icon="Download"
              @click="downloadResult(row)"
            >
              下载
            </el-button>
            <el-popconfirm
              v-if="row.status !== 'running'"
              title="确定要删除这条执行记录吗？"
              @confirm="deleteExecution(row)"
            >
              <template #reference>
                <el-button
                  type="danger"
                  size="small"
                  :icon="Delete"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Refresh,
  VideoPlay,
  VideoPause,
  Download,
  Delete
} from '@element-plus/icons-vue'
import { taskApi, executionApi } from '@/api'
import type { TaskExecution, AnalysisTask } from '@/types/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const executeLoading = ref(false)
const executionList = ref<(TaskExecution & { cancelLoading?: boolean; retryLoading?: boolean })[]>([])
const taskInfo = ref<AnalysisTask | null>(null)
const taskId = computed(() => route.params.id as string)

// 搜索表单
const searchForm = reactive({
  status: '',
  trigger_type: '',
  start_date: '',
  end_date: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 统计信息
const stats = reactive({
  running_count: 0,
  success_count: 0,
  failed_count: 0,
  total_count: 0
})

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      task_id: parseInt(taskId.value),
      status: searchForm.status || undefined,
      trigger_type: searchForm.trigger_type || undefined,
      start_date: searchForm.start_date || undefined,
      end_date: searchForm.end_date || undefined
    }

    const response = await executionApi.getList(params)
    executionList.value = response.items.map(item => ({
      ...item,
      cancelLoading: false,
      retryLoading: false
    }))
    pagination.total = response.total

    // 更新统计信息
    updateStats()
  } catch (error) {
    console.error('获取执行记录失败:', error)
  } finally {
    loading.value = false
  }
}

const showRetryConfirmDialog = async (execution: TaskExecution & { retryLoading?: boolean }) => {
  if (!execution) return

  try {
    await ElMessageBox.confirm(
      `确定要重试执行 "${execution.execution_id || execution.id}" 吗？这将使用原始Webhook数据重新执行整个任务流程。`,
      '确认重试',
      {
        confirmButtonText: '确定重试',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    // 确认后执行重试
    await retryTaskExecution(execution)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试确认失败:', error)
    }
  }
}

const retryTaskExecution = async (execution: TaskExecution & { retryLoading?: boolean }) => {
  if (!execution) return

  execution.retryLoading = true
  try {
    // 使用execution_id作为参数，因为后端API使用的是execution_id（字符串）
    const executionIdentifier = execution.execution_id || execution.id
    const result = await executionApi.retry(executionIdentifier)

    if (result.success) {
      ElMessage.success(`重试任务已启动，新的执行ID: ${result.new_execution_id}`)

      // 刷新数据以显示新的执行记录
      setTimeout(() => {
        refreshData()
      }, 1000)
    } else {
      ElMessage.error(`重试失败: ${result.error || '未知错误'}`)
    }
  } catch (error) {
    console.error('重试执行失败:', error)
    ElMessage.error('重试执行失败')
  } finally {
    execution.retryLoading = false
  }
}

const loadTaskInfo = async () => {
  try {
    taskInfo.value = await taskApi.getById(parseInt(taskId.value))
  } catch (error) {
    console.error('获取任务信息失败:', error)
  }
}

const updateStats = () => {
  stats.running_count = executionList.value.filter(exec => exec.execution_status === 'processing').length
  stats.success_count = executionList.value.filter(exec => exec.execution_status === 'success').length
  stats.failed_count = executionList.value.filter(exec => exec.execution_status === 'failed').length
  stats.total_count = executionList.value.length
}

const handleSearch = () => {
  pagination.page = 1
  refreshData()
}

const handleSortChange = ({ prop, order }: any) => {
  refreshData()
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  refreshData()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  refreshData()
}

const handleExpandChange = (row: TaskExecution, expanded: boolean) => {
  // 展开时可以加载更多详细信息
  if (expanded) {
    console.log('展开执行记录详情:', row.id)
  }
}

const executeTask = async () => {
  if (!taskInfo.value) return
  
  executeLoading.value = true
  try {
    const result = await taskApi.execute(taskInfo.value.id)
    ElMessage.success('任务执行已启动')
    
    // 刷新数据以显示新的执行记录
    setTimeout(() => {
      refreshData()
    }, 1000)
  } catch (error) {
    console.error('执行任务失败:', error)
  } finally {
    executeLoading.value = false
  }
}

const cancelExecution = async (execution: TaskExecution & { cancelLoading?: boolean }) => {
  execution.cancelLoading = true
  try {
    await executionApi.cancel(execution.id)
    ElMessage.success('任务已取消')
    refreshData()
  } catch (error) {
    console.error('取消任务失败:', error)
  } finally {
    execution.cancelLoading = false
  }
}

const retryExecution = async (execution: TaskExecution & { retryLoading?: boolean }) => {
  execution.retryLoading = true
  try {
    const result = await executionApi.retry(execution.id)
    ElMessage.success('重试任务已启动')
    
    // 刷新数据以显示新的执行记录
    setTimeout(() => {
      refreshData()
    }, 1000)
  } catch (error) {
    console.error('重试任务失败:', error)
  } finally {
    execution.retryLoading = false
  }
}

const downloadResult = async (execution: TaskExecution) => {
  try {
    const blob = await executionApi.downloadResult(execution.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `execution_${execution.id}_result.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('结果已下载')
  } catch (error) {
    console.error('下载结果失败:', error)
  }
}

const deleteExecution = async (execution: TaskExecution) => {
  try {
    await executionApi.delete(execution.id)
    ElMessage.success('删除成功')
    refreshData()
  } catch (error) {
    console.error('删除执行记录失败:', error)
  }
}

const goBack = () => {
  router.push({ name: 'TaskList' })
}

const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    'running': 'primary',
    'success': 'success',
    'failed': 'danger',
    'cancelled': 'warning'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'running': '运行中',
    'success': '成功',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return labelMap[status] || status
}

const getTriggerTagType = (triggerType: string) => {
  const typeMap: Record<string, string> = {
    'manual': 'primary',
    'scheduled': 'success',
    'api': 'warning'
  }
  return typeMap[triggerType] || 'info'
}

const getTriggerTypeLabel = (triggerType: string) => {
  const labelMap: Record<string, string> = {
    'manual': '手动',
    'scheduled': '定时',
    'api': 'API'
  }
  return labelMap[triggerType] || triggerType
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

const formatFileSize = (size: number) => {
  const units = ['B', 'KB', 'MB', 'GB']
  let unitIndex = 0
  let fileSize = size
  
  while (fileSize >= 1024 && unitIndex < units.length - 1) {
    fileSize /= 1024
    unitIndex++
  }
  
  return `${fileSize.toFixed(1)} ${units[unitIndex]}`
}

const formatDuration = (seconds: number) => {
  if (seconds < 60) {
    return `${seconds}秒`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}分${remainingSeconds}秒`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  }
}

const formatJson = (data: any) => {
  if (!data) return 'N/A'
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

// 生命周期
onMounted(() => {
  loadTaskInfo()
  refreshData()
  
  // 如果URL中有execution_id参数，滚动到对应记录
  const executionId = route.query.execution_id
  if (executionId) {
    setTimeout(() => {
      const element = document.querySelector(`[data-execution-id="${executionId}"]`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth' })
      }
    }, 1000)
  }
})
</script>

<style scoped>
.task-executions {
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-row {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #ddd;
}

.stat-card.running {
  border-left-color: #409eff;
}

.stat-card.success {
  border-left-color: #67c23a;
}

.stat-card.failed {
  border-left-color: #f56c6c;
}

.stat-card.total {
  border-left-color: #909399;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-card.running .stat-number {
  color: #409eff;
}

.stat-card.success .stat-number {
  color: #67c23a;
}

.stat-card.failed .stat-number {
  color: #f56c6c;
}

.stat-card.total .stat-number {
  color: #909399;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.file-path {
  max-width: 200px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.execution-detail {
  padding: 20px;
  background-color: #fafafa;
  border-radius: 4px;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.detail-item label {
  min-width: 80px;
  font-weight: 600;
  color: #606266;
  font-size: 12px;
}

.detail-item code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.prompt-content,
.json-content {
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  margin: 0;
}

.result-content {
  background-color: #f0f9ff;
  color: #1e40af;
  padding: 15px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  border-left: 4px solid #3b82f6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 800px;
  overflow-y: auto;
}

.error-message {
  background-color: #fef0f0;
  color: #f56c6c;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  border-left: 4px solid #f56c6c;
}

@media (max-width: 768px) {
  .search-row .el-col {
    margin-bottom: 10px;
  }
  
  .stats-row .el-col {
    margin-bottom: 10px;
  }
  
  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .detail-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .detail-item label {
    min-width: auto;
  }
}
</style>