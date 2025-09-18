<template>
  <div class="webhook-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">Webhook管理</h1>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showSimpleCreateDialog">
          快速创建
        </el-button>
        <el-button type="info" :icon="Plus" @click="showCreateDialog">
          完整创建
        </el-button>
        <el-button :icon="Refresh" @click="refreshData" :loading="loading">
          刷新
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="page-container">
      <el-row :gutter="20" class="search-row">
        <el-col :xs="24" :sm="12" :md="8">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索Webhook名称或URL"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-select
            v-model="searchForm.event_type"
            placeholder="选择事件类型"
            clearable
            @change="handleSearch"
          >
            <el-option label="任务完成" value="task_completed" />
            <el-option label="任务失败" value="task_failed" />
            <el-option label="任务开始" value="task_started" />
            <el-option label="系统错误" value="system_error" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-select
            v-model="searchForm.status"
            placeholder="选择状态"
            clearable
            @change="handleSearch"
          >
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- Webhook列表 -->
    <div class="page-container">
      <el-table
        v-loading="loading"
        :data="webhookList"
        stripe
        @sort-change="handleSortChange"
      >
        <el-table-column prop="name" label="Webhook名称" sortable min-width="180">
          <template #default="{ row }">
            <div class="webhook-name">
              <div class="webhook-title">
                <strong>{{ row.name }}</strong>
              </div>
              <div v-if="row.description" class="webhook-description">
                <el-text type="info" size="small">
                  {{ row.description }}
                </el-text>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="webhook_url" label="URL地址" min-width="250">
          <template #default="{ row }">
            <el-text class="webhook-url" truncated>
              {{ row.webhook_url }}
            </el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="webhook_id" label="Webhook ID" width="180" align="center">
          <template #default="{ row }">
            <div class="webhook-id-container">
              <el-tooltip content="点击复制到剪贴板" placement="top">
                <el-tag
                  size="small"
                  type="info"
                  class="webhook-id-tag"
                  @click="copyToClipboard(row.webhook_id)"
                >
                  {{ row.webhook_id }}
                </el-tag>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_active" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleStatusChange(row)"
              :loading="row.statusLoading"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="last_triggered_at" label="最后触发" width="180">
          <template #default="{ row }">
            <span v-if="row.last_triggered_at">
              {{ formatTime(row.last_triggered_at) }}
            </span>
            <el-text v-else type="info">未触发</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <div class="action-row">
                <el-button
                  type="info"
                  size="small"
                  :icon="Document"
                  @click="viewLogs(row)"
                >
                  日志
                </el-button>
                <el-button
                  type="primary"
                  size="small"
                  :icon="View"
                  @click="viewWebhook(row)"
                >
                  查看
                </el-button>
              </div>
              <div class="action-row">
                <el-button
                  type="warning"
                  size="small"
                  :icon="Edit"
                  @click="editWebhook(row)"
                >
                  编辑
                </el-button>
                <el-popconfirm
                  title="确定要删除这个Webhook吗？"
                  @confirm="deleteWebhook(row)"
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
              </div>
            </div>
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="Webhook名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入Webhook名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="URL地址" prop="url">
          <el-input
            v-model="formData.url"
            placeholder="请输入Webhook URL地址"
            type="url"
          />
          <div class="form-tip">
            例如: https://api.example.com/webhook/callback
          </div>
        </el-form-item>
        
        <el-form-item label="请求方法" prop="method">
          <el-select v-model="formData.method" placeholder="请选择请求方法">
            <el-option label="POST" value="POST" />
            <el-option label="PUT" value="PUT" />
            <el-option label="PATCH" value="PATCH" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="事件类型" prop="event_type">
          <el-select v-model="formData.event_type" placeholder="请选择事件类型">
            <el-option label="任务完成" value="task_completed" />
            <el-option label="任务失败" value="task_failed" />
            <el-option label="任务开始" value="task_started" />
            <el-option label="系统错误" value="system_error" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="请求头">
          <div class="headers-container">
            <div 
              v-for="(header, index) in formData.headers" 
              :key="index" 
              class="header-item"
            >
              <el-input
                v-model="header.key"
                placeholder="Header名称"
                style="width: 40%"
              />
              <el-input
                v-model="header.value"
                placeholder="Header值"
                style="width: 50%"
              />
              <el-button
                type="danger"
                :icon="Delete"
                size="small"
                @click="removeHeader(index)"
                style="width: 8%"
              />
            </div>
            <el-button
              type="primary"
              :icon="Plus"
              size="small"
              @click="addHeader"
            >
              添加Header
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="超时时间">
          <el-input-number
            v-model="formData.timeout"
            :min="1"
            :max="300"
            :step="1"
            controls-position="right"
          />
          <span class="ml-10">秒</span>
        </el-form-item>
        
        <el-form-item label="重试次数">
          <el-input-number
            v-model="formData.retry_count"
            :min="0"
            :max="10"
            :step="1"
            controls-position="right"
          />
        </el-form-item>
        
        <el-form-item label="启用状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button
            type="info"
            @click="testFormWebhook"
            :loading="testLoading"
          >
            测试Webhook
          </el-button>
          <el-button
            type="primary"
            @click="submitForm"
            :loading="submitLoading"
          >
            {{ isEdit ? '更新' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="Webhook详情"
      width="600px"
    >
      <div v-if="currentWebhook" class="webhook-detail">
        <div class="detail-item">
          <label>Webhook名称:</label>
          <span>{{ currentWebhook.name }}</span>
        </div>
        <div class="detail-item">
          <label>URL地址:</label>
          <span class="url-text">{{ currentWebhook.url }}</span>
        </div>
        <div class="detail-item">
          <label>请求方法:</label>
          <el-tag :type="getMethodTagType(currentWebhook.method)">
            {{ currentWebhook.method }}
          </el-tag>
        </div>
        <div class="detail-item">
          <label>事件类型:</label>
          <el-tag :type="getEventTagType(currentWebhook.event_type || '')">
            {{ getEventTypeLabel(currentWebhook.event_type || '') }}
          </el-tag>
        </div>
        <div class="detail-item">
          <label>请求头:</label>
          <div class="headers-display">
            <div 
              v-for="(value, key) in currentWebhook.headers" 
              :key="key"
              class="header-display-item"
            >
              <code>{{ key }}: {{ value }}</code>
            </div>
            <span v-if="!Object.keys(currentWebhook.headers || {}).length" class="no-headers">
              无自定义请求头
            </span>
          </div>
        </div>
        <div class="detail-item">
          <label>超时时间:</label>
          <span>{{ currentWebhook.timeout }}秒</span>
        </div>
        <div class="detail-item">
          <label>重试次数:</label>
          <span>{{ currentWebhook.retry_count }}次</span>
        </div>
        <div class="detail-item">
          <label>状态:</label>
          <el-tag :type="currentWebhook.is_active ? 'success' : 'danger'">
            {{ currentWebhook.is_active ? '启用' : '禁用' }}
          </el-tag>
        </div>
        <div class="detail-item">
          <label>最后触发:</label>
          <span v-if="currentWebhook.last_triggered_at">
            {{ formatTime(currentWebhook.last_triggered_at) }}
          </span>
          <el-text v-else type="info">未触发</el-text>
        </div>
        <div class="detail-item">
          <label>创建时间:</label>
          <span>{{ formatTime(currentWebhook.created_at) }}</span>
        </div>
        <div class="detail-item">
          <label>更新时间:</label>
          <span>{{ formatTime(currentWebhook.updated_at) }}</span>
        </div>
      </div>
    </el-dialog>

    <!-- 快速创建对话框 -->
    <el-dialog
      v-model="simpleDialogVisible"
      title="快速创建Webhook"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="simpleFormRef"
        :model="simpleFormData"
        :rules="simpleFormRules"
        label-width="100px"
      >
        <el-form-item label="Webhook名称" prop="name">
          <el-input
            v-model="simpleFormData.name"
            placeholder="请输入Webhook名称，如：飞书项目通知"
            maxlength="100"
            show-word-limit
          />
          <div class="form-tip">
            输入一个有意义的名称，便于识别和管理
          </div>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="simpleFormData.description"
            type="textarea"
            :rows="3"
            placeholder="可选：简要描述这个Webhook的用途"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="启用状态">
          <el-switch v-model="simpleFormData.is_active" />
          <span class="ml-10">{{ simpleFormData.is_active ? '立即启用' : '暂时禁用' }}</span>
        </el-form-item>

        <el-alert 
          title="自动配置说明" 
          type="info" 
          :closable="false"
          show-icon
        >
          <template #default>
            <ul style="margin: 0; padding-left: 20px;">
              <li>系统将自动生成Webhook URL和密钥</li>
              <li>使用默认配置：POST请求，30秒超时，3次重试</li>
              <li>创建后可在详情中查看完整URL地址</li>
            </ul>
          </template>
        </el-alert>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="simpleDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitSimpleForm"
            :loading="simpleSubmitLoading"
          >
            创建Webhook
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Plus,
  Refresh,
  Search,
  View,
  Edit,
  Delete,
  Connection,
  Document
} from '@element-plus/icons-vue'
import { webhookApi } from '@/api'
import type { Webhook, WebhookCreate } from '@/types/api'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const webhookList = ref<(Webhook & { statusLoading?: boolean; testLoading?: boolean })[]>([])
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const simpleDialogVisible = ref(false)
const isEdit = ref(false)
const currentWebhook = ref<Webhook | null>(null)
const testLoading = ref(false)
const submitLoading = ref(false)
const simpleSubmitLoading = ref(false)
const formRef = ref<FormInstance>()
const simpleFormRef = ref<FormInstance>()

// 搜索表单
const searchForm = reactive({
  search: '',
  event_type: '',
  status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单数据
const formData = reactive<WebhookCreate & { headers: Array<{ key: string; value: string }> }>({
  name: '',
  url: '',
  method: 'POST',
  event_type: '',
  headers: [],
  timeout: 30,
  retry_count: 3,
  is_active: true
})

// 简化版表单数据
const simpleFormData = reactive({
  name: '',
  description: '',
  is_active: true
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入Webhook名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  url: [
    { required: true, message: '请输入URL地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL地址', trigger: 'blur' }
  ],
  method: [
    { required: true, message: '请选择请求方法', trigger: 'change' }
  ],
  event_type: [
    { required: true, message: '请选择事件类型', trigger: 'change' }
  ]
}

// 简化版表单验证规则
const simpleFormRules: FormRules = {
  name: [
    { required: true, message: '请输入Webhook名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑Webhook' : '创建Webhook')

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      search: searchForm.search || undefined,
      event_type: searchForm.event_type || undefined,
      is_active: searchForm.status === 'active' ? true : searchForm.status === 'inactive' ? false : undefined
    }
    
    const response = await webhookApi.getList(params)
    
    // 兼容处理：API返回可能是数组或分页对象
    if (Array.isArray(response)) {
      webhookList.value = response.map(item => ({ 
        ...item, 
        statusLoading: false,
        testLoading: false
      }))
      pagination.total = response.length
    } else {
      webhookList.value = response.items.map(item => ({ 
        ...item, 
        statusLoading: false,
        testLoading: false
      }))
      pagination.total = response.total
    }
  } catch (error) {
    console.error('获取Webhook列表失败:', error)
    ElMessage.error('获取Webhook列表失败')
  } finally {
    loading.value = false
  }
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

const showCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const showSimpleCreateDialog = () => {
  resetSimpleForm()
  simpleDialogVisible.value = true
}

const viewWebhook = (webhook: Webhook) => {
  currentWebhook.value = webhook
  viewDialogVisible.value = true
}

const editWebhook = (webhook: Webhook) => {
  isEdit.value = true
  currentWebhook.value = webhook
  
  // 填充表单数据
  Object.assign(formData, {
    name: webhook.name,
    url: webhook.url,
    method: webhook.method,
    event_type: webhook.event_type,
    headers: Object.entries(webhook.headers || {}).map(([key, value]) => ({ key, value })),
    timeout: webhook.timeout,
    retry_count: webhook.retry_count,
    is_active: webhook.is_active
  })
  
  dialogVisible.value = true
}

const deleteWebhook = async (webhook: Webhook) => {
  try {
    await webhookApi.delete(webhook.id)
    ElMessage.success('删除成功')
    refreshData()
  } catch (error) {
    console.error('删除Webhook失败:', error)
  }
}

const handleStatusChange = async (webhook: Webhook & { statusLoading?: boolean }) => {
  webhook.statusLoading = true
  try {
    await webhookApi.update(webhook.id, { is_active: webhook.is_active })
    ElMessage.success(`${webhook.is_active ? '启用' : '禁用'}成功`)
  } catch (error) {
    // 恢复原状态
    webhook.is_active = !webhook.is_active
    console.error('更新状态失败:', error)
  } finally {
    webhook.statusLoading = false
  }
}

const testWebhook = async (webhook: Webhook & { testLoading?: boolean }) => {
  webhook.testLoading = true
  try {
    const result = await webhookApi.test(webhook.id)
    
    if (result.success) {
      ElMessage.success('Webhook测试成功')
    } else {
      ElMessage.error(`Webhook测试失败: ${result.message}`)
    }
  } catch (error) {
    console.error('测试Webhook失败:', error)
  } finally {
    webhook.testLoading = false
  }
}

const testFormWebhook = async () => {
  if (!formData.url || !formData.method || !formData.event_type) {
    ElMessage.warning('请先填写完整的Webhook信息')
    return
  }
  
  testLoading.value = true
  try {
    // 转换headers格式
    const headers = formData.headers.reduce((acc, header) => {
      if (header.key && header.value) {
        acc[header.key] = header.value
      }
      return acc
    }, {} as Record<string, string>)
    
    const result = await webhookApi.testUrl({
      url: formData.url,
      method: formData.method,
      headers,
      timeout: formData.timeout
    })
    
    if (result.success) {
      ElMessage.success('Webhook测试成功')
    } else {
      ElMessage.error(`Webhook测试失败: ${result.message}`)
    }
  } catch (error) {
    console.error('测试Webhook失败:', error)
  } finally {
    testLoading.value = false
  }
}

const submitForm = async () => {
  if (!formRef.value) return
  
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  submitLoading.value = true
  try {
    // 过滤有效的headers
    const headers = formData.headers.filter(header => header.key && header.value)
    
    const submitData = {
      name: formData.name,
      url: formData.url,
      method: formData.method,
      event_type: formData.event_type,
      headers,
      timeout: formData.timeout,
      retry_count: formData.retry_count,
      is_active: formData.is_active
    }
    
    if (isEdit.value && currentWebhook.value) {
      await webhookApi.update(currentWebhook.value.id, submitData)
      ElMessage.success('更新成功')
    } else {
      await webhookApi.create(submitData)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    refreshData()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    url: '',
    method: 'POST',
    event_type: '',
    headers: [],
    timeout: 30,
    retry_count: 3,
    is_active: true
  })
  formRef.value?.resetFields()
}

const resetSimpleForm = () => {
  Object.assign(simpleFormData, {
    name: '',
    description: '',
    is_active: true
  })
  simpleFormRef.value?.resetFields()
}

const submitSimpleForm = async () => {
  if (!simpleFormRef.value) return
  
  const valid = await simpleFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  simpleSubmitLoading.value = true
  try {
    const result = await webhookApi.createSimple({
      name: simpleFormData.name,
      description: simpleFormData.description,
      is_active: simpleFormData.is_active
    })
    
    ElMessage.success('Webhook创建成功！')
    
    // 创建成功后显示详细信息
    ElMessageBox.alert(
      `<div style="text-align: left;">
        <p><strong>Webhook已创建成功！</strong></p>
        <p><strong>名称：</strong>${result.name}</p>
        <p><strong>Webhook URL：</strong><br/>
        <code style="word-break: break-all; background: #f5f7fa; padding: 4px;">${result.webhook_url || 'URL正在生成中...'}</code></p>
        <p><strong>状态：</strong>${result.is_active ? '启用' : '禁用'}</p>
        <p style="color: #909399; font-size: 14px; margin-top: 10px;">
          <i class="el-icon-info"></i> 
          您可以将此URL配置到飞书项目或其他系统中
        </p>
      </div>`,
      '创建成功',
      {
        confirmButtonText: '好的',
        dangerouslyUseHTMLString: true,
        customClass: 'webhook-success-dialog'
      }
    )
    
    simpleDialogVisible.value = false
    refreshData()
  } catch (error: any) {
    console.error('创建简化Webhook失败:', error)
    ElMessage.error(`创建失败: ${error.response?.data?.detail || error.message || '未知错误'}`)
  } finally {
    simpleSubmitLoading.value = false
  }
}

const addHeader = () => {
  formData.headers.push({ key: '', value: '' })
}

const removeHeader = (index: number) => {
  formData.headers.splice(index, 1)
}

const viewLogs = (webhook: Webhook) => {
  router.push({ name: 'WebhookLogsById', params: { id: webhook.id } })
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

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.webhook-list {
  padding: 0;
}

.search-row {
  margin-bottom: 20px;
}

.webhook-name {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
}

.webhook-title {
  font-weight: 600;
  color: #303133;
}

.webhook-description {
  margin-top: 2px;
  color: #909399;
  font-size: 12px;
  line-height: 1.4;
}

.webhook-url {
  max-width: 250px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.headers-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.header-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.webhook-detail {
  display: flex;
  flex-direction: column;
  gap: 15px;
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
}

.detail-item span {
  flex: 1;
  word-break: break-all;
}

.url-text {
  font-family: 'Courier New', monospace;
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.headers-display {
  flex: 1;
}

.header-display-item {
  margin-bottom: 5px;
}

.header-display-item code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.no-headers {
  color: #909399;
  font-style: italic;
}

.webhook-id-container {
  width: 100%;
}

.webhook-id-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.webhook-id-tag:hover {
  background-color: #409eff;
  color: white;
  transform: scale(1.02);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
}

.action-row {
  display: flex;
  gap: 8px;
  justify-content: center;
}

@media (max-width: 768px) {
  .search-row .el-col {
    margin-bottom: 10px;
  }
  
  .webhook-name {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-item {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-item .el-input {
    width: 100% !important;
  }
  
  .header-item .el-button {
    width: auto !important;
    align-self: flex-end;
  }
}
</style>