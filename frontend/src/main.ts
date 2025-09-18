import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import router from './router'
import './assets/styles/main.css'

// 创建应用实例
const app = createApp(App)

// 创建 Pinia 实例
const pinia = createPinia()

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn,
  size: 'default'
})

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('全局错误:', err)
  console.error('错误信息:', info)
  console.error('组件实例:', vm)
}

// 全局警告处理
app.config.warnHandler = (msg, vm, trace) => {
  console.warn('全局警告:', msg)
  console.warn('组件实例:', vm)
  console.warn('组件追踪:', trace)
}

// 挂载应用
app.mount('#app')

// 开发环境下的调试信息
if (import.meta.env.DEV) {
  console.log('🚀 应用已启动')
  console.log('📦 Vue版本:', app.version)
  console.log('🌐 环境:', import.meta.env.MODE)
  console.log('🔗 API地址:', import.meta.env.VITE_API_BASE_URL)
}