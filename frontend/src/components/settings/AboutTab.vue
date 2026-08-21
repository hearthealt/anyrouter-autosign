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
          <template v-if="canUpdate">
            <n-button size="small" type="primary" @click="confirmingUpdate = true">
              <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
              更新并重启
            </n-button>
            <n-modal
              v-model:show="confirmingUpdate"
              preset="dialog"
              title="确认更新并重启"
              content="更新准备会随机等待 15-30 秒，成功后再等待 10 秒让服务重启并自动刷新页面。确定继续吗？"
              positive-text="确定更新"
              negative-text="取消"
              :mask-closable="false"
              @positive-click="confirmUpdate"
            />
          </template>
          <n-button v-else size="small" disabled>
            <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
            更新并重启
          </n-button>
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
          <div v-if="reloadCountdown > 0" class="update-countdown">
            <strong>{{ reloadCountdown }}</strong>
            <span>秒后自动刷新页面</span>
          </div>
          <n-button size="small" @click="reloadPage">立即刷新</n-button>
        </div>
      </div>
    </n-modal>
  </n-spin>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { CloudDownloadOutline, InformationCircleOutline, RefreshOutline } from '@vicons/ionicons5'
import { useVersionStore } from '../../stores'
import { apiError } from '../../utils/apiError'
import { useSystemUpdate } from '../../composables/useSystemUpdate'
import ExternalLink from '../common/ExternalLink.vue'

const versionStore = useVersionStore()
const {
  updating,
  updateStage,
  updateHint,
  reloadCountdown,
  canUpdate,
  doUpdate,
  reloadPage
} = useSystemUpdate()

const loading = computed(() => versionStore.loading)
const checking = computed(() => versionStore.checking)
const checked = computed(() => versionStore.checked)
const version = computed(() => versionStore.info)
const currentTag = computed(() => versionStore.currentTag)
const latestTag = computed(() => versionStore.latestTag)
const latestError = computed(() => versionStore.error)
const changelog = computed(() => versionStore.changelog)
const hasNewVersion = computed(() => versionStore.hasNewVersion)
const confirmingUpdate = ref(false)

const confirmUpdate = () => {
  confirmingUpdate.value = false
  void doUpdate()
}

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

onMounted(async () => {
  if (!versionStore.info) await load()
  if (!versionStore.checked) await checkLatest()
})

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
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-top: var(--spacing-2);
}

.update-countdown {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  color: var(--primary-color);
  font-size: var(--text-sm);
}

.update-countdown strong {
  font-family: var(--font-mono);
  font-size: var(--text-lg);
}
</style>
