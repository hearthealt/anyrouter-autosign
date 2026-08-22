<template>
  <div class="sign-logs-page page-shell">
    <div class="workspace-toolbar">
      <div class="toolbar-summary">
        <div class="toolbar-label">签到日志 <span class="toolbar-count">{{ pagination.itemCount }}</span></div>
        <div class="toolbar-stats">
          <span class="toolbar-stat success">成功 <strong>{{ summary.success_count }}</strong></span>
          <span class="toolbar-stat error">失败 <strong>{{ summary.fail_count }}</strong></span>
        </div>
      </div>
      <div class="toolbar-actions">
        <n-button size="small" @click="loadLogs(1)" :loading="loading">
          <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
      </div>
    </div>

    <div class="control-strip">
      <div class="filter-strip logs-filter">
      <n-select
        v-model:value="filters.account_id"
        :options="accountOptions"
        placeholder="全部账号"
        size="small"
        clearable
        class="filter-item"
        @update:value="loadLogs(1)"
      />
      <n-select
        v-model:value="filters.success"
        :options="statusOptions"
        placeholder="全部状态"
        size="small"
        clearable
        class="filter-item"
        @update:value="loadLogs(1)"
      />
      <n-date-picker
        v-model:value="filters.dateRange"
        type="daterange"
        size="small"
        clearable
        class="filter-date"
        @update:value="loadLogs(1)"
      />
      </div>
    </div>

    <div class="logs-card data-surface">
      <div v-if="loading || logs.length > 0" class="table-wrap">
        <n-data-table
          :columns="columns"
          :data="logs"
          :row-key="(row: SignLogRow) => row.id"
          :loading="loading"
          :pagination="false"
          :single-line="false"
          :remote="true"
          size="small"
          @update:sorter="handleSorterChange"
        />
      </div>

      <div v-else class="empty-state">
        <n-icon :size="32" color="var(--text-quaternary)"><DocumentTextOutline /></n-icon>
        <div class="empty-title">暂无签到记录</div>
        <div class="empty-desc">当前筛选条件下没有匹配数据</div>
      </div>

      <div v-if="pagination.itemCount > 0" class="pagination-wrap">
        <n-pagination
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  NTag,
  type DataTableColumns,
  type DataTableSortOrder,
  type DataTableSortState
} from 'naive-ui'
import {
  RefreshOutline,
  DocumentTextOutline,
} from '@vicons/ionicons5'
import { signApi, accountApi } from '../api'
import { useFormat, useViewRefresh } from '../composables'
import { formatRewardAmount } from '../utils'
import ExternalLink from '../components/common/ExternalLink.vue'
import type { Account, SignLog } from '../types'

const { formatDateTime } = useFormat()
const route = useRoute()

type SignLogRow = SignLog & { username?: string }

const loading = ref(false)
const logs = ref<SignLogRow[]>([])
const accounts = ref<Account[]>([])
const summary = ref({
  success_count: 0,
  fail_count: 0
})

const filters = ref({
  account_id: null as number | null,
  success: null as boolean | null,
  dateRange: null as [number, number] | null
})

const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100]
})
type LogSortKey = 'username' | 'platform' | 'status' | 'reward' | 'sign_time'

const sortState = ref<{ columnKey: LogSortKey; order: DataTableSortOrder }>({
  columnKey: 'sign_time',
  order: 'descend'
})

const accountOptions = ref<{ label: string; value: number }[]>([])

const statusOptions = [
  { label: '签到成功', value: true },
  { label: '签到失败', value: false }
]

const buildTodayRange = (): [number, number] => {
  const start = new Date()
  start.setHours(0, 0, 0, 0)

  const end = new Date()
  end.setHours(23, 59, 59, 999)

  return [start.getTime(), end.getTime()]
}

const buildDateRangeFromQuery = (startDate?: string, endDate?: string): [number, number] | null => {
  if (!startDate || !endDate) return null

  const start = new Date(`${startDate}T00:00:00`)
  const end = new Date(`${endDate}T23:59:59.999`)
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return null
  }

  return [start.getTime(), end.getTime()]
}

const syncFiltersFromRoute = () => {
  const accountId = Number(route.query.account_id)
  filters.value.account_id = Number.isInteger(accountId) && accountId > 0 ? accountId : null

  if (route.query.success === 'true') {
    filters.value.success = true
  } else if (route.query.success === 'false') {
    filters.value.success = false
  } else {
    filters.value.success = null
  }

  if (route.query.today) {
    filters.value.dateRange = buildTodayRange()
    return
  }

  const startDate = typeof route.query.start_date === 'string' ? route.query.start_date : undefined
  const endDate = typeof route.query.end_date === 'string' ? route.query.end_date : undefined
  filters.value.dateRange = buildDateRangeFromQuery(startDate, endDate)
}

const getStatusTagType = (status?: string): 'success' | 'warning' | 'error' => {
  switch (status) {
    case 'success':
      return 'success'
    case 'already_signed':
      return 'warning'
    case 'failed':
      return 'error'
    default:
      return 'error'
  }
}

const getStatusLabel = (status?: string): string => {
  switch (status) {
    case 'success':
      return '成功'
    case 'already_signed':
      return '已签到'
    case 'failed':
      return '失败'
    default:
      return '失败'
  }
}

const getRewardDisplay = (row: SignLogRow) => {
  if (!Number(row.reward_quota || 0)) return '-'
  return `+${formatRewardAmount(row.reward_quota, row.reward_unit, row.reward_display)}`
}

const getPlatformName = (row: SignLogRow) => row.platform?.name || row.platform_name || '未配置平台'
const getPlatformUrl = (row: SignLogRow) => row.platform?.base_url || ''
const getSortOrder = (columnKey: LogSortKey): DataTableSortOrder =>
  sortState.value.columnKey === columnKey ? sortState.value.order : false

const columns = computed<DataTableColumns<SignLogRow>>(() => [
  {
    title: '账号',
    key: 'username',
    minWidth: 80,
    ellipsis: { tooltip: true },
    sorter: 'default',
    sortOrder: getSortOrder('username'),
    render: row => h('div', { class: 'log-account-cell' }, [
      h('span', { class: 'log-account-name' }, row.username || `账号${row.account_id ?? '-'}`),
      h('span', { class: 'log-account-meta' }, `ID ${row.account_id ?? '-'}`)
    ])
  },
  {
    title: '平台',
    key: 'platform',
    minWidth: 220,
    sorter: 'default',
    sortOrder: getSortOrder('platform'),
    render: row => h(ExternalLink, {
      href: getPlatformUrl(row),
      label: getPlatformUrl(row) || getPlatformName(row),
      mono: true
    })
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    align: 'center',
    sorter: 'default',
    sortOrder: getSortOrder('status'),
    render: row =>
      h(
        NTag,
        {
          type: getStatusTagType(row.status),
          size: 'small',
          bordered: false,
          round: false
        },
        { default: () => getStatusLabel(row.status) }
      )
  },
  {
    title: '奖励',
    key: 'reward',
    width: 120,
    align: 'right',
    sorter: 'default',
    sortOrder: getSortOrder('reward'),
    render: row => h('span', { class: 'reward-value' }, getRewardDisplay(row))
  },
  {
    title: '结果',
    key: 'message',
    minWidth: 280,
    ellipsis: { tooltip: true },
    render: row => row.message || '-'
  },
  {
    title: '时间',
    key: 'sign_time',
    width: 170,
    sorter: 'default',
    sortOrder: getSortOrder('sign_time'),
    render: row => (row.sign_time ? formatDateTime(row.sign_time) : '-')
  }
])

const loadAccounts = async () => {
  try {
    const res = await accountApi.getList()
    accounts.value = res.data || []
    accountOptions.value = accounts.value.map(account => ({
      label: account.username || `账号${account.id}`,
      value: account.id
    }))
  } catch (e: any) {
    window.$notify(e.message, 'error')
  }
}

const loadLogs = async (page = 1) => {
  loading.value = true
  try {
    const params: any = {
      page,
      size: pagination.value.pageSize
    }

    if (filters.value.account_id) {
      params.account_id = filters.value.account_id
    }
    if (filters.value.success !== null) {
      params.success = filters.value.success
    }
    if (filters.value.dateRange) {
      params.start_date = new Date(filters.value.dateRange[0]).toISOString().split('T')[0]
      params.end_date = new Date(filters.value.dateRange[1]).toISOString().split('T')[0]
    }
    params.sort_by = sortState.value.columnKey
    params.sort_order = sortState.value.order === 'ascend' ? 'asc' : 'desc'

    const res = await signApi.getAllLogs(params)
    logs.value = res.data?.items || []
    pagination.value.itemCount = res.data?.total || 0
    pagination.value.page = page
    summary.value.success_count = res.data?.success_count || 0
    summary.value.fail_count = res.data?.fail_count || 0
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  loadLogs(page)
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  loadLogs(1)
}

const handleSorterChange = (sorter: DataTableSortState | DataTableSortState[] | null) => {
  const nextSorter = Array.isArray(sorter) ? (sorter[0] ?? null) : sorter

  if (!nextSorter?.columnKey || !nextSorter.order) {
    sortState.value = {
      columnKey: 'sign_time',
      order: 'descend'
    }
    loadLogs(1)
    return
  }

  sortState.value = {
    columnKey: String(nextSorter.columnKey) as LogSortKey,
    order: nextSorter.order
  }
  loadLogs(1)
}

onMounted(() => {
  loadAccounts()
  syncFiltersFromRoute()
  loadLogs()
})

watch(
  () => [
    route.query.today,
    route.query.account_id,
    route.query.success,
    route.query.start_date,
    route.query.end_date
  ],
  () => {
    syncFiltersFromRoute()
    loadLogs(1)
  }
)

useViewRefresh(() => loadLogs(pagination.value.page))
</script>

<style scoped>
.sign-logs-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.logs-filter {
  width: 100%;
}

.filter-item {
  width: 180px;
}

.filter-date {
  width: 260px;
}

.logs-card {
  overflow: hidden;
}

.table-wrap {
  padding: 0;
}

.table-wrap :deep(.n-data-table) {
  border: none;
  border-radius: 0;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-3) var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.empty-state {
  padding: var(--spacing-12) var(--spacing-5);
}

.sign-logs-page :deep(.reward-value) {
  font-weight: var(--font-semibold);
  color: var(--primary-color);
  font-family: var(--font-mono);
}

.sign-logs-page :deep(.log-account-cell) {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 2px;
}

.sign-logs-page :deep(.log-account-name) {
  min-width: 0;
  overflow: hidden;
  color: var(--text-primary);
  font-weight: var(--font-medium);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sign-logs-page :deep(.log-account-meta) {
  color: var(--text-tertiary);
  font-family: var(--font-mono);
  font-size: 10px;
}

@media (max-width: 640px) {
  .logs-filter {
    align-items: stretch;
    flex-direction: column;
  }

  .filter-item,
  .filter-date {
    width: 100%;
  }
}
</style>
