<template>
  <n-modal
    :show="show"
    :mask-closable="!updating"
    :close-on-esc="!updating"
    @update:show="(value: boolean) => emit('update:show', value)"
  >
    <div class="version-modal">
      <template v-if="updating">
        <div class="update-state">
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
      </template>

      <template v-else>
        <div class="modal-head">
          <div class="modal-title-wrap">
            <div class="modal-icon"><n-icon :size="18"><InformationCircleOutline /></n-icon></div>
            <div>
              <h3>版本信息</h3>
              <p>检查正式发布版本并直接更新</p>
            </div>
          </div>
          <n-button text aria-label="关闭" @click="close">
            <template #icon><n-icon :size="18"><CloseOutline /></n-icon></template>
          </n-button>
        </div>

        <div class="modal-body">
          <div class="version-grid">
            <div class="version-row">
              <span class="row-label">当前版本</span>
              <span class="version-value mono">{{ currentTag || '加载中…' }}</span>
            </div>
            <div class="version-row">
              <span class="row-label">最新正式版本</span>
              <span v-if="latestError" class="version-error">{{ latestError }}</span>
              <span v-else-if="checking" class="version-value">检查中…</span>
              <span v-else class="version-value mono">{{ latestTag || '未检查' }}</span>
            </div>
          </div>

          <div v-if="hasNewVersion" class="release-badge">
            <n-icon :size="16"><CloudDownloadOutline /></n-icon>
            <span>发现新版本 {{ latestTag }}</span>
          </div>
          <div v-else-if="checked && !latestError" class="release-badge is-latest">
            <n-icon :size="16"><CheckmarkCircleOutline /></n-icon>
            <span>当前已是最新正式版本</span>
          </div>

          <div v-if="changelog" class="changelog-section">
            <div class="section-title">更新日志</div>
            <pre class="changelog">{{ changelog }}</pre>
          </div>
        </div>

        <div class="modal-footer">
          <ExternalLink :href="version?.changelog_url" label="在 GitHub 查看完整日志" />
          <div class="footer-actions">
            <n-button size="small" :loading="checking" @click="checkLatest(true)">
              <template #icon><n-icon :size="14"><CloudDownloadOutline /></n-icon></template>
              检查更新
            </n-button>
            <template v-if="canUpdate">
              <n-button
                size="small"
                type="primary"
                @click="confirmingUpdate = true"
              >
                <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
                更新并重启
              </n-button>
              <n-modal
                v-model:show="confirmingUpdate"
                preset="dialog"
                title="确认更新并重启"
                content="将拉取最新镜像并重建容器，服务会中断约 10 秒。确定继续吗？"
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
      </template>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  CheckmarkCircleOutline,
  CloudDownloadOutline,
  CloseOutline,
  InformationCircleOutline,
  RefreshOutline
} from '@vicons/ionicons5'
import ExternalLink from '../common/ExternalLink.vue'
import { useVersionStore } from '../../stores'
import { apiError } from '../../utils/apiError'
import { useSystemUpdate } from '../../composables/useSystemUpdate'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{ (e: 'update:show', value: boolean): void }>()

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

const close = () => {
  if (updating.value) return
  updating.value = false
  emit('update:show', false)
}

watch(
  () => props.show,
  async (visible) => {
    if (!visible) return
    if (!versionStore.info && !loading.value) await load()
    if (!versionStore.checked && !checking.value) await checkLatest()
  },
  { immediate: true }
)
</script>

<style scoped>
.version-modal {
  width: min(92vw, 560px);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-head,
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
}

.modal-head {
  border-bottom: 1px solid var(--border-color-light);
}

.modal-title-wrap {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  min-width: 0;
}

.modal-icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: var(--radius-sm);
  background: var(--primary-color-light);
  color: var(--primary-color);
}

.modal-head h3 {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.modal-head p {
  margin: 3px 0 0;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
  padding: var(--spacing-4);
}

.version-grid {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.version-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-3);
  min-height: 24px;
}

.row-label {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.version-value {
  color: var(--text-primary);
  font-size: var(--text-sm);
  text-align: right;
}

.version-error {
  max-width: 68%;
  color: var(--warning-color);
  font-size: var(--text-xs);
  line-height: 1.5;
  text-align: right;
}

.mono {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.release-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-sm);
  background: var(--primary-color-light);
  color: var(--primary-color);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.release-badge.is-latest {
  background: var(--success-color-light);
  color: var(--success-color);
}

.changelog-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.section-title {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.changelog {
  max-height: 260px;
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

.modal-footer {
  align-items: flex-end;
  border-top: 1px solid var(--border-color-light);
}

.footer-actions {
  display: flex;
  flex-shrink: 0;
  gap: var(--spacing-2);
}

.update-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-3);
  width: 100%;
  min-height: 220px;
  box-sizing: border-box;
  padding: var(--spacing-6);
  text-align: center;
}

.update-title {
  color: var(--text-primary);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
}

.update-hint {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
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
  font-size: var(--text-lg);
  font-family: var(--font-mono);
}

@media (max-width: 560px) {
  .modal-footer {
    align-items: stretch;
    flex-direction: column;
  }

  .footer-actions {
    justify-content: flex-end;
  }
}
</style>
