<template>
  <div class="sign-logs-page">
    <!-- 筛选条件 -->
    <div class="filter-card">
      <div class="filter-left">
        <n-select
          v-model:value="filters.account_id"
          :options="accountOptions"
          placeholder="全部账号"
          clearable
          style="width: 200px;"
          @update:value="loadLogs(1)"
        />
        <n-select
          v-model:value="filters.success"
          :options="statusOptions"
          placeholder="全部状态"
          clearable
          style="width: 140px;"
          @update:value="loadLogs(1)"
        />
        <n-date-picker
          v-model:value="filters.dateRange"
          type="daterange"
          clearable
          style="width: 260px;"
          @update:value="loadLogs(1)"
        />
      </div>
      <div class="filter-right">
        <n-button @click="loadLogs(1)" :loading="loading">
          <template #icon><n-icon><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
      </div>
    </div>

    <!-- 签到记录 -->
    <div class="logs-card">
      <div class="card-header">
        <div class="card-title-section">
          <h3 class="card-title">
            <n-icon><ListOutline /></n-icon>
            签到记录
          </h3>
          <span class="card-subtitle">共 {{ pagination.itemCount }} 条记录</span>
        </div>
      </div>

      <div class="logs-table-wrapper" v-if="loading || logs.length > 0">
        <n-data-table
          class="logs-table"
          :columns="columns"
          :data="logs"
          :row-key="(row: any) => row.id"
          :loading="loading"
          :pagination="false"
          :single-line="false"
          size="small"
        />
      </div>

      <!-- 空状态 -->
      <div class="logs-empty" v-else>
        <div class="empty-illustration">
          <n-icon :size="64" color="var(--text-quaternary)"><DocumentTextOutline /></n-icon>
        </div>
        <div class="empty-title">暂无签到记录</div>
        <div class="empty-desc">签到后记录将显示在这里</div>
      </div>

      <!-- 分页 -->
      <div class="logs-pagination" v-if="pagination.itemCount > 0">
        <n-pagination
          v-model:page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :item-count="pagination.itemCount"
          :page-sizes="pagination.pageSizes"
          show-size-picker
          show-quick-jumper
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { NTag, type DataTableColumns } from 'naive-ui'
import {
  RefreshOutline,
  DocumentTextOutline,
  ListOutline
} from '@vicons/ionicons5'
import { signApi, accountApi } from '../api'
import { useFormat } from '../composables'

const { formatDateTime } = useFormat()

const loading = ref(false)
const logs = ref<any[]>([])
const accounts = ref<any[]>([])

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
  pageSizes: [10, 20, 50]
})

const accountOptions = ref<{ label: string; value: number }[]>([])

const statusOptions = [
  { label: '签到成功', value: true },
  { label: '签到失败', value: false }
]

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
      return '签到成功'
    case 'already_signed':
      return '今日已签到'
    case 'failed':
      return '签到失败'
    default:
      return '签到失败'
  }
}

const getRewardDisplay = (row: any) => {
  if (!row.reward_quota) return '-'
  return `+${row.reward_display || row.reward_quota}`
}

const columns = computed<DataTableColumns<any>>(() => [
  {
    title: '账号',
    key: 'username',
    minWidth: 180,
    ellipsis: { tooltip: true },
    render: (row) => row.username || `账号${row.account_id ?? '-'}`
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    align: 'center',
    render: (row) =>
      h(
        NTag,
        {
          type: getStatusTagType(row.status),
          size: 'small',
          bordered: false
        },
        {
          default: () => getStatusLabel(row.status)
        }
      )
  },
  {
    title: '奖励',
    key: 'reward',
    width: 130,
    align: 'center',
    render: (row) => h('span', { class: 'reward-value' }, getRewardDisplay(row))
  },
  {
    title: '签到结果',
    key: 'message',
    minWidth: 300,
    ellipsis: { tooltip: true },
    render: (row) => row.message || '-'
  },
  {
    title: '签到时间',
    key: 'sign_time',
    width: 200,
    render: (row) => (row.sign_time ? formatDateTime(row.sign_time) : '-')
  }
])

const loadAccounts = async () => {
  try {
    const res = await accountApi.getList()
    accounts.value = res.data || []
    accountOptions.value = accounts.value.map((a: any) => ({
      label: a.username || `账号${a.id}`,
      value: a.id
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

    const res = await signApi.getAllLogs(params)
    logs.value = res.data?.items || []
    pagination.value.itemCount = res.data?.total || 0
    pagination.value.page = page
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

onMounted(() => {
  loadAccounts()
  loadLogs()
})
</script>

<style scoped>
.sign-logs-page {
  margin: 0 auto;
  padding: var(--spacing-6);
}

/* 筛选卡片 */
.filter-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  padding: var(--spacing-4) var(--spacing-5);
  margin-bottom: var(--spacing-5);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-4);
  box-shadow: var(--shadow-sm);
}

.filter-left {
  display: flex;
  gap: var(--spacing-3);
  flex-wrap: wrap;
  align-items: center;
}

.filter-right {
  flex-shrink: 0;
}

/* 日志卡片 */
.logs-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
}

.card-title-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.card-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0;
}

.card-subtitle {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.logs-table-wrapper {
  padding: var(--spacing-3);
}

.logs-table {
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.logs-table :deep(.n-data-table-wrapper) {
  border-radius: var(--radius-lg);
}

.logs-table :deep(.n-data-table-th) {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
  font-weight: var(--font-semibold);
}

.logs-table :deep(.n-data-table-td),
.logs-table :deep(.n-data-table-th) {
  padding-top: 12px;
  padding-bottom: 12px;
}

.logs-table :deep(.n-data-table-tr:hover .n-data-table-td) {
  background: var(--bg-card-hover);
}

.logs-table :deep(.reward-value) {
  color: var(--warning-color);
  font-weight: var(--font-semibold);
}

/* 空状态 */
.logs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-10);
  text-align: center;
}

.empty-illustration {
  margin-bottom: var(--spacing-4);
  opacity: 0.5;
}

.empty-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-2);
}

.empty-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* 分页 */
.logs-pagination {
  display: flex;
  justify-content: center;
  padding: var(--spacing-5);
  border-top: 1px solid var(--border-color-light);
}

/* 响应式 */
@media (max-width: 768px) {
  .sign-logs-page {
    padding: var(--spacing-4);
  }

  .filter-card {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-left {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-left .n-select,
  .filter-left .n-date-picker {
    width: 100% !important;
  }

  .filter-right {
    width: 100%;
  }

  .filter-right .n-button {
    width: 100%;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-3);
  }

  .logs-table-wrapper {
    overflow-x: auto;
    padding: var(--spacing-2);
  }

  .logs-table {
    min-width: 860px;
  }
}

</style>
