<template>
  <div class="analytics">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1 class="page-title">统计分析</h1>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          @change="loadData"
          class="date-picker"
        />
        <el-button :icon="Refresh" @click="refreshData" :loading="loading">
          刷新
        </el-button>
        <el-button :icon="Download" @click="exportReport">
          导出报告
        </el-button>
      </div>
    </div>

    <!-- 概览统计 -->
    <el-row :gutter="20" class="overview-stats">
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-item">
            <div class="stat-number">{{ stats.total_tasks || 0 }}</div>
            <div class="stat-label">总任务数</div>
            <div class="stat-change" :class="getChangeClass(stats.tasks_change)">
              <el-icon><TrendCharts /></el-icon>
              {{ formatChange(stats.tasks_change) }}
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-item">
            <div class="stat-number">{{ stats.total_executions || 0 }}</div>
            <div class="stat-label">总执行次数</div>
            <div class="stat-change" :class="getChangeClass(stats.executions_change || 0)">
              <el-icon><TrendCharts /></el-icon>
              {{ formatChange(stats.executions_change || 0) }}
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-item success">
            <div class="stat-number">{{ formatSuccessRate(stats.success_rate) }}</div>
            <div class="stat-label">成功率</div>
            <div class="stat-change" :class="getChangeClass(stats.success_rate_change || 0)">
              <el-icon><TrendCharts /></el-icon>
              {{ formatChange(stats.success_rate_change || 0) }}%
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-item warning">
            <div class="stat-number">{{ formatDuration(stats.avg_duration || 0) }}</div>
            <div class="stat-label">平均耗时</div>
            <div class="stat-change" :class="getChangeClass(stats.duration_change || 0)">
              <el-icon><TrendCharts /></el-icon>
              {{ formatChange(stats.duration_change || 0) }}s
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-item info">
            <div class="stat-number">{{ formatNumber(stats.total_tokens || 0) }}</div>
            <div class="stat-label">Token消耗</div>
            <div class="stat-change" :class="getChangeClass(stats.tokens_change || 0)">
              <el-icon><TrendCharts /></el-icon>
              {{ formatChange(stats.tokens_change || 0) }}
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-item">
            <div class="stat-number">{{ stats.total_files || 0 }}</div>
            <div class="stat-label">处理文件数</div>
            <div class="stat-change" :class="getChangeClass(stats.files_change || 0)">
              <el-icon><TrendCharts /></el-icon>
              {{ formatChange(stats.files_change || 0) }}
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-item">
            <div class="stat-number">{{ stats.active_tasks || 0 }}</div>
            <div class="stat-label">活跃任务</div>
            <div class="stat-change" :class="getChangeClass(stats.active_tasks_change || 0)">
              <el-icon><TrendCharts /></el-icon>
              {{ formatChange(stats.active_tasks_change || 0) }}
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="6">
        <el-card class="stat-card" shadow="never">
          <div class="stat-item">
            <div class="stat-number">{{ formatFileSize(stats.avg_file_size || 0) }}</div>
            <div class="stat-label">平均文件大小</div>
            <div class="stat-change" :class="getChangeClass(stats.file_size_change || 0)">
              <el-icon><TrendCharts /></el-icon>
              {{ formatChange(stats.file_size_change || 0) }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-section">
      <!-- 执行趋势图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">执行趋势</span>
              <el-radio-group v-model="executionTrendPeriod" size="small" @change="loadExecutionTrend">
                <el-radio-button label="hour">小时</el-radio-button>
                <el-radio-button label="day">天</el-radio-button>
                <el-radio-button label="week">周</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="executionTrendChart" class="chart-container" v-loading="chartsLoading.executionTrend"></div>
        </el-card>
      </el-col>
      
      <!-- 成功率趋势图 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">成功率趋势</span>
              <el-radio-group v-model="successRatePeriod" size="small" @change="loadSuccessRateTrend">
                <el-radio-button label="hour">小时</el-radio-button>
                <el-radio-button label="day">天</el-radio-button>
                <el-radio-button label="week">周</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="successRateChart" class="chart-container" v-loading="chartsLoading.successRate"></div>
        </el-card>
      </el-col>
      
      <!-- 任务类型分布 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <span class="card-title">任务类型分布</span>
          </template>
          <div ref="taskTypeChart" class="chart-container" v-loading="chartsLoading.taskType"></div>
        </el-card>
      </el-col>
      
      <!-- Token消耗趋势 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">Token消耗趋势</span>
              <el-radio-group v-model="tokenTrendPeriod" size="small" @change="loadTokenTrend">
                <el-radio-button label="hour">小时</el-radio-button>
                <el-radio-button label="day">天</el-radio-button>
                <el-radio-button label="week">周</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="tokenTrendChart" class="chart-container" v-loading="chartsLoading.tokenTrend"></div>
        </el-card>
      </el-col>
      
      <!-- 执行时长分布 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <span class="card-title">执行时长分布</span>
          </template>
          <div ref="durationChart" class="chart-container" v-loading="chartsLoading.duration"></div>
        </el-card>
      </el-col>
      
      <!-- 文件类型分布 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="never">
          <template #header>
            <span class="card-title">文件类型分布</span>
          </template>
          <div ref="fileTypeChart" class="chart-container" v-loading="chartsLoading.fileType"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 任务统计详情 -->
    <el-card class="detail-table-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">任务统计详情</span>
          <div class="header-actions">
            <el-button size="small" @click="exportTaskStats">
              导出数据
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        :data="taskStatsData"
        v-loading="taskStatsLoading"
        stripe
        @sort-change="handleTaskStatsSort"
      >
        <el-table-column prop="task_name" label="任务名称" min-width="150">
          <template #default="{ row }">
            <el-link
              type="primary"
              @click="viewTaskDetail(row.task_id)"
              :underline="false"
            >
              {{ row.task_name }}
            </el-link>
          </template>
        </el-table-column>
        
        <el-table-column prop="task_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getTaskTypeLabel(row.task_type) }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="total_executions" label="执行次数" width="100" sortable="custom" />
        <el-table-column prop="success_executions" label="成功次数" width="100" sortable="custom" />
        <el-table-column prop="failed_executions" label="失败次数" width="100" sortable="custom" />
        
        <el-table-column prop="success_rate" label="成功率" width="100" sortable="custom">
          <template #default="{ row }">
            <el-progress
              :percentage="row.success_rate"
              :color="getSuccessRateColor(row.success_rate)"
              :show-text="false"
              :stroke-width="8"
            />
            <span class="success-rate-text">{{ row.success_rate }}%</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="avg_duration" label="平均耗时" width="100" sortable="custom">
          <template #default="{ row }">
            {{ formatDuration(row.avg_duration) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="total_tokens" label="Token消耗" width="120" sortable="custom">
          <template #default="{ row }">
            {{ formatNumber(row.total_tokens) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="total_files" label="处理文件" width="100" sortable="custom" />
        
        <el-table-column prop="last_execution" label="最后执行" width="180" sortable="custom">
          <template #default="{ row }">
            {{ formatTime(row.last_execution) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="viewTaskDetail(row.task_id)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="taskStatsPagination.page"
          v-model:page-size="taskStatsPagination.size"
          :page-sizes="[10, 20, 50]"
          :total="taskStatsPagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleTaskStatsPageSizeChange"
          @current-change="handleTaskStatsPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Download,
  TrendCharts
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { analyticsApi } from '@/api'
import type { ECharts } from 'echarts'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const taskStatsLoading = ref(false)
const dateRange = ref<[string, string] | null>(null)

const chartsLoading = reactive({
  executionTrend: false,
  successRate: false,
  taskType: false,
  tokenTrend: false,
  duration: false,
  fileType: false
})

const executionTrendPeriod = ref('day')
const successRatePeriod = ref('day')
const tokenTrendPeriod = ref('day')

const stats = reactive({
  total_tasks: 0,
  total_executions: 0,
  success_rate: 0,
  avg_duration: 0,
  total_tokens: 0,
  total_files: 0,
  active_tasks: 0,
  avg_file_size: 0,
  tasks_change: 0,
  executions_change: 0,
  success_rate_change: 0,
  duration_change: 0,
  tokens_change: 0,
  files_change: 0,
  active_tasks_change: 0,
  file_size_change: 0
})

const taskStatsData = ref<any[]>([])
const taskStatsPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const taskStatsSortConfig = reactive({
  prop: 'total_executions',
  order: 'descending'
})

// 图表实例
const executionTrendChart = ref<HTMLElement>()
const successRateChart = ref<HTMLElement>()
const taskTypeChart = ref<HTMLElement>()
const tokenTrendChart = ref<HTMLElement>()
const durationChart = ref<HTMLElement>()
const fileTypeChart = ref<HTMLElement>()

let executionTrendChartInstance: ECharts | null = null
let successRateChartInstance: ECharts | null = null
let taskTypeChartInstance: ECharts | null = null
let tokenTrendChartInstance: ECharts | null = null
let durationChartInstance: ECharts | null = null
let fileTypeChartInstance: ECharts | null = null

// 方法
const refreshData = () => {
  loadData()
}

const loadData = async () => {
  await Promise.all([
    loadOverviewStats(),
    loadExecutionTrend(),
    loadSuccessRateTrend(),
    loadTaskTypeDistribution(),
    loadTokenTrend(),
    loadDurationDistribution(),
    loadFileTypeDistribution(),
    loadTaskStats()
  ])
}

const loadOverviewStats = async () => {
  loading.value = true
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    }
    const response = await analyticsApi.getOverviewStats(params)
    Object.assign(stats, response)
  } catch (error) {
    console.error('获取概览统计失败:', error)
    ElMessage.error('获取概览统计失败')
  } finally {
    loading.value = false
  }
}

const loadExecutionTrend = async () => {
  chartsLoading.executionTrend = true
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      period: executionTrendPeriod.value
    }
    const response = await analyticsApi.getExecutionTrend(params)
    renderExecutionTrendChart(response)
  } catch (error) {
    console.error('获取执行趋势失败:', error)
  } finally {
    chartsLoading.executionTrend = false
  }
}

const loadSuccessRateTrend = async () => {
  chartsLoading.successRate = true
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      period: successRatePeriod.value
    }
    const response = await analyticsApi.getSuccessRateTrend(params)
    renderSuccessRateChart(response)
  } catch (error) {
    console.error('获取成功率趋势失败:', error)
  } finally {
    chartsLoading.successRate = false
  }
}

const loadTaskTypeDistribution = async () => {
  chartsLoading.taskType = true
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    }
    const response = await analyticsApi.getTaskTypeDistribution(params)
    renderTaskTypeChart(response)
  } catch (error) {
    console.error('获取任务类型分布失败:', error)
  } finally {
    chartsLoading.taskType = false
  }
}

const loadTokenTrend = async () => {
  chartsLoading.tokenTrend = true
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      period: tokenTrendPeriod.value
    }
    const response = await analyticsApi.getTokenTrend(params)
    renderTokenTrendChart(response)
  } catch (error) {
    console.error('获取Token趋势失败:', error)
  } finally {
    chartsLoading.tokenTrend = false
  }
}

const loadDurationDistribution = async () => {
  chartsLoading.duration = true
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    }
    const response = await analyticsApi.getDurationDistribution(params)
    renderDurationChart(response)
  } catch (error) {
    console.error('获取时长分布失败:', error)
  } finally {
    chartsLoading.duration = false
  }
}

const loadFileTypeDistribution = async () => {
  chartsLoading.fileType = true
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    }
    const response = await analyticsApi.getFileTypeDistribution(params)
    renderFileTypeChart(response)
  } catch (error) {
    console.error('获取文件类型分布失败:', error)
  } finally {
    chartsLoading.fileType = false
  }
}

const loadTaskStats = async () => {
  taskStatsLoading.value = true
  try {
    const params = {
      page: taskStatsPagination.page,
      size: taskStatsPagination.size,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      sort_by: taskStatsSortConfig.prop,
      sort_order: taskStatsSortConfig.order === 'ascending' ? 'asc' : 'desc'
    }
    const response = await analyticsApi.getTaskStats(params)
    taskStatsData.value = response.items
    taskStatsPagination.total = response.total
  } catch (error) {
    console.error('获取任务统计失败:', error)
  } finally {
    taskStatsLoading.value = false
  }
}

// 图表渲染方法
const renderExecutionTrendChart = (data: any) => {
  if (!executionTrendChartInstance) {
    executionTrendChartInstance = echarts.init(executionTrendChart.value!)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['总执行', '成功', '失败']
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.time)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总执行',
        type: 'line',
        data: data.map((item: any) => item.total),
        smooth: true
      },
      {
        name: '成功',
        type: 'line',
        data: data.map((item: any) => item.success),
        smooth: true,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '失败',
        type: 'line',
        data: data.map((item: any) => item.failed),
        smooth: true,
        itemStyle: { color: '#F56C6C' }
      }
    ]
  }
  
  executionTrendChartInstance.setOption(option)
}

const renderSuccessRateChart = (data: any) => {
  if (!successRateChartInstance) {
    successRateChartInstance = echarts.init(successRateChart.value!)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: '{b}: {c}%'
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.time)
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '成功率',
        type: 'line',
        data: data.map((item: any) => item.success_rate),
        smooth: true,
        areaStyle: {
          opacity: 0.3
        },
        itemStyle: { color: '#409EFF' }
      }
    ]
  }
  
  successRateChartInstance.setOption(option)
}

const renderTaskTypeChart = (data: any) => {
  if (!taskTypeChartInstance) {
    taskTypeChartInstance = echarts.init(taskTypeChart.value!)
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '任务类型',
        type: 'pie',
        radius: '50%',
        data: data.map((item: any) => ({
          value: item.count,
          name: getTaskTypeLabel(item.task_type)
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  taskTypeChartInstance.setOption(option)
}

const renderTokenTrendChart = (data: any) => {
  if (!tokenTrendChartInstance) {
    tokenTrendChartInstance = echarts.init(tokenTrendChart.value!)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        return `${params[0].name}: ${formatNumber(params[0].value)}`
      }
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.time)
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: function(value: number) {
          return formatNumber(value)
        }
      }
    },
    series: [
      {
        name: 'Token消耗',
        type: 'bar',
        data: data.map((item: any) => item.tokens),
        itemStyle: { color: '#E6A23C' }
      }
    ]
  }
  
  tokenTrendChartInstance.setOption(option)
}

const renderDurationChart = (data: any) => {
  if (!durationChartInstance) {
    durationChartInstance = echarts.init(durationChart.value!)
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}'
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.range)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '执行次数',
        type: 'bar',
        data: data.map((item: any) => item.count),
        itemStyle: { color: '#909399' }
      }
    ]
  }
  
  durationChartInstance.setOption(option)
}

const renderFileTypeChart = (data: any) => {
  if (!fileTypeChartInstance) {
    fileTypeChartInstance = echarts.init(fileTypeChart.value!)
  }
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [
      {
        name: '文件类型',
        type: 'pie',
        radius: ['40%', '70%'],
        data: data.map((item: any) => ({
          value: item.count,
          name: item.file_type
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  fileTypeChartInstance.setOption(option)
}

// 表格处理方法
const handleTaskStatsSort = ({ prop, order }: { prop: string; order: string }) => {
  taskStatsSortConfig.prop = prop
  taskStatsSortConfig.order = order
  loadTaskStats()
}

const handleTaskStatsPageSizeChange = (size: number) => {
  taskStatsPagination.size = size
  taskStatsPagination.page = 1
  loadTaskStats()
}

const handleTaskStatsPageChange = (page: number) => {
  taskStatsPagination.page = page
  loadTaskStats()
}

const viewTaskDetail = (taskId: string) => {
  router.push({ name: 'TaskDetail', params: { id: taskId } })
}

const exportReport = async () => {
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    }
    
    const blob = await analyticsApi.exportReport(params)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `analytics_report_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const exportTaskStats = async () => {
  try {
    const params = {
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1]
    }
    
    const blob = await analyticsApi.exportTaskStats(params)
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `task_stats_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 工具方法
const getChangeClass = (change: number) => {
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

const formatChange = (change: number) => {
  if (change === null || change === undefined || isNaN(change)) return '0'
  if (change > 0) return `+${change}`
  if (change === 0) return '0'
  return change.toString()
}

const getSuccessRateColor = (rate: number) => {
  if (rate >= 90) return '#67C23A'
  if (rate >= 70) return '#E6A23C'
  return '#F56C6C'
}

const getTaskTypeLabel = (taskType: string) => {
  const labelMap: Record<string, string> = {
    'document_analysis': '文档分析',
    'data_extraction': '数据提取',
    'content_summary': '内容总结',
    'sentiment_analysis': '情感分析',
    'keyword_extraction': '关键词提取',
    'custom_analysis': '自定义分析'
  }
  return labelMap[taskType] || taskType
}

const formatTime = (time: string) => {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN')
  } catch (error) {
    return '-'
  }
}

const formatDuration = (seconds: number) => {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '0秒'
  if (seconds === 0) return '0秒'
  
  const roundedSeconds = Math.round(seconds)
  
  if (roundedSeconds < 60) {
    return `${roundedSeconds}秒`
  } else if (roundedSeconds < 3600) {
    const minutes = Math.floor(roundedSeconds / 60)
    const remainingSeconds = roundedSeconds % 60
    return remainingSeconds > 0 ? `${minutes}分${remainingSeconds}秒` : `${minutes}分钟`
  } else {
    const hours = Math.floor(roundedSeconds / 3600)
    const minutes = Math.floor((roundedSeconds % 3600) / 60)
    return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`
  }
}

const formatNumber = (num: number) => {
  if (num === null || num === undefined || isNaN(num)) return '0'
  if (num === 0) return '0'
  
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`
  } else if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`
  }
  return Math.round(num).toString()
}

const formatFileSize = (bytes: number) => {
  if (!bytes || bytes === 0 || isNaN(bytes)) return '-'
  
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const formatSuccessRate = (rate?: number) => {
  if (rate === undefined || rate === null || isNaN(rate)) return '0%'
  // 后端返回0-1之间的小数，需要转换为百分比
  const percentage = rate * 100
  return `${percentage.toFixed(1)}%`
}

// 初始化图表
const initCharts = async () => {
  await nextTick()
  
  // 监听窗口大小变化
  const handleResize = () => {
    executionTrendChartInstance?.resize()
    successRateChartInstance?.resize()
    taskTypeChartInstance?.resize()
    tokenTrendChartInstance?.resize()
    durationChartInstance?.resize()
    fileTypeChartInstance?.resize()
  }
  
  window.addEventListener('resize', handleResize)
  
  // 组件卸载时移除监听器
  // onUnmounted(() => {
  //   window.removeEventListener('resize', handleResize)
  // })
}

// 生命周期
onMounted(async () => {
  await initCharts()
  loadData()
})
</script>

<style scoped>
.analytics {
  padding: 0;
}

.date-picker {
  margin-right: 10px;
}

.overview-stats {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 20px;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.stat-item.success .stat-number {
  color: var(--el-color-success);
}

.stat-item.warning .stat-number {
  color: var(--el-color-warning);
}

.stat-item.info .stat-number {
  color: var(--el-color-info);
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 5px;
}

.stat-change {
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.stat-change.positive {
  color: var(--el-color-success);
}

.stat-change.negative {
  color: var(--el-color-danger);
}

.stat-change.neutral {
  color: var(--el-text-color-secondary);
}

.charts-section {
  margin-bottom: 20px;
}

.chart-card,
.detail-table-card {
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

.chart-container {
  height: 300px;
  width: 100%;
}

.success-rate-text {
  margin-left: 8px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .stat-number {
    font-size: 24px;
  }
  
  .stat-item {
    padding: 15px;
  }
  
  .chart-container {
    height: 250px;
  }
  
  .date-picker {
    width: 100%;
    margin-bottom: 10px;
  }
  
  .header-actions {
    flex-direction: column;
    gap: 10px;
  }
}
</style>