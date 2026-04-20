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
  if (e instanceof ApiError) return e.message || fallback
  if (e instanceof Error) return e.message || fallback
  if (typeof e === 'string') return e || fallback
  return fallback
}

export function notifyApiError(e: unknown, fallback = '操作失败'): void {
  const notify = (window as unknown as { $notify?: (msg: string, type: string) => void }).$notify
  notify?.(apiError(e, fallback), 'error')
}
