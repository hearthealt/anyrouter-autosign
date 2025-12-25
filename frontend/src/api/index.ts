import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.detail || error.message
    return Promise.reject(new Error(message))
  }
)

export default api

// 账号 API
export const accountApi = {
  getList: () => api.get('/accounts'),
  create: (data: { session_cookie: string; user_id: string }) => api.post('/accounts', data),
  get: (id: number) => api.get(`/accounts/${id}`),
  update: (id: number, data: any) => api.put(`/accounts/${id}`, data),
  delete: (id: number) => api.delete(`/accounts/${id}`),
  getInfo: (id: number) => api.get(`/accounts/${id}/info`),
  getSignLogs: (id: number, page = 1, size = 20) =>
    api.get(`/accounts/${id}/sign-logs`, { params: { page, size } }),
  // Token 相关
  getTokens: (id: number) => api.get(`/accounts/${id}/tokens`),
  syncTokens: (id: number) => api.post(`/accounts/${id}/tokens/sync`)
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
