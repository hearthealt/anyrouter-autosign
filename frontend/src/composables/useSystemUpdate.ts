import { computed, onBeforeUnmount, ref } from 'vue'
import { systemApi } from '../api'
import { apiError } from '../utils/apiError'
import { useVersionStore } from '../stores'
import type { UpdateResult } from '../types'

const POLL_INTERVAL = 2000
/** 触发后多久还没观察到服务中断，就认为更新没有真的发生 */
const DOWN_TIMEOUT = 30_000
/** 服务中断后等待恢复的上限 */
const UP_TIMEOUT = 180_000

/**
 * 系统更新流程：触发 watchtower 后等待当前服务先掉线、再恢复。
 * 关于页和全局版本弹窗共用，避免两个入口的更新行为不一致。
 */
export function useSystemUpdate() {
  const versionStore = useVersionStore()
  const updating = ref(false)
  const updateSettled = ref(false)
  const updateStage = ref('')
  const updateHint = ref('')

  let pollTimer: ReturnType<typeof setTimeout> | null = null

  const canUpdate = computed(() => (
    versionStore.checked &&
    !versionStore.checking &&
    !versionStore.error &&
    Boolean(versionStore.latestTag) &&
    versionStore.hasNewVersion &&
    !updating.value
  ))

  const reloadPage = () => window.location.reload()

  /** 直接用 fetch 而不是 axios：重启期间的 401/网络错误不该触发全局跳转登录 */
  const probeHealth = async (): Promise<boolean> => {
    try {
      const res = await fetch('/health', { cache: 'no-store' })
      return res.ok
    } catch {
      return false
    }
  }

  const clearPoll = () => {
    if (pollTimer) {
      clearTimeout(pollTimer)
      pollTimer = null
    }
  }

  /**
   * 等服务先掉线、再恢复，恢复后自动刷新页面。
   * 只等「恢复」是不够的：刚触发时旧容器还活着，会立刻误判成已完成。
   */
  const watchRestart = () => {
    clearPoll()
    const startedAt = Date.now()
    let sawDown = false

    const tick = async () => {
      const alive = await probeHealth()

      if (!sawDown) {
        if (!alive) {
          sawDown = true
          updateStage.value = '服务已停止，等待新容器启动'
          updateHint.value = '恢复后会自动刷新页面'
        } else if (Date.now() - startedAt > DOWN_TIMEOUT) {
          updateSettled.value = true
          updateStage.value = '未观察到服务重启'
          updateHint.value = '可能是 watchtower 容器没有运行，或者远端没有更新的镜像。可执行 docker compose logs watchtower 确认。'
          return
        }
      } else if (alive) {
        updateStage.value = '更新完成，正在刷新'
        reloadPage()
        return
      } else if (Date.now() - startedAt > UP_TIMEOUT) {
        updateSettled.value = true
        updateStage.value = '等待服务恢复超时'
        updateHint.value = '容器可能启动失败，请执行 docker compose logs app 查看原因。'
        return
      }

      pollTimer = setTimeout(tick, POLL_INTERVAL)
    }

    pollTimer = setTimeout(tick, POLL_INTERVAL)
  }

  const doUpdate = async () => {
    // 前端按钮会根据该条件禁用，后端也会再次校验正式 Release；这里再守一道门，
    // 防止检查请求尚未完成、检查失败或版本已变成最新时通过其他调用触发更新。
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

    updating.value = true
    updateSettled.value = false
    updateStage.value = '正在触发更新'
    updateHint.value = '正在通知 watchtower 拉取新镜像'

    try {
      const res = await systemApi.triggerUpdate()
      const result = res.data as UpdateResult

      if (result.status === 'triggered') {
        updateStage.value = '更新已触发'
        updateHint.value = '等待容器重启'
        watchRestart()
        return
      }

      updating.value = false
      window.$notify(result.message, result.status === 'no_update' ? 'info' : 'error')
    } catch (e) {
      updating.value = false
      window.$notify(apiError(e, '触发更新失败'), 'error')
    }
  }

  onBeforeUnmount(() => {
    clearPoll()
  })

  return {
    updating,
    updateSettled,
    updateStage,
    updateHint,
    canUpdate,
    doUpdate,
    reloadPage
  }
}
