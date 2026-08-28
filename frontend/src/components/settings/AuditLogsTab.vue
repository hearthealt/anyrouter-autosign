<template>
  <UiLoading :show="loading">
    <div class="settings-pane">
      <div class="pane-head">
        <div class="pane-heading">
          <div class="pane-title"><ScrollText :size="15" />审计日志</div>
          <div class="pane-desc">记录系统中的所有敏感操作，包括登录、账号变更等</div>
        </div>
        <div class="pane-actions">
          <UiButton size="small" @click="exportAuditLogs">
            <template #icon><Download /></template>
            导出
          </UiButton>
          <UiButton size="small" type="error" ghost @click="openCleanup">
            <template #icon><Trash2 /></template>
            清理
          </UiButton>
        </div>
      </div>

      <div class="pane-toolbar filter-strip">
        <UiSelect
          v-model:value="filters.action"
          :options="actionOptions"
          placeholder="操作类型"
          clearable
          class="filter-field"
          size="small"
        />
        <UiDateRange
          v-model:value="filters.dateRange"
          type="daterange"
          clearable
          size="small"
          class="filter-field--lg"
        />
        <UiInput
          v-model:value="filters.keyword"
          placeholder="搜索关键词"
          clearable
          size="small"
          class="filter-search"
          @keyup.enter="load"
        />
        <div class="filter-actions">
          <UiButton size="small" type="primary" @click="load">
            <template #icon><Search /></template>
            查询
          </UiButton>
        </div>
      </div>

      <DataGrid
        :columns="columns"
        :data="logs"
        :loading="loading"
        :bordered="false"
        size="small"
      />

      <div v-if="pagination.itemCount > 0" class="pagination-wrap">
        <UiPagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.itemCount"
          :page-sizes="pagination.pageSizes"
          show-size-picker
          size="small"
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </div>

    <UiModal
      v-model:show="showCleanup"
      title="清理审计日志"
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
          <template v-if="cleanupPreview === null">正在统计影响范围…</template>
          <template v-else-if="cleanupPreview === 0">该范围内没有记录，无需清理。</template>
          <template v-else>将删除 <strong>{{ cleanupPreview.toLocaleString() }}</strong> 条记录，此操作不可撤销。</template>
        </p>
        <p class="cleanup-note">
          清理动作本身会记录一条审计日志，保留操作痕迹。
        </p>
      </div>
    </UiModal>
  </UiLoading>
</template>

<script setup lang="ts">
import { DataGrid, UiButton, UiDateRange, UiInput, UiLoading, UiModal, UiPagination, UiSelect } from '../../ui'
import { ref, watch, onMounted } from 'vue'
import { Download, ScrollText, Search, Trash2 } from 'lucide-vue-next'
import { auditApi } from '../../api'
import { getToken } from '../../utils/auth'
import { apiError } from '../../utils/apiError'

const loading = ref(false)
const logs = ref<any[]>([])
const filters = ref({
  action: null as string | null,
  dateRange: null as [number, number] | null,
  keyword: ''
})
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  pageSizes: [10, 20, 50, 100]
})
const actionOptions = ref<{ label: string; value: string }[]>([])

const showCleanup = ref(false)
const cleaning = ref(false)
/** 0 表示清空全部 */
const cleanupScope = ref(30)
/** null 表示预估仍在加载 */
const cleanupPreview = ref<number | null>(null)
const cleanupOptions = [
  { label: '保留最近 7 天', value: 7 },
  { label: '保留最近 30 天', value: 30 },
  { label: '保留最近 90 天', value: 90 },
  { label: '清空全部', value: 0 }
]

const columns = [
  {
    title: '时间',
    key: 'created_at',
    width: 160,
    render: (row: any) => row.created_at?.replace('T', ' ').substring(0, 19) || '-'
  },
  { title: '操作类型', key: 'action_name', width: 120, ellipsis: true },
  { title: '操作用户', key: 'username', width: 120, ellipsis: true, render: (row: any) => row.username || '-' },
  {
    title: '目标',
    key: 'target',
    width: 180,
    ellipsis: true,
    render: (row: any) => row.target_name ? `${row.target_type || ''}: ${row.target_name}` : (row.target_type || '-')
  },
  {
    title: '详情',
    key: 'detail',
    width: 280,
    ellipsis: { tooltip: true },
    render: (row: any) => {
      if (!row.detail) return '-'
      try {
        const detail = typeof row.detail === 'string' ? JSON.parse(row.detail) : row.detail
        return JSON.stringify(detail)
      } catch {
        return row.detail
      }
    }
  },
  { title: 'IP 地址', key: 'ip_address', width: 130, ellipsis: true, render: (row: any) => row.ip_address || '-' }
]

const load = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.value.page,
      size: pagination.value.pageSize
    }
    if (filters.value.action) params.action = filters.value.action
    if (filters.value.dateRange) {
      params.start_date = new Date(filters.value.dateRange[0]).toISOString().split('T')[0]
      params.end_date = new Date(filters.value.dateRange[1]).toISOString().split('T')[0]
    }
    if (filters.value.keyword) params.keyword = filters.value.keyword

    const res = await auditApi.getLogs(params)
    logs.value = res.data?.items || []
    pagination.value.itemCount = res.data?.total || 0
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    loading.value = false
  }
}

const loadActions = async () => {
  try {
    const res = await auditApi.getActions()
    // 后端返回 [{ value, label }] 数组
    actionOptions.value = (res.data || []).map((item: any) => ({
      value: item.value,
      label: item.label
    }))
  } catch {
    // 静默失败
  }
}

/** 把「保留最近 N 天」换算成清理截止日（含当天，与后端 created_at < now - N 天 对齐） */
const cutoffDate = (days: number) => {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().split('T')[0]
}

/** 预估影响：复用列表接口只取 total，不额外加后端接口 */
const loadCleanupPreview = async () => {
  cleanupPreview.value = null
  try {
    const params: any = { page: 1, size: 1 }
    if (cleanupScope.value > 0) params.end_date = cutoffDate(cleanupScope.value)
    const res = await auditApi.getLogs(params)
    cleanupPreview.value = res.data?.total || 0
  } catch {
    cleanupPreview.value = 0
  }
}

const openCleanup = () => {
  showCleanup.value = true
  loadCleanupPreview()
}

watch(cleanupScope, () => {
  if (showCleanup.value) loadCleanupPreview()
})

const confirmCleanup = async () => {
  cleaning.value = true
  try {
    const res: any = await auditApi.cleanup({ before_days: cleanupScope.value || null })
    window.$notify(res.message || '清理完成', 'success')
    showCleanup.value = false
    pagination.value.page = 1
    await load()
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    cleaning.value = false
  }
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  load()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  load()
}

const exportAuditLogs = () => {
  const params: any = { format: 'csv' }
  if (filters.value.action) params.action = filters.value.action
  if (filters.value.dateRange) {
    params.start_date = new Date(filters.value.dateRange[0]).toISOString().split('T')[0]
    params.end_date = new Date(filters.value.dateRange[1]).toISOString().split('T')[0]
  }
  const url = auditApi.export(params)
  const token = getToken()

  fetch(url, { headers: { 'Authorization': `Bearer ${token}` } })
    .then(res => res.blob())
    .then(blob => {
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
      window.$notify('导出成功', 'success')
    })
    .catch(() => {
      window.$notify('导出失败', 'error')
    })
}

defineExpose({ load })

onMounted(() => {
  load()
  loadActions()
})
</script>

<style scoped>
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
}

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
</style>
