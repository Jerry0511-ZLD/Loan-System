// main.js 是整个前端的“入口文件”，就像一个程序的 main 函数
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css' // UI 组件库的样式
import zhCn from 'element-plus/es/locale/lang/zh-cn' // 组件内部文字用中文
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import './styles/main.css'

const app = createApp(App)

// 把 element-plus 的所有图标注册成全局组件
// 之后在任意 .vue 里都能直接写 <el-icon><User /></el-icon>
for (const [name, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(name, component)
}

app.use(ElementPlus, { locale: zhCn })
app.use(router) // 启用路由（页面跳转）
app.mount('#app') // 挂载到 index.html 里的 <div id="app">