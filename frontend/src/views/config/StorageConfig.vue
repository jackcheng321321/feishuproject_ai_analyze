<template>
  <div class="storage-config">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">存储凭证配置</h1>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateDialog">
          添加凭证
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
            placeholder="搜索凭证名称或服务器地址"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-select
            v-model="searchForm.protocol_type"
            placeholder="选择协议类型"
            clearable
            @change="handleSearch"
          >
            <el-option label="SMB" value="smb" />
            <el-option label="NFS" value="nfs" />
            <el-option label="FTP" value="ftp" />
            <el-option label="SFTP" value="sftp" />
            <el-option label="HTTP" value="http" />
            <el-option label="HTTPS" value="https" />
            <el-option label="S3" value="s3" />
            <el-option label="WebDAV" value="webdav" />
            <el-option label="本地" value="local" />
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

    <!-- 凭证列表 -->
    <div class="page-container">
      <el-table
        v-loading="loading"
        :data="credentialList"
        stripe
        @sort-change="handleSortChange"
      >
        <el-table-column prop="name" label="凭证名称" sortable min-width="150">
          <template #default="{ row }">
            <div class="credential-name">
              <strong>{{ row.name }}</strong>
              <el-tag
                :type="getProtocolTagType(row.protocol_type)"
                size="small"
                class="ml-10"
              >
                {{ row.protocol_type }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="server_address" label="服务器地址" min-width="200">
          <template #default="{ row }">
            <el-text class="server-address" truncated>
              {{ row.server_address }}
            </el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="username" label="用户名" width="120">
          <template #default="{ row }">
            <el-text truncated>{{ row.username }}</el-text>
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
        
        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              type="success"
              size="small"
              :icon="Connection"
              @click="testConnection(row)"
              :loading="row.testLoading"
            >
              测试
            </el-button>
            <el-button
              type="primary"
              size="small"
              :icon="View"
              @click="viewCredential(row)"
            >
              查看
            </el-button>
            <el-button
              type="warning"
              size="small"
              :icon="Edit"
              @click="editCredential(row)"
            >
              编辑
            </el-button>
            <el-popconfirm
              title="确定要删除这个存储凭证吗？"
              @confirm="deleteCredential(row)"
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

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="凭证名称" prop="name">
          <el-input
            v-model="formData.name"
            placeholder="请输入凭证名称"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="协议类型" prop="protocol_type">
          <el-select 
            v-model="formData.protocol_type" 
            placeholder="请选择协议类型"
            @change="handleProtocolChange"
          >
            <el-option label="SMB (Windows共享)" value="smb">
              <div class="protocol-option">
                <span>SMB</span>
                <small>Windows共享文件夹</small>
              </div>
            </el-option>
            <el-option label="NFS (网络文件系统)" value="nfs">
              <div class="protocol-option">
                <span>NFS</span>
                <small>Unix/Linux网络文件系统</small>
              </div>
            </el-option>
            <el-option label="FTP (文件传输协议)" value="ftp">
              <div class="protocol-option">
                <span>FTP</span>
                <small>标准文件传输协议</small>
              </div>
            </el-option>
            <el-option label="SFTP (安全文件传输)" value="sftp">
              <div class="protocol-option">
                <span>SFTP</span>
                <small>SSH安全文件传输协议</small>
              </div>
            </el-option>
            <el-option label="HTTP (超文本传输协议)" value="http">
              <div class="protocol-option">
                <span>HTTP</span>
                <small>标准Web协议</small>
              </div>
            </el-option>
            <el-option label="HTTPS (安全超文本传输协议)" value="https">
              <div class="protocol-option">
                <span>HTTPS</span>
                <small>安全Web协议</small>
              </div>
            </el-option>
            <el-option label="S3 (Amazon S3)" value="s3">
              <div class="protocol-option">
                <span>S3</span>
                <small>Amazon简单存储服务</small>
              </div>
            </el-option>
            <el-option label="WebDAV (Web分布式创作)" value="webdav">
              <div class="protocol-option">
                <span>WebDAV</span>
                <small>基于HTTP的文件管理</small>
              </div>
            </el-option>
            <el-option label="本地存储" value="local">
              <div class="protocol-option">
                <span>Local</span>
                <small>本地文件系统</small>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="服务器地址" prop="server_address">
          <el-input
            v-model="formData.server_address"
            :placeholder="getAddressPlaceholder()"
          />
          <div class="form-tip">
            {{ getAddressExample() }}
          </div>
        </el-form-item>
        
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名"
          />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            placeholder="请输入密码"
            type="password"
            show-password
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
            @click="testFormConnection"
            :loading="testLoading"
          >
            测试连接
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
      title="凭证详情"
      width="500px"
    >
      <div v-if="currentCredential" class="credential-detail">
        <div class="detail-item">
          <label>凭证名称:</label>
          <span>{{ currentCredential.name }}</span>
        </div>
        <div class="detail-item">
          <label>协议类型:</label>
          <el-tag :type="getProtocolTagType(currentCredential.protocol_type)">
            {{ currentCredential.protocol_type }}
          </el-tag>
        </div>
        <div class="detail-item">
          <label>服务器地址:</label>
          <span>{{ currentCredential.server_address }}</span>
        </div>
        <div class="detail-item">
          <label>用户名:</label>
          <span>{{ currentCredential.username }}</span>
        </div>
        <div class="detail-item">
          <label>状态:</label>
          <el-tag :type="currentCredential.is_active ? 'success' : 'danger'">
            {{ currentCredential.is_active ? '启用' : '禁用' }}
          </el-tag>
        </div>
        <div class="detail-item">
          <label>创建时间:</label>
          <span>{{ formatTime(currentCredential.created_at) }}</span>
        </div>
        <div class="detail-item">
          <label>更新时间:</label>
          <span>{{ formatTime(currentCredential.updated_at) }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Plus,
  Refresh,
  Search,
  View,
  Edit,
  Delete,
  Connection
} from '@element-plus/icons-vue'
import { storageApi } from '@/api'
import type { StorageCredential, StorageCredentialCreate } from '@/types/api'

// 响应式数据
const loading = ref(false)
const credentialList = ref<(StorageCredential & { statusLoading?: boolean; testLoading?: boolean })[]>([])
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const isEdit = ref(false)
const currentCredential = ref<StorageCredential | null>(null)
const testLoading = ref(false)
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

// 搜索表单
const searchForm = reactive({
  search: '',
  protocol_type: '',
  status: ''
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单数据
const formData = reactive<StorageCredentialCreate>({
  name: '',
  protocol_type: '',
  server_address: '',
  username: '',
  password: '',
  is_active: true
})

// 表单验证规则
const formRules: FormRules = {
  name: [
    { required: true, message: '请输入凭证名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  protocol_type: [
    { required: true, message: '请选择协议类型', trigger: 'change' }
  ],
  server_address: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑凭证' : '添加凭证')

// 方法
const refreshData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      search: searchForm.search || undefined,
      protocol_type: searchForm.protocol_type || undefined,
      is_active: searchForm.status === 'active' ? true : searchForm.status === 'inactive' ? false : undefined
    }
    
    const response = await storageApi.getList(params)
    credentialList.value = response.items.map(item => ({ 
      ...item, 
      statusLoading: false,
      testLoading: false
    }))
    pagination.total = response.total
  } catch (error) {
    console.error('获取凭证列表失败:', error)
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

const viewCredential = (credential: StorageCredential) => {
  currentCredential.value = credential
  viewDialogVisible.value = true
}

const editCredential = (credential: StorageCredential) => {
  isEdit.value = true
  currentCredential.value = credential
  
  // 填充表单数据
  Object.assign(formData, {
    name: credential.name,
    protocol_type: credential.protocol_type,
    server_address: credential.server_address,
    username: credential.username,
    password: '', // 不显示原密码
    is_active: credential.is_active
  })
  
  dialogVisible.value = true
}

const deleteCredential = async (credential: StorageCredential) => {
  try {
    await storageApi.delete(credential.id)
    ElMessage.success('删除成功')
    refreshData()
  } catch (error) {
    console.error('删除凭证失败:', error)
  }
}

const handleStatusChange = async (credential: StorageCredential & { statusLoading?: boolean }) => {
  credential.statusLoading = true
  try {
    await storageApi.update(credential.id, { is_active: credential.is_active })
    ElMessage.success(`${credential.is_active ? '启用' : '禁用'}成功`)
  } catch (error) {
    // 恢复原状态
    credential.is_active = !credential.is_active
    console.error('更新状态失败:', error)
  } finally {
    credential.statusLoading = false
  }
}

const testConnection = async (credential: StorageCredential & { testLoading?: boolean }) => {
  credential.testLoading = true
  try {
    const result = await storageApi.testConnection({
      server_address: credential.server_address,
      protocol_type: credential.protocol_type,
      username: credential.username,
      password: '' // 后端会使用存储的密码
    })
    
    if (result.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(`连接测试失败: ${result.message}`)
    }
  } catch (error) {
    console.error('测试连接失败:', error)
  } finally {
    credential.testLoading = false
  }
}

const testFormConnection = async () => {
  if (!formData.server_address || !formData.username || !formData.password || !formData.protocol_type) {
    ElMessage.warning('请先填写完整的连接信息')
    return
  }
  
  testLoading.value = true
  try {
    const result = await storageApi.testConnection({
      server_address: formData.server_address,
      protocol_type: formData.protocol_type,
      username: formData.username,
      password: formData.password
    })
    
    if (result.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.error(`连接测试失败: ${result.message}`)
    }
  } catch (error) {
    console.error('测试连接失败:', error)
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
    if (isEdit.value && currentCredential.value) {
      await storageApi.update(currentCredential.value.id, formData)
      ElMessage.success('更新成功')
    } else {
      await storageApi.create(formData)
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
    protocol_type: '',
    server_address: '',
    username: '',
    password: '',
    is_active: true
  })
  formRef.value?.resetFields()
}

const handleProtocolChange = () => {
  // 协议类型改变时清空服务器地址，让用户重新输入
  formData.server_address = ''
}

const getProtocolTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    'smb': 'primary',
    'nfs': 'success',
    'ftp': 'warning',
    'sftp': 'info',
    'http': 'danger',
    'https': 'success',
    's3': 'warning',
    'webdav': 'info',
    'local': 'success'
  }
  return typeMap[type] || 'info'
}

const getAddressPlaceholder = () => {
  const placeholders: Record<string, string> = {
    'smb': '请输入SMB服务器地址',
    'nfs': '请输入NFS服务器地址',
    'ftp': '请输入FTP服务器地址',
    'sftp': '请输入SFTP服务器地址',
    'http': '请输入HTTP服务器地址',
    'https': '请输入HTTPS服务器地址',
    's3': '请输入S3存储桶地址',
    'webdav': '请输入WebDAV服务器地址',
    'local': '请输入本地路径'
  }
  return placeholders[formData.protocol_type] || '请输入服务器地址'
}

const getAddressExample = () => {
  const examples: Record<string, string> = {
    'smb': '例如: //192.168.1.100/share 或 //server.domain.com/folder',
    'nfs': '例如: 192.168.1.100:/export/data',
    'ftp': '例如: ftp://192.168.1.100:21 或 ftp://ftp.example.com',
    'sftp': '例如: sftp://192.168.1.100:22 或 sftp://server.example.com',
    'http': '例如: http://files.example.com/api/v1/files/',
    'https': '例如: https://files.example.com/api/v1/files/',
    's3': '例如: s3://mybucket.s3.amazonaws.com 或 https://s3.amazonaws.com/mybucket',
    'webdav': '例如: https://webdav.example.com/remote.php/dav/files/username/',
    'local': '例如: /home/user/files 或 C:\\Users\\user\\Documents'
  }
  return examples[formData.protocol_type] || ''
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN')
}

// 生命周期
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.storage-config {
  padding: 0;
}

.search-row {
  margin-bottom: 20px;
}

.credential-name {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 5px;
}

.server-address {
  max-width: 200px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.protocol-option {
  display: flex;
  flex-direction: column;
}

.protocol-option small {
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

.credential-detail {
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

@media (max-width: 768px) {
  .search-row .el-col {
    margin-bottom: 10px;
  }
  
  .credential-name {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>