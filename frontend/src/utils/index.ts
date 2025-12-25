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
