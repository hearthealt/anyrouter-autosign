<template>
  <UiLoading :show="loading">
    <div class="settings-pane">
      <div class="pane-head">
        <div class="pane-heading">
          <div class="pane-title"><Terminal :size="15" />系统日志</div>
          <div class="pane-desc">查看应用运行日志，支持按级别筛选和关键词搜索</div>
        </div>
        <div class="pane-actions">
          <UiCheckbox v-model:checked="autoRefresh" size="small">自动刷新</UiCheckbox>
          <UiButton size="small" @click="loadLogs">
            <template #icon><RefreshCw /></template>
            刷新
          </UiButton>
          <UiButton size="small" @click="downloadFile" aria-label="下载日志文件">
            <template #icon><Download /></template>
            下载
          </UiButton>
          <UiButton size="small" type="error" ghost @click="openCleanup">
            <template #icon><Archive /></template>
            批量清理
          </UiButton>
        </div>
      </div>

      <div class="pane-toolbar filter-strip">
        <UiSelect
          v-model:value="filters.file"
          :options="fileOptions"
          placeholder="选择日志文件"
          class="filter-field--lg"
          size="small"
        />
        <UiSelect
          v-model:value="filters.level"
          :options="levelOptions"
          placeholder="日志级别"
          clearable
          class="filter-field"
          size="small"
        />
        <UiInput
          v-model:value="filters.keyword"
          placeholder="搜索关键词"
          clearable
          size="small"
          class="filter-search"
          @keyup.enter="loadLogs"
        />
        <div class="filter-actions">
          <UiButton size="small" type="primary" @click="loadLogs" aria-label="查询日志">
            <template #icon><Search /></template>
            查询
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
      </div>

      <div class="log-console">
        <div class="log-console-bar">
          <span class="log-console-file mono">{{ filters.file }}</span>
          <span class="log-console-count mono">{{ logs.length }} 行{{ hasMore ? ' · 还有更多' : '' }}</span>
          <span v-if="autoRefresh" class="log-console-live">LIVE</span>
        </div>
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
              <span class="log-logger" :title="log.logger">{{ log.logger }}</span>
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
      </div>

      <div class="pane-section" v-if="files.length > 0">
        <div class="pane-section-title">日志文件</div>
        <div class="log-files-grid">
          <button
            v-for="file in files"
            :key="file.name"
            type="button"
            class="log-file-item"
            :class="{ 'is-active': file.name === filters.file }"
            @click="selectFile(file.name)"
          >
            <span class="log-file-name mono">{{ file.name }}</span>
            <span class="log-file-meta">
              <span class="mono">{{ file.size_display }}</span>
              <span>{{ file.modified }}</span>
            </span>
          </button>
        </div>
      </div>
    </div>

    <UiModal
      v-model:show="showCleanup"
      title="批量清理日志"
      size="sm"
      negative-text="取消"
      positive-text="确认清理"
      positive-tone="error"
      :positive-loading="cleaning"
      @positive-click="confirmCleanup"
    >
      <div class="cleanup-body">
        <div class="cleanup-field">
          <span class="cleanup-label">清理范围</span>
          <UiSelect
            v-model:value="cleanupScope"
            :options="cleanupOptions"
            size="small"
          />
        </div>
        <p class="cleanup-impact">
          <template v-if="cleanupPreview.count === 0">该范围内没有归档文件，无需清理。</template>
          <template v-else>
            将删除 <strong>{{ cleanupPreview.count }}</strong> 个归档文件，释放约
            <strong>{{ formatBytes(cleanupPreview.bytes) }}</strong>。
          </template>
        </p>
        <p class="cleanup-note">
          <template v-if="cleanupScope === 0">
            清空全部还会把 app.log、error.log、app.daily.log 三个正在写入的文件截为空
            （文件本身保留，否则日志会写入已删除的文件而静默丢失）。
          </template>
          <template v-else>
            按天保留只删除归档文件，正在写入的 app.log、error.log、app.daily.log 不受影响。
          </template>
        </p>
      </div>
    </UiModal>
  </UiLoading>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { UiButton, UiCheckbox, UiConfirm, UiInput, UiLoading, UiModal, UiSelect } from '../../ui'
import { Archive, Download, RefreshCw, Search, Terminal, Trash2 } from 'lucide-vue-next'
import { logsApi } from '../../api'
import { getToken } from '../../utils/auth'
import { apiError } from '../../utils/apiError'

interface LogItem {
  timestamp: string
  level: string
  logger: string
  message: string
  extra?: Record<string, unknown>
}

interface LogFile {
  name: string
  size: number
  size_display: string
  modified: string
}

/** 与后端 app/services/log_cleanup.py 的 ACTIVE_LOG_FILES 保持一致 */
const ACTIVE_LOG_FILES = ['app.log', 'error.log', 'app.daily.log']

const loading = ref(false)
const loadingMore = ref(false)
const logs = ref<LogItem[]>([])
const hasMore = ref(false)
const files = ref<LogFile[]>([])
const autoRefresh = ref(false)
let timer: number | null = null

const showCleanup = ref(false)
const cleaning = ref(false)
/** 0 表示清空全部 */
const cleanupScope = ref(30)
const cleanupOptions = [
  { label: '保留最近 7 天', value: 7 },
  { label: '保留最近 30 天', value: 30 },
  { label: '保留最近 90 天', value: 90 },
  { label: '清空全部', value: 0 }
]

const formatBytes = (size: number) => {
  let value = size
  for (const unit of ['B', 'KB', 'MB', 'GB']) {
    if (value < 1024) return `${value.toFixed(1)} ${unit}`
    value /= 1024
  }
  return `${value.toFixed(1)} TB`
}

/**
 * 预估影响直接从已加载的 files 本地算，不额外请求后端。
 * 判定规则要和 log_cleanup.cleanup_log_files 一致：只看归档文件的修改时间。
 */
const cleanupPreview = computed(() => {
  const archived = files.value.filter(f => !ACTIVE_LOG_FILES.includes(f.name))
  if (cleanupScope.value === 0) {
    return { count: archived.length, bytes: archived.reduce((sum, f) => sum + (f.size || 0), 0) }
  }
  const cutoff = Date.now() - cleanupScope.value * 86400_000
  const hit = archived.filter(f => new Date(f.modified.replace(' ', 'T')).getTime() < cutoff)
  return { count: hit.length, bytes: hit.reduce((sum, f) => sum + (f.size || 0), 0) }
})

const openCleanup = () => {
  showCleanup.value = true
}

const confirmCleanup = async () => {
  cleaning.value = true
  try {
    const res: any = await logsApi.cleanup({ before_days: cleanupScope.value || null })
    window.$notify(res.message || '清理完成', 'success')
    showCleanup.value = false
    await Promise.all([loadFiles(), loadLogs()])
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    cleaning.value = false
  }
}

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

/** 点击底部文件卡片直接切换当前查看的文件 */
const selectFile = (name: string) => {
  if (filters.value.file === name) return
  filters.value.file = name
  loadLogs()
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
.cleanup-body {
  display: flex;
  flex-direction: column;
  gap: var(--s3);
}

.cleanup-field {
  display: flex;
  flex-direction: column;
  gap: var(--s2);
}

.cleanup-label {
  color: var(--ink);
  font-size: var(--fn-sm);
  font-weight: var(--weight-medium);
}

.cleanup-impact {
  color: var(--ink-strong);
  font-size: var(--fn-sm);
  line-height: var(--leading-loose);
}

.cleanup-impact strong {
  color: var(--bad);
  font-weight: var(--weight-semibold);
  font-variant-numeric: tabular-nums;
}

.cleanup-note {
  color: var(--ink-faint);
  font-size: var(--fn-xs);
  line-height: var(--leading-loose);
}

/**
 * 日志控制台 —— 两个主题下都保持深色。
 * 日志是等宽、密集、要靠颜色分级的内容，浅底反而更难扫读；
 * 控制台内部的颜色因此写成局部变量，不跟随主题令牌。
 */
.log-console {
  --console-bg: #0b0d10;
  --console-bar: #14171c;
  --console-line: rgba(255, 255, 255, 0.07);
  --console-dim: #6b7280;
  --console-text: #e5e9f0;

  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--console-bg);
}

.log-console-bar {
  display: flex;
  align-items: center;
  gap: var(--s3);
  padding: 7px 12px;
  border-bottom: 1px solid var(--console-line);
  background: var(--console-bar);
  font-size: var(--fn-2xs);
  letter-spacing: var(--track-wide);
}

.log-console-file { color: var(--console-text); font-weight: var(--weight-semibold); }
.log-console-count { margin-left: auto; color: var(--console-dim); }

.log-console-live {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--signal);
  font-family: var(--font-mono);
  font-weight: var(--weight-semibold);
}

.log-console-live::before {
  content: "";
  width: 5px;
  height: 5px;
  border-radius: var(--r-full);
  background: var(--signal);
  box-shadow: 0 0 8px var(--signal);
}

.log-container {
  max-height: 480px;
  padding: var(--s2) 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  font-family: var(--font-mono);
  font-size: 12px;
}

.log-empty {
  padding: var(--s10);
  color: var(--console-dim);
  text-align: center;
}

.log-list { display: flex; flex-direction: column; }

/**
 * 每行用 grid 对齐四列（时间 / 级别 / logger / 正文），
 * 原来的 flex-wrap 会让每行的字段起始位置随内容长度左右跳。
 */
.log-item {
  display: grid;
  grid-template-columns: 148px 56px minmax(0, 150px) minmax(0, 1fr);
  gap: var(--s2);
  padding: 3px 12px;
  color: var(--console-text);
  line-height: 1.6;
}

.log-item:hover { background: rgba(255, 255, 255, 0.045); }

.log-time { color: var(--console-dim); }

.log-level-tag {
  justify-self: start;
  width: 100%;
  border-radius: var(--r-xs);
  color: #000;
  font-size: 10px;
  font-weight: var(--weight-bold);
  letter-spacing: 0.04em;
  text-align: center;
}

.log-level-debug .log-level-tag { background: #38bdf8; }
.log-level-info .log-level-tag { background: #4ade80; }
.log-level-warning .log-level-tag { background: #fbbf24; }
.log-level-error .log-level-tag { background: #fb7185; }
.log-level-critical .log-level-tag { background: #f472b6; }

.log-logger {
  overflow: hidden;
  color: #8b93e0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-message {
  color: #fff;
  overflow-wrap: anywhere;
}

.log-extra {
  grid-column: 4;
  color: var(--console-dim);
  font-size: 11px;
  overflow-wrap: anywhere;
}

.log-load-more {
  display: flex;
  justify-content: center;
  padding: var(--s2);
  border-top: 1px solid var(--console-line);
  background: var(--console-bar);
}

/* 文件卡片：点一下就切到那个文件，当前文件用信号色描边标出 */
.log-files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(232px, 1fr));
  gap: var(--s2);
}

.log-file-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 9px 11px;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-md);
  background: var(--surface-inset);
  color: var(--ink-strong);
  font-size: var(--fn-xs);
  text-align: left;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.log-file-item:hover { border-color: var(--line-strong); background: var(--surface-hover); }

.log-file-item.is-active {
  border-color: var(--signal-deep);
  background: var(--signal-wash);
}

.log-file-name { font-weight: var(--weight-semibold); }

.log-file-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s2);
  color: var(--ink-faint);
  font-size: var(--fn-2xs);
}

@media (max-width: 700px) {
  .log-item {
    grid-template-columns: minmax(0, 1fr);
    gap: 2px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--console-line);
  }

  .log-level-tag { width: 56px; }
  .log-extra { grid-column: 1; }
}
</style>
