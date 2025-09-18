<template>
  <div class="task-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">任务管理</h1>
      <div class="header-actions">
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
            placeholder="搜索任务名称或描述"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
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
        <el-col :xs="24" :sm="12" :md="8">
          <el-select
            v-model="searchForm.ai_model_id"
            placeholder="选择AI模型"
            clearable
            @change="handleSearch"
          >
            <el-option
              v-for="model in aiModels"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- 任务列表 -->
    <div class="page-container">
      <el-table
        v-loading="loading"
        :data="taskList"
        stripe
        @sort-change="handleSortChange"
      >
        <el-table-column prop="name" label="任务名称" sortable min-width="150">
          <template #default="{ row }">
            <div class="task-name">
              <strong>{{ row.name }}</strong>
              <el-tag
                v-if="row.is_scheduled"
                type="info"
                size="small"
                class="ml-10"
              >
                定时任务
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            <el-text class="task-description" truncated>
              {{ row.description || '无描述' }}
            </el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="ai_model" label="AI模型" width="150">
          <template #default="{ row }">
            <el-text v-if="row.ai_model" truncated>
              {{ row.ai_model.name }}
            </el-text>
            <el-text v-else type="info">未配置</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="storage_credential" label="存储凭证" width="150">
          <template #default="{ row }">
            <el-text v-if="row.storage_credential" truncated>
              {{ row.storage_credential.name }}
            </el-text>
            <el-text v-else type="info">未配置</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="webhook" label="Webhook" width="150">
          <template #default="{ row }">
            <el-text v-if="row.webhook" truncated>
              {{ row.webhook.name }}
            </el-text>
            <el-text v-else type="info">未配置</el-text>
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
        
        <el-table-column prop="last_executed_at" label="最后执行" width="180">
          <template #default="{ row }">
            <span v-if="row.last_executed_at">
              {{ formatTime(row.last_executed_at) }}
            </span>
            <el-text v-else type="info">未执行</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <div class="operation-buttons">
              <div class="button-row">
                <el-button
                  type="primary"
                  size="small"
                  :icon="View"
                  @click="viewTask(row)"
                >
                  查看
                </el-button>
                <el-button
                  type="warning"
                  size="small"
                  :icon="Edit"
                  @click="editTask(row)"
                >
                  编辑
                </el-button>
              </div>
              <div class="button-row">
                <el-button
                  type="info"
                  size="small"
                  :icon="Document"
                  @click="viewLogs(row)"
                >
                  日志
                </el-button>
                <el-popconfirm
                  title="确定要删除这个任务吗？"
                  @confirm="deleteTask(row)"
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


    <!-- 查看详情对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="任务详情"
      width="800px"
    >
      <div v-if="currentTask" class="task-detail">
        <!-- 基本信息 -->
        <div class="detail-section">
          <h4 class="section-title">基本信息</h4>
          <div class="detail-item">
            <label>任务名称:</label>
            <span>{{ currentTask.name }}</span>
          </div>
          <div class="detail-item">
            <label>显示名称:</label>
            <span>{{ currentTask.display_name || '未设置' }}</span>
          </div>
          <div class="detail-item">
            <label>任务描述:</label>
            <span>{{ currentTask.description || '无描述' }}</span>
          </div>
          <div class="detail-item">
            <label>状态:</label>
            <el-tag :type="currentTask.is_active ? 'success' : 'danger'">
              {{ currentTask.is_active ? '启用' : '禁用' }}
            </el-tag>
          </div>
          <div class="detail-item">
            <label>触发类型:</label>
            <el-tag type="info">{{ currentTask.trigger_type }}</el-tag>
          </div>
          <div class="detail-item">
            <label>优先级:</label>
            <span>{{ currentTask.priority || 0 }}</span>
          </div>
        </div>

        <!-- 关联配置 -->
        <div class="detail-section">
          <h4 class="section-title">关联配置</h4>
          <div class="detail-item">
            <label>Webhook:</label>
            <span v-if="currentTask.webhook">
              {{ currentTask.webhook.name }}
              <small class="detail-url">({{ currentTask.webhook.url }})</small>
            </span>
            <el-text v-else type="info">未配置</el-text>
          </div>
          <div class="detail-item">
            <label>AI模型:</label>
            <span v-if="currentTask.ai_model">
              {{ currentTask.ai_model.name }}
              <small v-if="currentTask.ai_model.model_name">({{ currentTask.ai_model.model_name }})</small>
              <el-tag v-if="currentTask.ai_model.model_type" size="small" class="ml-5">
                {{ currentTask.ai_model.model_type }}
              </el-tag>
            </span>
            <el-text v-else type="info">未配置</el-text>
          </div>
          <div class="detail-item">
            <label>存储凭证:</label>
            <span v-if="currentTask.storage_credential">
              {{ currentTask.storage_credential.name }}
              <el-tag v-if="currentTask.storage_credential.protocol_type" size="small" class="ml-5">
                {{ currentTask.storage_credential.protocol_type }}
              </el-tag>
            </span>
            <el-text v-else type="info">未配置</el-text>
          </div>
        </div>

        <!-- AI分析配置 -->
        <div class="detail-section">
          <h4 class="section-title">AI分析配置</h4>
          <div class="detail-item">
            <label>温度参数:</label>
            <span>{{ currentTask.temperature || '未设置' }}</span>
          </div>
          <div class="detail-item">
            <label>最大Token数:</label>
            <span>{{ currentTask.max_tokens || '未设置' }}</span>
          </div>
          <div class="detail-item">
            <label>富文本解析:</label>
            <el-tag :type="currentTask.enable_rich_text_parsing ? 'success' : 'info'">
              {{ currentTask.enable_rich_text_parsing ? '启用' : '禁用' }}
            </el-tag>
          </div>
        </div>

        <!-- 执行统计 -->
        <div class="detail-section">
          <h4 class="section-title">执行统计</h4>
          <div class="detail-item">
            <label>总执行次数:</label>
            <span>{{ currentTask.total_executions || 0 }}</span>
          </div>
          <div class="detail-item">
            <label>成功执行次数:</label>
            <span>{{ currentTask.successful_executions || 0 }}</span>
          </div>
          <div class="detail-item">
            <label>失败执行次数:</label>
            <span>{{ currentTask.failed_executions || 0 }}</span>
          </div>
          <div class="detail-item">
            <label>最后执行时间:</label>
            <span v-if="currentTask.last_executed_at">
              {{ formatTime(currentTask.last_executed_at) }}
            </span>
            <el-text v-else type="info">未执行</el-text>
          </div>
        </div>

        <!-- 系统信息 -->
        <div class="detail-section">
          <h4 class="section-title">系统信息</h4>
          <div class="detail-item">
            <label>版本号:</label>
            <span>{{ currentTask.version || 1 }}</span>
          </div>
          <div class="detail-item">
            <label>标签:</label>
            <span>{{ currentTask.tags || '无' }}</span>
          </div>
          <div class="detail-item">
            <label>创建时间:</label>
            <span>{{ formatTime(currentTask.created_at) }}</span>
          </div>
          <div class="detail-item">
            <label>更新时间:</label>
            <span>{{ formatTime(currentTask.updated_at) }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Refresh,
  Search,
  View,
  Edit,
  Delete,
  Document
} from '@element-plus/icons-vue'
import { taskApi, aiModelApi, storageApi } from '@/api'
import type { AnalysisTask, AnalysisTaskCreate, AIModel, StorageCredential } from '@/types/api'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const taskList = ref<(AnalysisTask & { statusLoading?: boolean; executeLoading?: boolean })[]>([])
const aiModels = ref<AIModel[]>([])
const storageCredentials = ref<StorageCredential[]>([])
const viewDialogVisible = ref(false)
const currentTask = ref<AnalysisTask | null>(null)

// 搜索表单
const searchForm = reactive({
  search: '',
  status: '',
  ai_model_id: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})


// 方法
const refreshData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      search: searchForm.search || undefined,
      ai_model_id: searchForm.ai_model_id || undefined,
      is_active: searchForm.status === 'active' ? true : searchForm.status === 'inactive' ? false : undefined
    }
    
    const response = await taskApi.getList(params)
    taskList.value = response.items.map(item => ({ 
      ...item, 
      statusLoading: false,
      executeLoading: false
    }))
    pagination.total = response.total
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

const loadAIModels = async () => {
  try {
    const response = await aiModelApi.getList({ size: 100 })
    aiModels.value = response.items.filter(item => item.is_active)
  } catch (error) {
    console.error('获取AI模型列表失败:', error)
  }
}

const loadStorageCredentials = async () => {
  try {
    const response = await storageApi.getList({ size: 100 })
    storageCredentials.value = response.items.filter(item => item.is_active)
  } catch (error) {
    console.error('获取存储凭证列表失败:', error)
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


const viewTask = (task: AnalysisTask) => {
  currentTask.value = task
  viewDialogVisible.value = true
}

const editTask = (task: AnalysisTask) => {
  // 跳转到任务编辑页面
  router.push({ name: 'TaskEdit', params: { id: task.id } })
}

const viewLogs = (task: AnalysisTask) => {
  // 跳转到任务日志页面
  router.push({ name: 'TaskLogs', params: { id: task.id } })
}

const deleteTask = async (task: AnalysisTask) => {
  try {
    await taskApi.delete(task.id)
    ElMessage.success('删除成功')
    refreshData()
  } catch (error) {
    console.error('删除任务失败:', error)
  }
}

const handleStatusChange = async (task: AnalysisTask & { statusLoading?: boolean }) => {
  task.statusLoading = true
  try {
    await taskApi.update(task.id, { is_active: task.is_active })
    ElMessage.success(`${task.is_active ? '启用' : '禁用'}成功`)
  } catch (error) {
    // 恢复原状态
    task.is_active = !task.is_active
    console.error('更新状态失败:', error)
  } finally {
    task.statusLoading = false
  }
}



const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  refreshData()
  loadAIModels()
  loadStorageCredentials()
})
</script>

<style scoped>
.task-list {
  padding: 0;
}

.search-row {
  margin-bottom: 20px;
}

.task-name {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
}

.task-description {
  max-width: 200px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.model-option,
.credential-option {
  display: flex;
  flex-direction: column;
}

.model-option small,
.credential-option small {
  color: #909399;
  font-size: 12px;
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

.task-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  background-color: #fafafa;
}

.section-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-item label {
  min-width: 100px;
  font-weight: 600;
  color: #606266;
  flex-shrink: 0;
}

.detail-item span {
  flex: 1;
  word-break: break-all;
  color: #303133;
}

.detail-item small {
  color: #909399;
  font-size: 12px;
}

.detail-url {
  display: block;
  margin-top: 2px;
  font-family: monospace;
}

.ml-5 {
  margin-left: 5px;
}

.detail-item code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.prompt-content {
  flex: 1;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .search-row .el-col {
    margin-bottom: 10px;
  }
  
  .task-name {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .detail-item {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .detail-item label {
    min-width: auto;
  }
}

/* 操作按钮样式 */
.operation-buttons {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.button-row {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.button-row .el-button {
  min-width: 60px;
  font-size: 12px;
}
</style>