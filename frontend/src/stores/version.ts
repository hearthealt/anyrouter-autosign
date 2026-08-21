import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { systemApi } from '../api'
import { apiError } from '../utils/apiError'
import { isNewerVersion, normalizeVersionTag } from '../utils/version'
import type { LatestVersionInfo, VersionInfo } from '../types'

/**
 * 版本状态。侧边栏的版本标签和设置页「关于」共用，避免重复请求。
 */
export const useVersionStore = defineStore('version', () => {
  const info = ref<VersionInfo | null>(null)
  const latestVersion = ref('')
  const changelog = ref('')
  /** 取云端版本失败的可读原因 */
  const error = ref('')
  const checked = ref(false)
  const loading = ref(false)
  const checking = ref(false)

  const currentTag = computed(() => normalizeVersionTag(info.value?.version))
  const latestTag = computed(() => normalizeVersionTag(latestVersion.value))
  const hasNewVersion = computed(() => isNewerVersion(latestTag.value, currentTag.value))

  const loadVersion = async () => {
    if (loading.value) return
    loading.value = true
    try {
      const res = await systemApi.getVersion()
      info.value = res.data as VersionInfo
    } finally {
      loading.value = false
    }
  }

  /** 检查云端版本；失败不抛出，原因写进 error 由调用方决定是否提示 */
  const checkLatest = async () => {
    // App.vue 挂载时和「关于」标签打开时可能同时触发，避免重复请求 GitHub
    if (checking.value) return
    checking.value = true
    error.value = ''
    try {
      const res = await systemApi.getLatestVersion()
      const data = res.data as LatestVersionInfo
      checked.value = true

      if (data.error) {
        latestVersion.value = ''
        changelog.value = ''
        error.value = data.error
        return
      }

      latestVersion.value = data.version || ''
      changelog.value = data.changelog || ''
    } catch (e) {
      latestVersion.value = ''
      changelog.value = ''
      error.value = apiError(e, '检查更新失败')
    } finally {
      checking.value = false
    }
  }

  return {
    info,
    latestVersion,
    changelog,
    error,
    checked,
    loading,
    checking,
    currentTag,
    latestTag,
    hasNewVersion,
    loadVersion,
    checkLatest
  }
})
