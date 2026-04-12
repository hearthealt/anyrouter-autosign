<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card accounts">
        <div class="stat-icon">
          <n-icon :size="26"><PeopleOutline /></n-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard?.account_count || 0 }}</div>
          <div class="stat-label">账号总数</div>
        </div>
        <span class="trend-badge error" v-if="(dashboard?.unhealthy_account_count ?? 0) > 0">
          {{ dashboard?.unhealthy_account_count }} 异常
        </span>
      </div>

      <div class="stat-card sign">
        <div class="stat-icon">
          <n-icon :size="26"><CheckmarkCircleOutline /></n-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ dashboard?.today_sign_success || 0 }}
            <span class="stat-sub">/{{ dashboard?.today_sign_count || 0 }}</span>
          </div>
          <div class="stat-label">今日签到</div>
          <div class="stat-progress">
            <n-progress
              type="line"
              :percentage="dashboard?.success_rate || 0"
              :show-indicator="false"
              :height="6"
              :border-radius="3"
              color="var(--success-color)"
              rail-color="var(--border-color-light)"
            />
            <span class="progress-text">{{ dashboard?.success_rate || 0 }}%</span>
          </div>
        </div>
      </div>

      <div class="stat-card reward">
        <div class="stat-icon">
          <n-icon :size="26"><GiftOutline /></n-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard?.month_reward_display || '$0.00' }}</div>
          <div class="stat-label">本月奖励</div>
        </div>
      </div>

      <div class="stat-card quota">
        <div class="stat-icon">
          <n-icon :size="26"><WalletOutline /></n-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard?.total_quota_display || '$0.00' }}</div>
          <div class="stat-label">总剩余额度</div>
        </div>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="quick-actions card">
      <div class="card-header">
        <h3 class="card-title">快捷操作</h3>
      </div>
      <div class="quick-actions-grid">
        <button class="quick-action-card" @click="handleBatchSign" :class="{ loading: batchSigning }" :disabled="batchSigning">
          <div class="card-icon" v-if="!batchSigning">⚡</div>
          <div class="card-icon loading-spinner" v-else><n-spin :size="18" /></div>
          <div class="card-text">
            <div class="card-title">{{ batchSigning ? '签到中...' : '一键签到' }}</div>
            <div class="card-desc">批量触发全部启用账号签到</div>
          </div>
        </button>

        <button class="quick-action-card" @click="refreshData" :class="{ loading: refreshing }" :disabled="refreshing">
          <div class="card-icon" v-if="!refreshing">🔄</div>
          <div class="card-icon loading-spinner" v-else><n-spin :size="18" /></div>
          <div class="card-text">
            <div class="card-title">{{ refreshing ? '刷新中...' : '刷新数据' }}</div>
            <div class="card-desc">更新仪表盘统计与账号状态</div>
          </div>
        </button>

        <button class="quick-action-card" @click="showAddModal">
          <div class="card-icon">➕</div>
          <div class="card-text">
            <div class="card-title">添加账号</div>
            <div class="card-desc">快速新增签到账号</div>
          </div>
        </button>

        <button class="quick-action-card" @click="handleSyncEndpoints" :class="{ loading: syncingEndpoints }" :disabled="syncingEndpoints">
          <div class="card-icon" v-if="!syncingEndpoints">🔗</div>
          <div class="card-icon loading-spinner" v-else><n-spin :size="18" /></div>
          <div class="card-text">
            <div class="card-title">{{ syncingEndpoints ? '同步中...' : '同步节点' }}</div>
            <div class="card-desc">获取最新 API 节点列表</div>
          </div>
        </button>

        <button class="quick-action-card" @click="$router.push('/statistics')">
          <div class="card-icon">📊</div>
          <div class="card-text">
            <div class="card-title">数据统计</div>
            <div class="card-desc">查看更完整的趋势分析</div>
          </div>
        </button>
      </div>
    </div>

    <div class="workspace-grid">
      <div class="workspace-main">
        <!-- 签到趋势 -->
        <div class="chart-card card trend-card">
          <div class="card-header">
            <h3 class="card-title">签到趋势</h3>
            <n-radio-group v-model:value="trendDays" size="small">
              <n-radio-button :value="7">7天</n-radio-button>
              <n-radio-button :value="30">30天</n-radio-button>
              <n-radio-button :value="60">60天</n-radio-button>
            </n-radio-group>
          </div>
          <div class="card-body chart-body">
            <TrendChart :data="dashboard?.daily_trend || []" :is-dark="isDarkMode" />
          </div>
        </div>

        <!-- 账号状态列表 -->
        <div class="status-card card">
          <div class="card-header">
            <h3 class="card-title">账号状态</h3>
            <n-button text size="small" @click="$router.push('/accounts')">账号管理</n-button>
          </div>

          <div class="status-filter-row">
            <div class="status-group" :class="{ active: statusFilter === 'healthy' }" @click="filterByStatus('healthy')">
              <div class="status-dot success"></div>
              <span class="status-label">健康</span>
              <span class="status-count">{{ healthyCount }}</span>
            </div>
            <div class="status-group" :class="{ active: statusFilter === 'unhealthy' }" @click="filterByStatus('unhealthy')">
              <div class="status-dot error"></div>
              <span class="status-label">异常</span>
              <span class="status-count">{{ unhealthyCount }}</span>
            </div>
            <div class="status-group" :class="{ active: statusFilter === 'pending' }" @click="filterByStatus('pending')">
              <div class="status-dot warning"></div>
              <span class="status-label">待签到</span>
              <span class="status-count">{{ pendingCount }}</span>
            </div>
            <div class="status-group" :class="{ active: statusFilter === 'disabled' }" @click="filterByStatus('disabled')" v-if="disabledCount > 0">
              <div class="status-dot disabled"></div>
              <span class="status-label">已禁用</span>
              <span class="status-count">{{ disabledCount }}</span>
            </div>
          </div>

          <div class="account-quick-list">
            <div
              v-for="account in displayAccounts.slice(0, 6)"
              :key="account.id"
              class="account-quick-item"
            >
              <div class="account-avatar" :class="{ inactive: !account.is_active }" @click="$router.push(`/account/${account.id}`)">
                {{ (account.username || 'U')[0].toUpperCase() }}
              </div>
              <div class="account-info" @click="$router.push(`/account/${account.id}`)">
                <span class="account-name">
                  {{ account.username || '-' }}
                  <span v-if="!account.is_active" class="disabled-tag">已禁用</span>
                </span>
                <span class="account-meta-line">
                  <span class="account-quota">{{ account.quota_display || '$0.00' }}</span>
                  <span class="meta-divider">·</span>
                  <span class="last-sign-time" v-if="account.last_sign">
                    {{ formatRelativeTime(account.last_sign.time) }}
                  </span>
                  <span class="last-sign-time" v-else>未签到</span>
                </span>
              </div>
              <div class="account-quick-actions">
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary circle @click.stop="handleSign(account)" :loading="signingId === account.id" :disabled="!account.is_active">
                      <template #icon><n-icon :size="16"><FlashOutline /></n-icon></template>
                    </n-button>
                  </template>
                  {{ account.is_active ? '签到' : '已禁用' }}
                </n-tooltip>
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary circle @click.stop="handleHealthCheck(account)" :loading="checkingId === account.id">
                      <template #icon><n-icon :size="16"><PulseOutline /></n-icon></template>
                    </n-button>
                  </template>
                  健康检查
                </n-tooltip>
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary circle @click.stop="showTokens(account)">
                      <template #icon><n-icon :size="16"><KeyOutline /></n-icon></template>
                    </n-button>
                  </template>
                  令牌管理
                </n-tooltip>
              </div>
              <div class="account-status" :class="account.is_active ? account.health_status : 'disabled'">
                <span class="status-indicator"></span>
              </div>
            </div>

            <div v-if="displayAccounts.length === 0" class="account-list-empty">
              暂无匹配的账号
            </div>

            <div v-if="accounts.length > 6" class="view-all" @click="$router.push('/accounts')">
              进入账号管理 · {{ accounts.length }} 个账号
            </div>
          </div>
        </div>
      </div>

      <div class="workspace-side">
        <!-- 额度分布 -->
        <div class="chart-card card quota-card">
          <div class="card-header">
            <h3 class="card-title">额度分布</h3>
          </div>
          <div class="card-body chart-body">
            <QuotaPieChart :accounts="accounts" :is-dark="isDarkMode" />
          </div>
        </div>

        <!-- 最近活动 -->
        <div class="activity-card card">
          <div class="card-header">
            <h3 class="card-title">最近活动</h3>
            <n-button text size="small" @click="$router.push('/logs')">
              更多
              <template #icon><n-icon><ChevronForwardOutline /></n-icon></template>
            </n-button>
          </div>
          <div class="activity-timeline">
            <div v-for="activity in recentActivities" :key="activity.id" class="timeline-item">
              <div class="timeline-dot" :class="activity.type"></div>
              <div class="timeline-content">
                <div class="timeline-title">
                  <span class="activity-account">{{ activity.account }}</span>
                  <span class="activity-action">{{ activity.action }}</span>
                </div>
                <div class="timeline-time">{{ activity.time }}</div>
              </div>
            </div>
            <div v-if="recentActivities.length === 0" class="timeline-empty">
              <n-icon :size="32" color="var(--text-tertiary)"><TimeOutline /></n-icon>
              <span>暂无活动记录</span>
            </div>
          </div>
        </div>

        <!-- API 节点 -->
        <div class="endpoints-card card">
          <div class="card-header">
            <h3 class="card-title">API 节点</h3>
            <n-button text size="small" @click="handleSyncEndpoints" :loading="syncingEndpoints">
              <template #icon><n-icon><SyncOutline /></n-icon></template>
              同步
            </n-button>
          </div>
          <div class="endpoints-list">
            <div v-for="ep in apiEndpoints" :key="ep.id" class="endpoint-item">
              <div class="endpoint-status" :class="ep.color"></div>
              <div class="endpoint-info">
                <span class="endpoint-name">{{ ep.route }}</span>
                <span class="endpoint-url">{{ ep.url }}</span>
              </div>
              <n-button size="tiny" quaternary @click="copyEndpoint(ep.url)">
                <template #icon><n-icon :size="14"><CopyOutline /></n-icon></template>
              </n-button>
            </div>
            <div v-if="apiEndpoints.length === 0" class="endpoints-empty">
              暂无节点，点击同步获取
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 弹窗 -->
    <AccountModal
      ref="accountModalRef"
      v-model:show="showAccountModal"
      :account="editingAccount"
      :groups="groups"
      @submit="handleAccountSubmit"
    />

    <TokensModal
      v-model:show="showTokensVisible"
      :account="tokenAccount"
      :tokens="tokens"
      :loading="loadingTokens"
      :syncing="syncingTokens"
      :deleting-id="deletingTokenId"
      @sync="handleSyncTokens"
      @delete="handleDeleteToken"
      @create="handleCreateToken"
      @edit="handleEditToken"
    />

    <!-- 全部账号弹窗 -->
    <n-modal v-model:show="showAllAccounts" preset="card" title="全部账号" style="width: 700px; max-width: 90vw;">
      <div class="all-accounts-list">
        <div
          v-for="account in displayAccounts"
          :key="account.id"
          class="account-list-item"
        >
          <div class="account-avatar" :class="{ inactive: !account.is_active }" @click="$router.push(`/account/${account.id}`)">
            {{ (account.username || 'U')[0].toUpperCase() }}
          </div>
          <div class="account-details" @click="$router.push(`/account/${account.id}`)">
            <div class="account-name">
              {{ account.username || '-' }}
              <span v-if="!account.is_active" class="disabled-tag">已禁用</span>
            </div>
            <div class="account-meta">
              <span>{{ account.quota_display || '$0.00' }}</span>
              <span class="divider">·</span>
              <span :class="['health', account.is_active ? account.health_status : 'disabled']">
                {{ !account.is_active ? '已禁用' : account.health_status === 'healthy' ? '正常' : account.health_status === 'unhealthy' ? '异常' : '未知' }}
              </span>
              <span class="divider">·</span>
              <span class="sign-time">
                {{ account.last_sign ? formatRelativeTime(account.last_sign.time) : '未签到' }}
              </span>
            </div>
          </div>
          <div class="account-actions">
            <n-button-group size="small">
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-button @click.stop="handleSign(account)" :loading="signingId === account.id" :disabled="!account.is_active">
                    <template #icon><n-icon><FlashOutline /></n-icon></template>
                  </n-button>
                </template>
                {{ account.is_active ? '签到' : '已禁用' }}
              </n-tooltip>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-button @click.stop="handleHealthCheck(account)" :loading="checkingId === account.id">
                    <template #icon><n-icon><PulseOutline /></n-icon></template>
                  </n-button>
                </template>
                健康检查
              </n-tooltip>
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-button @click.stop="showTokens(account)">
                    <template #icon><n-icon><KeyOutline /></n-icon></template>
                  </n-button>
                </template>
                令牌管理
              </n-tooltip>
            </n-button-group>
          </div>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { TrendChart, AccountModal, QuotaPieChart, TokensModal } from '../components/dashboard'
import { accountApi, dashboardApi, notifyApi, apiEndpointsApi, groupsApi, signApi, statisticsApi } from '../api'
import type { Account, AccountGroup, ApiToken, DashboardData, ApiEndpoint, CreateTokenParams } from '../types'
import {
  PeopleOutline,
  CheckmarkCircleOutline,
  GiftOutline,
  WalletOutline,
  FlashOutline,
  SyncOutline,
  CopyOutline,
  ChevronForwardOutline,
  TimeOutline,
  PulseOutline,
  KeyOutline
} from '@vicons/ionicons5'
import { useFormat } from '../composables'

const { formatRelativeTime } = useFormat()

// 主题检测
const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
mediaQuery.addEventListener('change', (e) => {
  isDarkMode.value = e.matches
})

// 数据状态
const loading = ref(false)
const accounts = ref<Account[]>([])
const groups = ref<AccountGroup[]>([])
const dashboard = ref<DashboardData | null>(null)
const apiEndpoints = ref<ApiEndpoint[]>([])
const trendDays = ref(7)
const statusFilter = ref<string | null>(null)
const showAllAccounts = ref(false)

// 计算属性
const healthyCount = computed(() => accounts.value.filter(a => a.is_active && a.health_status === 'healthy').length)
const unhealthyCount = computed(() => accounts.value.filter(a => a.is_active && a.health_status === 'unhealthy').length)
const pendingCount = computed(() => accounts.value.filter(a => a.is_active && (!a.last_sign || !isToday(a.last_sign.time))).length)
const disabledCount = computed(() => accounts.value.filter(a => !a.is_active).length)

const displayAccounts = computed(() => {
  if (!statusFilter.value) return accounts.value
  if (statusFilter.value === 'pending') {
    return accounts.value.filter(a => a.is_active && (!a.last_sign || !isToday(a.last_sign.time)))
  }
  if (statusFilter.value === 'disabled') {
    return accounts.value.filter(a => !a.is_active)
  }
  return accounts.value.filter(a => a.is_active && a.health_status === statusFilter.value)
})

// 最近活动
const recentActivities = computed(() => {
  const activities: Array<{ id: number; account: string; action: string; type: string; time: string }> = []
  accounts.value.forEach(account => {
    if (account.last_sign) {
      activities.push({
        id: account.id,
        account: account.username || '未知账号',
        action: account.last_sign.success ? '签到成功' : '签到失败',
        type: account.last_sign.success ? 'success' : 'error',
        time: formatRelativeTime(account.last_sign.time)
      })
    }
  })
  return activities.slice(0, 8)
})

// 辅助函数
const isToday = (dateStr: string) => {
  const date = new Date(dateStr)
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

const filterByStatus = (status: string) => {
  statusFilter.value = statusFilter.value === status ? null : status
}

// 复制节点地址
const copyEndpoint = async (url: string) => {
  try {
    await navigator.clipboard.writeText(url)
    window.$notify('已复制到剪贴板', 'success')
  } catch {
    window.$notify('复制失败', 'error')
  }
}

// 签到状态
const signingId = ref<number | null>(null)
const batchSigning = ref(false)
const checkingId = ref<number | null>(null)
const refreshing = ref(false)

// API 节点状态
const syncingEndpoints = ref(false)

// 账号弹窗状态
const showAccountModal = ref(false)
const editingAccount = ref<Account | null>(null)
const accountModalRef = ref<InstanceType<typeof AccountModal> | null>(null)

// Token 弹窗状态
const showTokensVisible = ref(false)
const tokenAccount = ref<Account | null>(null)
const tokens = ref<ApiToken[]>([])
const loadingTokens = ref(false)
const syncingTokens = ref(false)
const deletingTokenId = ref<number | null>(null)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const [accountsRes, dashboardRes] = await Promise.all([
      accountApi.getList(),
      dashboardApi.get()
    ])
    accounts.value = accountsRes.data || []
    dashboard.value = dashboardRes.data
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loading.value = false
  }
}

// 加载趋势数据
const loadTrendData = async (days: number) => {
  try {
    const res = await statisticsApi.getDaily(days)
    if (dashboard.value && res.data) {
      // 创建新对象来触发响应式更新
      dashboard.value = {
        ...dashboard.value,
        daily_trend: res.data
      }
    }
  } catch (e: any) {
    console.error('Failed to load trend data:', e)
  }
}

const loadGroups = async () => {
  try {
    const res = await groupsApi.getList()
    groups.value = res.data || []
  } catch (e) {
    console.error('Failed to load groups:', e)
  }
}

const loadEndpoints = async () => {
  try {
    const res = await apiEndpointsApi.getList()
    apiEndpoints.value = res.data || []
  } catch (e) {
    console.error('Failed to load endpoints:', e)
  }
}

// 一键签到
const handleBatchSign = async () => {
  batchSigning.value = true
  try {
    const res: any = await signApi.batchSign()
    window.$notify(res.message || '批量签到完成', 'success')
    loadData()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    batchSigning.value = false
  }
}

// 刷新数据
const refreshData = async () => {
  refreshing.value = true
  try {
    await loadData()
    window.$notify('数据已刷新', 'success')
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    refreshing.value = false
  }
}

// 显示添加账号弹窗
const showAddModal = () => {
  editingAccount.value = null
  showAccountModal.value = true
}

// 同步 API 节点
const handleSyncEndpoints = async () => {
  syncingEndpoints.value = true
  try {
    const res: any = await apiEndpointsApi.sync()
    window.$notify(res.message || '同步成功', 'success')
    loadEndpoints()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    syncingEndpoints.value = false
  }
}

const handleAccountSubmit = async (data: any) => {
  try {
    if (editingAccount.value) {
      const updateData: any = { is_active: data.is_active }
      if (data.user_id.trim()) updateData.user_id = data.user_id.trim()
      if (data.session_cookie.trim()) updateData.session_cookie = data.session_cookie.trim()
      if (data.clear_login_credentials) {
        updateData.clear_login_credentials = true
      } else {
        const previousLoginUsername = editingAccount.value.login_username?.trim() || ''
        const currentLoginUsername = data.login_username.trim()
        if (currentLoginUsername && currentLoginUsername !== previousLoginUsername) {
          updateData.login_username = currentLoginUsername
        }
        if (data.login_password) {
          updateData.login_password = data.login_password
        }
      }
      if (data.group_id !== editingAccount.value.group_id) {
        updateData.group_id = data.group_id || 0
      }
      if (data.platform_id) {
        updateData.platform_id = data.platform_id
      }
      await accountApi.update(editingAccount.value.id, updateData)

      const notifyData = {
        channels: data.notify_channel_ids.map((id: number) => ({
          channel_id: id,
          is_enabled: true,
          notify_config: {}
        }))
      }
      await notifyApi.updateAccountNotify(editingAccount.value.id, notifyData)
      window.$notify('更新成功', 'success')
    } else {
      const res = await accountApi.create({
        session_cookie: data.session_cookie.trim() || undefined,
        user_id: data.user_id.trim(),
        login_username: data.login_username.trim() || undefined,
        login_password: data.login_password || undefined,
        platform_id: data.platform_id,
        group_id: data.group_id || undefined
      })

      if (data.notify_channel_ids.length > 0 && res.data?.id) {
        const notifyData = {
          channels: data.notify_channel_ids.map((id: number) => ({
            channel_id: id,
            is_enabled: true,
            notify_config: {}
          }))
        }
        await notifyApi.updateAccountNotify(res.data.id, notifyData)
      }
      window.$notify('账号添加成功', 'success')
    }

    showAccountModal.value = false
    loadData()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    accountModalRef.value?.setSubmitting(false)
  }
}

// 签到操作
const handleSign = async (account: Account) => {
  if (!account.is_active) {
    window.$notify('该账号已禁用，无法签到', 'warning')
    return
  }
  signingId.value = account.id
  try {
    const res = await signApi.sign(account.id)
    window.$notify(res.data?.message || '签到成功', 'success')
    loadData()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    signingId.value = null
  }
}

// 健康检查
const handleHealthCheck = async (account: Account) => {
  checkingId.value = account.id
  try {
    await accountApi.healthCheck(account.id)
    window.$notify('健康检查完成', 'success')
    loadData()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    checkingId.value = null
  }
}

// 显示令牌管理
const showTokens = async (account: Account) => {
  tokenAccount.value = account
  showTokensVisible.value = true
  loadingTokens.value = true
  try {
    const res = await accountApi.getTokens(account.id)
    tokens.value = res.data || []
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loadingTokens.value = false
  }
}
// Token 操作
const handleSyncTokens = async () => {
  if (!tokenAccount.value) return
  syncingTokens.value = true
  try {
    await accountApi.syncTokens(tokenAccount.value.id)
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    window.$notify('刷新成功', 'success')
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    syncingTokens.value = false
  }
}

const handleDeleteToken = async (token: ApiToken) => {
  if (!tokenAccount.value) return
  deletingTokenId.value = token.token_id
  try {
    await accountApi.deleteToken(tokenAccount.value.id, token.token_id)
    window.$notify('删除成功', 'success')
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    deletingTokenId.value = null
  }
}

const handleCreateToken = async (data: CreateTokenParams, done?: (success: boolean) => void) => {
  if (!tokenAccount.value) {
    done?.(false)
    return false
  }
  try {
    await accountApi.createToken(tokenAccount.value.id, data)
    window.$notify('令牌创建成功', 'success')
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    done?.(true)
    return true
  } catch (e: any) {
    window.$notify(e.message, 'error')
    done?.(false)
    return false
  }
}

const handleEditToken = async (tokenId: number, data: CreateTokenParams, done?: (success: boolean) => void) => {
  if (!tokenAccount.value) {
    done?.(false)
    return false
  }
  try {
    await accountApi.updateToken(tokenAccount.value.id, tokenId, data)
    window.$notify('令牌更新成功', 'success')
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    done?.(true)
    return true
  } catch (e: any) {
    window.$notify(e.message, 'error')
    done?.(false)
    return false
  }
}

onMounted(() => {
  loadData()
  loadGroups()
  loadEndpoints()
  // 初始加载趋势数据
  loadTrendData(trendDays.value)
})

// 监听趋势天数变化
watch(trendDays, (newDays) => {
  loadTrendData(newDays)
})
</script>

<style scoped>
.dashboard {
  max-width: 1500px;
  margin: 0 auto;
  padding: var(--spacing-6);
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
}

.card-title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-5);
}

.stat-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-4);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  background: var(--bg-card);
  padding: var(--spacing-5);
  min-height: 132px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 4px;
  border-radius: var(--radius-xl) 0 0 var(--radius-xl);
  background: var(--primary-color);
  opacity: 0.7;
}

.stat-card.sign::before {
  background: var(--success-color);
}

.stat-card.reward::before {
  background: var(--warning-color);
}

.stat-card.quota::before {
  background: var(--info-color);
}

.stat-icon {
  width: 54px;
  height: 54px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--primary-color);
  background: rgba(124, 58, 237, 0.12);
}

.stat-card.sign .stat-icon {
  color: var(--success-color);
  background: rgba(24, 160, 88, 0.12);
}

.stat-card.reward .stat-icon {
  color: var(--warning-color);
  background: rgba(240, 160, 32, 0.14);
}

.stat-card.quota .stat-icon {
  color: var(--info-color);
  background: rgba(32, 128, 240, 0.14);
}

.stat-info {
  min-width: 0;
  flex: 1;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-sub {
  font-size: var(--text-md);
  font-weight: var(--font-normal);
  color: var(--text-tertiary);
}

.stat-label {
  margin-top: 4px;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.trend-badge {
  position: absolute;
  right: var(--spacing-3);
  top: var(--spacing-3);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.trend-badge.error {
  color: var(--error-color);
  background: rgba(208, 48, 80, 0.12);
}

.stat-progress {
  margin-top: var(--spacing-2);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.progress-text {
  font-size: var(--text-xs);
  color: var(--success-color);
  font-weight: var(--font-semibold);
}

.quick-actions {
  margin-bottom: var(--spacing-6);
}

.quick-actions-grid {
  padding: var(--spacing-3);
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--spacing-2);
}

.quick-action-card {
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-lg);
  background: var(--bg-card);
  width: 100%;
  text-align: left;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-3);
  min-height: 108px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-action-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--primary-color);
}

.quick-action-card:disabled,
.quick-action-card.loading {
  opacity: 0.72;
  cursor: not-allowed;
}

.quick-action-card .card-icon {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  background: var(--bg-card-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 18px;
}

.quick-action-card .card-text {
  min-width: 0;
  width: 100%;
}

.quick-action-card .card-title {
  margin: 0;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.quick-action-card .card-desc {
  margin-top: 2px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  line-height: 1.35;
  min-height: 32px;
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.9fr);
  gap: var(--spacing-5);
}

.workspace-main,
.workspace-side {
  min-width: 0;
  display: grid;
  gap: var(--spacing-5);
  align-content: start;
}

.trend-card .chart-body {
  height: 300px;
  padding: var(--spacing-3) var(--spacing-4);
}

.quota-card .chart-body {
  height: 300px;
}

.chart-body {
  padding: var(--spacing-4);
}

.trend-card :deep(.trend-section) {
  margin: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.trend-card :deep(.section-header) {
  display: none;
}

.trend-card :deep(.trend-chart-container) {
  height: 100%;
  min-height: 0;
  flex: 1;
  margin-top: 0;
}

.quota-card :deep(.quota-pie-section) {
  height: 100%;
  min-height: 0;
}

.quota-card :deep(.pie-chart-container) {
  height: 100%;
  min-height: 0;
}

.status-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
}

.status-group {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: 6px 12px;
  border-radius: var(--radius-full);
  background: var(--bg-card-hover);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: var(--text-sm);
}

.status-group:hover {
  border-color: var(--border-color-light);
}

.status-group.active {
  color: white;
  background: var(--primary-color);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.success {
  background: var(--success-color);
}

.status-dot.error {
  background: var(--error-color);
}

.status-dot.warning {
  background: var(--warning-color);
}

.status-dot.disabled {
  background: var(--text-quaternary);
}

.status-group.active .status-dot {
  background: white;
}

.status-count {
  font-weight: var(--font-semibold);
}

.account-quick-list {
  max-height: 560px;
  overflow-y: auto;
}

.account-quick-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
  transition: background var(--transition-fast);
}

.account-quick-item:hover {
  background: var(--bg-card-hover);
}

.account-quick-item:last-child {
  border-bottom: none;
}

.account-avatar {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #00b38a 0%, #18a058 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: var(--font-semibold);
  flex-shrink: 0;
  cursor: pointer;
}

.account-avatar.inactive {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

.account-info {
  min-width: 0;
  flex: 1;
  cursor: pointer;
}

.account-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.disabled-tag {
  display: inline-flex;
  align-items: center;
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  background: rgba(148, 163, 184, 0.12);
}

.account-meta-line {
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.account-quota {
  color: var(--success-color);
  font-weight: var(--font-medium);
}

.meta-divider {
  color: var(--text-quaternary);
}

.account-quick-actions {
  display: flex;
  gap: var(--spacing-1);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.account-quick-item:hover .account-quick-actions {
  opacity: 1;
}

.account-status {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 3px;
}

.status-indicator {
  display: block;
  width: 100%;
  height: 100%;
  opacity: 0.75;
}

.account-status.healthy .status-indicator {
  background: var(--success-color);
}

.account-status.unhealthy .status-indicator {
  background: var(--error-color);
}

.account-status.unknown .status-indicator {
  background: var(--warning-color);
}

.account-status.disabled .status-indicator {
  background: var(--text-quaternary);
}

.account-list-empty {
  padding: var(--spacing-8) 0;
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.view-all {
  border-top: 1px solid var(--border-color-light);
  padding: var(--spacing-3);
  text-align: center;
  color: var(--primary-color);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.view-all:hover {
  background: var(--bg-card-hover);
}

.activity-timeline {
  padding: var(--spacing-4) var(--spacing-5);
  max-height: 280px;
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.timeline-dot.success {
  background: var(--success-color);
}

.timeline-dot.error {
  background: var(--error-color);
}

.timeline-content {
  min-width: 0;
  flex: 1;
}

.timeline-title {
  margin-bottom: 2px;
}

.activity-account {
  margin-right: var(--spacing-1);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.activity-action {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.timeline-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.timeline-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-8) 0;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.endpoints-list {
  padding: var(--spacing-3) var(--spacing-4);
  max-height: 260px;
  overflow-y: auto;
}

.endpoint-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-2);
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.endpoint-item:hover {
  background: var(--bg-card-hover);
}

.endpoint-status {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--info-color);
}

.endpoint-status.green {
  background: var(--success-color);
}

.endpoint-status.yellow {
  background: var(--warning-color);
}

.endpoint-status.red {
  background: var(--error-color);
}

.endpoint-status.blue {
  background: var(--info-color);
}

.endpoint-info {
  min-width: 0;
  flex: 1;
}

.endpoint-name {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

.endpoint-url {
  display: block;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.endpoints-empty {
  padding: var(--spacing-6) 0;
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.all-accounts-list {
  max-height: 70vh;
  overflow-y: auto;
}

.account-list-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
  transition: background var(--transition-fast);
}

.account-list-item:hover {
  background: var(--bg-card-hover);
}

.account-list-item:last-child {
  border-bottom: none;
}

.account-details {
  min-width: 0;
  flex: 1;
  cursor: pointer;
}

.account-meta {
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.divider {
  color: var(--text-quaternary);
}

.health.healthy {
  color: var(--success-color);
}

.health.unhealthy {
  color: var(--error-color);
}

.health.disabled {
  color: var(--text-tertiary);
}

.account-actions {
  flex-shrink: 0;
}

@media (max-width: 1320px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .quick-actions-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 1080px) {
  .workspace-grid {
    grid-template-columns: 1fr;
  }

  .workspace-side {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-side .endpoints-card {
    grid-column: span 2;
  }

  .quick-actions-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: var(--spacing-4);
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .quick-actions-grid {
    grid-template-columns: 1fr;
  }

  .workspace-side {
    grid-template-columns: 1fr;
  }

  .workspace-side .endpoints-card {
    grid-column: span 1;
  }

  .account-quick-actions {
    opacity: 1;
  }

  .quick-action-card .card-desc {
    min-height: auto;
  }

  .trend-card :deep(.trend-chart-container) {
    height: 100%;
  }

  .trend-card .chart-body,
  .quota-card .chart-body {
    height: 240px;
  }
}

@media (max-width: 560px) {
  .card-header {
    padding: var(--spacing-3) var(--spacing-4);
  }

  .status-filter-row,
  .activity-timeline {
    padding: var(--spacing-3) var(--spacing-4);
  }

  .account-quick-item {
    padding: var(--spacing-3) var(--spacing-4);
  }

  .account-list-item {
    flex-wrap: wrap;
  }

  .account-actions {
    width: 100%;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
