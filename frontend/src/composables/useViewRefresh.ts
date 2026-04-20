import { inject, onMounted, onUnmounted, provide, ref, type Ref } from 'vue'

const REFRESH_KEY = Symbol('view-refresh')

type Handler = () => void | Promise<void>

interface RefreshBus {
  trigger: () => Promise<void>
  register: (handler: Handler) => void
  unregister: (handler: Handler) => void
  refreshing: Ref<boolean>
}

export function provideViewRefresh(): RefreshBus {
  const handlers = new Set<Handler>()
  const refreshing = ref(false)

  const bus: RefreshBus = {
    refreshing,
    register(handler: Handler) {
      handlers.add(handler)
    },
    unregister(handler: Handler) {
      handlers.delete(handler)
    },
    async trigger() {
      if (refreshing.value) return
      refreshing.value = true
      try {
        await Promise.all(Array.from(handlers).map(h => Promise.resolve(h())))
      } finally {
        refreshing.value = false
      }
    }
  }

  provide(REFRESH_KEY, bus)
  return bus
}

/**
 * 在当前视图注册刷新回调。视图卸载时自动移除。
 */
export function useViewRefresh(handler: Handler) {
  const bus = inject<RefreshBus | null>(REFRESH_KEY, null)
  if (!bus) return

  onMounted(() => bus.register(handler))
  onUnmounted(() => bus.unregister(handler))
}

/**
 * 获取当前刷新总线（通常在主框架里使用）。
 */
export function useRefreshBus() {
  return inject<RefreshBus | null>(REFRESH_KEY, null)
}
