// 账号相关类型
export interface Account {
  id: number
  anyrouter_user_id: string
  username: string
  display_name?: string
  is_active: boolean
  health_status: 'healthy' | 'unhealthy' | 'unknown'
  health_message?: string
  last_health_check?: string
  group_id?: number
  group?: AccountGroup
  cached_quota?: number
  cached_used_quota?: number
  cached_request_count?: number
  cached_user_group?: string
  cached_aff_code?: string
  cached_aff_count?: number
  cached_aff_history_quota?: number
  quota_updated_at?: string
  quota_display?: string
  quota_percent?: string
  last_sign?: {
    success: boolean
    time: string
    message?: string
  }
  created_at: string
  updated_at: string
}

export interface AccountGroup {
  id: number
  name: string
  description?: string
  color: GroupColor
  created_at: string
  updated_at: string
}

export type GroupColor = 'default' | 'blue' | 'green' | 'red' | 'orange' | 'purple' | 'pink' | 'cyan'

export interface CreateAccountParams {
  session_cookie: string
  user_id: string
  group_id?: number
}

export interface UpdateAccountParams {
  user_id?: string
  session_cookie?: string
  is_active?: boolean
  group_id?: number
}

// API Token 相关类型
export interface ApiToken {
  id: number
  account_id: number
  token_id: number
  key: string
  name?: string
  status: number
  remain_quota: number
  used_quota: number
  unlimited_quota: boolean
  model_limits_enabled: boolean
  model_limits?: string
  group?: string
  allow_ips?: string
  created_time?: number
  accessed_time?: number
  expired_time?: number
  synced_at?: string
}

export interface CreateTokenParams {
  name: string
  remain_quota: number
  expired_time: number
  unlimited_quota: boolean
  model_limits_enabled: boolean
  model_limits: string
  allow_ips: string
  group: string
}

export interface CreateTokenParamsOptional {
  name: string
  remain_quota?: number
  expired_time?: number
  unlimited_quota?: boolean
  model_limits_enabled?: boolean
  model_limits?: string
  group?: string
  allow_ips?: string
}

export interface UpdateTokenParams extends CreateTokenParams {
  token_id?: number
}

// 签到相关类型
export interface SignLog {
  id: number
  account_id: number
  account?: Account
  sign_time: string
  success: boolean
  message?: string
  reward_quota?: number
  retry_count: number
}

export interface SignResult {
  success: boolean
  message: string
  reward_quota?: number
}

export interface BatchSignResult {
  success_count: number
  fail_count: number
  results: SignResult[]
}

// 推送渠道相关类型
export type NotifyChannelType = 'pushplus' | 'wechat_mp' | 'wechat_work' | 'dingtalk' | 'feishu' | 'email'

export interface NotifyChannel {
  id: number
  type: NotifyChannelType
  name: string
  config: Record<string, any>
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface AccountNotify {
  id: number
  account_id: number
  channel_id: number
  channel?: NotifyChannel
  notify_config: Record<string, any>
  is_enabled: boolean
}

// API 节点相关类型
export interface ApiEndpoint {
  id: number
  endpoint_id: number
  route: string
  url: string
  description?: string
  color: 'green' | 'blue' | 'yellow' | 'red'
  created_at: string
  updated_at: string
}

// 仪表盘相关类型
export interface DashboardData {
  account_count: number
  unhealthy_account_count: number
  today_sign_count: number
  today_sign_success: number
  success_rate?: number
  month_reward: number
  month_reward_display: string
  total_quota: number
  total_quota_display: string
  daily_trend: DailyTrend[]
}

export interface DailyTrend {
  date: string
  success: number
  fail: number
}

// 统计相关类型
export interface StatisticsOverview {
  total_accounts: number
  total_signs: number
  total_success: number
  total_reward: number
  success_rate: number
}

export interface DailyStatistics {
  date: string
  sign_count: number
  success_count: number
  fail_count: number
  reward_quota: number
}

export interface MonthlyStatistics {
  month: string
  sign_count: number
  success_count: number
  fail_count: number
  reward_quota: number
}

export interface AccountStatistics {
  account_id: number
  account_name: string
  sign_count: number
  success_count: number
  fail_count: number
  reward_quota: number
}

// 系统设置相关类型
export interface SystemSettings {
  auto_sign_enabled: boolean
  auto_sign_time: string
  health_check_enabled: boolean
  health_check_interval: number
  sign_retry_enabled: boolean
  sign_max_retries: number
  sign_retry_interval: number
}

// 审计日志相关类型
export interface AuditLog {
  id: number
  user_id: number
  username: string
  action: string
  target_type?: string
  target_id?: number
  target_name?: string
  detail?: Record<string, any>
  ip_address?: string
  user_agent?: string
  created_at: string
}

// 用户相关类型
export interface User {
  id: number
  username: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  access_token: string
  token_type: string
}

export interface ChangePasswordParams {
  old_password: string
  new_password: string
}

// API 响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 表单相关类型
export interface AddAccountForm {
  session_cookie: string
  user_id: string
  group_id: number | null
  notify_channel_ids: number[]
}

export interface EditAccountForm {
  user_id: string
  session_cookie: string
  is_active: boolean
  group_id: number | null
  notify_channel_ids: number[]
}

export interface TokenForm {
  name: string
  remain_quota: number
  expired_time: number
  unlimited_quota: boolean
  model_limits_enabled: boolean
  model_limits_array: string[]
  group: string
  allow_ips: string
}

// 选项类型
export interface SelectOption<T = any> {
  label: string
  value: T
  disabled?: boolean
}

// 健康检查结果
export interface HealthCheckResult {
  account_id: number
  health_status: 'healthy' | 'unhealthy'
  health_message?: string
}

export interface BatchHealthCheckResult {
  healthy_count: number
  unhealthy_count: number
  results: HealthCheckResult[]
}
