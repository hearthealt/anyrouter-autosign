import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { systemApi } from '../api'
import { ApiError, apiError } from '../utils/apiError'
import { useVersionStore } from '../stores'
import type { SystemHealthInfo, UpdateResult } from '../types'

const UPDATE_STORAGE_KEY = 'anyrouter-update-state'
const DEFAULT_POLL_INTERVAL_SECONDS = 3
const DEFAULT_TIMEOUT_SECONDS = 180
const RELOAD_AFTER_READY_MS = 800

type PersistedUpdate = {
  updateId: string
  targetVersion: string
  startedAt: number
  pollIntervalSeconds: number
  timeoutSeconds: number
}

/**
 * 系统更新流程：触发 Watchtower 后轮询当前服务的健康状态和运行版本。
 *
 * 更新过程中旧容器可能被重建，Cloudflare 会暂时返回 502/503；这些响应只代表
 * 当前连接被重启打断，不代表更新失败。只有新容器返回 ready=true，或明确返回
 * failed/no_update，流程才会结束。
 */
function createSystemUpdate() {
  const versionStore = useVersionStore()
  const initialUpdate = readPersistedUpdate()
  const updating = ref(Boolean(initialUpdate))
  const updateStage = ref(initialUpdate ? '正在确认更新状态' : '')
  const updateHint = ref(initialUpdate ? '正在连接新版本服务，请稍候' : '')
  // 保留原字段名，数值改为“已等待秒数”，避免影响已有组件调用。
  const reloadCountdown = ref(initialUpdate ? elapsedSeconds(initialUpdate.startedAt) : 0)

  let activeUpdate: PersistedUpdate | null = initialUpdate
  let pollTimer: ReturnType<typeof setTimeout> | null = null
  let reloadTimer: ReturnType<typeof setTimeout> | null = null
  let pollInFlight = false
  let autoReloading = false
  let pollingEnabled = false

  const canUpdate = computed(() => (
    versionStore.checked &&
    !versionStore.checking &&
    !versionStore.error &&
    Boolean(versionStore.latestTag) &&
    versionStore.hasNewVersion &&
    !updating.value
  ))

  const reloadPage = () => window.location.reload()

  function readPersistedUpdate(): PersistedUpdate | null {
    try {
      const raw = window.sessionStorage.getItem(UPDATE_STORAGE_KEY)
      if (!raw) return null
      const parsed = JSON.parse(raw) as Partial<PersistedUpdate>
      if (
        typeof parsed.updateId !== 'string' ||
        !parsed.updateId ||
        typeof parsed.startedAt !== 'number' ||
        !Number.isFinite(parsed.startedAt)
      ) {
        return null
      }

      return {
        updateId: parsed.updateId,
        targetVersion: typeof parsed.targetVersion === 'string' ? parsed.targetVersion : '',
        startedAt: parsed.startedAt,
        pollIntervalSeconds: normalizeSeconds(parsed.pollIntervalSeconds, DEFAULT_POLL_INTERVAL_SECONDS),
        timeoutSeconds: normalizeSeconds(parsed.timeoutSeconds, DEFAULT_TIMEOUT_SECONDS)
      }
    } catch {
      return null
    }
  }

  function persistUpdate(update: PersistedUpdate) {
    activeUpdate = update
    try {
      window.sessionStorage.setItem(UPDATE_STORAGE_KEY, JSON.stringify(update))
    } catch {
      // sessionStorage 不可用时仍然可以在当前页面内继续轮询。
    }
  }

  function clearPersistedUpdate() {
    activeUpdate = null
    try {
      window.sessionStorage.removeItem(UPDATE_STORAGE_KEY)
    } catch {
      // 忽略浏览器存储不可用的情况。
    }
  }

  function normalizeSeconds(value: unknown, fallback: number) {
    return typeof value === 'number' && Number.isFinite(value) && value > 0
      ? Math.max(1, Math.round(value))
      : fallback
  }

  function elapsedSeconds(startedAt: number) {
    return Math.max(0, Math.floor((Date.now() - startedAt) / 1000))
  }

  function clearPollTimer() {
    if (pollTimer) {
      clearTimeout(pollTimer)
      pollTimer = null
    }
  }

  function clearReloadTimer() {
    if (reloadTimer) {
      clearTimeout(reloadTimer)
      reloadTimer = null
    }
  }

  function clearTimers() {
    clearPollTimer()
    clearReloadTimer()
  }

  function setWaitingMessage(message: string, elapsed = activeUpdate ? elapsedSeconds(activeUpdate.startedAt) : 0) {
    reloadCountdown.value = elapsed
    updateHint.value = `${message}，已等待 ${elapsed} 秒`
  }

  function createUpdateId() {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
    return `update-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
  }

  function isTransientError(error: unknown) {
    return error instanceof ApiError && (error.status === undefined || error.status >= 500)
  }

  function schedulePoll(delayMs: number) {
    clearPollTimer()
    pollTimer = setTimeout(() => {
      pollTimer = null
      void pollUpdateStatus()
    }, Math.max(0, delayMs))
  }

  function finishAndReload() {
    const elapsed = activeUpdate ? elapsedSeconds(activeUpdate.startedAt) : reloadCountdown.value
    clearPollTimer()
    clearPersistedUpdate()
    updating.value = true
    updateStage.value = '服务已恢复，正在刷新页面'
    setWaitingMessage('已确认新版本服务恢复', elapsed)
    autoReloading = true
    clearReloadTimer()
    reloadTimer = setTimeout(() => {
      reloadTimer = null
      reloadPage()
    }, RELOAD_AFTER_READY_MS)
  }

  function stopWithError(message: string, notify = true) {
    clearTimers()
    clearPersistedUpdate()
    updating.value = false
    autoReloading = false
    updateStage.value = ''
    updateHint.value = ''
    reloadCountdown.value = 0
    if (notify) window.$notify(message, 'error')
  }

  async function pollUpdateStatus() {
    const update = activeUpdate
    if (!update || pollInFlight || autoReloading) return

    pollInFlight = true
    const elapsed = elapsedSeconds(update.startedAt)
    reloadCountdown.value = elapsed

    if (elapsed >= update.timeoutSeconds) {
      pollInFlight = false
      clearPollTimer()
      clearPersistedUpdate()
      updating.value = true
      updateStage.value = '更新仍在进行'
      setWaitingMessage('暂未确认新版本服务恢复，可稍后手动刷新', elapsed)
      return
    }

    try {
      const res = await systemApi.getHealth(update.updateId)
      const data = res.data as SystemHealthInfo
      const serverElapsed = typeof data.elapsed_seconds === 'number' ? data.elapsed_seconds : 0
      const currentElapsed = Math.max(elapsed, serverElapsed)
      reloadCountdown.value = currentElapsed

      if (data.ready === true || data.update_status === 'ready') {
        finishAndReload()
        return
      }

      if (data.update_status === 'failed') {
        stopWithError(data.message || '更新失败')
        return
      }

      if (data.update_status === 'no_update') {
        stopWithError(data.message || '未发现可更新的镜像', false)
        window.$notify(data.message || '未发现可更新的镜像', 'info')
        return
      }

      updateStage.value = data.update_status === 'updating'
        ? '正在拉取新镜像并重启服务'
        : '正在等待新版本服务恢复'
      setWaitingMessage(data.message || '服务正在更新，请稍候', currentElapsed)
    } catch (error) {
      // 502/503/网络超时都可能是容器正在重启，继续轮询直到达到超时上限。
      const currentElapsed = elapsedSeconds(update.startedAt)
      reloadCountdown.value = currentElapsed
      updateStage.value = '正在等待新版本服务恢复'
      setWaitingMessage(
        isTransientError(error) ? '服务正在重启，暂时无法连接' : '暂时无法确认服务状态',
        currentElapsed
      )
    } finally {
      pollInFlight = false
      if (activeUpdate === update && updating.value && !autoReloading && pollingEnabled) {
        const currentElapsed = elapsedSeconds(update.startedAt)
        if (currentElapsed >= update.timeoutSeconds) {
          clearPersistedUpdate()
          updateStage.value = '更新仍在进行'
          setWaitingMessage('暂未确认新版本服务恢复，可稍后手动刷新', currentElapsed)
        } else {
          schedulePoll(update.pollIntervalSeconds * 1000)
        }
      }
    }
  }

  function beginPolling(update: PersistedUpdate) {
    clearTimers()
    persistUpdate(update)
    updating.value = true
    pollingEnabled = true
    autoReloading = false
    updateStage.value = '正在等待新版本服务恢复'
    setWaitingMessage('更新任务已创建，正在确认服务状态')
    void pollUpdateStatus()
  }

  const doUpdate = async () => {
    if (activeUpdate) {
      beginPolling(activeUpdate)
      return
    }

    // 前端按钮会根据该条件禁用，后端也会再次校验正式 Release。
    if (!canUpdate.value) {
      if (versionStore.error) {
        window.$notify(versionStore.error, 'warning')
      } else if (versionStore.checked && !versionStore.hasNewVersion) {
        window.$notify(`当前已是最新版本 ${versionStore.currentTag}`, 'info')
      } else {
        window.$notify('请先成功检查更新，再执行更新并重启', 'info')
      }
      return
    }

    const update: PersistedUpdate = {
      updateId: createUpdateId(),
      targetVersion: versionStore.latestTag,
      startedAt: Date.now(),
      pollIntervalSeconds: DEFAULT_POLL_INTERVAL_SECONDS,
      timeoutSeconds: DEFAULT_TIMEOUT_SECONDS
    }
    // 先保存前端生成的任务 ID，但要等创建接口返回后再开始轮询，避免第一次
    // 健康请求与创建任务请求并发，导致旧的轮询结果覆盖新任务的定时器。
    clearTimers()
    persistUpdate(update)
    updating.value = true
    pollingEnabled = true
    autoReloading = false
    reloadCountdown.value = 0
    updateStage.value = '正在创建更新任务'
    updateHint.value = '正在通知服务器执行更新，请稍候'

    try {
      const res = await systemApi.triggerUpdate(update.updateId)
      const result = res.data as UpdateResult

      if (result.status !== 'triggered') {
        stopWithError(result.message || '无法创建更新任务', result.status !== 'no_update')
        if (result.status === 'no_update') {
          window.$notify(result.message || '当前已是最新版本', 'info')
        }
        return
      }

      beginPolling({
        ...update,
        updateId: result.update_id || update.updateId,
        targetVersion: result.target_version || update.targetVersion,
        pollIntervalSeconds: normalizeSeconds(result.poll_interval_seconds, update.pollIntervalSeconds),
        timeoutSeconds: normalizeSeconds(result.timeout_seconds, update.timeoutSeconds)
      })
    } catch (error) {
      // 触发请求可能正好撞上旧容器重启。保留任务 ID，继续通过健康接口确认结果。
      if (isTransientError(error)) {
        updateStage.value = '正在等待新版本服务恢复'
        setWaitingMessage('更新连接被重启过程打断，正在确认更新结果')
        schedulePoll(update.pollIntervalSeconds * 1000)
        return
      }

      stopWithError(apiError(error, '触发更新失败'))
    }
  }

  function resumeFromStorage() {
    const pending = readPersistedUpdate()
    if (!pending) return
    if (activeUpdate?.updateId === pending.updateId && updating.value && pollingEnabled) return
    beginPolling(pending)
  }

  function pausePolling() {
    pollingEnabled = false
    clearTimers()
  }

  return {
    updating,
    updateStage,
    updateHint,
    reloadCountdown,
    canUpdate,
    doUpdate,
    reloadPage,
    resumeFromStorage,
    pausePolling
  }
}

let sharedSystemUpdate: ReturnType<typeof createSystemUpdate> | null = null
let mountedConsumers = 0

/**
 * 更新弹窗同时存在于 App 和设置页时，两个组件仍然共享同一个更新控制器，
 * 避免重复轮询、重复刷新，以及其中一个组件卸载后误停掉另一个组件的任务。
 */
export function useSystemUpdate() {
  const controller = sharedSystemUpdate ?? (sharedSystemUpdate = createSystemUpdate())

  onMounted(() => {
    mountedConsumers += 1
    controller.resumeFromStorage()
  })

  onBeforeUnmount(() => {
    mountedConsumers = Math.max(0, mountedConsumers - 1)
    if (mountedConsumers === 0) controller.pausePolling()
  })

  return controller
}
