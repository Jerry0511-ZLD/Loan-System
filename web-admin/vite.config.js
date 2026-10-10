import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Vite 是开发服务器 + 打包工具，这个文件是它的配置
export default defineConfig({
  // 让 .vue 文件能被识别
  plugins: [vue()],

  resolve: {
    // 配置 @ 指向 src 目录，这样 import 时写 '@/views/Login.vue'
    // 不用写 '../../../views/Login.vue'
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },

  server: {
    port: 5173,
    open: true,
    // 代理：前端里写 '/api/loan/list'，Vite 会转发到后端的 8080 端口
    // 这样前后端分开开发时不会有跨域(CORS)问题
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true
      }
    }
  }
})