<template>
  <n-popover
    trigger="click"
    placement="bottom-end"
    :width="320"
    :show="notificationsOpen"
    @update:show="handleToggle"
  >
    <template #trigger>
      <n-badge :value="unreadCount" :max="99" :show="unreadCount > 0" :offset="[-2, 4]">
        <n-button quaternary size="small" class="icon-btn" aria-label="通知中心">
          <template #icon><n-icon :size="16"><NotificationsOutline /></n-icon></template>
        </n-button>
      </n-badge>
    </template>
    <div class="notification-panel">
      <div class="notification-header">
        <span>通知中心</span>
        <n-button text size="tiny" @click="clearNotifications">清空</n-button>
      </div>
      <div class="notification-list" v-if="notifications.length > 0">
        <div
          v-for="(notif, index) in notifications"
          :key="notif.id || index"
          class="notification-item"
          :class="{ clickable: !!notif.route }"
          @click="handleNotificationClick(notif)"
        >
          <div class="notif-icon" :class="notif.type">
            <n-icon :size="12">
              <CheckmarkCircleOutline v-if="notif.type === 'success'" />
              <AlertCircleOutline v-else-if="notif.type === 'warning'" />
              <CloseCircleOutline v-else-if="notif.type === 'error'" />
              <InformationCircleOutline v-else />
            </n-icon>
          </div>
          <div class="notif-content">
            <div class="notif-title">{{ notif.title }}</div>
            <div class="notif-time">{{ notif.time }}</div>
          </div>
          <n-button
            text
            size="tiny"
            @click.stop="notifications.splice(index, 1)"
            class="notif-close"
            aria-label="移除此通知"
          >
            <template #icon><n-icon :size="12"><CloseOutline /></n-icon></template>
          </n-button>
        </div>
      </div>
      <div class="notification-empty" v-else>
        <n-icon :size="24" color="var(--text-quaternary)"><NotificationsOffOutline /></n-icon>
        <span>暂无通知</span>
      </div>
    </div>
  </n-popover>

  <Teleport to="body">
    <div class="toast-stack">
      <transition-group name="toast">
        <div
          v-for="toast in visibleToasts"
          :key="toast.id"
          class="toast-item"
          :class="toast.type"
          @click="dismissToast(toast.id)"
        >
          <div class="toast-icon">
            <n-icon :size="14">
              <CheckmarkCircleOutline v-if="toast.type === 'success'" />
              <AlertCircleOutline v-else-if="toast.type === 'warning'" />
              <CloseCircleOutline v-else-if="toast.type === 'error'" />
              <InformationCircleOutline v-else />
            </n-icon>
          </div>
          <div class="toast-title">{{ toast.title }}</div>
          <n-button
            text
            size="tiny"
            class="toast-close"
            @click.stop="dismissToast(toast.id)"
            aria-label="关闭"
          >
            <template #icon><n-icon :size="12"><CloseOutline /></n-icon></template>
          </n-button>
        </div>
      </transition-group>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NotificationsOutline, NotificationsOffOutline,
  CheckmarkCircleOutline, AlertCircleOutline, CloseCircleOutline,
  CloseOutline, InformationCircleOutline
} from '@vicons/ionicons5'

type NotificationTone = 'success' | 'warning' | 'error' | 'info'

interface NotifyOptions {
  duration?: number
  route?: string
}

interface NotificationItem {
  id: string
  type: NotificationTone
  title: string
  time: string
  route?: string
}

declare global {
  interface Window {
    $notify: (
      title: string,
      type?: NotificationTone,
      durationOrOptions?: number | NotifyOptions,
      options?: NotifyOptions
    ) => void
  }
}

const route = useRoute()
const router = useRouter()

const notificationsOpen = ref(false)
const unreadCount = ref(0)
const notifications = ref<NotificationItem[]>([])
const visibleToasts = ref<Array<{ id: string; type: NotificationTone; title: string }>>([])

const clearNotifications = () => {
  notifications.value = []
  unreadCount.value = 0
}

const dismissToast = (id: string) => {
  visibleToasts.value = visibleToasts.value.filter(t => t.id !== id)
}

const handleToggle = (show: boolean) => {
  notificationsOpen.value = show
  if (show) unreadCount.value = 0
}

const handleNotificationClick = (notif: NotificationItem) => {
  notificationsOpen.value = false
  if (notif.route) {
    router.push(notif.route).catch(() => {})
  }
}

const normalizeNotifyOptions = (
  durationOrOptions?: number | NotifyOptions,
  options?: NotifyOptions
) => {
  if (typeof durationOrOptions === 'number') {
    return { duration: durationOrOptions, route: options?.route }
  }
  if (durationOrOptions && typeof durationOrOptions === 'object') {
    return {
      duration: durationOrOptions.duration ?? 4500,
      route: durationOrOptions.route ?? options?.route
    }
  }
  return { duration: options?.duration ?? 4500, route: options?.route }
}

const addNotification = (
  title: string,
  type: NotificationTone = 'info',
  durationOrOptions?: number | NotifyOptions,
  options?: NotifyOptions
) => {
  const normalized = normalizeNotifyOptions(durationOrOptions, options)
  const id = `notif-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const time = new Date().toLocaleTimeString()
  const targetRoute = normalized.route ?? route.fullPath ?? '/'

  notifications.value.unshift({ id, title, type, time, route: targetRoute })
  if (!notificationsOpen.value) {
    unreadCount.value += 1
  }
  if (notifications.value.length > 100) {
    notifications.value = notifications.value.slice(0, 100)
  }

  const toastDuration = normalized.duration > 0
    ? normalized.duration
    : (type === 'error' ? 8000 : type === 'warning' ? 6000 : 4500)
  visibleToasts.value.push({ id, type, title })
  if (visibleToasts.value.length > 5) {
    visibleToasts.value = visibleToasts.value.slice(visibleToasts.value.length - 5)
  }

  if (toastDuration > 0) {
    setTimeout(() => dismissToast(id), toastDuration)
  }
}

let previous: Window['$notify'] | undefined

onMounted(() => {
  previous = window.$notify
  window.$notify = addNotification
})

onBeforeUnmount(() => {
  if (previous) {
    window.$notify = previous
  }
})
</script>

<style scoped>
.notification-panel {
  overflow: hidden;
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}

.notification-list {
  max-height: 320px;
  overflow-y: auto;
}

.notification-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: var(--spacing-2);
  align-items: start;
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
  transition: background var(--transition-fast);
}

.notification-item.clickable { cursor: pointer; }
.notification-item:hover { background: var(--bg-card-hover); }
.notification-item:last-child { border-bottom: none; }

.notif-icon {
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  border-radius: 999px;
}

.notif-icon.success { background: var(--success-color-light); color: var(--success-color); }
.notif-icon.warning { background: var(--warning-color-light); color: var(--warning-color); }
.notif-icon.error { background: var(--error-color-light); color: var(--error-color); }
.notif-icon.info { background: var(--info-color-light); color: var(--info-color); }

.notif-title { color: var(--text-primary); font-size: var(--text-sm); line-height: 1.4; }
.notif-time { margin-top: 2px; color: var(--text-tertiary); font-size: var(--text-xs); }
.notif-close { opacity: 0.5; }

.notification-empty {
  display: grid;
  justify-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-8);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.toast-stack {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1100;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  pointer-events: none;
  max-width: 360px;
}

.toast-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: var(--spacing-2);
  align-items: center;
  padding: 10px var(--spacing-3);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-left: 3px solid var(--text-tertiary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  font-size: var(--text-sm);
  color: var(--text-primary);
  pointer-events: auto;
  cursor: pointer;
  min-width: 240px;
}

.toast-item.success { border-left-color: var(--success-color); }
.toast-item.warning { border-left-color: var(--warning-color); }
.toast-item.error { border-left-color: var(--error-color); }
.toast-item.info { border-left-color: var(--info-color); }

.toast-icon {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  color: var(--text-tertiary);
}

.toast-item.success .toast-icon { background: var(--success-color-light); color: var(--success-color); }
.toast-item.warning .toast-icon { background: var(--warning-color-light); color: var(--warning-color); }
.toast-item.error .toast-icon { background: var(--error-color-light); color: var(--error-color); }
.toast-item.info .toast-icon { background: var(--info-color-light); color: var(--info-color); }

.toast-title { line-height: 1.45; word-break: break-word; }
.toast-close { opacity: 0.5; color: var(--text-tertiary); }
.toast-close:hover { opacity: 1; }

.toast-enter-active,
.toast-leave-active { transition: all 0.22s ease; }

.toast-enter-from { opacity: 0; transform: translateX(20px); }
.toast-leave-to { opacity: 0; transform: translateX(20px); }
.toast-leave-active { position: absolute; right: 0; }

@media (max-width: 768px) {
  .toast-stack {
    right: 12px;
    left: 12px;
    bottom: calc(var(--tabbar-height) + 16px);
    max-width: none;
  }
  .toast-item { min-width: 0; }
}
</style>
