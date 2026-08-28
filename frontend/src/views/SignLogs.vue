<template>
  <div class="sign-logs-page page-shell">
    <section class="logs-console control-strip">
      <div class="filter-strip logs-filter">
        <UiSelect
          v-model:value="filters.account_id"
          :options="accountOptions"
          placeholder="全部账号"
          size="small"
          clearable
          class="filter-field--lg"
          @update:value="loadLogs(1)"
        />
        <UiSelect
          v-model:value="filters.success"
          :options="statusOptions"
          placeholder="全部状态"
          size="small"
          clearable
          class="filter-field"
          @update:value="loadLogs(1)"
        />
        <UiDateRange
          v-model:value="filters.dateRange"
          type="daterange"
          size="small"
          clearable
          class="filter-field--lg"
          @update:value="loadLogs(1)"
        />

        <div class="filter-actions">
          <span class="filter-meta">
            <span>共 <strong>{{ pagination.itemCount }}</strong></span>
            <span class="success">成功 <strong>{{ summary.success_count }}</strong></span>
            <span class="error">失败 <strong>{{ summary.fail_count }}</strong></span>
          </span>
          <UiButton size="small" :loading="loading" @click="loadLogs(1)">
            <template #icon><RefreshCw :size="14" /></template>
            刷新
          </UiButton>
        </div>
      </div>
    </section>
    <div class="logs-card data-surface">
      <div v-if="loading || logs.length > 0" class="table-wrap">
        <DataGrid
          :columns="columns"
          :data="logs"
          :row-key="(row: SignLogRow) => row.id"
          :loading="loading"
          :pagination="false"
          :single-line="false"
          :remote="true"
          size="small"
          :scroll-x="1040"
          @update:sorter="handleSorterChange"
        />
      </div>

      <div v-else class="empty-state">
        <FileText :size="32" />
        <div class="empty-title">暂无签到记录</div>
        <div class="empty-desc">当前筛选条件下没有匹配数据</div>
      </div>

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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h, watch } from 'vue'
import { useRoute } from 'vue-router'
import { DataGrid, UiButton, UiDateRange, UiPagination, UiSelect, UiTag, type GridColumns, type GridSortState, type SortOrder } from '../ui'
import { FileText, RefreshCw } from 'lucide-vue-next'
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

const sortState = ref<{ columnKey: LogSortKey; order: SortOrder }>({
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
const getSortOrder = (columnKey: LogSortKey): SortOrder =>
  sortState.value.columnKey === columnKey ? sortState.value.order : false

const columns = computed<GridColumns<SignLogRow>>(() => [
  {
    title: '账号',
    key: 'username',
    width: 190,
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
    width: 230,
    ellipsis: { tooltip: true },
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
        UiTag,
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
    width: 230,
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

const handleSorterChange = (sorter: GridSortState | GridSortState[] | null) => {
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

/* ────────── event stream visual layer */
.sign-logs-page { gap: clamp(14px, 1.8vw, 24px); padding-bottom: 48px; }
.logs-hero { position: relative; isolation: isolate; min-height: 275px; display: grid; grid-template-columns: minmax(0, 1.25fr) minmax(270px, .75fr); gap: 26px; align-items: center; overflow: hidden; padding: clamp(24px, 4vw, 48px); border: 1px solid var(--line); border-radius: 26px; background: radial-gradient(circle at 92% 24%, var(--bad-wash), transparent 24%), linear-gradient(135deg, var(--surface-raised), var(--surface-inset)); box-shadow: var(--lift-3); }
.logs-hero__grid { position: absolute; inset: 0; z-index: -1; opacity: .55; background-image: linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px); background-size: 38px 38px; mask-image: linear-gradient(to right, black 26%, transparent 100%); }
.logs-hero::after { content: ''; position: absolute; right: -70px; top: -170px; z-index: -1; width: 410px; height: 410px; border: 1px solid color-mix(in srgb, var(--signal) 28%, transparent); border-radius: 50%; box-shadow: 0 0 0 48px color-mix(in srgb, var(--signal) 5%, transparent), 0 0 0 100px color-mix(in srgb, var(--signal) 3%, transparent); }
.logs-hero__copy { max-width: 700px; }
.eyebrow-line { display: flex; align-items: center; gap: 9px; color: var(--ink-muted); font-family: var(--font-mono); font-size: 10px; letter-spacing: .14em; }
.eyebrow-line .mono { margin-left: auto; color: var(--ink-faint); }
.live-pulse { width: 7px; height: 7px; flex: 0 0 auto; border-radius: 50%; background: var(--signal); box-shadow: 0 0 0 5px var(--signal-wash), 0 0 14px var(--signal-glow); }
.logs-hero h2 { margin: 35px 0 14px; color: var(--ink-max); font-family: var(--font-display); font-size: clamp(40px, 5.4vw, 76px); font-weight: 470; line-height: .96; letter-spacing: -.07em; }
.logs-hero h2 em { display: block; color: var(--signal-deep); font-style: normal; font-weight: 720; }
.logs-hero p { max-width: 560px; margin: 0; color: var(--ink-muted); font-size: 13px; line-height: 1.85; }
.logs-hero__metrics { display: grid; grid-template-columns: 1fr; gap: 1px; overflow: hidden; border: 1px solid var(--line); border-radius: 16px; background: var(--line-faint); }
.logs-hero__metrics > div { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 17px 18px; background: color-mix(in srgb, var(--surface-overlay) 78%, transparent); }
.logs-hero__metrics span { color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .11em; }
.logs-hero__metrics strong { color: var(--ink-max); font-family: var(--font-display); font-size: 28px; font-weight: 620; letter-spacing: -.05em; }
.logs-hero__metrics .success strong { color: var(--ok); }
.logs-hero__metrics .error strong { color: var(--bad); }
.logs-hero__footer { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-top: 16px; border-top: 1px solid var(--line-faint); }
.logs-hero__footer > .mono { color: var(--ink-faint); font-size: 9px; letter-spacing: .16em; }
.hero-link { display: inline-flex; align-items: center; gap: 7px; margin-left: auto; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .12em; }
.logs-console { gap: 14px; padding: 17px; border-radius: 20px; background: linear-gradient(135deg, var(--surface-raised), var(--surface-inset)); box-shadow: var(--lift-2); }
.console-topline { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--line-faint); }
.console-topline > div { display: flex; align-items: baseline; gap: 13px; }
.console-code { color: var(--signal-deep); font-size: 9px; letter-spacing: .14em; }
.console-topline strong { color: var(--ink-strong); font-size: 12px; }
.console-live { display: inline-flex; align-items: center; gap: 7px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .09em; }
.console-live span { width: 5px; height: 5px; border-radius: 50%; background: var(--signal); box-shadow: 0 0 9px var(--signal-glow); }
.logs-card { border-color: var(--line); border-radius: 20px; box-shadow: var(--lift-2); }
.table-wrap { position: relative; }
.table-wrap::before { content: 'EVENT TIMELINE'; display: block; padding: 13px 20px; border-bottom: 1px solid var(--line-faint); color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .15em; background: var(--surface-inset); }
.table-wrap :deep(.n-data-table) { border: none; border-radius: 0; background: transparent; }
.pagination-wrap { background: var(--surface-inset); border-color: var(--line-faint); }
.sign-logs-page :deep(.reward-value) { color: var(--signal-deep); }

@media (max-width: 780px) {
  .logs-hero { grid-template-columns: 1fr; align-items: stretch; }
  .logs-hero__metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .logs-hero__metrics > div { display: block; padding: 14px; }
  .logs-hero__metrics strong { display: block; margin-top: 9px; }
}
@media (max-width: 640px) {
  .logs-hero { min-height: 0; padding: 22px; border-radius: 20px; }
  .eyebrow-line .mono { display: none; }
  .logs-hero h2 { margin-top: 34px; font-size: clamp(42px, 13vw, 60px); }
  .logs-hero__metrics { grid-template-columns: 1fr; }
  .logs-hero__metrics > div { display: flex; }
  .logs-hero__footer { align-items: flex-start; flex-direction: column; }
  .hero-link { margin-left: 0; }
  .logs-console .logs-filter { align-items: stretch; flex-direction: column; }
  .filter-item, .filter-date { width: 100%; }
  .table-wrap::before { padding: 11px 14px; }
}</style>
