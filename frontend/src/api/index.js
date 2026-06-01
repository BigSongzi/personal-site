// axios 单例:统一加 Authorization 头与错误提示
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth'
import router from '@/router'

const http = axios.create({
  baseURL: '/',
  timeout: 15000
})

// 请求拦截:挂上 token
http.interceptors.request.use((cfg) => {
  const auth = useAuthStore()
  if (auth.token) {
    cfg.headers = cfg.headers || {}
    cfg.headers.Authorization = `Bearer ${auth.token}`
  }
  return cfg
})

// 响应拦截:统一错误提示;401 跳登录
http.interceptors.response.use(
  (resp) => {
    const body = resp.data
    if (body && typeof body === 'object' && 'code' in body && body.code !== 0) {
      ElMessage.error(body.msg || '请求失败')
      return Promise.reject(body)
    }
    return body
  },
  (err) => {
    const status = err?.response?.status
    const msg = err?.response?.data?.msg || err.message || '网络错误'
    if (status === 401) {
      const auth = useAuthStore()
      auth.clear()
      ElMessage.warning('请先登录')
      router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    } else {
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  }
)

export default http
