import axios from 'axios'
import { ElMessage } from 'element-plus'

/**
 * 统一的 axios 实例：集中处理“请求头带 token”和“错误提示”。
 * 这样每个页面就不需要重复写这些逻辑。
 */
const request = axios.create({
  baseURL: '/api', // 会被 vite.config.js 里的 proxy 转发到后端 8080
  timeout: 10000
})

// 请求拦截器：发出去之前，自动带上登录凭证
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：后端返回 { code, message, data }，这里统一拆包和报错
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端成功码是 200（配置项 api_success_code），早期约定是 0，两个都放行
    if (res.code !== 0 && res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res.data // 直接把业务数据交给页面，页面里不用再写 res.data.data
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      localStorage.removeItem('token')
      window.location.href = '/login'
    } else {
      ElMessage.error(error.message || '网络异常')
    }
    return Promise.reject(error)
  }
)

export default request