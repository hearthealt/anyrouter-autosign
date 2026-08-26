/**
 * 动效偏好 —— 系统设置与用户开关的合并结果。
 *
 * 两个来源：
 * 1. `prefers-reduced-motion: reduce`（操作系统）
 * 2. localStorage 里的显式开关（设置页可关）—— 显式开关优先级更高
 *
 * design/motion.ts 里所有动效入口都读这里。关掉之后动效不是"变快"，
 * 而是**直接跳到终态**，避免留下半截动画。
 */
import { computed, ref, type ComputedRef } from 'vue'

const STORAGE_KEY = 'anyrouter-motion'

export type MotionSetting = 'full' | 'reduced' | 'system'

const setting = ref<MotionSetting>(readSetting())
const systemReduced = ref(matchSystemReduced())

function readSetting(): MotionSetting {
  const stored = localStorage.getItem(STORAGE_KEY)
  return stored === 'full' || stored === 'reduced' ? stored : 'system'
}

function matchSystemReduced(): boolean {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

if (typeof window !== 'undefined' && window.matchMedia) {
  const query = window.matchMedia('(prefers-reduced-motion: reduce)')
  const sync = () => { systemReduced.value = query.matches }
  // Safari < 14 只有 addListener
  if (query.addEventListener) query.addEventListener('change', sync)
  else query.addListener(sync)
}

/** 当前是否应当禁用装饰性动效。 */
const reduced = computed(() => {
  if (setting.value === 'reduced') return true
  if (setting.value === 'full') return false
  return systemReduced.value
})

function applyToDocument() {
  if (typeof document === 'undefined') return
  document.documentElement.dataset.motion = reduced.value ? 'reduced' : 'full'
}

applyToDocument()

export function setMotionSetting(next: MotionSetting) {
  setting.value = next
  if (next === 'system') localStorage.removeItem(STORAGE_KEY)
  else localStorage.setItem(STORAGE_KEY, next)
  applyToDocument()
}

export function useMotionPreference(): {
  setting: typeof setting
  reduced: ComputedRef<boolean>
  setMotionSetting: typeof setMotionSetting
} {
  return { setting, reduced, setMotionSetting }
}

/** 给非组件代码（motion.ts）用的同步读取，避免每次都建 computed。 */
export function motionReduced(): boolean {
  return reduced.value
}
