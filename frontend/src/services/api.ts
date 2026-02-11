import axios from 'axios'
import { getToken, removeToken } from '@/utils/token'

// 使用 ?? 而不是 || 來正確處理空字串（空字串表示使用相對路徑）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: 自動附加 Token
api.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response Interceptor: 處理 401 錯誤
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 只有非登入 API 的 401 錯誤才自動登出
    // 登入 API 返回 401 是預期行為（密碼錯誤）
    const isLoginRequest = error.config?.url?.includes('/auth/login')
    if (error.response?.status === 401 && !isLoginRequest) {
      removeToken()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
