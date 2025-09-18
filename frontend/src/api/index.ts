import { request } from '@/utils/request'
import type {
  AIModel,
  AIModelCreate,
  AIModelUpdate,
  StorageCredential,
  StorageCredentialCreate,
  StorageCredentialUpdate,
  Webhook,
  WebhookCreate,
  WebhookUpdate,
  AnalysisTask,
  AnalysisTaskCreate,
  AnalysisTaskUpdate,
  TaskExecution,
  DashboardStats,
  ExecutionStats,
  PaginatedResponse
} from '@/types/api'

// AI模型配置API
export const aiModelApi = {
  // 获取AI模型列表
  getList(params?: { page?: number; size?: number; search?: string }): Promise<PaginatedResponse<AIModel>> {
    const apiParams = {
      skip: params?.page ? (params.page - 1) * (params.size || 20) : 0,
      limit: params?.size || 20,
      search: params?.search
    }
    return request.get('/api/v1/ai-models', apiParams)
  },
  
  // 获取AI模型详情
  getById(id: number): Promise<AIModel> {
    return request.get(`/api/v1/ai-models/${id}`)
  },
  
  // 创建AI模型
  create(data: AIModelCreate): Promise<AIModel> {
    return request.post('/api/v1/ai-models', data)
  },
  
  // 更新AI模型
  update(id: number, data: Partial<AIModelCreate>): Promise<AIModel> {
    return request.put(`/api/v1/ai-models/${id}`, data)
  },
  
  // 删除AI模型
  delete(id: number): Promise<void> {
    return request.delete(`/api/v1/ai-models/${id}`)
  },
  
  // 测试AI模型连接
  testConnection(data: { api_endpoint: string; api_key: string; model_type: string }): Promise<{ success: boolean; message: string }> {
    return request.post('/api/v1/ai-models/test-connection', data)
  }
}

// 模型配置API别名
export const modelConfigApi = aiModelApi

// 存储凭证API
export const storageApi = {
  // 获取存储凭证列表
  getList(params?: { page?: number; size?: number; search?: string }): Promise<PaginatedResponse<StorageCredential>> {
    const apiParams = {
      skip: params?.page ? (params.page - 1) * (params.size || 20) : 0,
      limit: params?.size || 20,
      search: params?.search
    }
    return request.get('/api/v1/storage-credentials', apiParams)
  },
  
  // 获取存储凭证详情
  getById(id: number): Promise<StorageCredential> {
    return request.get(`/api/v1/storage-credentials/${id}`)
  },
  
  // 创建存储凭证
  create(data: StorageCredentialCreate): Promise<StorageCredential> {
    return request.post('/api/v1/storage-credentials', data)
  },
  
  // 更新存储凭证
  update(id: number, data: Partial<StorageCredentialCreate>): Promise<StorageCredential> {
    return request.put(`/api/v1/storage-credentials/${id}`, data)
  },
  
  // 删除存储凭证
  delete(id: number): Promise<void> {
    return request.delete(`/api/v1/storage-credentials/${id}`)
  },
  
  // 测试存储连接
  testConnection(data: { server_address: string; protocol_type: string; username: string; password: string }): Promise<{ success: boolean; message: string }> {
    return request.post('/api/v1/storage-credentials/test-connection', data)
  },
  
  // 验证存储文件访问
  validateFileAccess(credentialId: number, filePath: string): Promise<{ success: boolean; message: string; fileInfo?: any }> {
    return request.post('/api/v1/storage-credentials/validate-file-access', {
      credential_id: credentialId,
      file_path: filePath
    })
  }
}

// 存储配置API别名
export const storageConfigApi = storageApi

// Webhook API
export const webhookApi = {
  // 获取Webhook列表
  getList(params?: { page?: number; size?: number; search?: string }): Promise<PaginatedResponse<Webhook>> {
    const apiParams = {
      skip: params?.page ? (params.page - 1) * (params.size || 20) : 0,
      limit: params?.size || 20,
      search: params?.search
    }
    return request.get('/api/v1/webhooks', apiParams)
  },
  
  // 获取Webhook详情
  getById(id: number): Promise<Webhook> {
    return request.get(`/api/v1/webhooks/${id}`)
  },
  
  // 创建Webhook
  create(data: WebhookCreate): Promise<Webhook> {
    return request.post('/api/v1/webhooks', data)
  },
  
  // 创建简化版Webhook
  createSimple(data: { name: string; description?: string; is_active?: boolean }): Promise<Webhook> {
    return request.post('/api/v1/webhooks/simple', data)
  },
  
  // 更新Webhook
  update(id: number, data: Partial<WebhookCreate>): Promise<Webhook> {
    return request.put(`/api/v1/webhooks/${id}`, data)
  },
  
  // 删除Webhook
  delete(id: number): Promise<void> {
    return request.delete(`/api/v1/webhooks/${id}`)
  },
  
  // 获取Webhook请求日志
  getLogs(webhookId: number, params?: { page?: number; size?: number; start_date?: string; end_date?: string }): Promise<PaginatedResponse<any>> {
    return request.get(`/api/v1/webhooks/${webhookId}/logs`, params)
  },
  
  // 获取Webhook最新日志记录（用于任务创建页面的数据预览）
  getLatestLog(webhookId: number): Promise<{ field_value: string | null; record_id: string | null; project_key?: string | null; work_item_type_key?: string | null; log_id?: number; created_at?: string; message?: string }> {
    return request.get(`/api/v1/webhooks/${webhookId}/latest-log`)
  },
  
  // 获取所有Webhook日志
  getAllLogs(params?: { page?: number; size?: number; webhook_id?: number }): Promise<PaginatedResponse<any>> {
    // 转换前端参数到后端参数格式，只传递后端支持的参数
    const apiParams = {
      skip: params?.page ? (params.page - 1) * (params.size || 20) : 0,
      limit: params?.size || 20,
      webhook_id: params?.webhook_id || undefined
    }
    return request.get('/api/v1/webhook-logs', apiParams)
  },
  
  // 重试Webhook
  retry(id: number): Promise<void> {
    return request.post(`/api/v1/webhooks/logs/${id}/retry`)
  },
  
  // 清除Webhook日志
  clearLogs(webhookId: number): Promise<void> {
    return request.delete(`/api/v1/webhooks/${webhookId}/logs`)
  },
  
  // 测试Webhook
  test(id: number): Promise<{ success: boolean; message: string }> {
    return request.post(`/api/v1/webhooks/${id}/test`)
  },
  
  // 测试Webhook URL
  testUrl(data: { url: string; method: string; headers: Record<string, string>; timeout?: number }): Promise<{ success: boolean; message: string }> {
    return request.post('/api/v1/webhooks/test-url', data)
  },
  
  // 测试Webhook连接
  testConnection(id: number): Promise<{ success: boolean; message: string }> {
    return request.post(`/api/v1/webhooks/${id}/test-connection`)
  },
  
  // 获取Webhook统计信息
  getStats(params: { webhook_id: number; days?: number }): Promise<{ total: number; success: number; failed: number; pending: number }> {
    return request.get('/api/v1/webhooks/stats', params)
  },

  // 获取Webhook日志统计信息
  getLogStats(params?: { webhook_id?: number }): Promise<{ total: number; success: number; failed: number; pending: number; success_rate: number }> {
    return request.get('/api/v1/webhook-logs/stats/summary', params)
  },

  // 检查Webhook关联状态
  checkAssociationStatus(webhookId: number): Promise<{
    webhook_id: number;
    webhook_name: string;
    is_active: boolean;
    associated_task_count: number;
    associated_tasks: Array<{
      id: number;
      name: string;
      is_active: boolean;
      created_at: string;
    }>;
    can_be_associated: boolean;
    restriction_reason: string | null;
  }> {
    return request.get(`/api/v1/webhooks/${webhookId}/association-status`)
  }
}

// 分析任务API
export const taskApi = {
  // 获取任务列表
  getList(params?: { page?: number; size?: number; search?: string; status?: string; is_active?: boolean }): Promise<PaginatedResponse<AnalysisTask>> {
    // 转换前端参数到后端参数
    const apiParams = {
      skip: params?.page ? (params.page - 1) * (params.size || 20) : 0,
      limit: params?.size || 20,
      search: params?.search,
      status: params?.status,
      is_active: params?.is_active
    }
    return request.get('/api/v1/analysis-tasks', apiParams)
  },
  
  // 获取任务详情
  getById(id: number): Promise<AnalysisTask> {
    return request.get(`/api/v1/analysis-tasks/${id}`)
  },
  
  // 创建任务
  create(data: AnalysisTaskCreate): Promise<AnalysisTask> {
    return request.post('/api/v1/analysis-tasks', data)
  },
  
  // 更新任务
  update(id: number, data: Partial<AnalysisTaskCreate>): Promise<AnalysisTask> {
    return request.put(`/api/v1/analysis-tasks/${id}`, data)
  },
  
  // 删除任务
  delete(id: number): Promise<void> {
    return request.delete(`/api/v1/analysis-tasks/${id}`)
  },
  
  // 启用/禁用任务
  toggleStatus(id: number, isActive: boolean): Promise<AnalysisTask> {
    return request.patch(`/api/v1/analysis-tasks/${id}/status`, { is_active: isActive })
  },
  
  // 手动执行任务
  execute(id: number, payload?: any): Promise<{ execution_id: string }> {
    return request.post(`/api/v1/analysis-tasks/${id}/trigger`, { payload_data: payload || {} })
  },
  
  // 测试JSONPath配置
  testJsonPath(data: { sample_data: any; extraction_config: any }): Promise<{ extracted_data: any }> {
    return request.post('/tasks/test-jsonpath', data)
  },
  
  // 获取任务统计信息
  getStats(params: { task_id: string; start_date?: string; end_date?: string }): Promise<any> {
    return request.get(`/api/v1/analysis-tasks/${params.task_id}/stats`, { start_date: params.start_date, end_date: params.end_date })
  },
  
  // 获取任务执行记录
  getExecutions(params: { task_id: string; page?: number; size?: number }): Promise<PaginatedResponse<TaskExecution>> {
    const { task_id, ...queryParams } = params
    return request.get(`/api/v1/analysis-tasks/${task_id}/executions`, queryParams)
  },
  
  // 测试飞书写入配置
  testFeishuConfig(config: any): Promise<{ success: boolean; message: string }> {
    return request.post('/api/v1/analysis-tasks/test-feishu-config', config)
  },
  
  // AI分析测试
  testAiAnalysis(data: {
    ai_model_id: number
    prompt: string
    temperature: number
    max_tokens: number
    storage_credential_id?: number
    webhook_data: {
      field_value: string | null
      record_id: string | null
    }
    rich_text_images?: any[]
    content_type?: string
  }): Promise<{
    success: boolean
    content: string
    model_name: string
    token_usage: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
    response_time: number
  }> {
    return request.post('/api/v1/analysis-tasks/test-ai-analysis', data)
  },
  
  // 查询富文本字段详情
  queryRichTextField(data: {
    webhook_data: any
    plugin_id: string
    plugin_secret: string
    user_key: string
  }): Promise<{
    success: boolean
    message?: string
    field_key?: string
    doc?: string
    doc_text?: string
    doc_html?: string
    is_empty?: boolean
    work_item_id?: string
    work_item_name?: string
    webhook_info?: any
    timestamp?: string
    error?: string
  }> {
    return request.post('/api/v1/analysis-tasks/query-rich-text-field', data)
  },
  
  // 测试飞书写入功能
  testFeishuWrite(data: {
    field_key: string
    analysis_result: string
    webhook_data: any
    project_key: string
    work_item_type_key: string
    work_item_id: string
    plugin_token?: string
    user_key: string
  }): Promise<{
    success: boolean
    message?: string
    project_key?: string
    work_item_id?: string
    work_item_type_key?: string
    field_key?: string
    write_response?: any
    error?: string
    details?: string
  }> {
    return request.post('/api/v1/analysis-tasks/test-feishu-write', data)
  },

  // 测试多字段查询
  testMultiFieldQuery(data: {
    multi_field_config: {
      fields: Array<{
        field_key: string
        field_name: string
        placeholder: string
        required: boolean
      }>
    }
    webhook_data: {
      project_key: string
      work_item_type_key: string
      id: string
    }
    plugin_id?: string
    plugin_secret?: string
    user_key?: string
  }): Promise<{
    success: boolean
    message?: string
    project_key?: string
    work_item_id?: string
    work_item_type_key?: string
    field_data?: any
    field_count?: number
    failed_fields?: string[]
    query_details?: Array<{
      field_key: string
      field_name: string
      success: boolean
      value?: any
      value_type?: string
      has_value?: boolean
      error?: string
    }>
    timestamp?: string
    execution_time_ms?: number
    error?: string
  }> {
    return request.post('/api/v1/analysis-tasks/test-multi-field-query', data)
  }
}

// 任务执行记录API
export const executionApi = {
  // 获取执行记录列表
  getList(params?: { 
    page?: number; 
    size?: number; 
    task_id?: number; 
    status?: string; 
    start_date?: string; 
    end_date?: string 
  }): Promise<PaginatedResponse<TaskExecution>> {
    // 转换前端参数到后端参数
    const apiParams = {
      skip: params?.page ? (params.page - 1) * (params.size || 20) : 0,
      limit: params?.size || 20,
      task_id: params?.task_id,
      status: params?.status,
      start_date: params?.start_date,
      end_date: params?.end_date
    }
    return request.get('/api/v1/executions', apiParams)
  },
  
  // 获取执行记录详情
  getById(id: number | string): Promise<TaskExecution> {
    return request.get(`/api/v1/executions/${id}`)
  },
  
  // 重新执行任务
  retry(id: number | string): Promise<{
    success: boolean;
    message: string;
    original_execution_id: string;
    new_execution_id: string;
    retry_result?: any;
    error?: string;
  }> {
    return request.post(`/api/v1/executions/${id}/retry`)
  },
  
  // 取消执行
  cancel(id: number): Promise<void> {
    return request.post(`/api/v1/executions/${id}/cancel`)
  },
  
  // 导出执行记录
  export(params?: any): Promise<Blob> {
    return request.get('/api/v1/executions/export', params, { responseType: 'blob' })
  },
  
  // 下载执行结果
  downloadResult(id: number): Promise<Blob> {
    return request.get(`/api/v1/executions/${id}/result`, {}, { responseType: 'blob' })
  },
  
  // 删除执行记录
  delete(id: number): Promise<void> {
    return request.delete(`/api/v1/executions/${id}`)
  }
}

// 监控统计API
export const monitoringApi = {
  // 获取仪表板统计数据
  getDashboardStats(): Promise<DashboardStats> {
    return request.get('/api/v1/monitoring/overview-stats')
  },
  
  // 获取执行统计数据
  getExecutionStats(params?: { 
    start_date?: string; 
    end_date?: string; 
    task_id?: number 
  }): Promise<ExecutionStats[]> {
    return request.get('/api/v1/monitoring/execution-stats', params)
  },
  
  // 获取Token使用统计
  getTokenStats(params?: { 
    start_date?: string; 
    end_date?: string; 
    model_id?: number 
  }): Promise<any[]> {
    return request.get('/api/v1/monitoring/token-stats', params)
  },
  
  // 获取错误统计
  getErrorStats(params?: { 
    start_date?: string; 
    end_date?: string 
  }): Promise<any[]> {
    return request.get('/api/v1/monitoring/error-stats', params)
  },
  
  // 获取概览统计
  getOverviewStats(params?: any): Promise<any> {
    return request.get('/api/v1/monitoring/overview-stats', params)
  },
  
  // 获取执行趋势
  getExecutionTrend(params?: any): Promise<any> {
    return request.get('/api/v1/monitoring/execution-trend', params)
  },
  
  // 获取成功率趋势
  getSuccessRateTrend(params?: any): Promise<any> {
    return request.get('/api/v1/monitoring/success-rate-trend', params)
  },
  
  // 获取任务类型分布
  getTaskTypeDistribution(params?: any): Promise<any> {
    return request.get('/api/v1/monitoring/task-type-distribution', params)
  },
  
  // 获取Token趋势
  getTokenTrend(params?: any): Promise<any> {
    return request.get('/api/v1/monitoring/token-trend', params)
  },
  
  // 获取执行时长分布
  getDurationDistribution(params?: any): Promise<any> {
    return request.get('/api/v1/monitoring/duration-distribution', params)
  },
  
  // 获取文件类型分布
  getFileTypeDistribution(params?: any): Promise<any> {
    return request.get('/api/v1/monitoring/file-type-distribution', params)
  },
  
  // 获取任务统计
  getTaskStats(params?: any): Promise<any> {
    return request.get('/api/v1/monitoring/task-stats', params)
  },
  
  // 导出报告
  exportReport(params?: any): Promise<Blob> {
    return request.get('/api/v1/monitoring/export-report', params, { responseType: 'blob' })
  },
  
  // 导出任务统计
  exportTaskStats(params?: any): Promise<Blob> {
    return request.get('/api/v1/monitoring/export-task-stats', params, { responseType: 'blob' })
  }
}

// 分析统计API别名
export const analyticsApi = monitoringApi

// 系统配置API
export const systemApi = {
  // 获取系统信息
  getSystemInfo(): Promise<any> {
    return request.get('/api/v1/system-configs')
  },
  
  // 获取健康检查
  getHealthCheck(): Promise<{ status: string; checks: any }> {
    return request.get('/health/')
  }
}