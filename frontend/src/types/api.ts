// 通用API响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 分页响应类型
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// AI模型配置类型
export interface AIModel {
  id: number
  name: string
  model_type: 'OpenAI-Compatible' | 'Gemini' | 'Claude' | 'Other'
  model_name: string
  api_endpoint: string
  api_key_encrypted: string
  default_params: Record<string, any>
  use_proxy: boolean
  proxy_url?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AIModelCreate {
  name: string
  model_type: string
  model_name: string
  api_endpoint: string
  api_key: string
  default_params?: Record<string, any>
  use_proxy?: boolean
  proxy_url?: string
  is_active?: boolean
}

export interface AIModelUpdate extends Partial<AIModelCreate> {
  id: number
}

// 存储凭证类型
export interface StorageCredential {
  id: number
  name: string
  server_address: string
  protocol_type: 'SMB' | 'NFS' | 'FTP' | 'WebDAV' | 'HTTP'
  username: string
  password_encrypted: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface StorageCredentialCreate {
  name: string
  server_address: string
  protocol_type: string
  username: string
  password: string
  is_active?: boolean
}

export interface StorageCredentialUpdate extends Partial<StorageCredentialCreate> {
  id: number
}

// Webhook类型
export interface Webhook {
  id: number
  name: string
  webhook_id: string
  url: string
  method: string
  description?: string
  is_active: boolean
  headers?: Record<string, string>
  event_type?: string
  timeout?: number
  retry_count?: number
  last_triggered_at?: string
  auth_type?: string
  auth_config?: Record<string, any>
  status?: string
  created_at: string
  updated_at: string
}

export interface WebhookCreate {
  name: string
  url: string
  method: string
  description?: string
  is_active?: boolean
  headers: { key: string; value: string }[]
  event_type?: string
  timeout?: number
  retry_count?: number
}

export interface WebhookUpdate extends Partial<WebhookCreate> {
  id: number
}

// Webhook日志类型
export interface WebhookLog {
  id: number
  webhook_id: number
  webhook_name: string
  method: string
  status: string
  source_ip: string
  response_status: number
  response_time_ms: number
  created_at: string
  request_payload: Record<string, any>
  request_headers: Record<string, string>
  validation_errors: string[] | null
  is_valid: boolean
  user_agent: string
  retryLoading?: boolean
}

// 分析任务类型
export interface AnalysisTask {
  id: number
  name: string
  description?: string
  webhook_id: number
  ai_model_id: number
  storage_credential_id?: number
  data_extraction_config: Record<string, any>
  prompt_template: string
  analysis_prompt: string
  temperature?: number
  max_tokens?: number
  feishu_config: Record<string, any>
  feishu_write_config?: {
    field_id: string
    [key: string]: any  // 允许其他配置字段
  }
  field_mapping: Record<string, any>
  is_active: boolean
  is_scheduled?: boolean
  cron_expression?: string
  created_at: string
  updated_at: string
  webhook?: Webhook
  ai_model?: AIModel
  storage_credential?: StorageCredential
}

export interface AnalysisTaskCreate {
  name: string
  description?: string
  webhook_id: number
  ai_model_id: number
  storage_credential_id?: number
  data_extraction_config: Record<string, any>
  prompt_template: string
  analysis_prompt: string
  temperature?: number
  max_tokens?: number
  feishu_config: Record<string, any>
  feishu_write_config: {
    field_id: string
    [key: string]: any  // 允许其他配置字段
  }
  field_mapping: Record<string, any>
  is_active?: boolean
  is_scheduled?: boolean
  cron_expression?: string
}

export interface AnalysisTaskUpdate extends Partial<AnalysisTaskCreate> {
  id: number
}

// 任务执行记录类型
export interface TaskExecution {
  id: number
  task_id: number
  webhook_payload: Record<string, any>
  extracted_data?: Record<string, any>
  file_content?: string
  ai_response?: string
  execution_status: 'pending' | 'processing' | 'success' | 'failed'
  error_message?: string
  token_usage?: number
  execution_time_ms?: number
  started_at: string
  completed_at?: string
  task?: AnalysisTask
}

// 统计数据类型
export interface DashboardStats {
  total_tasks: number
  active_tasks: number
  total_executions: number
  success_rate: number
  avg_duration: number
  total_tokens: number
}

export interface ExecutionStats {
  date: string
  total_executions: number
  success_executions: number
  failed_executions: number
  avg_execution_time: number
  total_tokens: number
}

// 表单验证规则类型
export interface FormRule {
  required?: boolean
  message?: string
  trigger?: string | string[]
  min?: number
  max?: number
  pattern?: RegExp
  validator?: (rule: any, value: any, callback: any) => void
}

export type FormRules = Record<string, FormRule[]>