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
