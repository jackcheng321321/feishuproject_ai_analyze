<template>
  <div class="webhook-logs">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">返回</el-button>
        <h1 class="page-title">Webhook日志</h1>
        <el-tag v-if="currentWebhookName" type="primary" class="ml-10">
          {{ currentWebhookName }}
        </el-tag>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="refreshData" :loading="loading">
          刷新
        </el-button>
        <el-button :icon="Delete" @click="clearLogs" type="danger">
          清空日志
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
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="超时" value="timeout" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-select
            v-model="searchForm.webhook_id"
            placeholder="选择Webhook任务"
            clearable
            @change="handleSearch"
            filterable
          >
            <el-option
              label="全选"
              value="all"
            />
            <el-option
              v-for="webhook in webhookList"
              :key="webhook.id"
              :label="webhook.name"
              :value="webhook.id"
            />
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
          <div class="stat-card timeout">
            <div class="stat-number">{{ stats.timeout_count }}</div>
            <div class="stat-label">超时</div>
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

    <!-- 日志列表 -->
    <div class="page-container">
      <el-table
        v-loading="loading"
        :data="logList"
        stripe
        @sort-change="handleSortChange"
        @expand-change="handleExpandChange"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="log-detail">
              <div class="detail-section">
                <h4>请求信息</h4>
                <div class="detail-content">
                  <div class="detail-item">
                    <label>URL:</label>
                    <code>{{ row.request_url }}</code>
                  </div>
                  <div class="detail-item">
                    <label>方法:</label>
                    <el-tag :type="getMethodTagType(row.request_method)" size="small">
                      {{ row.request_method }}
                    </el-tag>
                  </div>
                  <div class="detail-item">
                    <label>请求头:</label>
                    <pre class="json-content">{{ formatJson(row.request_headers) }}</pre>
                  </div>
                  <div class="detail-item">
                    <label>请求体:</label>
                    <pre class="json-content">{{ formatJson(row.request_payload) }}</pre>
                  </div>
                </div>
              </div>
              
              <div class="detail-section">
                <h4>响应信息</h4>
                <div class="detail-content">
                  <div class="detail-item">
                    <label>状态码:</label>
                    <el-tag :type="getStatusTagType(row.response_status)" size="small">
                      {{ row.response_status || 'N/A' }}
                    </el-tag>
                  </div>
                  <div class="detail-item">
                    <label>响应头:</label>
                    <pre class="json-content">{{ formatJson(row.response_headers) }}</pre>
                  </div>
                  <div class="detail-item">
                    <label>响应体:</label>
                    <pre class="json-content">{{ formatJson(row.response_body) }}</pre>
                  </div>
                  <div class="detail-item">
                    <label>耗时:</label>
                    <span>{{ row.duration }}ms</span>
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
        
        <el-table-column prop="webhook_name" label="任务名称" width="200">
          <template #default="{ row }">
            <el-text class="webhook-name-text" :title="row.webhook_name">
              {{ row.webhook_name }}
            </el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="response_status" label="状态码" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.response_status">
              {{ row.response_status }}
            </span>
            <el-text v-else type="info">N/A</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="duration" label="耗时" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.duration !== null">
              {{ row.duration }}ms
            </span>
            <el-text v-else type="info">N/A</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="retry_count" label="重试次数" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.retry_count > 0">
              {{ row.retry_count }}
            </span>
            <el-text v-else type="info">0</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="error_message" label="错误信息" min-width="200">
          <template #default="{ row }">
            <el-text v-if="row.error_message" class="error-text" truncated>
              {{ row.error_message }}
            </el-text>
            <el-text v-else type="success">无</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="触发时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
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
  Delete
} from '@element-plus/icons-vue'
import { webhookApi } from '@/api'
import type { WebhookLog, Webhook } from '@/types/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const logList = ref<(WebhookLog & { retryLoading?: boolean })[]>([])
const webhookInfo = ref<Webhook | null>(null)
const webhookList = ref<Webhook[]>([])
const webhookId = computed(() => {
  const id = route.params.id as string
  return id && !isNaN(Number(id)) ? id : null  // null表示显示所有webhook的日志
})

// 当前显示的webhook名称（用于标题显示）
const currentWebhookName = computed(() => {
  if (searchForm.webhook_id === 'all' || !searchForm.webhook_id) {
    return null // 全选状态不显示标签
  }
  const webhook = webhookList.value.find(w => w.id === Number(searchForm.webhook_id))
  return webhook?.name || null
})

// 搜索表单
const searchForm = reactive({
  status: '',
  webhook_id: 'all' as string | number,  // 使用字符串'all'表示全选
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
  success_count: 0,
  failed_count: 0,
  timeout_count: 0,
  total_count: 0
})

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      webhook_id: (searchForm.webhook_id === 'all' || !searchForm.webhook_id) ? undefined : Number(searchForm.webhook_id)
    }
    
    // 如果webhookId为null，获取所有webhook日志
    let response
    if (webhookId.value === null) {
      // 调用通用日志API（所有webhook的日志）
      response = await webhookApi.getAllLogs(params)
    } else {
      // 调用特定webhook的日志API
      response = await webhookApi.getLogs(Number(webhookId.value), params)
    }
    
    // 处理不同的API响应格式
    // getAllLogs 返回 {items: [], total: 0}
    // getLogs 直接返回数组
    let filteredItems = []
    let originalTotal = 0

    if (Array.isArray(response)) {
      // 直接是数组格式（来自 getLogs）
      filteredItems = response
      originalTotal = response.length
    } else if (response && Array.isArray(response.items)) {
      // 分页格式（来自 getAllLogs）
      filteredItems = response.items
      originalTotal = response.total || response.items.length
    } else {
      console.warn('API响应格式异常:', response)
      filteredItems = []
      originalTotal = 0
    }

    console.log('API响应数据:', response)
    console.log('filteredItems初始值:', filteredItems, '原始总数:', originalTotal)

    // 在前端进行状态筛选
    if (searchForm.status && filteredItems.length > 0) {
      filteredItems = filteredItems.filter((item: any) => item.status === searchForm.status)
    }

    // 在前端进行日期筛选
    if (searchForm.start_date && filteredItems.length > 0) {
      filteredItems = filteredItems.filter((item: any) =>
        new Date(item.created_at) >= new Date(searchForm.start_date)
      )
    }
    if (searchForm.end_date && filteredItems.length > 0) {
      filteredItems = filteredItems.filter((item: any) =>
        new Date(item.created_at) <= new Date(searchForm.end_date)
      )
    }

    // 安全的map操作
    logList.value = filteredItems.map((item: any) => ({
      ...item,
      retryLoading: false
    }))

    // 设置分页总数
    // 注意：对于特定webhook的API（返回数组），我们无法获取真实总数，只能使用当前数据量
    if (webhookId.value === null) {
      // 使用通用API的总数
      pagination.total = originalTotal
    } else {
      // 特定webhook API，使用筛选后的数据量（这可能不是真实总数）
      pagination.total = filteredItems.length
    }
    
    // 更新统计信息（在获取数据后单独调用）
    await updateStats()
  } catch (error) {
    console.error('获取Webhook日志失败:', error)
  } finally {
    loading.value = false
  }
}

const loadWebhookInfo = async () => {
  if (webhookId.value === null) {
    webhookInfo.value = null  // 显示所有日志时不需要特定的webhook信息
    return
  }

  try {
    webhookInfo.value = await webhookApi.getById(Number(webhookId.value))
  } catch (error) {
    console.error('获取Webhook信息失败:', error)
  }
}

const loadWebhookList = async () => {
  try {
    const response = await webhookApi.getList({ page: 1, size: 100 })
    webhookList.value = response.items
  } catch (error) {
    console.error('获取Webhook列表失败:', error)
  }
}

const updateStats = () => {
  // 使用后端API获取统计信息，考虑当前筛选条件
  getWebhookStats()
}

const getWebhookStats = async () => {
  try {
    // 如果有状态或日期筛选，使用带筛选的统计逻辑
    if (searchForm.status || searchForm.start_date || searchForm.end_date) {
      console.log('检测到前端筛选条件，使用分页数据计算统计')
      await getWebhookStatsWithFiltering()
      return
    }

    // 使用专门的统计API，避免分页限制和422错误
    const params: any = {}

    // 如果选中了具体的webhook，则只统计该webhook的数据
    if (searchForm.webhook_id !== 'all' && searchForm.webhook_id) {
      params.webhook_id = Number(searchForm.webhook_id)
    }

    console.log('调用统计API，参数:', params)

    const response = await webhookApi.getLogStats(params)

    console.log('统计API响应:', response)

    // 映射后端API字段到前端stats对象
    stats.success_count = response.success
    stats.failed_count = response.failed
    stats.timeout_count = response.pending  // 将pending映射为timeout_count
    stats.total_count = response.total

    console.log('更新后的统计信息:', stats)
  } catch (error) {
    console.error('获取统计信息失败:', error)
    // 如果API失败，使用当前页面数据计算
    stats.success_count = logList.value.filter(log => log.status === '成功').length
    stats.failed_count = logList.value.filter(log => log.status === '失败').length
    stats.timeout_count = logList.value.filter(log => log.status === '超时' || log.status === '处理中').length
    stats.total_count = logList.value.length
  }
}

// 带筛选条件的统计计算（前端筛选）
const getWebhookStatsWithFiltering = async () => {
  try {
    const params: any = {
      page: 1,
      size: 200 // 后端API限制最大为200
    }

    if (searchForm.webhook_id !== 'all' && searchForm.webhook_id) {
      params.webhook_id = Number(searchForm.webhook_id)
    }

    const response = await webhookApi.getAllLogs(params)
    let filteredLogs = response.items

    // 在前端进行状态筛选
    if (searchForm.status) {
      filteredLogs = filteredLogs.filter((log: any) => log.status === searchForm.status)
    }

    // 在前端进行日期筛选
    if (searchForm.start_date) {
      filteredLogs = filteredLogs.filter((log: any) =>
        new Date(log.created_at) >= new Date(searchForm.start_date)
      )
    }
    if (searchForm.end_date) {
      filteredLogs = filteredLogs.filter((log: any) =>
        new Date(log.created_at) <= new Date(searchForm.end_date)
      )
    }

    stats.success_count = filteredLogs.filter((log: any) => log.status === '成功').length
    stats.failed_count = filteredLogs.filter((log: any) => log.status === '失败').length
    stats.timeout_count = filteredLogs.filter((log: any) => log.status === '超时' || log.status === '处理中').length
    stats.total_count = filteredLogs.length
  } catch (error) {
    console.error('获取带筛选的统计信息失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  refreshData()
  // 筛选条件变化时也更新统计信息
  updateStats()
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

const handleExpandChange = (row: WebhookLog, expanded: boolean) => {
  // 展开时可以加载更多详细信息
  if (expanded) {
    console.log('展开日志详情:', row.id)
  }
}


const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有日志吗？此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await webhookApi.clearLogs(Number(webhookId.value))
    ElMessage.success('日志已清空')
    refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空日志失败:', error)
    }
  }
}

const goBack = () => {
  router.push({ name: 'WebhookList' })
}

const getStatusTagType = (status: string | number) => {
  if (typeof status === 'number') {
    if (status >= 200 && status < 300) return 'success'
    if (status >= 400 && status < 500) return 'warning'
    if (status >= 500) return 'danger'
    return 'info'
  }
  
  const typeMap: Record<string, string> = {
    'success': 'success',
    'failed': 'danger',
    'timeout': 'warning'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'success': '成功',
    'failed': '失败',
    'timeout': '超时'
  }
  return labelMap[status] || status
}

const getEventTagType = (eventType: string) => {
  const typeMap: Record<string, string> = {
    'task_completed': 'success',
    'task_failed': 'danger',
    'task_started': 'primary',
    'system_error': 'warning'
  }
  return typeMap[eventType] || 'info'
}

const getEventTypeLabel = (eventType: string) => {
  const labelMap: Record<string, string> = {
    'task_completed': '任务完成',
    'task_failed': '任务失败',
    'task_started': '任务开始',
    'system_error': '系统错误'
  }
  return labelMap[eventType] || eventType
}

const getMethodTagType = (method: string) => {
  const typeMap: Record<string, string> = {
    'POST': 'primary',
    'PUT': 'success',
    'PATCH': 'warning'
  }
  return typeMap[method] || 'info'
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
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
onMounted(async () => {
  // 首先加载webhook列表，这样下拉框才能正确显示选中的webhook名称
  await loadWebhookList()
  await loadWebhookInfo()

  // 设置初始筛选状态（在webhook列表加载完成后）
  if (webhookId.value) {
    // 从特定webhook进入，设置为对应的webhook ID
    const targetWebhookId = Number(webhookId.value)
    // 确保该webhook在列表中存在
    const targetWebhook = webhookList.value.find(w => w.id === targetWebhookId)
    if (targetWebhook) {
      searchForm.webhook_id = targetWebhookId
    } else {
      searchForm.webhook_id = 'all'
    }
  } else {
    // 从菜单进入，设置为全选状态
    searchForm.webhook_id = 'all'
  }

  refreshData()
})
</script>

<style scoped>
.webhook-logs {
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

.stat-card.success {
  border-left-color: #67c23a;
}

.stat-card.failed {
  border-left-color: #f56c6c;
}

.stat-card.timeout {
  border-left-color: #e6a23c;
}

.stat-card.total {
  border-left-color: #409eff;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.stat-card.success .stat-number {
  color: #67c23a;
}

.stat-card.failed .stat-number {
  color: #f56c6c;
}

.stat-card.timeout .stat-number {
  color: #e6a23c;
}

.stat-card.total .stat-number {
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.log-detail {
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
  flex: 1;
}

.error-message {
  background-color: #fef0f0;
  color: #f56c6c;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  border-left: 4px solid #f56c6c;
}

.error-text {
  color: #f56c6c;
  max-width: 200px;
}

.webhook-name-text {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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