export function useFormat() {
  // 格式化额度（将数字转换为美元显示）
  function formatQuota(quota: number | undefined | null): string {
    if (quota === undefined || quota === null) return '$0.00'
    const dollars = quota / 500000
    return `$${dollars.toFixed(2)}`
  }

  // 格式化时间为相对时间
  function formatRelativeTime(time: string | undefined | null): string {
    if (!time) return ''
    const date = new Date(time)
    const now = new Date()
    const diff = now.getTime() - date.getTime()

    if (diff < 0) return '刚刚'
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
    if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
    if (diff < 172800000) return '1天前'
    if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
    if (diff < 2592000000) return Math.floor(diff / 604800000) + '周前'
    if (diff < 31536000000) return Math.floor(diff / 2592000000) + '个月前'

    return Math.floor(diff / 31536000000) + '年前'
  }

  // 格式化日期
  function formatDate(time: string | undefined | null, format = 'YYYY-MM-DD'): string {
    if (!time) return ''
    const date = new Date(time)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    return format
      .replace('YYYY', String(year))
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hours)
      .replace('mm', minutes)
      .replace('ss', seconds)
  }

  // 格式化日期时间
  function formatDateTime(time: string | undefined | null): string {
    return formatDate(time, 'YYYY-MM-DD HH:mm:ss')
  }

  // 格式化短日期（用于图表）
  function formatShortDate(dateStr: string): string {
    const parts = dateStr.split('-')
    return parts.length >= 3 ? `${parts[1]}/${parts[2]}` : dateStr
  }

  // 格式化百分比
  function formatPercent(value: number, decimals = 1): string {
    return `${value.toFixed(decimals)}%`
  }

  // 格式化数字（千分位）
  function formatNumber(num: number): string {
    return num.toLocaleString()
  }

  // 解析模型限制字符串
  function parseModels(modelLimits: string | undefined | null): string[] {
    if (!modelLimits) return []
    return modelLimits.split(',').map(m => m.trim()).filter(m => m)
  }

  // 获取健康状态类型
  function getHealthStatusType(status: string): 'success' | 'error' | 'default' {
    if (status === 'healthy') return 'success'
    if (status === 'unhealthy') return 'error'
    return 'default'
  }

  // 获取健康状态文本
  function getHealthStatusText(status: string): string {
    if (status === 'healthy') return '正常'
    if (status === 'unhealthy') return '异常'
    return '未知'
  }

  return {
    formatQuota,
    formatRelativeTime,
    formatDate,
    formatDateTime,
    formatShortDate,
    formatPercent,
    formatNumber,
    parseModels,
    getHealthStatusType,
    getHealthStatusText
  }
}
