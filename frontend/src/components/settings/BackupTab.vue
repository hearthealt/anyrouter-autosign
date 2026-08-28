<template>
  <UiLoading :show="loading">
    <div class="settings-pane">
      <div class="pane-head">
        <div class="pane-heading">
          <div class="pane-title"><DatabaseBackup :size="15" />数据备份</div>
          <div class="pane-desc">导出或导入系统数据，用于迁移或恢复</div>
        </div>
      </div>

      <div class="backup-stats">
        <div class="stat-item">
          <div class="stat-value tabular">{{ backupInfo.account_count || 0 }}</div>
          <div class="stat-label">账号数量</div>
        </div>
        <div class="stat-item">
          <div class="stat-value tabular">{{ backupInfo.sign_log_count || 0 }}</div>
          <div class="stat-label">签到日志</div>
        </div>
        <div class="stat-item">
          <div class="stat-value tabular">{{ backupInfo.notify_channel_count || 0 }}</div>
          <div class="stat-label">推送渠道</div>
        </div>
        <div class="stat-item">
          <div class="stat-value tabular">{{ backupInfo.setting_count || 0 }}</div>
          <div class="stat-label">配置项</div>
        </div>
      </div>

      <div class="backup-actions">
        <section class="backup-action">
          <header class="action-head">
            <span class="action-icon"><Download :size="16" /></span>
            <div class="action-heading">
              <span class="action-title">导出备份</span>
              <span class="action-desc">将账号、设置、推送渠道等数据导出为 JSON 文件</span>
            </div>
          </header>
          <div class="action-controls">
            <UiCheckbox v-model:checked="exportIncludeLogs" size="small">包含签到日志（最近 1000 条）</UiCheckbox>
            <UiCheckbox v-model:checked="exportIncludeCredentials" size="small">包含敏感凭证</UiCheckbox>
            <UiButton type="primary" size="small" @click="handleExport" :loading="exporting">
              <template #icon><Download /></template>
              导出备份
            </UiButton>
          </div>
        </section>

        <section class="backup-action">
          <header class="action-head">
            <span class="action-icon"><CloudUpload :size="16" /></span>
            <div class="action-heading">
              <span class="action-title">导入备份</span>
              <span class="action-desc">从备份文件恢复数据（支持 JSON 格式）</span>
            </div>
          </header>
          <div class="action-controls">
            <UiCheckbox v-model:checked="importOverwrite" size="small">覆盖现有数据</UiCheckbox>
            <UiFileDrop accept=".json" @select="handleImportFile">
              <UiButton size="small" :loading="importing">
                <template #icon><CloudUpload :size="14" /></template>
                选择文件导入
              </UiButton>
            </UiFileDrop>
          </div>
        </section>
      </div>

      <div class="pane-note is-warn">
        <Info />
        <span>
          默认备份不包含 Cookie、Token、登录密码、代理地址和推送渠道配置；
          勾选「包含敏感凭证」后可完整迁移，但请妥善保管导出的文件。
        </span>
      </div>
    </div>
  </UiLoading>
</template>

<script setup lang="ts">
import { UiFileDrop, UiButton, UiCheckbox, UiLoading } from '../../ui'
import { ref, onMounted, watch } from 'vue'
import { CloudUpload, DatabaseBackup, Download, Info } from 'lucide-vue-next'
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
.backup-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--s3);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 13px;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-lg);
  background: var(--surface-inset);
}

.stat-value {
  color: var(--ink-max);
  font-family: var(--font-display);
  font-size: var(--fn-2xl);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-tight);
  line-height: 1;
}

.stat-label {
  color: var(--ink-faint);
  font-size: var(--fn-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-caps);
  text-transform: uppercase;
}

.backup-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--s3);
}

.backup-action {
  display: flex;
  flex-direction: column;
  gap: var(--s3);
  padding: 14px;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-lg);
  background: var(--surface-raised);
}

.action-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.action-icon {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: var(--r-md);
  background: var(--signal-wash);
  color: var(--signal-deep);
}

.action-heading {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.action-title {
  color: var(--ink-max);
  font-size: var(--fn-md);
  font-weight: var(--weight-semibold);
}

.action-desc {
  color: var(--ink-faint);
  font-size: var(--fn-xs);
  line-height: 1.5;
}

/* 勾选项竖排、按钮压在底部：两张卡的按钮因此永远在同一条基线上 */
.action-controls {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s2);
  margin-top: auto;
  padding-top: var(--s3);
  border-top: 1px solid var(--line-faint);
}
</style>
