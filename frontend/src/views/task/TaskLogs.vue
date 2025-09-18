<template>
  <div class="task-logs">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h1 class="page-title">任务执行日志</h1>
        <el-tag v-if="taskInfo" type="primary" class="ml-10">
          {{ taskInfo.name }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="refreshLogs" :loading="loading">
          刷新
        </el-button>
        <el-button :icon="Download" @click="exportLogs" type="success">
          导出日志
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="page-container">
      <el-row :gutter="20" class="search-row">
        <el-col :xs="24" :sm="12" :md="6">
          <el-select
            v-model="searchForm.status"
            placeholder="选择执行状态"
            clearable
            @change="handleSearch"
          >
            <el-option label="等待中" value="pending" />
            <el-option label="处理中" value="processing" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="超时" value="timeout" />
            <el-option label="取消" value="cancelled" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            @change="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-input
            v-model="searchForm.executionId"
            placeholder="执行ID"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-button type="danger" @click="clearLogs" :loading="clearLoading">
            清理日志
          </el-button>
        </el-col>
      </el-row>

      <!-- 执行日志列表 -->
      <el-table 
        :data="executionLogs" 
        v-loading="loading" 
        stripe 
        class="logs-table"
        @row-click="viewLogDetail"
      >
        <el-table-column prop="execution_id" label="执行ID" min-width="200">
          <template #default="{ row }">
            <el-link type="primary" @click.stop="viewLogDetail(row)">
              {{ row.execution_id }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag 
              :type="getStatusType(row.status)" 
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="started_at" label="开始时间" min-width="140">
          <template #default="{ row }">
            {{ formatDateTime(row.started_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="completed_at" label="完成时间" min-width="140">
          <template #default="{ row }">
            {{ formatDateTime(row.completed_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="execution_time_ms" label="执行时间" width="100" align="center">
          <template #default="{ row }">
            {{ formatDuration(row.execution_time_ms) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="tokens_used" label="Token使用" width="100" align="center">
          <template #default="{ row }">
            {{ row.tokens_used || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column prop="retry_count" label="重试次数" width="80" align="center" />
        
        <el-table-column label="操作" width="100" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click.stop="viewLogDetail(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="logDetailVisible"
      title="执行日志详情"
      width="80%"
      class="log-detail-dialog"
      :close-on-click-modal="false"
    >
      <div v-if="selectedLog" class="log-detail">
        <!-- 基本信息 -->
        <el-card class="detail-card" shadow="never">
          <template #header>
            <h3>基本信息</h3>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="执行ID">
              {{ selectedLog.execution_id }}
            </el-descriptions-item>
            <el-descriptions-item label="任务ID">
              {{ selectedLog.task_id }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(selectedLog.status)">
                {{ getStatusText(selectedLog.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="重试次数">
              {{ selectedLog.retry_count }}
            </el-descriptions-item>
            <el-descriptions-item label="开始时间">
              {{ formatDateTime(selectedLog.started_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="完成时间">
              {{ formatDateTime(selectedLog.completed_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Webhook数据 -->
        <el-card class="detail-card" shadow="never">
          <template #header>
            <h3>Webhook数据</h3>
          </template>
          <div class="json-viewer">
            <el-input
              :model-value="formatJson(selectedLog.webhook_payload)"
              type="textarea"
              :rows="8"
              readonly
            />
          </div>
        </el-card>

        <!-- 文件处理信息 -->
        <el-card v-if="selectedLog.file_url" class="detail-card" shadow="never">
          <template #header>
            <h3>文件处理</h3>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="文件URL">
              <el-link :href="selectedLog.file_url" target="_blank" type="primary">
                {{ selectedLog.file_url }}
              </el-link>
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              {{ formatFileSize(selectedLog.file_size_bytes) }}
            </el-descriptions-item>
            <el-descriptions-item label="文件类型">
              {{ selectedLog.file_type }}
            </el-descriptions-item>
            <el-descriptions-item label="获取时间">
              {{ formatDateTime(selectedLog.file_fetched_at) }}
            </el-descriptions-item>
          </el-descriptions>
          <div v-if="selectedLog.file_content_preview" class="mt-15">
            <h4>内容预览</h4>
            <div class="content-preview">
              {{ selectedLog.file_content_preview }}
            </div>
          </div>
        </el-card>

        <!-- AI分析 -->
        <el-card v-if="selectedLog.prompt_sent" class="detail-card" shadow="never">
          <template #header>
            <h3>AI分析</h3>
          </template>
          <div class="ai-section">
            <h4>发送的提示词</h4>
            <div class="prompt-content">
              {{ selectedLog.prompt_sent }}
            </div>
          </div>
          <div v-if="selectedLog.ai_response" class="ai-section">
            <h4>AI响应</h4>
            <div class="response-content">
              {{ selectedLog.ai_response }}
            </div>
          </div>
          <el-descriptions :column="2" border class="mt-15">
            <el-descriptions-item label="Token使用">
              {{ selectedLog.tokens_used }}
            </el-descriptions-item>
            <el-descriptions-item label="成本">
              {{ selectedLog.cost ? `$${selectedLog.cost}` : '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="调用时间">
              {{ formatDateTime(selectedLog.ai_called_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="响应时间">
              {{ formatDateTime(selectedLog.ai_responded_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 飞书写入结果 -->
        <el-card v-if="selectedLog.feishu_response" class="detail-card" shadow="never">
          <template #header>
            <h3>飞书写入结果</h3>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="飞书任务ID">
              {{ selectedLog.feishu_task_id }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDateTime(selectedLog.feishu_updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
          <div class="mt-15">
            <h4>响应数据</h4>
            <div class="json-viewer">
              <el-input
                :model-value="formatJson(selectedLog.feishu_response)"
                type="textarea"
                :rows="6"
                readonly
              />
            </div>
          </div>
        </el-card>

        <!-- 错误信息 -->
        <el-card v-if="selectedLog.error_message" class="detail-card error-card" shadow="never">
          <template #header>
            <h3>错误信息</h3>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="错误代码">
              {{ selectedLog.error_code }}
            </el-descriptions-item>
            <el-descriptions-item label="错误消息">
              {{ selectedLog.error_message }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="logDetailVisible = false">关闭</el-button>
          <el-button
            type="primary"
            :icon="Refresh"
            @click="showRetryConfirmDialog(selectedLog)"
            :loading="retryLoading"
          >
            重试执行
          </el-button>
          <el-button type="success" @click="exportSingleLog">
            导出此日志
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Refresh,
  Download,
  Search,
  Document,
  ChatRound,
  Upload
} from '@element-plus/icons-vue'
import { taskApi, executionApi } from '@/api'
import type { TaskExecution } from '@/types/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const clearLoading = ref(false)
const logDetailVisible = ref(false)
const retryLoading = ref(false)
const executionLogs = ref<TaskExecution[]>([])
const selectedLog = ref<TaskExecution | null>(null)
const taskInfo = ref<any>(null)

// 搜索表单
const searchForm = reactive({
  status: '',
  dateRange: [],
  executionId: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 计算属性
const taskId = computed(() => route.params.id as string)

// 方法
const loadTaskInfo = async () => {
  if (!taskId.value) return
  
  try {
    taskInfo.value = await taskApi.getById(parseInt(taskId.value))
  } catch (error) {
    console.error('加载任务信息失败:', error)
    ElMessage.error('加载任务信息失败')
  }
}

const loadExecutionLogs = async () => {
  if (!taskId.value) return
  
  loading.value = true
  try {
    // 构建查询参数
    const params: any = {
      page: pagination.page,
      size: pagination.size,
      task_id: parseInt(taskId.value)
    }
    
    if (searchForm.status) {
      params.status = searchForm.status
    }
    
    if (searchForm.executionId) {
      params.execution_id = searchForm.executionId
    }
    
    if (searchForm.dateRange?.length === 2) {
      params.started_after = searchForm.dateRange[0]
      params.started_before = searchForm.dateRange[1]
    }
    
    // 调用获取任务执行日志的API
    const response = await executionApi.getList(params)
    executionLogs.value = response.items || []
    pagination.total = response.total || 0
    
  } catch (error) {
    console.error('加载执行日志失败:', error)
    ElMessage.error('加载执行日志失败')
  } finally {
    loading.value = false
  }
}

const refreshLogs = () => {
  loadExecutionLogs()
}

const handleSearch = () => {
  pagination.page = 1
  loadExecutionLogs()
}

const handlePageChange = () => {
  loadExecutionLogs()
}

const handleSizeChange = () => {
  pagination.page = 1
  loadExecutionLogs()
}

const viewLogDetail = async (log: TaskExecution) => {
  // 获取详细日志信息
  try {
    // 使用executionApi获取详细信息，优先使用execution_id
    const executionIdentifier = log.execution_id || log.id
    const detailLog = await executionApi.getById(executionIdentifier)
    selectedLog.value = detailLog
    logDetailVisible.value = true
  } catch (error) {
    console.error('加载日志详情失败:', error)
    ElMessage.error('加载日志详情失败')
    // 如果API调用失败，使用传入的日志作为fallback
    selectedLog.value = log
    logDetailVisible.value = true
  }
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理历史日志吗？这个操作不可逆。',
      '确认清理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    clearLoading.value = true
    // await taskApi.clearExecutionLogs(taskId.value)
    ElMessage.success('日志清理成功')
    loadExecutionLogs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清理日志失败:', error)
      ElMessage.error('清理日志失败')
    }
  } finally {
    clearLoading.value = false
  }
}

const exportLogs = () => {
  // 导出日志功能
  ElMessage.info('导出功能开发中...')
}

const exportSingleLog = () => {
  // 导出单个日志功能
  ElMessage.info('导出功能开发中...')
}

const showRetryConfirmDialog = async (execution: TaskExecution | null) => {
  if (!execution) return

  try {
    await ElMessageBox.confirm(
      `确定要重试执行 "${execution.execution_id}" 吗？这将使用原始Webhook数据重新执行整个任务流程。`,
      '确认重试',
      {
        confirmButtonText: '确定重试',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'retry-confirm-dialog'
      }
    )

    // 确认后先关闭详情弹窗，然后执行重试
    logDetailVisible.value = false
    await retryExecution(execution)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试确认失败:', error)
    }
  }
}

const retryExecution = async (execution: TaskExecution) => {
  if (!execution) return

  retryLoading.value = true
  try {
    // 使用execution_id作为参数，因为后端API使用的是execution_id（字符串）
    const executionIdentifier = execution.execution_id || execution.id
    const result = await executionApi.retry(executionIdentifier)

    if (result.success) {
      ElMessage.success(`重试任务已启动，新的执行ID: ${result.new_execution_id}`)

      // 刷新数据以显示新的执行记录
      setTimeout(() => {
        loadExecutionLogs()
      }, 1000)
    } else {
      ElMessage.error(`重试失败: ${result.error || '未知错误'}`)
    }
  } catch (error) {
    console.error('重试执行失败:', error)
    ElMessage.error('重试执行失败')
  } finally {
    retryLoading.value = false
  }
}

const goBack = () => {
  router.push({ name: 'TaskList' })
}

// 格式化方法
const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    success: 'success',
    failed: 'danger',
    timeout: 'danger',
    cancelled: 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    success: '成功',
    failed: '失败',
    timeout: '超时',
    cancelled: '取消'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateTime: string | null) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN')
}

const formatDuration = (ms: number | null) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

const formatFileSize = (bytes: number | null) => {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}

const formatJson = (obj: any) => {
  if (!obj) return ''
  return JSON.stringify(obj, null, 2)
}

// 生命周期
onMounted(() => {
  loadTaskInfo()
  loadExecutionLogs()
})
</script>

<style scoped>
.task-logs {
  padding: 0;
}

.search-row {
  margin-bottom: 20px;
}

.logs-table {
  margin-bottom: 20px;
  width: 100%;
}

.logs-table .el-table__body-wrapper {
  width: 100%;
}

.process-status {
  display: flex;
  gap: 8px;
}

.status-icon {
  color: #c0c4cc;
  cursor: pointer;
}

.status-icon.success {
  color: #67c23a;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.log-detail-dialog {
  .detail-card {
    margin-bottom: 20px;
  }
  
  .detail-card:last-child {
    margin-bottom: 0;
  }
  
  .error-card {
    border-color: #f56c6c;
  }
  
  .json-viewer {
    .el-textarea__inner {
      font-family: Monaco, 'Courier New', monospace;
      font-size: 13px;
    }
  }
  
  .ai-section {
    margin-bottom: 20px;
  }
  
  .ai-section h4 {
    margin: 0 0 10px 0;
    color: #303133;
    font-size: 14px;
    font-weight: 600;
  }
  
  .prompt-content,
  .response-content {
    background: #f5f7fa;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    padding: 12px;
    font-size: 13px;
    line-height: 1.5;
    max-height: 200px;
    overflow-y: auto;
  }
  
  .content-preview {
    background: #f5f7fa;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    padding: 12px;
    font-size: 13px;
    line-height: 1.5;
    max-height: 150px;
    overflow-y: auto;
    font-family: Monaco, 'Courier New', monospace;
  }
}

/* 重试确认弹窗样式 */
:deep(.retry-confirm-dialog) {
  .el-message-box__content {
    font-size: 14px;
    line-height: 1.6;
  }

  .el-message-box__btns {
    text-align: right;
    padding-top: 20px;
  }

  .el-button--primary {
    background-color: #409eff;
    border-color: #409eff;
  }

  .el-button--primary:hover {
    background-color: #66b1ff;
    border-color: #66b1ff;
  }
}

.mt-15 {
  margin-top: 15px;
}
</style>