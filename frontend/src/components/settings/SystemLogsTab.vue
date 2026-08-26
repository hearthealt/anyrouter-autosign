<template>
  <div class="card settings-panel">
    <UiLoading :show="loading">
      <div class="channel-header">
        <div class="channel-header-info">
          <div class="channel-header-title">系统日志</div>
          <div class="channel-header-desc">查看应用运行日志，支持按级别筛选和关键词搜索</div>
        </div>
        <div class="log-header-actions">
          <UiCheckbox v-model:checked="autoRefresh" size="small">自动刷新</UiCheckbox>
          <UiButton size="small" @click="loadLogs">
            <template #icon><RefreshCw /></template>
            刷新
          </UiButton>
        </div>
      </div>

      <UiDivider style="margin: 16px 0;" />

      <div class="audit-filters">
        <UiSelect
          v-model:value="filters.file"
          :options="fileOptions"
          placeholder="选择日志文件"
          style="width: 180px;"
          size="small"
        />
        <UiSelect
          v-model:value="filters.level"
          :options="levelOptions"
          placeholder="日志级别"
          clearable
          style="width: 120px;"
          size="small"
        />
        <UiInput
          v-model:value="filters.keyword"
          placeholder="搜索关键词"
          clearable
          size="small"
          style="width: 160px;"
          @keyup.enter="loadLogs"
        />
        <UiButton size="small" type="primary" @click="loadLogs" aria-label="查询日志">
          <template #icon><Search /></template>
          查询
        </UiButton>
        <UiButton size="small" @click="downloadFile" aria-label="下载日志文件">
          <template #icon><Download /></template>
          下载
        </UiButton>
        <UiConfirm @positive-click="clearFile">
          <template #trigger>
            <UiButton size="small" type="error" ghost aria-label="清空日志">
              <template #icon><Trash2 /></template>
              清空
            </UiButton>
          </template>
          确定清空此日志文件？
        </UiConfirm>
      </div>

      <UiDivider style="margin: 16px 0;" />

      <div class="log-container">
        <div v-if="logs.length === 0" class="log-empty">暂无日志</div>
        <div v-else class="log-list">
          <div
            v-for="(log, index) in logs"
            :key="index"
            class="log-item"
            :class="'log-level-' + (log.level || 'info').toLowerCase()"
          >
            <span class="log-time">{{ log.timestamp }}</span>
            <span class="log-level-tag">{{ log.level }}</span>
            <span class="log-logger">{{ log.logger }}</span>
            <span class="log-message">{{ log.message }}</span>
            <span v-if="log.extra && Object.keys(log.extra).length > 0" class="log-extra">
              {{ JSON.stringify(log.extra) }}
            </span>
          </div>
        </div>
      </div>

      <div v-if="hasMore" class="log-load-more">
        <UiButton size="small" @click="loadMore" :loading="loadingMore">加载更多</UiButton>
      </div>

      <div class="log-files-info" v-if="files.length > 0">
        <UiDivider style="margin: 16px 0;" />
        <div class="log-files-title">日志文件</div>
        <div class="log-files-grid">
          <div v-for="file in files" :key="file.name" class="log-file-item">
            <span class="log-file-name">{{ file.name }}</span>
            <span class="log-file-size">{{ file.size_display }}</span>
            <span class="log-file-time">{{ file.modified }}</span>
          </div>
        </div>
      </div>
    </UiLoading>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { UiButton, UiCheckbox, UiConfirm, UiDivider, UiInput, UiLoading, UiSelect } from '../../ui'
import { Download, RefreshCw, Search, Trash2 } from 'lucide-vue-next'
import { logsApi } from '../../api'
import { getToken } from '../../utils/auth'

interface LogItem {
  timestamp: string
  level: string
  logger: string
  message: string
  extra?: Record<string, unknown>
}

interface LogFile {
  name: string
  size_display: string
  modified: string
}

const loading = ref(false)
const loadingMore = ref(false)
const logs = ref<LogItem[]>([])
const hasMore = ref(false)
const files = ref<LogFile[]>([])
const autoRefresh = ref(false)
let timer: number | null = null

const filters = ref<{ file: string; level: string | null; keyword: string }>({
  file: 'app.log',
  level: null,
  keyword: ''
})
const offset = ref(0)

const fileOptions = ref<{ label: string; value: string }[]>([
  { label: 'app.log', value: 'app.log' }
])

const levelOptions = [
  { label: 'DEBUG', value: 'DEBUG' },
  { label: 'INFO', value: 'INFO' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'CRITICAL', value: 'CRITICAL' }
]

const buildParams = (off: number) => {
  const params: Record<string, unknown> = {
    file: filters.value.file,
    lines: 100,
    offset: off
  }
  if (filters.value.level) params.level = filters.value.level
  if (filters.value.keyword) params.keyword = filters.value.keyword
  return params
}

const loadFiles = async () => {
  try {
    const res = await logsApi.getFiles()
    files.value = res.data || []
    if (files.value.length > 0) {
      fileOptions.value = files.value.map(f => ({
        label: `${f.name} (${f.size_display})`,
        value: f.name
      }))
    }
  } catch (e) {
    console.error('Failed to load log files:', e)
  }
}

const loadLogs = async () => {
  loading.value = true
  offset.value = 0
  try {
    const res = await logsApi.getLogs(buildParams(0))
    logs.value = res.data?.logs || []
    hasMore.value = res.data?.has_more || false
    offset.value = logs.value.length
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '加载日志失败'
    window.$notify(msg, 'error')
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  loadingMore.value = true
  try {
    const res = await logsApi.getLogs(buildParams(offset.value))
    const newLogs: LogItem[] = res.data?.logs || []
    logs.value = [...logs.value, ...newLogs]
    hasMore.value = res.data?.has_more || false
    offset.value += newLogs.length
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '加载更多失败'
    window.$notify(msg, 'error')
  } finally {
    loadingMore.value = false
  }
}

const downloadFile = () => {
  const url = logsApi.download(filters.value.file)
  const token = getToken()
  fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
    .then(res => res.blob())
    .then(blob => {
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filters.value.file
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
      window.$notify('下载成功', 'success')
    })
    .catch(() => {
      window.$notify('下载失败', 'error')
    })
}

const clearFile = async () => {
  try {
    await logsApi.clear(filters.value.file)
    window.$notify('日志已清空', 'success')
    loadLogs()
    loadFiles()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '清空失败'
    window.$notify(msg, 'error')
  }
}

watch(autoRefresh, (val) => {
  if (val) {
    timer = window.setInterval(() => loadLogs(), 5000)
  } else if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
})

onMounted(() => {
  loadFiles()
  loadLogs()
})

onUnmounted(() => {
  if (timer !== null) clearInterval(timer)
})

defineExpose({ refresh: () => { loadFiles(); loadLogs() } })
</script>

<style scoped>
.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-3);
}

.channel-header-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.channel-header-desc {
  margin-top: 4px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.log-header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.audit-filters {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.log-container {
  background: #0b0c0e;
  border-radius: var(--radius-sm);
  padding: var(--spacing-3);
  max-height: 500px;
  overflow-y: auto;
  font-family: var(--font-mono);
  font-size: 12px;
  border: 1px solid var(--border-color);
}

.log-empty {
  color: var(--text-tertiary);
  text-align: center;
  padding: var(--spacing-10);
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.log-item {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  padding: 2px var(--spacing-2);
  border-radius: var(--radius-xs);
  line-height: 1.5;
  color: #e2e8f0;
}

.log-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.log-time {
  color: #64748b;
  flex-shrink: 0;
}

.log-level-tag {
  padding: 0 4px;
  border-radius: var(--radius-xs);
  font-size: 10px;
  font-weight: var(--font-semibold);
  flex-shrink: 0;
}

.log-level-debug .log-level-tag { background: var(--cyan-color); color: #000; }
.log-level-info .log-level-tag { background: var(--success-color); color: #000; }
.log-level-warning .log-level-tag { background: var(--warning-color); color: #000; }
.log-level-error .log-level-tag { background: var(--error-color); color: #fff; }
.log-level-critical .log-level-tag { background: #db2777; color: #fff; }

.log-logger {
  color: #7b84dd;
  flex-shrink: 0;
}

.log-message {
  color: #fff;
  flex: 1;
  word-break: break-all;
}

.log-extra {
  color: #666;
  font-size: 11px;
  width: 100%;
  padding-left: 20px;
}

.log-load-more {
  display: flex;
  justify-content: center;
  padding: var(--spacing-3) 0;
}

.log-files-info {
  margin-top: var(--spacing-3);
}

.log-files-title {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-2);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.log-files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--spacing-2);
}

.log-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-2);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

.log-file-name {
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

.log-file-size,
.log-file-time {
  color: var(--text-tertiary);
}

@media (max-width: 600px) {
  .audit-filters {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
