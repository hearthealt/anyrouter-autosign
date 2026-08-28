/**
 * 格式化配额为美元
 */
export function formatQuota(quota: number): string {
  const usd = quota / 500000
  if (usd < 0.01) {
    return `$${usd.toFixed(4)}`
  } else if (usd < 1000) {
    return `$${usd.toFixed(2)}`
  } else {
    return `$${usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }
}

export type RewardTotals = Record<string, number>

/**
 * 统一账号状态：禁用优先，其次只有明确的 unhealthy 才算异常，其余启用账号均视为正常。
 * 这样可以避免禁用账号保留历史健康检查结果时继续显示为异常。
 */
export type AccountStatus = 'normal' | 'unhealthy' | 'disabled'

export function getAccountStatus(account: { is_active: boolean; health_status?: string | null }): AccountStatus {
  if (!account.is_active) return 'disabled'
  return account.health_status === 'unhealthy' ? 'unhealthy' : 'normal'
}

function formatRewardNumber(value: number, minimumFractionDigits = 0): string {
  const rounded = Math.round(value * 10000) / 10000
  return rounded.toLocaleString('zh-CN', {
    minimumFractionDigits,
    maximumFractionDigits: 4
  })
}

/** 按奖励单位格式化聚合结果；旧接口可通过 fallback 继续显示美元字段。 */
export function formatRewardTotals(
  totals?: RewardTotals | null,
  fallback = '$0.00'
): string {
  const entries = Object.entries(totals || {})
    .map(([unit, raw]) => [unit, Number(raw)] as const)
    .filter(([, value]) => Number.isFinite(value) && value !== 0)
    .sort(([left], [right]) => left === '$' ? -1 : right === '$' ? 1 : left.localeCompare(right, 'zh-CN'))

  if (!entries.length) return fallback

  return entries.map(([unit, value]) => {
    if (unit === '$') {
      return `$${formatRewardNumber(value, Math.abs(value) < 0.01 ? 4 : 2)}`
    }
    if (unit === '¥' || unit === '￥') {
      return `${unit}${formatRewardNumber(value, 2)}`
    }
    if (unit === 'count') {
      return `${formatRewardNumber(value)} 次`
    }
    return `${formatRewardNumber(value)} ${unit}`
  }).join('、')
}

/** 格式化一条签到日志的奖励，兼容没有 reward_display 的旧记录。 */
export function formatRewardAmount(
  amount?: number | null,
  unit?: string | null,
  display?: string | null
): string {
  if (display?.trim()) return display.trim()

  const value = Number(amount || 0)
  const normalizedUnit = (unit || 'quota').trim() || 'quota'
  if (normalizedUnit === 'quota') return formatQuota(value)
  if (normalizedUnit === '$' || normalizedUnit === '¥' || normalizedUnit === '￥') {
    return `${normalizedUnit}${formatRewardNumber(value, 2)}`
  }
  if (normalizedUnit === 'count') return `${formatRewardNumber(value)} 次`
  return `${formatRewardNumber(value)} ${normalizedUnit}`
}

/** 转义 ECharts HTML tooltip 中的外部数据。 */
export function escapeHtml(value: unknown): string {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * 表格里的自由文本硬性截断。
 *
 * 签到结果、审计详情这类字段长度完全由上游返回决定，只靠 CSS 省略号不够：
 * 列宽是 min-width，超长文本会把整行撑开、把后面的列挤出视口。这里先按字数
 * 砍掉，CSS 省略号只负责收尾。
 */
export function truncateText(value: unknown, max = 60): string {
  const text = String(value ?? '').replace(/\s+/g, ' ').trim()
  if (!text) return ''
  return text.length > max ? `${text.slice(0, max)}…` : text
}

/**
 * 校验并归一化对外跳转链接。
 * 平台 base_url 由用户手填并存库，只放行 http/https，其余（含 javascript:）返回空串，
 * 由调用方降级为纯文本展示。
 */
export function normalizeExternalUrl(raw?: string | null): string {
  const value = String(raw ?? '').trim()
  if (!value) return ''
  try {
    const parsed = new URL(value)
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return ''
    return value
  } catch {
    return ''
  }
}

/**
 * 格式化日期时间
 */
export function formatDateTime(date: string | Date): string {
  const d = new Date(date)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * 推送渠道类型映射
 */
export const channelTypes: Record<string, string> = {
  pushplus: 'PushPlus',
  wechat_mp: '微信公众号',
  wechat_work: '企业微信',
  dingtalk: '钉钉机器人',
  feishu: '飞书机器人',
  email: '邮箱 (SMTP)'
}

/**
 * 获取渠道类型显示名
 */
export function getChannelTypeName(type: string): string {
  return channelTypes[type] || type
}

/**
 * 复制文本到剪贴板（兼容非 HTTPS 环境）
 */
export async function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text)
  }
  // 降级方案：使用 execCommand
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    document.execCommand('copy')
  } finally {
    document.body.removeChild(textarea)
  }
}

/**
 * 主题模式: auto | light | dark
 */
export type ThemeMode = 'auto' | 'light' | 'dark'

const THEME_KEY = 'anyrouter-theme'

/**
 * 获取当前主题模式
 */
export function getThemeMode(): ThemeMode {
  const stored = localStorage.getItem(THEME_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'auto') {
    return stored
  }
  return 'auto'
}

/**
 * 设置主题模式
 */
export function setThemeMode(mode: ThemeMode): void {
  localStorage.setItem(THEME_KEY, mode)
  applyTheme(mode)
}

/**
 * 获取实际应用的主题（light 或 dark）
 */
export function getActiveTheme(): 'light' | 'dark' {
  const mode = getThemeMode()
  if (mode === 'auto') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return mode
}

/**
 * 应用主题到 DOM
 */
export function applyTheme(mode: ThemeMode): void {
  const theme = mode === 'auto'
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : mode

  document.documentElement.setAttribute('data-theme', theme)

  // 更新 meta theme-color
  const metaTheme = document.querySelector('meta[name="theme-color"]')
  if (metaTheme) {
    metaTheme.setAttribute('content', theme === 'dark' ? '#1a1a2e' : '#ffffff')
  }
}

/**
 * 初始化主题（在应用启动时调用）
 */
export function initTheme(): void {
  applyTheme(getThemeMode())

  // 监听系统主题变化
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (getThemeMode() === 'auto') {
      applyTheme('auto')
    }
  })
}
