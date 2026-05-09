import axios from 'axios'
import { getToken, removeToken } from '../utils/auth'
import router from '../router'
import { ApiError } from '../utils/apiError'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 300000
})

// 请求拦截器 - 添加 Token
api.interceptors.request.use(
  config => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const status = error.response?.status
    const detail = error.response?.data
    const message = detail?.detail || error.message

    // 401 未授权 - 跳转登录页（保留当前路径便于回跳）
    if (status === 401) {
      removeToken()
      const current = router.currentRoute.value
      if (current.path !== '/login') {
        router.push({
          path: '/login',
          query: current.fullPath !== '/' ? { redirect: current.fullPath } : undefined
        })
      }
    }

    return Promise.reject(new ApiError(message, status, detail))
  }
)

export default api

// 认证 API
export const authApi = {
  login: (data: { username: string; password: string }) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  changePassword: (data: { old_password: string; new_password: string }) => api.put('/auth/password', data)
}

// 平台 API
export const platformApi = {
  getList: () => api.get('/platforms'),
  create: (data: { name: string; base_url: string; sign_mode?: 'api' | 'login'; sign_api?: string; checkin_api?: string; user_api?: string; console_url?: string; models_api?: string; groups_api?: string; token_api?: string; status_api?: string }) => api.post('/platforms', data),
  get: (id: number) => api.get(`/platforms/${id}`),
  update: (id: number, data: any) => api.put(`/platforms/${id}`, data),
  delete: (id: number) => api.delete(`/platforms/${id}`)
}

// 账号 API
export const accountApi = {
  getList: (params?: {
    page?: number
    size?: number
    keyword?: string
    platform_id?: number
    group_id?: number
    status?: string
    sort_by?: string
    sort_order?: 'asc' | 'desc'
  }) => api.get('/accounts', { params }),
  create: (data: { session_cookie?: string; user_id?: string; login_username?: string; login_password?: string; note?: string; proxy_mode?: 'global' | 'direct' | 'custom'; proxy_url?: string; platform_id: number; group_id?: number }) => api.post('/accounts', data),
  batchImport: (data: {
    items: Array<{
      session_cookie?: string
      user_id?: string
      login_username?: string
      login_password?: string
      note?: string
      proxy_mode?: 'global' | 'direct' | 'custom'
      proxy_url?: string
      platform_id: number
      group_id?: number
    }>
  }) => api.post('/accounts/batch-import', data),
  get: (id: number) => api.get(`/accounts/${id}`),
  update: (id: number, data: any) => api.put(`/accounts/${id}`, data),
  delete: (id: number) => api.delete(`/accounts/${id}`),
  getInfo: (id: number) => api.get(`/accounts/${id}/info`),
  getCachedInfo: (id: number) => api.get(`/accounts/${id}/cached-info`),
  getSignLogs: (id: number, page = 1, size = 20) =>
    api.get(`/accounts/${id}/sign-logs`, { params: { page, size } }),
  getTokens: (id: number) => api.get(`/accounts/${id}/tokens`),
  syncTokens: (id: number) => api.post(`/accounts/${id}/tokens/sync`),
  createToken: (id: number, data: {
    name: string
    remain_quota: number
    expired_time: number
    unlimited_quota: boolean
    model_limits_enabled: boolean
    model_limits: string
    allow_ips: string
    group: string
  }) => api.post(`/accounts/${id}/tokens`, data),
  getAvailableModels: (id: number) => api.get(`/accounts/${id}/models`),
  getAccountGroups: (id: number) => api.get(`/accounts/${id}/groups`),
  deleteToken: (id: number, tokenId: number) => api.delete(`/accounts/${id}/tokens/${tokenId}`),
  updateToken: (id: number, tokenId: number, data: any) => api.put(`/accounts/${id}/tokens/${tokenId}`, data),
  healthCheck: (id: number) => api.post(`/accounts/${id}/health-check`),
  healthCheckAll: () => api.post('/accounts/health-check/all')
}

// 签到 API
export const signApi = {
  sign: (accountId: number) => api.post(`/accounts/${accountId}/sign`),
  batchSign: () => api.post('/sign/batch'),
  getAllLogs: (params?: {
    page?: number
    size?: number
    account_id?: number
    success?: boolean
    start_date?: string
    end_date?: string
    sort_by?: string
    sort_order?: 'asc' | 'desc'
  }) =>
    api.get('/sign-logs', { params })
}

// 推送渠道 API
export const notifyApi = {
  getChannels: () => api.get('/notify/channels'),
  createChannel: (data: any) => api.post('/notify/channels', data),
  updateChannel: (id: number, data: any) => api.put(`/notify/channels/${id}`, data),
  deleteChannel: (id: number) => api.delete(`/notify/channels/${id}`),
  testChannel: (id: number) => api.post(`/notify/channels/${id}/test`),
  getAccountNotify: (accountId: number) => api.get(`/notify/accounts/${accountId}`),
  updateAccountNotify: (accountId: number, data: any) =>
    api.put(`/notify/accounts/${accountId}`, data)
}

// 仪表盘 API
export const dashboardApi = {
  get: () => api.get('/dashboard')
}

// 设置 API
export const settingsApi = {
  get: () => api.get('/settings'),
  update: (data: any) => api.put('/settings', data),
  getScheduler: () => api.get('/settings/scheduler')
}

export const eventsApi = {
  streamUrl: (token: string) => `/api/v1/events?token=${encodeURIComponent(token)}`
}

// API 节点
export const apiEndpointsApi = {
  getList: (platformId?: number) =>
    api.get('/api-endpoints', { params: platformId != null ? { platform_id: platformId } : undefined }),
  sync: (platformId?: number) =>
    api.post('/api-endpoints/sync', null, { params: platformId != null ? { platform_id: platformId } : undefined })
}

// 备份恢复 API
export const backupApi = {
  getInfo: () => api.get('/backup/info'),
  // 导出走 fetch + Authorization header（见 Settings.vue handleExport），此处保留 path 供使用者拼装
  exportPath: (includeLogs = false) => `/api/v1/backup/export?include_logs=${includeLogs}`,
  import: (file: File, overwrite = false) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/backup/import?overwrite=${overwrite}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

// 统计 API
export const statisticsApi = {
  getOverview: () => api.get('/statistics/overview'),
  getDaily: (days = 30, startDate?: string, endDate?: string) => {
    const params: any = { days }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return api.get('/statistics/daily', { params })
  },
  getMonthly: (months = 12) => api.get('/statistics/monthly', { params: { months } }),
  getAccounts: () => api.get('/statistics/accounts'),
  export: (params?: { start_date?: string; end_date?: string; format?: string }) =>
    api.get('/statistics/export', { params })
}

// 分组 API
export const groupsApi = {
  getList: () => api.get('/groups'),
  create: (data: { name: string; description?: string; color?: string }) => api.post('/groups', data),
  update: (id: number, data: { name?: string; description?: string; color?: string }) => api.put(`/groups/${id}`, data),
  delete: (id: number) => api.delete(`/groups/${id}`),
  addAccounts: (id: number, accountIds: number[]) => api.post(`/groups/${id}/accounts`, accountIds),
  removeAccounts: (id: number, accountIds: number[]) => api.delete(`/groups/${id}/accounts`, { data: accountIds })
}

// 审计日志 API
export const auditApi = {
  getLogs: (params?: {
    page?: number
    size?: number
    action?: string
    user_id?: number
    start_date?: string
    end_date?: string
    keyword?: string
  }) => api.get('/audit/logs', { params }),
  getActions: () => api.get('/audit/actions'),
  export: (params?: {
    action?: string
    start_date?: string
    end_date?: string
    format?: 'json' | 'csv'
  }) => {
    const queryParams = new URLSearchParams()
    if (params?.action) queryParams.append('action', params.action)
    if (params?.start_date) queryParams.append('start_date', params.start_date)
    if (params?.end_date) queryParams.append('end_date', params.end_date)
    if (params?.format) queryParams.append('format', params.format)
    return `/api/v1/audit/export?${queryParams.toString()}`
  }
}

// 系统日志 API
export const logsApi = {
  getFiles: () => api.get('/logs/files'),
  getLogs: (params?: {
    file?: string
    level?: string
    keyword?: string
    lines?: number
    offset?: number
  }) => api.get('/logs', { params }),
  download: (filename: string) => {
    return `/api/v1/logs/download/${filename}`
  },
  clear: (filename: string) => api.delete(`/logs/${filename}`)
}
