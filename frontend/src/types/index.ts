export type PlatformAdapterType = 'new_api' | 'http'
export type RewardTotals = Record<string, number>

export interface PlatformCapabilities {
  requires_external_user_id: boolean
  supports_user_info: boolean
  supports_tokens: boolean
  supports_models: boolean
  supports_groups: boolean
  supports_health_check: boolean
}

// 平台与账号相关类型
export interface Platform {
  id: number
  name: string
  base_url: string
  adapter_type: PlatformAdapterType
  adapter_config?: Record<string, any>
  capabilities?: PlatformCapabilities
  sign_mode?: 'api' | 'login'
  sign_api?: string
  checkin_api?: string
  user_api?: string
  console_url?: string
  models_api?: string
  groups_api?: string
  token_api?: string
  status_api?: string
  captcha_api?: string
  is_default: boolean
  accounts_count?: number
  created_at: string
  updated_at: string
}

export interface PlatformBrief {
  id: number
  name: string
  base_url: string
  adapter_type?: PlatformAdapterType
}

export type AccountAuthType = 'none' | 'custom' | 'bearer' | 'cookie' | 'header' | 'basic'
export type AccountProxyMode = 'direct' | 'custom'

export interface Account {
  id: number
  anyrouter_user_id?: number
  external_user_id?: string
  username: string
  display_name?: string
  note?: string
  login_username?: string
  has_login_credentials?: boolean
  auth_type?: AccountAuthType
  has_auth_data?: boolean
  proxy_mode?: AccountProxyMode
  proxy_url?: string
  proxy_url_masked?: string
  is_active: boolean
  platform?: PlatformBrief
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
  session_cookie?: string
  user_id?: string
  external_user_id?: string
  username?: string
  display_name?: string
  login_username?: string
  login_password?: string
  auth_type?: AccountAuthType
  auth_data?: Record<string, any>
  note?: string
  proxy_mode?: AccountProxyMode
  proxy_url?: string
  platform_id: number
  group_id?: number
}

export interface BatchImportItem extends CreateAccountParams {}

export interface BatchImportResultItem {
  index: number
  success: boolean
  message: string
  account_id?: number
  username?: string
}

export interface BatchImportResponse {
  total: number
  success_count: number
  fail_count: number
  results: BatchImportResultItem[]
}

export interface UpdateAccountParams {
  user_id?: string
  external_user_id?: string
  username?: string
  display_name?: string
  session_cookie?: string
  login_username?: string
  login_password?: string
  auth_type?: AccountAuthType
  auth_data?: Record<string, any>
  clear_auth_data?: boolean
  note?: string
  proxy_mode?: AccountProxyMode
  proxy_url?: string
  clear_login_credentials?: boolean
  is_active?: boolean
  platform_id?: number
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
  platform?: PlatformBrief
  platform_name?: string
  sign_time: string
  success: boolean
  message?: string
  reward_quota?: number
  reward_display?: string
  reward_unit?: string
  status?: 'success' | 'already_signed' | 'failed'
  retry_count: number
}

export interface SignResult {
  success: boolean
  message: string
  reward_quota?: number
  reward_display?: string
  reward_unit?: string
  status?: 'success' | 'already_signed' | 'failed'
}

export interface BatchSignResult {
  success_count: number
  fail_count: number
  already_signed_count?: number
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
  platform_id: number
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
  active_account_count?: number
  normal_account_count?: number
  unhealthy_account_count: number
  disabled_account_count?: number
  today_sign_count: number
  today_sign_success: number
  success_rate?: number
  month_reward: number
  month_reward_display: string
  month_reward_totals?: RewardTotals
  total_quota: number
  total_used_quota?: number
  total_quota_display: string
  total_used_quota_display?: string
  total_request_count?: number
  daily_trend: DailyTrend[]
}

export interface DailyTrend {
  date: string
  success: number
  fail: number
  reward?: number
  reward_display?: string
  reward_totals?: RewardTotals
}

// 统计相关类型
export interface StatisticsOverview {
  total_accounts: number
  active_accounts: number
  today_success: number
  today_fail: number
  month_success: number
  month_total: number
  month_success_rate: number
  total_reward: number
  total_reward_display: string
  month_reward: number
  month_reward_display: string
  total_reward_totals?: RewardTotals
  month_reward_totals?: RewardTotals
  success_rate: number
}

export interface DailyStatistics {
  date: string
  success: number
  fail: number
  total: number
  reward: number
  reward_display: string
  reward_totals?: RewardTotals
}

export interface MonthlyStatistics {
  month: string
  success: number
  fail: number
  total: number
  success_rate: number
  reward: number
  reward_display: string
  reward_totals?: RewardTotals
}

export interface AccountStatistics {
  account_id: number
  username: string
  total_signs: number
  success_count: number
  fail_count: number
  success_rate: number
  total_reward: number
  total_reward_display: string
  reward_totals?: RewardTotals
  streak_days: number
  is_active: boolean
  health_status: 'healthy' | 'unhealthy' | 'unknown'
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
  sign_notify_enabled: boolean
  sign_notify_channel_ids: number[]
  quota_warning_threshold: number
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
  login_username: string
  login_password: string
  note: string
  proxy_mode: AccountProxyMode
  proxy_url: string
  clear_login_credentials: boolean
  platform_id: number | null
  group_id: number | null
  notify_channel_ids: number[]
}

export interface EditAccountForm {
  user_id: string
  session_cookie: string
  login_username: string
  login_password: string
  note: string
  proxy_mode: AccountProxyMode
  proxy_url: string
  clear_login_credentials: boolean
  is_active: boolean
  platform_id: number | null
  group_id: number | null
  notify_channel_ids: number[]
}

export interface ServerEvent {
  id?: string
  type: 'connected' | 'ping' | 'sign_completed' | 'health_changed' | 'account_changed'
  timestamp?: string
  account_id?: number
  username?: string
  action?: string
  success?: boolean
  already_signed?: boolean
  message?: string
  reward_quota?: number
  reward_display?: string
  reward_unit?: string
  health_status?: 'healthy' | 'unhealthy' | 'unknown'
  health_message?: string
  previous_status?: 'healthy' | 'unhealthy' | 'unknown'
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
  health_status: 'healthy' | 'unhealthy' | 'unknown'
  health_message?: string
}

export interface BatchHealthCheckResult {
  healthy_count: number
  unhealthy_count: number
  unknown_count: number
  results: HealthCheckResult[]
}

// 系统版本与更新
export interface VersionInfo {
  name: string
  version: string
  changelog_url: string
}

export interface LatestVersionInfo {
  version: string
  changelog: string
  /** 取不到云端版本时的可读原因 */
  error?: string | null
}

export interface UpdateResult {
  status: 'triggered' | 'no_update' | 'error'
  message: string
  update_id?: string | null
  current_version?: string
  target_version?: string
  poll_interval_seconds?: number
  timeout_seconds?: number
}

export interface UpdateStatus {
  update_id: string
  status: 'unknown' | 'triggered' | 'updating' | 'ready' | 'no_update' | 'failed'
  message: string
  healthy: boolean
  ready: boolean
  current_version: string
  target_version: string
  elapsed_seconds: number
}

export interface SystemHealthInfo {
  status: string
  healthy: boolean
  version: string
  update_id?: string | null
  update_status: string
  target_version: string
  message: string
  ready: boolean
  elapsed_seconds: number
}
