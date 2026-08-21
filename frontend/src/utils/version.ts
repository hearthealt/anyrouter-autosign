/**
 * 版本号处理
 */

/** 统一加上 v 前缀用于展示 */
export function normalizeVersionTag(value?: string | null): string {
  const clean = String(value ?? '').trim()
  if (!clean) return ''
  return clean.startsWith('v') ? clean : `v${clean}`
}

function versionParts(value: string): number[] | null {
  const match = value.trim().match(/^v?(\d+)\.(\d+)\.(\d+)/)
  return match ? match.slice(1, 4).map(Number) : null
}

/** latest 是否比 current 新；任一侧解析不出三段版本号时返回 false（不误报有更新） */
export function isNewerVersion(latest?: string | null, current?: string | null): boolean {
  const left = versionParts(String(latest ?? ''))
  const right = versionParts(String(current ?? ''))
  if (!left || !right) return false
  for (let i = 0; i < left.length; i += 1) {
    if (left[i] > right[i]) return true
    if (left[i] < right[i]) return false
  }
  return false
}
