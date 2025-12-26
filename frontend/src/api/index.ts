import axios from 'axios'
import { getToken, removeToken } from '../utils/auth'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
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
    const message = error.response?.data?.detail || error.message

    // 401 未授权 - 跳转登录页
    if (status === 401) {
      removeToken()
      // 避免在登录页面重复跳转
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(new Error(message))
  }
)

export default api

// 认证 API
export const authApi = {
  login: (data: { username: string; password: string }) => api.post('/auth/login', data),
  getMe: () => api.get('/auth/me'),
  changePassword: (data: { old_password: string; new_password: string }) => api.put('/auth/password', data)
}

// 账号 API
export const accountApi = {
  getList: () => api.get('/accounts'),
  create: (data: { session_cookie: string; user_id: string; group_id?: number }) => api.post('/accounts', data),
  get: (id: number) => api.get(`/accounts/${id}`),
  update: (id: number, data: any) => api.put(`/accounts/${id}`, data),
  delete: (id: number) => api.delete(`/accounts/${id}`),
  getInfo: (id: number) => api.get(`/accounts/${id}/info`),
  getCachedInfo: (id: number) => api.get(`/accounts/${id}/cached-info`),
  getSignLogs: (id: number, page = 1, size = 20) =>
    api.get(`/accounts/${id}/sign-logs`, { params: { page, size } }),
  // Token 相关
  getTokens: (id: number) => api.get(`/accounts/${id}/tokens`),
  syncTokens: (id: number) => api.post(`/accounts/${id}/tokens/sync`),
  createToken: (id: number, data: {
    name: string
    remain_quota: number
    expired_time: number  // -1 表示永不过期
    unlimited_quota: boolean
    model_limits_enabled: boolean
    model_limits: string  // 逗号分隔的模型列表
    allow_ips: string
    group: string
  }) => api.post(`/accounts/${id}/tokens`, data),
  // 获取可用模型列表
  getAvailableModels: (id: number) => api.get(`/accounts/${id}/models`),
  // 获取账号分组列表
  getAccountGroups: (id: number) => api.get(`/accounts/${id}/groups`),
  // 删除令牌
  deleteToken: (id: number, tokenId: number) => api.delete(`/accounts/${id}/tokens/${tokenId}`),
  // 更新令牌
  updateToken: (id: number, tokenId: number, data: any) => api.put(`/accounts/${id}/tokens/${tokenId}`, data),
  // 健康检查
  healthCheck: (id: number) => api.post(`/accounts/${id}/health-check`),
  healthCheckAll: () => api.post('/accounts/health-check/all')
}

// 签到 API
export const signApi = {
  sign: (accountId: number) => api.post(`/accounts/${accountId}/sign`),
  batchSign: () => api.post('/sign/batch'),
  getAllLogs: (params?: { page?: number; size?: number; account_id?: number; success?: boolean }) =>
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

// API 节点
export const apiEndpointsApi = {
  getList: () => api.get('/api-endpoints'),
  sync: () => api.post('/api-endpoints/sync')
}

// 备份恢复 API
export const backupApi = {
  getInfo: () => api.get('/backup/info'),
  export: (includeLogs = false) => {
    // 返回下载 URL，需要带上 token
    const token = getToken()
    return `/api/v1/backup/export?include_logs=${includeLogs}&token=${token}`
  },
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
  getDaily: (days = 30) => api.get('/statistics/daily', { params: { days } }),
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
