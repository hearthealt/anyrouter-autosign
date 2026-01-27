<template>
  <div class="sign-logs-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-title">
        <div class="title-icon">📋</div>
        <div class="title-text">
          <h1>签到日志</h1>
          <p>查看所有账号的签到记录</p>
        </div>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon total">
          <n-icon :size="24"><DocumentTextOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pagination.itemCount }}</div>
          <div class="stat-label">总记录数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon success">
          <n-icon :size="24"><CheckmarkCircleOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value success">{{ stats.successCount }}</div>
          <div class="stat-label">签到成功</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon fail">
          <n-icon :size="24"><CloseCircleOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value fail">{{ stats.failCount }}</div>
          <div class="stat-label">签到失败</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon rate">
          <n-icon :size="24"><TrendingUpOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.successRate }}%</div>
          <div class="stat-label">成功率</div>
        </div>
      </div>
    </div>

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

    <!-- 签到日志列表 -->
    <div class="logs-card">
      <div class="card-header">
        <div class="card-title-section">
          <h3 class="card-title">
            <n-icon><ListOutline /></n-icon>
            签到记录
          </h3>
          <span class="card-subtitle">共 {{ pagination.itemCount }} 条记录</span>
        </div>
        <div class="card-actions">
          <n-button-group size="small">
            <n-button :type="viewMode === 'list' ? 'primary' : 'default'" @click="viewMode = 'list'">
              <template #icon><n-icon><ListOutline /></n-icon></template>
            </n-button>
            <n-button :type="viewMode === 'timeline' ? 'primary' : 'default'" @click="viewMode = 'timeline'">
              <template #icon><n-icon><GitBranchOutline /></n-icon></template>
            </n-button>
          </n-button-group>
        </div>
      </div>

      <!-- 列表视图 -->
      <div class="logs-list" v-if="!loading && logs.length > 0 && viewMode === 'list'">
        <div v-for="log in logs" :key="log.id" class="log-item" :class="{ success: log.success, fail: !log.success }">
          <div class="log-avatar">
            <span>{{ (log.username || 'U')[0].toUpperCase() }}</span>
          </div>
          <div class="log-content">
            <div class="log-header">
              <span class="log-username">{{ log.username || '未知账号' }}</span>
              <n-tag :type="log.success ? 'success' : 'error'" size="small" :bordered="false">
                {{ log.success ? '签到成功' : '签到失败' }}
              </n-tag>
              <span class="log-reward" v-if="log.reward_quota">+{{ log.reward_display }}</span>
            </div>
            <div class="log-body" v-if="log.message">
              <span class="log-message">{{ log.message }}</span>
            </div>
            <div class="log-footer">
              <span class="log-time">
                <n-icon><TimeOutline /></n-icon>
                {{ formatDateTime(log.sign_time) }}
              </span>
            </div>
          </div>
          <div class="log-status-indicator" :class="log.success ? 'success' : 'fail'"></div>
        </div>
      </div>

      <!-- 时间线视图 -->
      <div class="logs-timeline" v-if="!loading && logs.length > 0 && viewMode === 'timeline'">
        <div v-for="log in logs" :key="log.id" class="timeline-item" :class="{ success: log.success, fail: !log.success }">
          <div class="timeline-dot">
            <n-icon :size="14">
              <CheckmarkOutline v-if="log.success" />
              <CloseOutline v-else />
            </n-icon>
          </div>
          <div class="timeline-content">
            <div class="timeline-header">
              <span class="timeline-username">{{ log.username || '未知账号' }}</span>
              <span class="timeline-status" :class="log.success ? 'success' : 'fail'">
                {{ log.success ? '签到成功' : '签到失败' }}
              </span>
              <span class="timeline-reward" v-if="log.reward_quota">+{{ log.reward_display }}</span>
            </div>
            <div class="timeline-message" v-if="log.message">{{ log.message }}</div>
            <div class="timeline-time">{{ formatDateTime(log.sign_time) }}</div>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div class="logs-loading" v-if="loading">
        <n-spin size="medium" />
        <span>加载中...</span>
      </div>

      <!-- 空状态 -->
      <div class="logs-empty" v-if="!loading && logs.length === 0">
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
import { ref, onMounted } from 'vue'
import {
  RefreshOutline,
  CheckmarkOutline,
  CloseOutline,
  DocumentTextOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  TrendingUpOutline,
  TimeOutline,
  ListOutline,
  GitBranchOutline
} from '@vicons/ionicons5'
import { signApi, accountApi } from '../api'
import { useFormat } from '../composables'

const { formatDateTime } = useFormat()

const loading = ref(false)
const logs = ref<any[]>([])
const accounts = ref<any[]>([])
const viewMode = ref<'list' | 'timeline'>('list')

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

// 统计数据
const stats = ref({
  successCount: 0,
  failCount: 0,
  successRate: 0
})

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

    // 更新统计数据
    const successCount = res.data?.success_count || 0
    const failCount = res.data?.fail_count || 0
    const total = successCount + failCount
    const successRate = total > 0 ? Math.round((successCount / total) * 100) : 0
    stats.value = { successCount, failCount, successRate }
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

/* 页面标题 */
.page-header {
  margin-bottom: var(--spacing-6);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.title-icon {
  font-size: 36px;
}

.title-text h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-1) 0;
}

.title-text p {
  font-size: var(--text-md);
  color: var(--text-tertiary);
  margin: 0;
}

/* 统计概览 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  padding: var(--spacing-4);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.stat-icon.total {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.stat-icon.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.stat-icon.fail {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.stat-icon.rate {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-value.success {
  color: var(--success-color);
}

.stat-value.fail {
  color: var(--error-color);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-top: var(--spacing-1);
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

/* 列表视图 */
.logs-list {
  padding: var(--spacing-4);
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-4);
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-3);
  background: var(--bg-card-hover);
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
}

.log-item:last-child {
  margin-bottom: 0;
}

.log-item:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow-sm);
}

.log-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: white;
  flex-shrink: 0;
}

.log-item.success .log-avatar {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.log-item.fail .log-avatar {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.log-content {
  flex: 1;
  min-width: 0;
}

.log-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-1);
}

.log-username {
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  font-size: var(--text-md);
}

.log-reward {
  color: var(--warning-color);
  font-weight: var(--font-semibold);
  font-size: var(--text-sm);
  background: var(--warning-color-light);
  padding: 2px 8px;
  border-radius: var(--radius-md);
}

.log-body {
  margin-bottom: var(--spacing-2);
}

.log-message {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  line-height: 1.5;
}

.log-footer {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.log-time {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.log-status-indicator {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.log-status-indicator.success {
  background: var(--success-color);
}

.log-status-indicator.fail {
  background: var(--error-color);
}

/* 时间线视图 */
.logs-timeline {
  padding: var(--spacing-5);
}

.timeline-item {
  display: flex;
  gap: var(--spacing-4);
  padding: var(--spacing-3) 0;
  position: relative;
}

.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 11px;
  top: 36px;
  bottom: -12px;
  width: 2px;
  background: var(--border-color-light);
}

.timeline-dot {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.timeline-item.success .timeline-dot {
  background: var(--success-color-light);
  color: var(--success-color);
}

.timeline-item.fail .timeline-dot {
  background: var(--error-color-light);
  color: var(--error-color);
}

.timeline-content {
  flex: 1;
  min-width: 0;
  background: var(--bg-card-hover);
  border-radius: var(--radius-lg);
  padding: var(--spacing-3) var(--spacing-4);
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-1);
}

.timeline-username {
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.timeline-status {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  padding: 2px 8px;
  border-radius: var(--radius-md);
}

.timeline-status.success {
  background: var(--success-color-light);
  color: var(--success-color);
}

.timeline-status.fail {
  background: var(--error-color-light);
  color: var(--error-color);
}

.timeline-reward {
  font-size: var(--text-sm);
  color: var(--warning-color);
  font-weight: var(--font-medium);
}

.timeline-message {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-1);
}

.timeline-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* 加载状态 */
.logs-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  padding: var(--spacing-10);
  color: var(--text-tertiary);
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
@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .sign-logs-page {
    padding: var(--spacing-4);
  }

  .stats-row {
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-3);
  }

  .stat-card {
    padding: var(--spacing-3);
  }

  .stat-icon {
    width: 40px;
    height: 40px;
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

  .log-item {
    flex-direction: column;
    gap: var(--spacing-3);
  }

  .log-avatar {
    width: 36px;
    height: 36px;
    font-size: var(--text-md);
  }
}

@media (max-width: 480px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
