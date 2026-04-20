import { computed, onMounted, onUnmounted, ref } from 'vue'
import { eventsApi } from '../api'
import { getToken } from '../utils/auth'
import type { ServerEvent } from '../types'

type EventListener = (event: ServerEvent) => void

const listeners = new Set<EventListener>()
const status = ref<'idle' | 'connecting' | 'connected' | 'error'>('idle')

let source: EventSource | null = null
let usageCount = 0
let reconnectTimer: number | null = null
let reconnectAttempt = 0

const MIN_BACKOFF_MS = 1000
const MAX_BACKOFF_MS = 30000
const MAX_RECONNECT_ATTEMPTS = 10

const emitEvent = (event: ServerEvent) => {
  listeners.forEach(listener => {
    try {
      listener(event)
    } catch (error) {
      console.error('Event stream listener failed:', error)
    }
  })
}

const clearReconnectTimer = () => {
  if (reconnectTimer !== null) {
    window.clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
}

const closeSource = () => {
  if (source) {
    source.close()
    source = null
  }
}

const nextBackoff = () => {
  const base = Math.min(MAX_BACKOFF_MS, MIN_BACKOFF_MS * 2 ** reconnectAttempt)
  const jitter = Math.floor(Math.random() * 500)
  return base + jitter
}

const scheduleReconnect = () => {
  if (usageCount <= 0 || reconnectTimer !== null) return
  if (reconnectAttempt >= MAX_RECONNECT_ATTEMPTS) return
  // 页面不可见时不重连（会在 visibilitychange 回来时立即重连）
  if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return
  const delay = nextBackoff()
  reconnectAttempt += 1
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    connect()
  }, delay)
}

const registerSourceHandlers = (eventSource: EventSource) => {
  const parseEvent = (type: ServerEvent['type']) => (event: MessageEvent) => {
    try {
      const parsed = JSON.parse(event.data || '{}')
      emitEvent({
        ...parsed,
        type,
      })
    } catch (error) {
      console.error('Failed to parse server event:', error)
    }
  }

  eventSource.addEventListener('connected', parseEvent('connected'))
  eventSource.addEventListener('sign_completed', parseEvent('sign_completed'))
  eventSource.addEventListener('health_changed', parseEvent('health_changed'))
  eventSource.addEventListener('account_changed', parseEvent('account_changed'))
  eventSource.addEventListener('ping', parseEvent('ping'))
}

const connect = () => {
  if (source || usageCount <= 0) return

  const token = getToken()
  if (!token) {
    status.value = 'error'
    return
  }

  status.value = 'connecting'
  const eventSource = new EventSource(eventsApi.streamUrl(token))
  registerSourceHandlers(eventSource)

  eventSource.onopen = () => {
    status.value = 'connected'
    reconnectAttempt = 0
  }

  eventSource.onerror = () => {
    status.value = 'error'
    closeSource()
    scheduleReconnect()
  }

  source = eventSource
}

const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible' && usageCount > 0 && !source) {
    clearReconnectTimer()
    reconnectAttempt = 0
    connect()
  }
}

let visibilityBound = false
const ensureVisibilityHook = () => {
  if (visibilityBound || typeof document === 'undefined') return
  document.addEventListener('visibilitychange', handleVisibilityChange)
  visibilityBound = true
}

const release = () => {
  usageCount = Math.max(0, usageCount - 1)
  if (usageCount === 0) {
    clearReconnectTimer()
    closeSource()
    reconnectAttempt = 0
    status.value = 'idle'
  }
}

export function useEventStream(onEvent?: EventListener) {
  onMounted(() => {
    ensureVisibilityHook()
    usageCount += 1
    if (onEvent) {
      listeners.add(onEvent)
    }
    connect()
  })

  onUnmounted(() => {
    if (onEvent) {
      listeners.delete(onEvent)
    }
    release()
  })

  return {
    status: computed(() => status.value),
    connected: computed(() => status.value === 'connected')
  }
}

