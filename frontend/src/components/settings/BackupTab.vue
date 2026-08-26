<template>
  <div class="card settings-panel">
    <UiLoading :show="loading">
      <div class="backup-section">
        <div class="backup-header">
          <div class="backup-header-info">
            <div class="backup-header-title">数据备份</div>
            <div class="backup-header-desc">导出或导入系统数据，用于迁移或恢复</div>
          </div>
        </div>

        <UiDivider style="margin: 16px 0;" />

        <div class="backup-stats">
          <div class="stat-item">
            <div class="stat-value">{{ backupInfo.account_count || 0 }}</div>
            <div class="stat-label">账号数量</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ backupInfo.sign_log_count || 0 }}</div>
            <div class="stat-label">签到日志</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ backupInfo.notify_channel_count || 0 }}</div>
            <div class="stat-label">推送渠道</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ backupInfo.setting_count || 0 }}</div>
            <div class="stat-label">配置项</div>
          </div>
        </div>

        <UiDivider style="margin: 16px 0;" />

        <div class="backup-action-section">
          <div class="action-info">
            <div class="action-title">导出备份</div>
            <div class="action-desc">将账号、设置、推送渠道等数据导出为 JSON 文件</div>
          </div>
          <div class="action-controls">
            <UiCheckbox v-model:checked="exportIncludeLogs">包含签到日志（最近1000条）</UiCheckbox>
            <UiCheckbox v-model:checked="exportIncludeCredentials">
              包含敏感凭证
            </UiCheckbox>
            <UiButton type="primary" @click="handleExport" :loading="exporting">
              <template #icon><Download /></template>
              导出备份
            </UiButton>
          </div>
        </div>

        <UiDivider style="margin: 16px 0;" />

        <div class="backup-action-section">
          <div class="action-info">
            <div class="action-title">导入备份</div>
            <div class="action-desc">从备份文件恢复数据（支持 JSON 格式）</div>
          </div>
          <div class="action-controls">
            <UiCheckbox v-model:checked="importOverwrite">覆盖现有数据</UiCheckbox>
            <UiFileDrop accept=".json" @select="handleImportFile">
              <UiButton :loading="importing">
                <template #icon><CloudUpload :size="14" /></template>
                选择文件导入
              </UiButton>
            </UiFileDrop>
          </div>
        </div>

        <div class="backup-tip">
          <Info />
          <span>
            默认备份不包含 Cookie、Token、登录密码、代理地址和推送渠道配置；
            勾选“包含敏感凭证”后可完整迁移，但请妥善保管导出的文件。
          </span>
        </div>
      </div>
    </UiLoading>
  </div>
</template>

<script setup lang="ts">
import { UiFileDrop, UiButton, UiCheckbox, UiDivider, UiLoading } from '../../ui'
import { ref, onMounted, watch } from 'vue'
import { CloudUpload, Download, Info } from 'lucide-vue-next'
import { backupApi } from '../../api'
import { getToken } from '../../utils/auth'
import { apiError } from '../../utils/apiError'

const emit = defineEmits<{
  (e: 'update:account-count', v: number): void
}>()

const loading = ref(false)
const backupInfo = ref<any>({})
const exportIncludeLogs = ref(false)
const exportIncludeCredentials = ref(false)
const exporting = ref(false)
const importOverwrite = ref(false)
const importing = ref(false)

watch(() => backupInfo.value.account_count, v => emit('update:account-count', v || 0))

const load = async () => {
  loading.value = true
  try {
    const res = await backupApi.getInfo()
    backupInfo.value = res.data || {}
  } catch {
    // 静默失败
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const token = getToken()
    const url = backupApi.exportPath(exportIncludeLogs.value, exportIncludeCredentials.value)
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('导出失败')

    const blob = await response.blob()
    const filename = `anyrouter_backup_${new Date().toISOString().slice(0, 10)}.json`
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
    window.$notify('备份导出成功', 'success')
  } catch (e) {
    window.$notify(apiError(e, '导出失败'), 'error')
  } finally {
    exporting.value = false
  }
}

// UiFileDrop 直接给原生 File，不再包 { file: { file } } 那层
const handleImportFile = async (rawFile: File) => {
  if (!rawFile) return
  importing.value = true
  try {
    const res = await backupApi.import(rawFile, importOverwrite.value)
    const data = res.data
    const warningText = Array.isArray(data.warnings) && data.warnings.length
      ? `；${data.warnings.join('；')}`
      : ''
    window.$notify(
      `导入成功: ${data.accounts} 个账号, ${data.notify_channels} 个渠道, ${data.settings} 个配置${warningText}`,
      data.warnings?.length ? 'warning' : 'success'
    )
    load()
  } catch (e) {
    window.$notify(apiError(e, '导入失败'), 'error')
  } finally {
    importing.value = false
  }
}

defineExpose({ load })

onMounted(load)
</script>

<style scoped>
.settings-panel :deep(.n-card__content) { padding: 0; }
.settings-panel :deep(.n-card) { background: transparent; border: none; box-shadow: none; }

.backup-section { padding: 0; }

.backup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}
.backup-header-info { flex: 1; }
.backup-header-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: 2px;
}
.backup-header-desc { font-size: var(--text-xs); color: var(--text-tertiary); }

.backup-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}
.backup-stats .stat-item {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}
.backup-stats .stat-value {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  line-height: 1;
}
.backup-stats .stat-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.backup-action-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3) 0;
  border-bottom: 1px solid var(--border-color-light);
}
.backup-action-section:last-child { border-bottom: none; }

.action-info { flex: 1; }
.action-title {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
  margin-bottom: 2px;
}
.action-desc { font-size: var(--text-xs); color: var(--text-tertiary); }

.action-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.backup-tip {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--warning-color);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--warning-color-light);
  border-radius: var(--radius-sm);
  border-left: 2px solid var(--warning-color);
  margin-top: var(--spacing-3);
}

@media (max-width: 900px) {
  .backup-stats { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .backup-header { flex-direction: column; align-items: flex-start; gap: var(--spacing-2); }
  .backup-action-section { flex-direction: column; align-items: flex-start; gap: var(--spacing-2); }
  .action-controls { width: 100%; flex-direction: column; align-items: stretch; }
}

@media (max-width: 560px) {
  .backup-stats { grid-template-columns: 1fr; }
}
</style>
