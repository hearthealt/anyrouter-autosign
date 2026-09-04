<template>
  <UiLoading :show="loading">
    <div class="settings-pane">
      <div class="pane-head">
        <div class="pane-heading">
          <div class="pane-title"><Info :size="15" />关于</div>
          <div class="pane-desc">版本信息与在线更新</div>
        </div>
        <div class="pane-actions">
          <UiButton size="small" :loading="checking" @click="checkLatest(true)">
            <template #icon><CloudDownload :size="14" /></template>
            检查更新
          </UiButton>
          <template v-if="canUpdate">
            <UiButton size="small" type="primary" @click="confirmingUpdate = true">
              <template #icon><RefreshCw :size="14" /></template>
              更新并重启
            </UiButton>
            <UiModal
              v-model:show="confirmingUpdate"
              preset="dialog"
              title="确认更新并重启"
              content="更新会在后台执行，页面将每 3 秒检查服务状态。确认新版本服务恢复后会自动刷新页面，最长等待约 3 分钟。确定继续吗？"
              positive-text="确定更新"
              negative-text="取消"
              :mask-closable="false"
              @positive-click="confirmUpdate"
            />
          </template>
          <UiButton v-else size="small" disabled>
            <template #icon><RefreshCw :size="14" /></template>
            更新并重启
          </UiButton>
        </div>
      </div>

      <div class="version-panel">
        <div class="version-cell">
          <span class="version-label">当前版本</span>
          <strong class="version-tag mono">{{ currentTag || '—' }}</strong>
        </div>
        <div class="version-cell">
          <span class="version-label">最新版本</span>
          <span v-if="latestError" class="version-error">{{ latestError }}</span>
          <strong v-else class="version-tag mono">{{ latestTag || '未检查' }}</strong>
        </div>
        <div class="version-cell">
          <span class="version-label">状态</span>
          <span v-if="hasNewVersion" class="version-state is-new">有新版本可用</span>
          <span v-else-if="checked && !latestError" class="version-state is-ok">已是最新</span>
          <span v-else class="version-state">未检查</span>
        </div>
        <div class="version-cell">
          <span class="version-label">更新日志</span>
          <ExternalLink :href="version?.changelog_url" label="在 GitHub 查看" />
        </div>
      </div>

      <div v-if="changelog" class="pane-section">
        <div class="pane-section-title">云端更新日志</div>
        <pre class="changelog">{{ changelog }}</pre>
      </div>
    </div>

    <UiModal :show="updating" bare :width="420" :mask-closable="false" :close-on-esc="false">
      <div class="update-overlay">
        <UiLoading :size="28" />
        <div class="update-title">{{ updateStage }}</div>
        <div class="update-hint">{{ updateHint }}</div>
        <div class="update-actions">
          <div v-if="reloadCountdown > 0" class="update-countdown">
            <strong>{{ reloadCountdown }}</strong>
            <span>{{ canManualReload ? '秒，仍未确认服务恢复' : '秒，正在确认服务恢复' }}</span>
          </div>
          <UiButton v-if="canManualReload" size="small" @click="reloadPage">立即刷新</UiButton>
        </div>
      </div>
    </UiModal>
  </UiLoading>
</template>

<script setup lang="ts">
import { UiButton, UiLoading, UiModal } from '../../ui'
import { computed, onMounted, ref } from 'vue'
import { CloudDownload, Info, RefreshCw } from 'lucide-vue-next'
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
  canManualReload,
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
/** 版本读数：四格并排，窄屏自动折行 */
.version-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(168px, 1fr));
  gap: 1px;
  overflow: hidden;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-lg);
  background: var(--line-faint);
}

.version-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px;
  background: var(--surface-raised);
}

.version-label {
  color: var(--ink-faint);
  font-size: var(--fn-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-caps);
  text-transform: uppercase;
}

.version-tag {
  color: var(--ink-max);
  font-size: var(--fn-lg);
  font-weight: var(--weight-semibold);
}

.version-error {
  color: var(--warn);
  font-size: var(--fn-xs);
  line-height: 1.5;
}

.version-state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--ink-muted);
  font-size: var(--fn-sm);
  font-weight: var(--weight-medium);
}

.version-state::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: var(--r-full);
  background: currentColor;
}

.version-state.is-ok { color: var(--ok); }
.version-state.is-new { color: var(--warn); }

.mono {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.changelog {
  max-height: 340px;
  margin: 0;
  padding: 14px;
  overflow: auto;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-md);
  background: var(--surface-inset);
  color: var(--ink);
  font-family: var(--font-mono);
  font-size: var(--fn-xs);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.update-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--s3);
  width: 100%;
  min-width: 0;
  min-height: 0;
  max-height: inherit;
  padding: var(--s6);
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
  text-align: center;
}

.update-title {
  color: var(--ink-max);
  font-size: var(--fn-lg);
  font-weight: var(--weight-semibold);
}

.update-hint {
  color: var(--ink-muted);
  font-size: var(--fn-sm);
  line-height: var(--leading-loose);
}

.update-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--s2);
  margin-top: var(--s2);
}

.update-countdown {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  color: var(--signal-deep);
  font-size: var(--fn-sm);
}

.update-countdown strong {
  font-family: var(--font-mono);
  font-size: var(--fn-lg);
}
</style>
