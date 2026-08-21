<template>
  <n-spin :show="loading">
    <div class="about-grid">
      <div class="setting-card">
        <div class="setting-card-header">
          <div class="setting-card-icon version">
            <n-icon :size="20"><InformationCircleOutline /></n-icon>
          </div>
          <div class="setting-card-title">
            <span>版本信息</span>
            <n-tag v-if="hasNewVersion" size="small" type="warning">有新版本</n-tag>
            <n-tag v-else-if="checked && !latestError" size="small" type="success">已是最新</n-tag>
          </div>
        </div>

        <div class="setting-card-body">
          <div class="setting-row">
            <span class="setting-row-label">当前版本</span>
            <span class="version-value mono">{{ currentTag || '—' }}</span>
          </div>
          <div class="setting-row">
            <span class="setting-row-label">最新版本</span>
            <span v-if="latestError" class="version-error">{{ latestError }}</span>
            <span v-else class="version-value mono">{{ latestTag || '未检查' }}</span>
          </div>
          <div class="setting-row">
            <span class="setting-row-label">更新日志</span>
            <ExternalLink :href="version?.changelog_url" label="在 GitHub 查看" />
          </div>
        </div>

        <div class="setting-card-footer actions">
          <n-button size="small" :loading="checking" @click="checkLatest(true)">
            <template #icon><n-icon :size="14"><CloudDownloadOutline /></n-icon></template>
            检查更新
          </n-button>
          <n-popconfirm @positive-click="doUpdate">
            <template #trigger>
              <n-button size="small" :type="hasNewVersion ? 'primary' : 'default'" :disabled="updating">
                <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
                更新并重启
              </n-button>
            </template>
            拉取最新镜像并重建容器，服务会中断约 10-30 秒。确定继续？
          </n-popconfirm>
        </div>
      </div>

      <div v-if="changelog" class="setting-card">
        <div class="setting-card-header">
          <div class="setting-card-title"><span>云端更新日志</span></div>
        </div>
        <div class="setting-card-body">
          <pre class="changelog">{{ changelog }}</pre>
        </div>
      </div>
    </div>

    <n-modal :show="updating" :mask-closable="false" :close-on-esc="false">
      <div class="update-overlay">
        <n-spin :size="28" />
        <div class="update-title">{{ updateStage }}</div>
        <div class="update-hint">{{ updateHint }}</div>
        <div class="update-actions">
          <n-button size="small" @click="reloadPage">手动刷新</n-button>
          <n-button v-if="updateSettled" size="small" quaternary @click="updating = false">关闭</n-button>
        </div>
      </div>
    </n-modal>
  </n-spin>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { CloudDownloadOutline, InformationCircleOutline, RefreshOutline } from '@vicons/ionicons5'
import { systemApi } from '../../api'
import { useVersionStore } from '../../stores'
import { apiError } from '../../utils/apiError'
import ExternalLink from '../common/ExternalLink.vue'
import type { UpdateResult } from '../../types'

const POLL_INTERVAL = 2000
/** 触发后多久还没观察到服务中断，就认为更新没有真的发生 */
const DOWN_TIMEOUT = 30_000
/** 服务中断后等待恢复的上限 */
const UP_TIMEOUT = 180_000

const versionStore = useVersionStore()

const updating = ref(false)
const updateSettled = ref(false)
const updateStage = ref('')
const updateHint = ref('')

let pollTimer: ReturnType<typeof setTimeout> | null = null

const loading = computed(() => versionStore.loading)
const checking = computed(() => versionStore.checking)
const checked = computed(() => versionStore.checked)
const version = computed(() => versionStore.info)
const currentTag = computed(() => versionStore.currentTag)
const latestTag = computed(() => versionStore.latestTag)
const latestError = computed(() => versionStore.error)
const changelog = computed(() => versionStore.changelog)
const hasNewVersion = computed(() => versionStore.hasNewVersion)

const load = async () => {
  try {
    await versionStore.loadVersion()
  } catch (e) {
    window.$notify(apiError(e, '获取版本信息失败'), 'error')
  }
}

const checkLatest = async (notify = false) => {
  await versionStore.checkLatest()

  if (!notify) return

  if (versionStore.error) {
    window.$notify(versionStore.error, 'warning')
  } else if (versionStore.hasNewVersion) {
    window.$notify(`发现新版本 ${versionStore.latestTag}`, 'info')
  } else {
    window.$notify(`当前已是最新版本 ${versionStore.currentTag}`, 'success')
  }
}

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

onMounted(async () => {
  if (!versionStore.info) await load()
  if (!versionStore.checked) await checkLatest()
})

onBeforeUnmount(clearPoll)

defineExpose({ load })
</script>

<style scoped>
.about-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.setting-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
}

.setting-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.setting-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--primary-color-light);
  color: var(--primary-color);
}

.setting-card-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.setting-card-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  min-height: 24px;
}

.setting-row-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.version-value {
  color: var(--text-primary);
}

.version-error {
  font-size: var(--text-xs);
  color: var(--warning-color);
  text-align: right;
}

.mono {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.setting-card-footer.actions {
  display: flex;
  gap: var(--spacing-2);
  margin-top: var(--spacing-4);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--border-color-light);
}

.changelog {
  max-height: 320px;
  margin: 0;
  padding: var(--spacing-3);
  overflow: auto;
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.update-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-3);
  width: min(420px, calc(100vw - 32px));
  padding: var(--spacing-6);
  background: var(--bg-modal);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  text-align: center;
}

.update-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.update-hint {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  line-height: 1.6;
}

.update-actions {
  display: flex;
  gap: var(--spacing-2);
  margin-top: var(--spacing-2);
}
</style>
