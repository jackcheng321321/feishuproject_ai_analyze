<template>
  <div class="webhook-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack" class="back-btn">
          返回
        </el-button>
        <h1 class="page-title">Webhook详情</h1>
      </div>
      <div class="header-actions">
        <el-button :icon="Edit" @click="editWebhook" v-if="webhook.id">
          编辑
        </el-button>
        <el-button :icon="Connection" @click="testConnection" :loading="testing">
          测试连接
        </el-button>
        <el-button :icon="Refresh" @click="refreshData" :loading="loading">
          刷新
        </el-button>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="page-container" v-loading="loading">
      <el-row :gutter="20" v-if="webhook.id">
        <!-- 基本信息 -->
        <el-col :xs="24" :lg="12">
          <el-card class="info-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">基本信息</span>
                <el-tag :type="getStatusType(webhook.status || 'active')" size="small">
                  {{ getStatusLabel(webhook.status || 'active') }}
                </el-tag>
              </div>
            </template>
            
            <div class="info-list">
              <div class="info-item">
                <label>名称:</label>
                <span>{{ webhook.name }}</span>
              </div>
              <div class="info-item">
                <label>URL:</label>
                <span class="url-text">{{ webhook.url }}</span>
              </div>
              <div class="info-item">
                <label>请求方法:</label>
                <el-tag size="small">{{ webhook.method }}</el-tag>
              </div>
              <div class="info-item">
                <label>超时时间:</label>
                <span>{{ webhook.timeout }}秒</span>
              </div>
              <div class="info-item">
                <label>重试次数:</label>
                <span>{{ webhook.retry_count }}次</span>
              </div>
              <div class="info-item">
                <label>创建时间:</label>
                <span>{{ formatTime(webhook.created_at) }}</span>
              </div>
              <div class="info-item">
                <label>更新时间:</label>
                <span>{{ formatTime(webhook.updated_at) }}</span>
              </div>
              <div class="info-item" v-if="webhook.description">
                <label>描述:</label>
                <span>{{ webhook.description }}</span>
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
              <h4>请求头</h4>
              <div v-if="webhook.headers && Object.keys(webhook.headers).length > 0" class="headers-list">
                <div v-for="(value, key) in webhook.headers" :key="key" class="header-item">
                  <span class="header-key">{{ key }}:</span>
                  <span class="header-value">{{ value }}</span>
                </div>
              </div>
              <el-text v-else type="info">无自定义请求头</el-text>
            </div>
            
            <el-divider />
            
            <div class="config-section">
              <h4>认证信息</h4>
              <div v-if="webhook.auth_type && webhook.auth_type !== 'none'">
                <div class="info-item">
                  <label>认证类型:</label>
                  <el-tag size="small">{{ getAuthTypeLabel(webhook.auth_type) }}</el-tag>
                </div>
                <div class="info-item" v-if="webhook.auth_config">
                  <label>认证配置:</label>
                  <span>已配置</span>
                </div>
              </div>
              <el-text v-else type="info">无认证配置</el-text>
            </div>
          </el-card>
        </el-col>
        
        <!-- 统计信息 -->
        <el-col :xs="24">
          <el-card class="stats-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">调用统计</span>
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
            
            <el-row :gutter="20" class="stats-row">
              <el-col :xs="12" :sm="6">
                <div class="stat-item success">
                  <div class="stat-number">{{ stats.total_calls }}</div>
                  <div class="stat-label">总调用次数</div>
                </div>
              </el-col>
              <el-col :xs="12" :sm="6">
                <div class="stat-item success">
                  <div class="stat-number">{{ stats.success_calls }}</div>
                  <div class="stat-label">成功次数</div>
                </div>
              </el-col>
              <el-col :xs="12" :sm="6">
                <div class="stat-item error">
                  <div class="stat-number">{{ stats.failed_calls }}</div>
                  <div class="stat-label">失败次数</div>
                </div>
              </el-col>
              <el-col :xs="12" :sm="6">
                <div class="stat-item warning">
                  <div class="stat-number">{{ stats.success_rate }}%</div>
                  <div class="stat-label">成功率</div>
                </div>
              </el-col>
            </el-row>
          </el-card>
        </el-col>
        
        <!-- 最近调用记录 -->
        <el-col :xs="24">
          <el-card class="logs-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">最近调用记录</span>
                <el-button size="small" @click="viewAllLogs">
                  查看全部
                </el-button>
              </div>
            </template>
            
            <el-table
              :data="recentLogs"
              stripe
              v-loading="logsLoading"
            >
              <el-table-column prop="id" label="ID" width="80" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="getLogStatusType(row.status)" size="small">
                    {{ getLogStatusLabel(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="response_code" label="响应码" width="100" />
              <el-table-column prop="duration" label="耗时" width="100">
                <template #default="{ row }">
                  {{ row.duration }}ms
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="调用时间" width="180">
                <template #default="{ row }">
                  {{ formatTime(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column prop="error_message" label="错误信息" min-width="200">
                <template #default="{ row }">
                  <span v-if="row.error_message" class="error-text">
                    {{ row.error_message }}
                  </span>
                  <el-text v-else type="success">正常</el-text>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button
                    type="primary"
                    size="small"
                    :icon="View"
                    @click="viewLogDetail(row.id)"
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
      <el-empty v-else description="Webhook不存在或已被删除" />
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
  Connection,
  Refresh,
  View
} from '@element-plus/icons-vue'
import { webhookApi } from '@/api'
import type { Webhook, WebhookLog } from '@/types/api'

const route = useRoute()
const router = useRouter()

// 响应式数据
const loading = ref(false)
const testing = ref(false)
const logsLoading = ref(false)
const statsDateRange = ref<[string, string] | null>(null)

const webhook = ref<Webhook>({
  id: 0,
  name: '',
  webhook_id: '',
  url: '',
  method: 'POST',
  is_active: true,
  headers: {},
  auth_type: 'none',
  auth_config: {},
  timeout: 30,
  retry_count: 3,
  status: 'active',
  description: '',
  created_at: '',
  updated_at: ''
})

const stats = reactive({
  total_calls: 0,
  success_calls: 0,
  failed_calls: 0,
  success_rate: 0
})

const recentLogs = ref<WebhookLog[]>([])

// 方法
const goBack = () => {
  router.back()
}

const refreshData = async () => {
  await Promise.all([
    loadWebhook(),
    loadStats(),
    loadRecentLogs()
  ])
}

const loadWebhook = async () => {
  const webhookId = route.params.id as string
  if (!webhookId || isNaN(Number(webhookId))) {
    ElMessage.error('无效的Webhook ID')
    return
  }
  
  loading.value = true
  try {
    const response = await webhookApi.getById(Number(webhookId))
    webhook.value = response
  } catch (error) {
    console.error('获取Webhook详情失败:', error)
    ElMessage.error('获取Webhook详情失败')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  const webhookId = route.params.id as string
  if (!webhookId || isNaN(Number(webhookId))) return
  
  try {
    const params = {
      webhook_id: Number(webhookId),
      start_date: statsDateRange.value?.[0],
      end_date: statsDateRange.value?.[1]
    }
    const response = await webhookApi.getStats(params)
    Object.assign(stats, response)
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

const loadRecentLogs = async () => {
  const webhookId = route.params.id as string
  if (!webhookId || isNaN(Number(webhookId))) return
  
  logsLoading.value = true
  try {
    const response = await webhookApi.getLogs(Number(webhookId))
    recentLogs.value = response.items
  } catch (error) {
    console.error('获取调用记录失败:', error)
  } finally {
    logsLoading.value = false
  }
}

const editWebhook = () => {
  // 跳转到编辑页面或打开编辑对话框
  router.push({ name: 'WebhookList', query: { edit: webhook.value.id } })
}

const testConnection = async () => {
  testing.value = true
  try {
    await webhookApi.testConnection(webhook.value.id)
    ElMessage.success('连接测试成功')
  } catch (error) {
    console.error('连接测试失败:', error)
    ElMessage.error('连接测试失败')
  } finally {
    testing.value = false
  }
}

const viewAllLogs = () => {
  router.push({ name: 'WebhookLogs', query: { webhook_id: webhook.value.id } })
}

const viewLogDetail = (logId: string) => {
  router.push({ name: 'WebhookLogs', query: { webhook_id: webhook.value.id, log_id: logId } })
}

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

const getAuthTypeLabel = (authType: string) => {
  const labelMap: Record<string, string> = {
    'none': '无认证',
    'basic': 'Basic认证',
    'bearer': 'Bearer Token',
    'api_key': 'API Key'
  }
  return labelMap[authType] || authType
}

const getLogStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    'success': 'success',
    'failed': 'danger',
    'timeout': 'warning'
  }
  return typeMap[status] || 'info'
}

const getLogStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    'success': '成功',
    'failed': '失败',
    'timeout': '超时'
  }
  return labelMap[status] || status
}

const formatTime = (time: string) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.webhook-detail {
  padding: 0;
}

.back-btn {
  margin-right: 15px;
}

.info-card,
.stats-card,
.logs-card {
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

.url-text {
  font-family: 'Courier New', monospace;
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
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

.headers-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.header-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  font-size: 12px;
}

.header-key {
  font-weight: 600;
  color: var(--el-color-primary);
}

.header-value {
  font-family: 'Courier New', monospace;
  color: var(--el-text-color-regular);
}

.stats-row {
  margin-top: 10px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  background: var(--el-fill-color-lighter);
}

.stat-item.success {
  border-left: 4px solid var(--el-color-success);
}

.stat-item.error {
  border-left: 4px solid var(--el-color-danger);
}

.stat-item.warning {
  border-left: 4px solid var(--el-color-warning);
}

.stat-number {
  font-size: 24px;
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

.error-text {
  color: var(--el-color-danger);
  font-size: 12px;
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
    padding: 15px;
  }
  
  .stat-number {
    font-size: 20px;
  }
}
</style>