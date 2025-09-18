import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ApiResponse } from '@/types/api'

// 创建axios实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 300000, // 5分钟超时，支持AI分析等耗时操作
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 在发送请求之前做些什么
    console.log('发送请求:', config.method?.toUpperCase(), config.url)
    
    // 移除认证相关代码，系统无需登录
    
    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data
    
    console.log('响应数据:', response.status, response.config.url, res)
    
    // 如果返回的状态码不是2xx，说明接口有问题
    if (response.status < 200 || response.status >= 300) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    
    // 如果是标准的API响应格式
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code !== 200) {
        ElMessage.error(res.message || '操作失败')
        return Promise.reject(new Error(res.message || '操作失败'))
      }
      return res.data
    }
    
    // 直接返回数据
    return res
  },
  (error) => {
    console.error('响应错误:', error)
    
    let message = '网络错误'
    
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          message = data?.message || '请求参数错误'
          break
        case 401:
          message = '请求被拒绝'
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 422:
          message = data?.message || '数据验证失败'
          break
        case 500:
          message = '服务器内部错误'
          break
        case 502:
          message = '网关错误'
          break
        case 503:
          message = '服务不可用'
          break
        case 504:
          message = '网关超时'
          break
        default:
          message = data?.message || `连接错误${status}`
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时'
    } else if (error.message) {
      message = error.message
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// 封装常用的请求方法
export const request = {
  get<T = any>(url: string, params?: any, config?: any): Promise<T> {
    return service.get(url, { params, ...config })
  },
  
  post<T = any>(url: string, data?: any): Promise<T> {
    return service.post(url, data)
  },
  
  put<T = any>(url: string, data?: any): Promise<T> {
    return service.put(url, data)
  },
  
  delete<T = any>(url: string, params?: any): Promise<T> {
    return service.delete(url, { params })
  },
  
  patch<T = any>(url: string, data?: any): Promise<T> {
    return service.patch(url, data)
  }
}

// 文件上传请求
export const uploadRequest = (url: string, formData: FormData, onProgress?: (progress: number) => void) => {
  return service.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    }
  })
}

// 下载文件请求
export const downloadRequest = (url: string, params?: any, filename?: string) => {
  return service.get(url, {
    params,
    responseType: 'blob'
  }).then((response) => {
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  })
}

export default service