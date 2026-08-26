/**
 * 浮层交互三件套：焦点陷阱、Esc 关闭、外部点击关闭。
 *
 * 拆成三个独立 composable 而不是一个大的，因为不同浮层需要的组合不同：
 * - modal / drawer：三个都要
 * - dropdown / select：外部点击 + Esc，不要焦点陷阱（要能 Tab 出去）
 * - tooltip：都不要
 */
import { onScopeDispose, watch, type Ref } from 'vue'

const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function focusableIn(root: HTMLElement): HTMLElement[] {
  return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
    el => el.offsetWidth > 0 || el.offsetHeight > 0 || el === document.activeElement,
  )
}

/**
 * 焦点陷阱。打开时把焦点移进去，关闭时还回原处。
 *
 * 同时给 `#app` 加 `inert`，这样屏幕阅读器和 Tab 都不会跑到背景内容上 ——
 * 只靠 JS 拦 Tab 键是不够的（触屏辅助技术能绕过）。
 */
export function useFocusTrap(active: Ref<boolean>, container: Ref<HTMLElement | null | undefined>) {
  let restore: HTMLElement | null = null

  function onKeydown(event: KeyboardEvent) {
    if (event.key !== 'Tab' || !container.value) return
    const items = focusableIn(container.value)
    if (!items.length) {
      event.preventDefault()
      return
    }
    const first = items[0]
    const last = items[items.length - 1]
    const current = document.activeElement as HTMLElement | null

    if (event.shiftKey && (current === first || !container.value.contains(current))) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && current === last) {
      event.preventDefault()
      first.focus()
    }
  }

  function setBackgroundInert(on: boolean) {
    const app = document.getElementById('app')
    if (!app) return
    // 浮层是 Teleport 到 body 的，所以让整个 #app 失活是安全的
    if (on) app.setAttribute('inert', '')
    else app.removeAttribute('inert')
  }

  watch(active, async isActive => {
    if (isActive) {
      restore = document.activeElement as HTMLElement | null
      setBackgroundInert(true)
      document.addEventListener('keydown', onKeydown, true)
      // 等浮层内容挂上再找可聚焦元素
      await new Promise(resolve => requestAnimationFrame(resolve))
      if (container.value) {
        const items = focusableIn(container.value)
        ;(items[0] ?? container.value).focus()
      }
    } else {
      document.removeEventListener('keydown', onKeydown, true)
      setBackgroundInert(false)
      restore?.focus?.()
      restore = null
    }
  })

  onScopeDispose(() => {
    document.removeEventListener('keydown', onKeydown, true)
    setBackgroundInert(false)
  })
}

/** Esc 关闭。`enabled` 为 false 时不监听。 */
export function useEscapeKey(enabled: Ref<boolean>, onEscape: () => void) {
  function handler(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      event.stopPropagation()
      onEscape()
    }
  }

  watch(enabled, on => {
    if (on) document.addEventListener('keydown', handler, true)
    else document.removeEventListener('keydown', handler, true)
  })

  onScopeDispose(() => document.removeEventListener('keydown', handler, true))
}

/**
 * 点击浮层与锚点之外时关闭。
 *
 * 用 pointerdown 而不是 click：click 会在 mousedown 已经改变 DOM 后才触发，
 * 导致 `contains()` 判断失效（元素已被移除）。
 */
export function useOutsidePointer(
  enabled: Ref<boolean>,
  elements: Array<Ref<HTMLElement | null | undefined>>,
  onOutside: () => void,
) {
  function handler(event: PointerEvent) {
    const target = event.target as Node | null
    if (!target) return
    for (const el of elements) {
      if (el.value?.contains(target)) return
    }
    onOutside()
  }

  watch(enabled, on => {
    if (on) {
      // 延后一帧绑定，避免"打开浮层的那次点击"立刻把它关掉
      requestAnimationFrame(() => document.addEventListener('pointerdown', handler, true))
    } else {
      document.removeEventListener('pointerdown', handler, true)
    }
  })

  onScopeDispose(() => document.removeEventListener('pointerdown', handler, true))
}

/**
 * 锁滚动。多个浮层同时打开时用计数器，避免先关的那个把锁提前解掉。
 */
let lockCount = 0
let savedPaddingRight = ''

export function useScrollLock(active: Ref<boolean>) {
  function lock() {
    if (lockCount++ > 0) return
    const gap = window.innerWidth - document.documentElement.clientWidth
    savedPaddingRight = document.body.style.paddingRight
    document.body.style.overflow = 'hidden'
    // 补上滚动条宽度，否则锁定瞬间页面会横向跳一下
    if (gap > 0) document.body.style.paddingRight = `${gap}px`
  }

  function unlock() {
    if (lockCount === 0) return
    if (--lockCount > 0) return
    document.body.style.overflow = ''
    document.body.style.paddingRight = savedPaddingRight
  }

  watch(active, on => (on ? lock() : unlock()))
  onScopeDispose(() => { if (active.value) unlock() })
}
