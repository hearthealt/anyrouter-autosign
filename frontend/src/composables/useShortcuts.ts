import { onMounted, onUnmounted, ref } from 'vue'

export interface ShortcutBinding {
  /** 组合键，支持 ctrl/cmd/shift/alt，分隔符 + 。例如 'mod+k' 'shift+?' */
  key: string
  description: string
  handler: (e: KeyboardEvent) => void | Promise<void>
  /** 默认 false：聚焦在 input/textarea/contenteditable 时不触发 */
  allowInInput?: boolean
}

export interface ShortcutSequence {
  /** 序列键如 'g a'，由空格分隔，依次按 */
  keys: string
  description: string
  handler: () => void | Promise<void>
}

const bindings = ref<ShortcutBinding[]>([])
const sequences = ref<ShortcutSequence[]>([])

let pending: string[] = []
let pendingTimer: number | null = null

const isEditable = (el: EventTarget | null) => {
  if (!(el instanceof HTMLElement)) return false
  const tag = el.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (el.isContentEditable) return true
  return false
}

const parseKey = (binding: string): { key: string; mod: boolean; shift: boolean; alt: boolean } => {
  const parts = binding.toLowerCase().split('+').map(p => p.trim())
  const mod = parts.includes('mod') || parts.includes('ctrl') || parts.includes('cmd') || parts.includes('meta')
  const shift = parts.includes('shift')
  const alt = parts.includes('alt') || parts.includes('option')
  const keyPart = parts.find(p => !['mod', 'ctrl', 'cmd', 'meta', 'shift', 'alt', 'option'].includes(p)) || ''
  return { key: keyPart, mod, shift, alt }
}

const matchBinding = (binding: ShortcutBinding, e: KeyboardEvent): boolean => {
  const parsed = parseKey(binding.key)
  if (parsed.key !== e.key.toLowerCase()) return false
  const modPressed = e.metaKey || e.ctrlKey
  if (parsed.mod !== modPressed) return false
  if (parsed.shift !== e.shiftKey) return false
  if (parsed.alt !== e.altKey) return false
  return true
}

const handleKeyDown = (e: KeyboardEvent) => {
  const editable = isEditable(e.target)
  // 普通绑定
  for (const binding of bindings.value) {
    if (editable && !binding.allowInInput) continue
    if (matchBinding(binding, e)) {
      e.preventDefault()
      binding.handler(e)
      return
    }
  }

  // 序列（不带修饰键、纯字母或数字）
  if (editable) return
  if (e.metaKey || e.ctrlKey || e.altKey) return
  const key = e.key.toLowerCase()
  if (!/^[a-z0-9?/]$/.test(key)) return

  pending.push(key)
  if (pendingTimer) window.clearTimeout(pendingTimer)
  pendingTimer = window.setTimeout(() => {
    pending = []
  }, 900)

  const joined = pending.join(' ')
  for (const seq of sequences.value) {
    if (seq.keys.toLowerCase() === joined) {
      e.preventDefault()
      pending = []
      if (pendingTimer) window.clearTimeout(pendingTimer)
      seq.handler()
      return
    }
  }

  // 如果当前前缀不匹配任何序列前缀，清空
  const anyPrefix = sequences.value.some(s => s.keys.toLowerCase().startsWith(joined))
  if (!anyPrefix) {
    pending = []
  }
}

let mounted = false

const ensureListener = () => {
  if (mounted) return
  window.addEventListener('keydown', handleKeyDown)
  mounted = true
}

/**
 * 注册若干快捷键，组件卸载时自动移除
 */
export function useShortcuts(
  items: Array<ShortcutBinding | ShortcutSequence>
) {
  const registered: Array<() => void> = []

  onMounted(() => {
    ensureListener()
    for (const item of items) {
      if ('keys' in item) {
        sequences.value.push(item)
        registered.push(() => {
          sequences.value = sequences.value.filter(s => s !== item)
        })
      } else {
        bindings.value.push(item)
        registered.push(() => {
          bindings.value = bindings.value.filter(b => b !== item)
        })
      }
    }
  })

  onUnmounted(() => {
    registered.forEach(fn => fn())
  })
}

/**
 * 快捷键查询（给帮助弹窗用）
 */
export function listShortcuts() {
  return {
    bindings: bindings.value,
    sequences: sequences.value
  }
}
