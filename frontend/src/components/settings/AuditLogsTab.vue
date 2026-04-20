<template>
  <n-card class="settings-panel">
    <n-spin :show="loading">
      <div class="channel-header">
        <div class="channel-header-info">
          <div class="channel-header-title">审计日志</div>
          <div class="channel-header-desc">记录系统中的所有敏感操作，包括登录、账号变更等</div>
        </div>
        <n-button @click="exportAuditLogs">
          <template #icon><n-icon><DownloadOutline /></n-icon></template>
          导出日志
        </n-button>
      </div>

      <n-divider style="margin: 16px 0;" />

      <div class="audit-filters">
        <n-select
          v-model:value="filters.action"
          :options="actionOptions"
          placeholder="操作类型"
          clearable
          style="width: 160px;"
          size="small"
        />
        <n-date-picker
          v-model:value="filters.dateRange"
          type="daterange"
          clearable
          size="small"
          style="width: 240px;"
        />
        <n-input
          v-model:value="filters.keyword"
          placeholder="搜索关键词"
          clearable
          size="small"
          style="width: 160px;"
        />
        <n-button size="small" type="primary" @click="load">
          <template #icon><n-icon><SearchOutline /></n-icon></template>
          查询
        </n-button>
      </div>

      <n-divider style="margin: 16px 0;" />

      <n-data-table
        :columns="columns"
        :data="logs"
        :pagination="pagination"
        :bordered="false"
        size="small"
        remote
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-spin>
  </n-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { DownloadOutline, SearchOutline } from '@vicons/ionicons5'
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
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100]
})
const actionOptions = ref<{ label: string; value: string }[]>([])

const columns = [
  {
    title: '时间',
    key: 'created_at',
    width: 160,
    render: (row: any) => row.created_at?.replace('T', ' ').substring(0, 19) || '-'
  },
  { title: '操作类型', key: 'action_name', width: 120 },
  { title: '操作用户', key: 'username', width: 100, render: (row: any) => row.username || '-' },
  {
    title: '目标',
    key: 'target',
    width: 150,
    render: (row: any) => row.target_name ? `${row.target_type || ''}: ${row.target_name}` : (row.target_type || '-')
  },
  {
    title: '详情',
    key: 'detail',
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
  { title: 'IP 地址', key: 'ip_address', width: 130, render: (row: any) => row.ip_address || '-' }
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
    const actions = res.data || {}
    actionOptions.value = Object.entries(actions).map(([value, label]) => ({
      value,
      label: label as string
    }))
  } catch {
    // 静默失败
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
.settings-panel :deep(.n-card__content) { padding: 0; }
.settings-panel :deep(.n-card) { background: transparent; border: none; box-shadow: none; }

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}
.channel-header-info { flex: 1; }
.channel-header-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: 2px;
}
.channel-header-desc { font-size: var(--text-xs); color: var(--text-tertiary); }

.audit-filters {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

@media (max-width: 768px) {
  .channel-header { flex-direction: column; align-items: flex-start; gap: var(--spacing-2); }
  .audit-filters { flex-direction: column; }
  .audit-filters .n-select,
  .audit-filters .n-date-picker,
  .audit-filters .n-input { width: 100% !important; }
}
</style>
