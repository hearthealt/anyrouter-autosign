import { computed, onBeforeUnmount, ref } from 'vue'
import { systemApi } from '../api'
import { ApiError, apiError } from '../utils/apiError'
import { useVersionStore } from '../stores'
import type { UpdateResult } from '../types'

/** 更新触发后预留给新容器启动的时间。倒计时结束后统一刷新页面。 */
const RELOAD_DELAY_SECONDS = 30

/**
 * 系统更新流程：调用 watchtower 后等待新容器启动，再刷新当前页面。
 * 通过 Cloudflare 访问时，旧容器被重建会导致请求返回 502；这属于更新过程中的
 * 预期断连，不能直接当成更新失败。
 */
export function useSystemUpdate() {
  const versionStore = useVersionStore()
  const updating = ref(false)
  const updateStage = ref('')
  const updateHint = ref('')
  const reloadCountdown = ref(0)

  let countdownTimer: ReturnType<typeof setInterval> | null = null

  const canUpdate = computed(() => (
    versionStore.checked &&
    !versionStore.checking &&
    !versionStore.error &&
    Boolean(versionStore.latestTag) &&
    versionStore.hasNewVersion &&
    !updating.value
  ))

  const reloadPage = () => window.location.reload()

  const clearCountdown = () => {
    if (countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }

  const startReloadCountdown = (hint = '服务正在重启，请等待倒计时结束') => {
    clearCountdown()
    updating.value = true
    updateStage.value = '更新已触发'

    const deadline = Date.now() + RELOAD_DELAY_SECONDS * 1000

    const tick = () => {
      const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
      reloadCountdown.value = remaining
      updateHint.value = `${hint}，${remaining} 秒后自动刷新页面`

      if (remaining <= 0) {
        clearCountdown()
        updateStage.value = '更新完成，正在刷新页面'
        reloadPage()
      }
    }

    tick()
    countdownTimer = setInterval(tick, 1000)
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
    updateStage.value = '正在触发更新'
    updateHint.value = '正在通知 watchtower 拉取新镜像'
    reloadCountdown.value = 0

    try {
      const res = await systemApi.triggerUpdate()
      const result = res.data as UpdateResult

      if (result.status === 'triggered') {
        startReloadCountdown()
        return
      }

      updating.value = false
      window.$notify(result.message, result.status === 'no_update' ? 'info' : 'error')
    } catch (e) {
      // 更新会重建当前 app 容器，Cloudflare 可能在后端来不及返回响应前给浏览器 502。
      // 此时更新通常已经成功触发，继续倒计时并刷新，而不是提示“更新失败”。
      if (e instanceof ApiError && e.status === 502) {
        startReloadCountdown('连接在更新过程中中断，更新通常已经开始')
        return
      }

      updating.value = false
      window.$notify(apiError(e, '触发更新失败'), 'error')
    }
  }

  onBeforeUnmount(() => {
    clearCountdown()
  })

  return {
    updating,
    updateStage,
    updateHint,
    reloadCountdown,
    canUpdate,
    doUpdate,
    reloadPage
  }
}
