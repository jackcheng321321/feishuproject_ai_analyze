<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 顶部导航栏 -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <el-icon><Setting /></el-icon>
            <span class="title">AI综合分析管理平台</span>
          </div>
        </div>
      </el-header>

      <el-container>
        <!-- 侧边导航 -->
        <el-aside width="250px" class="app-aside">
          <el-menu
            :default-active="$route.path"
            class="sidebar-menu"
            router
            unique-opened
          >
            <el-menu-item index="/">
              <el-icon><House /></el-icon>
              <span>仪表板</span>
            </el-menu-item>
            
            <el-sub-menu index="/config">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>配置管理</span>
              </template>
              <el-menu-item index="/config/models">
                <el-icon><Cpu /></el-icon>
                <span>AI模型配置</span>
              </el-menu-item>
              <el-menu-item index="/config/storage">
                <el-icon><FolderOpened /></el-icon>
                <span>存储凭证配置</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="/webhook">
              <template #title>
                <el-icon><Connection /></el-icon>
                <span>Webhook管理</span>
              </template>
              <el-menu-item index="/webhook/list">
                <el-icon><List /></el-icon>
                <span>Webhook列表</span>
              </el-menu-item>
              <el-menu-item index="/webhook/logs">
                <el-icon><Document /></el-icon>
                <span>请求日志</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="/task">
              <template #title>
                <el-icon><Operation /></el-icon>
                <span>任务管理</span>
              </template>
              <el-menu-item index="/task/list">
                <el-icon><List /></el-icon>
                <span>任务列表</span>
              </el-menu-item>
              <el-menu-item index="/task/create">
                <el-icon><Plus /></el-icon>
                <span>创建任务</span>
              </el-menu-item>
            </el-sub-menu>
            
            <el-sub-menu index="/monitoring">
              <template #title>
                <el-icon><DataAnalysis /></el-icon>
                <span>监控分析</span>
              </template>
              <el-menu-item index="/monitoring/executions">
                <el-icon><Clock /></el-icon>
                <span>执行历史</span>
              </el-menu-item>
              <el-menu-item index="/monitoring/analytics">
                <el-icon><TrendCharts /></el-icon>
                <span>统计分析</span>
              </el-menu-item>
            </el-sub-menu>
          </el-menu>
        </el-aside>

        <!-- 主内容区域 -->
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import {
  House,
  Setting,
  Cpu,
  FolderOpened,
  Connection,
  List,
  Document,
  Operation,
  Plus,
  DataAnalysis,
  Clock,
  TrendCharts
} from '@element-plus/icons-vue'
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.logo .el-icon {
  font-size: 24px;
  color: #409eff;
}

.app-aside {
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
}

.sidebar-menu {
  border-right: none;
  height: 100%;
}

.app-main {
  background-color: #f5f7fa;
  padding: 20px;
}
</style>