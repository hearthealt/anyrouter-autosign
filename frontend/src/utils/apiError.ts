export class ApiError extends Error {
  status?: number
  detail?: unknown

  constructor(message: string, status?: number, detail?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

export function apiError(e: unknown, fallback = '操作失败'): string {
  if (e instanceof ApiError) return extractErrorMessage(e.detail) || e.message || fallback
  if (e instanceof Error) {
    const value = e as Error & { response?: { data?: unknown }; detail?: unknown }
    return extractErrorMessage(value.response?.data) || extractErrorMessage(value.detail) || e.message || fallback
  }
  if (typeof e === 'string') return e || fallback
  const message = extractErrorMessage(e)
  if (message) return message
  return fallback
}

function extractErrorMessage(value: unknown): string {
  if (!value) return ''
  if (typeof value === 'string') return value.trim()
  if (Array.isArray(value)) return value.map(extractErrorMessage).filter(Boolean).join('；')
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>
    for (const key of ['detail', 'message', 'msg', 'error']) {
      const message = extractErrorMessage(record[key])
      if (message) return message
    }
  }
  return ''
}

export function notifyApiError(e: unknown, fallback = '操作失败'): void {
  const notify = (window as unknown as { $notify?: (msg: string, type: string) => void }).$notify
  notify?.(apiError(e, fallback), 'error')
}
