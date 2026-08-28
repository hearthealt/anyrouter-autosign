<template>
  <div class="dashboard">
    <section class="page-toolbar dashboard-toolbar" aria-label="总览操作">
      <div class="page-toolbar__summary">
        <span class="page-toolbar__label"><Activity :size="15" /> 实时概览</span>
        <div class="filter-meta page-toolbar__meta">
          <span>24H 成功率 <strong>{{ dashboard?.success_rate || 0 }}%</strong></span>
          <span class="success">成功 <strong>{{ dashboard?.today_sign_success || 0 }}</strong></span>
          <span>执行 <strong>{{ dashboard?.today_sign_count || 0 }}</strong></span>
        </div>
      </div>
      <div class="page-toolbar__actions">
        <UiButton size="small" :loading="refreshing" @click="refreshData">
          <template #icon><RefreshCw :size="14" /></template>
          刷新数据
        </UiButton>
        <UiButton size="small" @click="showAddModal">
          <template #icon><Plus :size="14" /></template>
          添加账号
        </UiButton>
        <UiButton size="small" type="primary" :loading="batchSigning" @click="handleBatchSign">
          <template #icon><Zap :size="14" /></template>
          一键签到
        </UiButton>
      </div>
    </section>

    <section class="status-rail" aria-label="账号运行状态">
      <div class="rail-intro">
        <span class="section-code">SYS / 02</span>
        <strong>运行信号</strong>
        <span>ACCOUNT HEALTH</span>
      </div>
      <div class="rail-items">
        <button
          class="rail-item rail-item-success"
          :class="{ active: statusFilter === 'normal' }"
          :aria-pressed="statusFilter === 'normal'"
          @click="filterByStatus('normal')"
        >
          <span class="rail-item-mark"><span class="status-dot success" aria-hidden="true"></span></span>
          <span class="rail-item-copy"><small>READY</small><b>正常</b></span>
          <strong class="rail-item-count">{{ normalCount }}</strong>
        </button>
        <button
          class="rail-item rail-item-error"
          :class="{ active: statusFilter === 'unhealthy' }"
          :aria-pressed="statusFilter === 'unhealthy'"
          @click="filterByStatus('unhealthy')"
        >
          <span class="rail-item-mark"><span class="status-dot error" aria-hidden="true"></span></span>
          <span class="rail-item-copy"><small>ATTENTION</small><b>异常</b></span>
          <strong class="rail-item-count">{{ unhealthyCount }}</strong>
        </button>
        <button
          v-if="disabledCount > 0"
          class="rail-item rail-item-muted"
          :class="{ active: statusFilter === 'disabled' }"
          :aria-pressed="statusFilter === 'disabled'"
          @click="filterByStatus('disabled')"
        >
          <span class="rail-item-mark"><span class="status-dot default" aria-hidden="true"></span></span>
          <span class="rail-item-copy"><small>PAUSED</small><b>已禁用</b></span>
          <strong class="rail-item-count">{{ disabledCount }}</strong>
        </button>
      </div>
      <div class="rail-total">
        <span class="rail-total-label">TOTAL ACCOUNTS</span>
        <strong>{{ accounts.length }}</strong>
        <span class="rail-total-line" aria-hidden="true"></span>
      </div>
    </section>

    <div v-if="lowQuotaAccounts.length > 0" class="warning-banner">
      <div class="warning-symbol" aria-hidden="true"><Activity :size="16" /></div>
      <div class="warning-copy">
        <div class="warning-title">有 {{ lowQuotaAccounts.length }} 个账号低于额度告警阈值</div>
        <div class="warning-desc">
          阈值 ${{ quotaWarningThreshold.toFixed(2) }}，
          {{ lowQuotaAccounts.slice(0, 4).map(account => `${account.username || '未命名'} ${account.quota_display || '$0.00'}`).join(' · ') }}
        </div>
      </div>
      <UiButton size="small" type="warning" @click="$router.push('/accounts')">
        去账号页处理
        <template #icon><ChevronRight :size="13" /></template>
      </UiButton>
    </div>

    <section class="metrics-section" aria-label="核心指标">
      <div class="section-heading">
        <div>
          <span class="section-code">SYS / 03</span>
          <h2>核心读数</h2>
        </div>
        <span class="section-aside">LIVE / SNAPSHOT</span>
      </div>

      <div class="metrics-grid" v-if="!initialLoading">
        <div class="metric-card metric-card-accounts interactive" @click="$router.push('/accounts')">
          <div class="metric-topline">
            <div class="metric-label">账号总数</div>
            <span class="metric-icon" aria-hidden="true"><Users :size="17" /></span>
          </div>
          <div class="metric-value">{{ dashboard?.account_count || 0 }}</div>
          <div class="metric-foot account-status-foot">
            <span class="metric-delta up">正常 {{ normalCount }}</span>
            <span v-if="unhealthyCount > 0" class="metric-delta down">异常 {{ unhealthyCount }}</span>
            <span v-if="disabledCount > 0" class="metric-sub-label">禁用 {{ disabledCount }}</span>
          </div>
          <span class="metric-index">01</span>
        </div>

        <div class="metric-card metric-card-sign interactive" @click="$router.push({ path: '/logs', query: { today: '1' } })">
          <div class="metric-topline">
            <div class="metric-label">今日签到</div>
            <span class="metric-icon" aria-hidden="true"><Zap :size="17" /></span>
          </div>
          <div class="metric-value">
            {{ dashboard?.today_sign_success || 0 }}
            <span class="metric-sub">/ {{ dashboard?.today_sign_count || 0 }}</span>
          </div>
          <div class="metric-foot">
            <div class="metric-bar"><span class="metric-bar-fill" :style="{ width: `${dashboard?.success_rate || 0}%` }"></span></div>
            <span class="metric-bar-text">{{ dashboard?.success_rate || 0 }}%</span>
          </div>
          <span class="metric-index">02</span>
        </div>

        <div class="metric-card metric-card-rewards interactive" @click="$router.push('/statistics')">
          <div class="metric-topline">
            <div class="metric-label">本月奖励</div>
            <span class="metric-icon" aria-hidden="true"><Activity :size="17" /></span>
          </div>
          <div class="metric-value metric-value-rewards">{{ monthRewardDisplay }}</div>
          <div class="metric-foot"><span class="metric-sub-label">累计签到所得</span></div>
          <span class="metric-index">03</span>
        </div>

        <div class="metric-card metric-card-quota interactive" @click="$router.push('/accounts')">
          <div class="metric-topline">
            <div class="metric-label">总剩余额度</div>
            <span class="metric-icon" aria-hidden="true"><KeyRound :size="17" /></span>
          </div>
          <div class="metric-value">{{ dashboard?.total_quota_display || '$0.00' }}</div>
          <div class="metric-foot"><span class="metric-sub-label">全部账号</span></div>
          <span class="metric-index">04</span>
        </div>
      </div>
      <div class="metrics-grid" v-else aria-busy="true" aria-label="加载中">
        <div v-for="i in 4" :key="i" class="metric-card">
          <UiSkeleton text :width="64" :height="12" />
          <UiSkeleton text :width="96" :height="28" style="margin-top: 12px" />
          <UiSkeleton text :width="80" :height="12" style="margin-top: 12px" />
        </div>
      </div>
    </section>

    <section class="workspace" aria-label="运行工作区">
      <div class="workspace-main">
        <div class="panel trend-panel">
          <div class="panel-head">
            <div class="panel-heading">
              <span class="panel-code">FLOW / 07—60D</span>
              <div class="panel-title">签到趋势</div>
            </div>
            <UiSegment v-model:value="trendDays" size="small" :options="[{ label: '7 天', value: 7 }, { label: '30 天', value: 30 }, { label: '60 天', value: 60 }]" />
          </div>
          <div class="panel-body chart-body">
            <TrendChart :data="dashboard?.daily_trend || []" :is-dark="isDarkMode" />
          </div>
        </div>

        <div class="panel accounts-panel">
          <div class="panel-head">
            <div class="panel-heading">
              <span class="panel-code">NODES / ACCOUNT MATRIX</span>
              <div class="panel-title">账号状态</div>
            </div>
            <UiButton text size="small" @click="$router.push('/accounts')">
              全部账号
              <template #icon><ChevronRight :size="12" /></template>
            </UiButton>
          </div>
          <div class="panel-subhead">
            <span>
              <span v-if="statusFilter === 'normal'">正在查看：正常账号</span>
              <span v-else-if="statusFilter === 'unhealthy'">正在查看：异常账号</span>
              <span v-else-if="statusFilter === 'disabled'">正在查看：已禁用账号</span>
              <span v-else>最近 6 个账号 · 点击行进入详情</span>
            </span>
            <span class="panel-subhead-count">{{ displayAccounts.length }} / {{ accounts.length }}</span>
          </div>
          <div class="account-rows">
            <div
              v-for="(account, index) in displayAccounts.slice(0, 6)"
              :key="account.id"
              class="account-row"
              :class="{ alert: getAccountStatus(account) === 'unhealthy' || isLowQuota(account) }"
              @click="$router.push(`/account/${account.id}`)"
            >
              <span class="row-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="row-avatar" :class="{ inactive: !account.is_active }">
                {{ (account.username || 'U')[0].toUpperCase() }}
              </div>
              <div class="row-main">
                <div class="row-title">
                  {{ account.username || '-' }}
                  <span
                    v-if="account.is_active"
                    class="row-status-dot"
                    :class="{
                      success: getAccountStatus(account) === 'normal',
                      error: getAccountStatus(account) === 'unhealthy'
                    }"
                  ></span>
                </div>
                <div class="row-meta">
                  <span class="row-quota" :class="{ danger: isLowQuota(account) }">{{ account.quota_display || '$0.00' }}</span>
                  <span class="divider">·</span>
                  <span>{{ account.last_sign ? formatRelativeTime(account.last_sign.time) : '未签到' }}</span>
                  <span v-if="!account.is_active" class="row-tag">已禁用</span>
                  <span v-else-if="isLowQuota(account)" class="row-tag warning">低额度</span>
                </div>
              </div>
              <div class="row-actions" @click.stop>
                <UiTooltip trigger="hover">
                  <template #trigger>
                    <UiButton size="tiny" quaternary :loading="signingId === account.id" :disabled="!account.is_active" @click="handleSign(account)">
                      <template #icon><Zap :size="14" /></template>
                    </UiButton>
                  </template>
                  签到
                </UiTooltip>
                <UiTooltip trigger="hover">
                  <template #trigger>
                    <UiButton size="tiny" quaternary :loading="checkingId === account.id" @click="handleHealthCheck(account)">
                      <template #icon><Activity :size="14" /></template>
                    </UiButton>
                  </template>
                  健康检查
                </UiTooltip>
                <UiTooltip trigger="hover">
                  <template #trigger>
                    <UiButton size="tiny" quaternary @click="showTokens(account)">
                      <template #icon><KeyRound :size="14" /></template>
                    </UiButton>
                  </template>
                  令牌
                </UiTooltip>
              </div>
            </div>
            <div v-if="displayAccounts.length === 0" class="row-empty">
              <Users :size="20" />
              <span>{{ accounts.length === 0 ? '还没有账号，先确认平台配置再添加账号' : '暂无匹配账号' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="workspace-side">
        <div class="panel quota-panel">
          <div class="panel-head">
            <div class="panel-heading">
              <span class="panel-code">CAPACITY / DISTRIBUTION</span>
              <div class="panel-title">额度分布</div>
            </div>
            <span class="panel-signal"><span class="status-dot info"></span> LIVE</span>
          </div>
          <div class="panel-body chart-body">
            <QuotaPieChart :accounts="accounts" :is-dark="isDarkMode" />
          </div>
        </div>

        <div class="panel activity-panel">
          <div class="panel-head">
            <div class="panel-heading">
              <span class="panel-code">EVENT STREAM / 08</span>
              <div class="panel-title">最近活动</div>
            </div>
            <UiButton text size="small" @click="$router.push('/logs')">
              更多
              <template #icon><ChevronRight :size="12" /></template>
            </UiButton>
          </div>
          <div class="activity-list">
            <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
              <span class="activity-dot" :class="activity.type"></span>
              <div class="activity-main">
                <div class="activity-title">
                  <b>{{ activity.account }}</b>
                  <span class="activity-action" :class="activity.type">{{ activity.action }}</span>
                </div>
                <div class="activity-time">{{ activity.time }}</div>
              </div>
              <span class="activity-arrow" aria-hidden="true"><ChevronRight :size="13" /></span>
            </div>
            <div v-if="recentActivities.length === 0" class="row-empty">
              <Clock :size="20" />
              <span>暂无活动</span>
            </div>
          </div>
        </div>

        <div class="panel endpoint-panel">
          <div class="panel-head">
            <div class="panel-heading">
              <span class="panel-code">NETWORK / ROUTES</span>
              <div class="panel-title">API 节点</div>
            </div>
            <div class="panel-head-actions">
              <UiSelect
                v-model:value="selectedPlatformId"
                :options="platformOptions"
                size="tiny"
                placeholder="平台"
                :loading="loadingPlatforms"
                class="platform-select"
              />
              <UiButton text size="small" :loading="syncingEndpoints" @click="handleSyncEndpoints">
                <template #icon><RefreshCcw :size="12" /></template>
                同步
              </UiButton>
            </div>
          </div>
          <div class="endpoints-list">
            <div v-for="ep in apiEndpoints" :key="ep.id" class="endpoint-row">
              <span class="endpoint-dot" :class="ep.color"></span>
              <div class="endpoint-main">
                <div class="endpoint-name">{{ ep.route }}</div>
                <ExternalLink class="endpoint-url" :href="ep.url" mono />
              </div>
              <UiButton size="tiny" quaternary @click="copyEndpoint(ep.url)">
                <template #icon><Copy :size="12" /></template>
              </UiButton>
            </div>
            <div v-if="apiEndpoints.length === 0" class="row-empty">
              <span>{{ selectedPlatformId ? '暂无节点，点击同步' : '请先在平台管理页创建平台' }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

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
  </div>
</template>

<script setup lang="ts">
import { UiButton, UiSegment, UiSelect, UiSkeleton, UiTooltip } from '../ui'
import { ref, computed, onMounted, watch } from 'vue'
import { TrendChart, AccountModal, QuotaPieChart, TokensModal } from '../components/dashboard'
import ExternalLink from '../components/common/ExternalLink.vue'
import { accountApi, dashboardApi, notifyApi, apiEndpointsApi, groupsApi, signApi, statisticsApi, platformApi, settingsApi } from '../api'
import type { Account, AccountAuthType, AccountGroup, AccountProxyMode, ApiToken, DashboardData, ApiEndpoint, CreateTokenParams, Platform, SelectOption } from '../types'
import { Activity, ChevronRight, Clock, Copy, KeyRound, Plus, RefreshCcw, RefreshCw, Users, Zap } from 'lucide-vue-next'
import { useEventStream, useFormat } from '../composables'
import { useClipboard } from '../composables/useClipboard'
import { useViewRefresh } from '../composables'
import type { SystemSettings } from '../types'
import { formatRewardTotals, getAccountStatus } from '../utils'

const { formatRelativeTime } = useFormat()
const { copy } = useClipboard()

const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
mediaQuery.addEventListener('change', (e) => {
  isDarkMode.value = e.matches
})

const accounts = ref<Account[]>([])
const groups = ref<AccountGroup[]>([])
const dashboard = ref<DashboardData | null>(null)
const apiEndpoints = ref<ApiEndpoint[]>([])
const platforms = ref<Platform[]>([])
const selectedPlatformId = ref<number | null>(null)
const loadingPlatforms = ref(false)
const initialLoading = ref(true)
const trendDays = ref(7)
type AccountStatusFilter = 'normal' | 'unhealthy' | 'disabled'

const statusFilter = ref<AccountStatusFilter | null>(null)
const quotaWarningThreshold = ref(5)
let eventRefreshTimer: number | null = null

const platformOptions = computed<SelectOption<number>[]>(() =>
  platforms.value.map(platform => ({
    label: platform.is_default ? `${platform.name} (默认)` : platform.name,
    value: platform.id
  }))
)

const normalCount = computed(() => accounts.value.filter(a => getAccountStatus(a) === 'normal').length)
const unhealthyCount = computed(() => accounts.value.filter(a => getAccountStatus(a) === 'unhealthy').length)
const disabledCount = computed(() => accounts.value.filter(a => getAccountStatus(a) === 'disabled').length)
const lowQuotaAccounts = computed(() =>
  accounts.value.filter(account => account.is_active && isLowQuota(account))
)
const monthRewardDisplay = computed(() => formatRewardTotals(
  dashboard.value?.month_reward_totals,
  dashboard.value?.month_reward_display || '$0.00'
))

const displayAccounts = computed(() => {
  if (!statusFilter.value) return accounts.value

  if (statusFilter.value === 'disabled') {
    return accounts.value.filter(a => getAccountStatus(a) === 'disabled')
  }
  return accounts.value.filter(a => getAccountStatus(a) === statusFilter.value)
})

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


const filterByStatus = (status: AccountStatusFilter) => {
  statusFilter.value = statusFilter.value === status ? null : status
}

const isLowQuota = (account: Account) => account.is_active && (account.cached_quota || 0) < quotaWarningThreshold.value * 500000

const copyEndpoint = (url: string) => {
  copy(url)
}

const signingId = ref<number | null>(null)
const batchSigning = ref(false)
const checkingId = ref<number | null>(null)
const refreshing = ref(false)
const syncingEndpoints = ref(false)

const showAccountModal = ref(false)
const editingAccount = ref<Account | null>(null)
const accountModalRef = ref<InstanceType<typeof AccountModal> | null>(null)

const showTokensVisible = ref(false)
const tokenAccount = ref<Account | null>(null)
const tokens = ref<ApiToken[]>([])
const loadingTokens = ref(false)
const syncingTokens = ref(false)
const deletingTokenId = ref<number | null>(null)

const loadData = async () => {
  try {
    const [accountsRes, dashboardRes, settingsRes] = await Promise.all([
      accountApi.getList(),
      dashboardApi.get(),
      settingsApi.get()
    ])
    accounts.value = accountsRes.data || []
    dashboard.value = dashboardRes.data
    quotaWarningThreshold.value = (settingsRes.data as Partial<SystemSettings> | undefined)?.quota_warning_threshold ?? 5
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    initialLoading.value = false
  }
}

const loadTrendData = async (days: number) => {
  try {
    const res = await statisticsApi.getDaily(days)
    if (dashboard.value && res.data) {
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
  if (selectedPlatformId.value == null) {
    apiEndpoints.value = []
    return
  }
  try {
    const res = await apiEndpointsApi.getList(selectedPlatformId.value)
    apiEndpoints.value = res.data || []
  } catch (e) {
    console.error('Failed to load endpoints:', e)
  }
}

const loadPlatformsForEndpoints = async () => {
  loadingPlatforms.value = true
  try {
    const res: any = await platformApi.getList()
    const loaded = (res.data || []) as Platform[]
    platforms.value = [...loaded].sort((a, b) => {
      if (a.is_default === b.is_default) return 0
      return a.is_default ? -1 : 1
    })
    if (selectedPlatformId.value == null) {
      const defaultPlatform = platforms.value.find(p => p.is_default) ?? platforms.value[0]
      selectedPlatformId.value = defaultPlatform ? defaultPlatform.id : null
    } else if (!platforms.value.some(p => p.id === selectedPlatformId.value)) {
      selectedPlatformId.value = platforms.value[0]?.id ?? null
    }
  } catch (e) {
    console.error('Failed to load platforms:', e)
  } finally {
    loadingPlatforms.value = false
  }
}

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

const showAddModal = () => {
  editingAccount.value = null
  showAccountModal.value = true
}

const handleSyncEndpoints = async () => {
  if (selectedPlatformId.value == null) {
    window.$notify('请先选择平台', 'warning')
    return
  }
  syncingEndpoints.value = true
  try {
    const res: any = await apiEndpointsApi.sync(selectedPlatformId.value)
    window.$notify(res.message || '同步成功', 'success')
    loadEndpoints()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    syncingEndpoints.value = false
  }
}

const handleAccountSubmit = async (data: {
  user_id: string
  external_user_id: string
  username: string
  display_name: string
  session_cookie: string
  login_username: string
  login_password: string
  auth_type: AccountAuthType
  auth_data?: Record<string, any>
  clear_auth_data: boolean
  note: string
  proxy_mode: AccountProxyMode
  proxy_url: string
  clear_login_credentials: boolean
  is_active?: boolean
  platform_id: number | null
  group_id: number | null
  notify_channel_ids: number[]
}) => {
  try {
    const targetPlatform = platforms.value.find(platform => platform.id === data.platform_id)
    const isHttpTarget = targetPlatform?.adapter_type === 'http'

    if (editingAccount.value) {
      const updateData: any = { is_active: data.is_active }
      const platformChanged = data.platform_id !== editingAccount.value.platform?.id
      if (data.platform_id) updateData.platform_id = data.platform_id

      if (isHttpTarget) {
        const externalUserId = data.external_user_id.trim()
        if (platformChanged || externalUserId !== (editingAccount.value.external_user_id || '')) {
          updateData.external_user_id = externalUserId
        }
        if (data.username.trim() !== (editingAccount.value.username || '')) {
          updateData.username = data.username.trim()
        }
        if (data.display_name.trim() !== (editingAccount.value.display_name || '')) {
          updateData.display_name = data.display_name.trim()
        }
        updateData.auth_type = data.clear_auth_data ? 'none' : data.auth_type
        if (data.auth_data) updateData.auth_data = data.auth_data
        if (data.clear_auth_data) updateData.clear_auth_data = true
        if (data.clear_login_credentials) updateData.clear_login_credentials = true
      } else {
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
          if (data.login_password) updateData.login_password = data.login_password
        }
      }

      if (data.note.trim() !== (editingAccount.value.note || '')) updateData.note = data.note.trim()
      if (data.group_id !== editingAccount.value.group_id) updateData.group_id = data.group_id || 0

      const previousProxyMode = editingAccount.value.proxy_mode || 'direct'
      if (data.proxy_mode !== previousProxyMode) updateData.proxy_mode = data.proxy_mode
      if (data.proxy_mode === 'custom' && data.proxy_url.trim()) {
        updateData.proxy_mode = 'custom'
        updateData.proxy_url = data.proxy_url.trim()
      } else if (data.proxy_mode !== 'custom' && previousProxyMode === 'custom') {
        updateData.proxy_url = ''
      }

      await accountApi.update(editingAccount.value.id, updateData)
      await notifyApi.updateAccountNotify(editingAccount.value.id, {
        channels: data.notify_channel_ids.map((id: number) => ({
          channel_id: id,
          is_enabled: true,
          notify_config: {}
        }))
      })
      window.$notify('更新成功', 'success')
    } else {
      const payload: any = {
        note: data.note.trim() || undefined,
        proxy_mode: data.proxy_mode,
        proxy_url: data.proxy_mode === 'custom' ? data.proxy_url.trim() || undefined : undefined,
        platform_id: data.platform_id as number,
        group_id: data.group_id || undefined
      }

      if (isHttpTarget) {
        payload.external_user_id = data.external_user_id.trim() || undefined
        payload.username = data.username.trim() || undefined
        payload.display_name = data.display_name.trim() || undefined
        payload.auth_type = data.auth_type
        payload.auth_data = data.auth_data
      } else {
        payload.session_cookie = data.session_cookie.trim() || undefined
        payload.user_id = data.user_id.trim() || undefined
        payload.login_username = data.login_username.trim() || undefined
        payload.login_password = data.login_password || undefined
      }

      const res = await accountApi.create(payload)
      if (data.notify_channel_ids.length > 0 && res.data?.id) {
        await notifyApi.updateAccountNotify(res.data.id, {
          channels: data.notify_channel_ids.map((id: number) => ({
            channel_id: id,
            is_enabled: true,
            notify_config: {}
          }))
        })
      }
      window.$notify('账号添加成功', 'success')
    }

    showAccountModal.value = false
    await loadData()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    accountModalRef.value?.setSubmitting(false)
  }
}
const handleSign = async (account: Account) => {
  if (!account.is_active) {
    window.$notify('该账号已禁用，无法签到', 'warning', { route: `/account/${account.id}` })
    return
  }
  signingId.value = account.id
  try {
    const res = await signApi.sign(account.id)
    window.$notify(res.data?.message || '签到成功', 'success', { route: `/account/${account.id}` })
    loadData()
  } catch (e: any) {
    window.$notify(e.message, 'error', { route: `/account/${account.id}` })
  } finally {
    signingId.value = null
  }
}

const handleHealthCheck = async (account: Account) => {
  checkingId.value = account.id
  try {
    await accountApi.healthCheck(account.id)
    window.$notify('健康检查完成', 'success', { route: `/account/${account.id}` })
    loadData()
  } catch (e: any) {
    window.$notify(e.message, 'error', { route: `/account/${account.id}` })
  } finally {
    checkingId.value = null
  }
}

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

onMounted(async () => {
  loadData()
  loadGroups()
  await loadPlatformsForEndpoints()
  loadEndpoints()
  loadTrendData(trendDays.value)
})

useViewRefresh(async () => {
  await Promise.all([loadData(), loadEndpoints(), loadTrendData(trendDays.value)])
})

useEventStream((event) => {
  if (!['sign_completed', 'health_changed', 'account_changed'].includes(event.type)) return
  if (eventRefreshTimer !== null) return
  eventRefreshTimer = window.setTimeout(async () => {
    eventRefreshTimer = null
    await Promise.all([loadData(), loadEndpoints(), loadTrendData(trendDays.value)])
  }, 600)
})

watch(selectedPlatformId, () => {
  loadEndpoints()
})

watch(trendDays, (newDays) => {
  loadTrendData(newDays)
})
</script>


<style scoped>
.dashboard {
  --dashboard-radius: clamp(14px, 1.4vw, 22px);
  --dashboard-gap: clamp(12px, 1.5vw, 20px);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--dashboard-gap);
  min-width: 0;
  isolation: isolate;
}

.dashboard::before {
  position: absolute;
  z-index: -1;
  top: -32px;
  right: -10%;
  left: -10%;
  height: 420px;
  pointer-events: none;
  content: '';
  opacity: 0.45;
  background-image: linear-gradient(to right, var(--grid-line) 1px, transparent 1px), linear-gradient(to bottom, var(--grid-line) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, #000, transparent 92%);
}

.hero-header {
  position: relative;
  min-height: 348px;
  overflow: hidden;
  padding: clamp(22px, 3vw, 42px);
  border: 1px solid var(--line-strong);
  border-radius: var(--dashboard-radius);
  background: var(--surface-inverse);
  color: var(--ink-inverse);
  box-shadow: var(--lift-4);
  isolation: isolate;
}

.hero-grid {
  position: absolute;
  z-index: -2;
  inset: 0;
  opacity: 0.55;
  pointer-events: none;
  background-image: linear-gradient(to right, color-mix(in srgb, var(--ink-inverse) 14%, transparent) 1px, transparent 1px), linear-gradient(to bottom, color-mix(in srgb, var(--ink-inverse) 14%, transparent) 1px, transparent 1px);
  background-position: 0 0;
  background-size: 42px 42px;
  mask-image: linear-gradient(125deg, #000 0%, rgba(0, 0, 0, 0.7) 48%, transparent 90%);
}

.hero-glow {
  position: absolute;
  z-index: -1;
  pointer-events: none;
  border-radius: 999px;
  filter: blur(2px);
  opacity: 0.72;
}

.hero-glow-a {
  top: -190px;
  right: 15%;
  width: 420px;
  height: 420px;
  border: 1px solid var(--signal);
  box-shadow: 0 0 0 34px color-mix(in srgb, var(--signal) 8%, transparent), 0 0 110px color-mix(in srgb, var(--signal) 18%, transparent);
}

.hero-glow-b {
  right: -160px;
  bottom: -210px;
  width: 540px;
  height: 540px;
  background: radial-gradient(circle, color-mix(in srgb, var(--signal) 13%, transparent), transparent 68%);
}

.hero-topline,
.hero-footer,
.hero-kicker,
.hero-live,
.hero-eyebrow,
.hero-note,
.hero-actions,
.metric-topline,
.metric-foot,
.panel-head,
.panel-heading,
.panel-head-actions,
.panel-signal,
.row-meta,
.row-actions,
.activity-title,
.endpoint-row {
  display: flex;
  align-items: center;
}

.hero-topline {
  position: relative;
  z-index: 2;
  justify-content: space-between;
  gap: var(--spacing-4);
  color: color-mix(in srgb, var(--ink-inverse) 60%, transparent);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-kicker,
.hero-live { gap: 10px; }

.hero-index {
  display: inline-grid;
  width: 26px;
  height: 26px;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--ink-inverse) 30%, transparent);
  border-radius: 999px;
  color: var(--signal-deep);
  font-size: 10px;
}

.hero-live {
  color: var(--signal-deep);
  font-weight: var(--weight-semibold);
}

.hero-live-dot,
.hero-note-line {
  display: inline-block;
  flex-shrink: 0;
  background: var(--signal);
}

.hero-live-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  box-shadow: 0 0 0 5px color-mix(in srgb, var(--signal) 15%, transparent), 0 0 18px var(--signal);
  animation: telemetry-pulse 2.2s ease-in-out infinite;
}

.hero-content {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(220px, 0.85fr);
  align-items: end;
  gap: clamp(28px, 8vw, 132px);
  min-height: 242px;
  padding: 40px 0 34px;
}

.hero-eyebrow {
  gap: 8px;
  margin-bottom: 14px;
  color: var(--signal-deep);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: var(--weight-semibold);
  letter-spacing: 0.08em;
}

.hero-title {
  margin: 0;
  max-width: 8em;
  color: var(--ink-inverse);
  font-family: var(--font-display);
  font-size: clamp(3.8rem, 10vw, 8.8rem);
  font-weight: var(--weight-black);
  letter-spacing: -0.1em;
  line-height: 0.78;
}

.hero-title span { color: var(--signal-deep); }

.hero-description {
  max-width: 390px;
  margin: 24px 0 0;
  color: color-mix(in srgb, var(--ink-inverse) 62%, transparent);
  font-size: var(--fn-md);
  line-height: 1.8;
}

.hero-readout {
  align-self: end;
  justify-self: end;
  width: min(100%, 290px);
  padding: 18px;
  border-top: 1px solid color-mix(in srgb, var(--ink-inverse) 32%, transparent);
  border-bottom: 1px solid color-mix(in srgb, var(--ink-inverse) 32%, transparent);
  background: color-mix(in srgb, var(--surface-inverse) 75%, transparent);
  backdrop-filter: blur(10px);
}

.readout-caption,
.readout-label,
.readout-meta,
.section-code,
.section-aside,
.panel-code,
.panel-subhead,
.rail-total-label,
.metric-label,
.metric-index {
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.readout-caption { color: color-mix(in srgb, var(--ink-inverse) 48%, transparent); font-size: 10px; }

.readout-value {
  margin-top: 9px;
  color: var(--ink-inverse);
  font-family: var(--font-display);
  font-size: clamp(3rem, 5vw, 4.6rem);
  font-weight: var(--weight-black);
  letter-spacing: -0.09em;
  line-height: 0.92;
  font-variant-numeric: tabular-nums;
}

.readout-value span { margin-left: 4px; color: var(--signal-deep); font-size: 0.42em; letter-spacing: -0.04em; }
.readout-label { margin-top: 10px; color: color-mix(in srgb, var(--ink-inverse) 58%, transparent); font-size: 10px; }

.readout-track { height: 3px; margin-top: 18px; overflow: hidden; background: color-mix(in srgb, var(--ink-inverse) 16%, transparent); }
.readout-track span { display: block; height: 100%; background: var(--signal); box-shadow: 0 0 14px var(--signal-glow); transition: width var(--transition-slow); }

.readout-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
  color: color-mix(in srgb, var(--ink-inverse) 48%, transparent);
  font-size: 10px;
}

.readout-meta b { color: var(--ink-inverse); font-weight: var(--weight-semibold); font-variant-numeric: tabular-nums; }

.hero-footer { position: relative; z-index: 2; justify-content: space-between; gap: var(--spacing-4); padding-top: 16px; border-top: 1px solid color-mix(in srgb, var(--ink-inverse) 18%, transparent); }
.hero-note { gap: 10px; color: color-mix(in srgb, var(--ink-inverse) 52%, transparent); font-size: 11px; }
.hero-note-line { width: 24px; height: 1px; }
.hero-actions { justify-content: flex-end; gap: 6px; }

.hero-actions :deep(.ui-btn--ghost) { border-color: color-mix(in srgb, var(--ink-inverse) 32%, transparent); color: var(--ink-inverse); }
.hero-actions :deep(.ui-btn--ghost:hover:not(:disabled)) { border-color: var(--signal-deep); color: var(--signal-deep); }

.hero-orbit { position: absolute; z-index: 0; right: clamp(12px, 9vw, 150px); bottom: -92px; width: clamp(230px, 31vw, 430px); aspect-ratio: 1; pointer-events: none; opacity: 0.78; transform: rotate(-18deg); }
.orbit-ring, .orbit-core, .orbit-cross { position: absolute; display: block; }
.orbit-ring { inset: 10%; border: 1px solid color-mix(in srgb, var(--signal) 60%, transparent); border-radius: 50%; transform: rotate(34deg) skewX(-10deg); }
.orbit-ring-one { animation: orbit-drift 18s linear infinite; }
.orbit-ring-two { inset: 22% 3%; border-color: color-mix(in srgb, var(--ink-inverse) 34%, transparent); transform: rotate(-48deg) skewY(16deg); animation: orbit-drift 26s linear reverse infinite; }
.orbit-core { top: 39%; left: 39%; width: 22%; height: 22%; border: 1px solid var(--signal); border-radius: 50%; background: radial-gradient(circle, var(--signal) 0 8%, color-mix(in srgb, var(--signal) 35%, transparent) 9% 30%, transparent 31%); box-shadow: 0 0 42px color-mix(in srgb, var(--signal) 40%, transparent); }
.orbit-cross { background: var(--signal); opacity: 0.82; }
.orbit-cross-a { top: 48%; right: 0; width: 42px; height: 1px; }
.orbit-cross-b { bottom: 2%; left: 48%; width: 1px; height: 42px; }

.status-rail { display: grid; grid-template-columns: minmax(168px, 0.72fr) minmax(0, 2fr) minmax(140px, 0.7fr); align-items: stretch; gap: 1px; overflow: hidden; border: 1px solid var(--line-faint); border-radius: var(--dashboard-radius); background: var(--line-faint); box-shadow: var(--lift-1); }
.rail-intro, .rail-total { display: flex; flex-direction: column; justify-content: center; gap: 6px; padding: 16px 18px; background: var(--surface-raised); }
.rail-intro strong { color: var(--ink-max); font-size: var(--fn-md); font-weight: var(--weight-semibold); }
.rail-intro > span:last-child { color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.1em; }
.section-code { color: var(--signal-deep); font-size: 10px; font-weight: var(--weight-semibold); }
.rail-items { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: var(--line-faint); }

.rail-item { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 11px; min-width: 0; padding: 12px 14px; border: 0; background: var(--surface-raised); color: var(--ink); text-align: left; cursor: pointer; transition: background var(--transition-bounce), color var(--transition-fast), transform var(--transition-bounce); }
.rail-item:hover, .rail-item.active { background: var(--surface-hover); color: var(--ink-max); }
.rail-item.active { box-shadow: inset 0 -2px 0 var(--signal-deep); }
.rail-item:hover { transform: translateY(-2px); }
.rail-item-mark { display: grid; width: 28px; height: 28px; place-items: center; border: 1px solid var(--line-faint); border-radius: 50%; background: var(--surface-inset); }
.rail-item-success .rail-item-mark { border-color: color-mix(in srgb, var(--ok) 32%, var(--line-faint)); }
.rail-item-error .rail-item-mark { border-color: color-mix(in srgb, var(--bad) 32%, var(--line-faint)); }
.rail-item-copy { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.rail-item-copy small { overflow: hidden; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.08em; text-overflow: ellipsis; white-space: nowrap; }
.rail-item-copy b { color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-medium); }
.rail-item-count { color: var(--ink-max); font-family: var(--font-display); font-size: 25px; font-weight: var(--weight-semibold); letter-spacing: -0.06em; line-height: 1; font-variant-numeric: tabular-nums; }
.rail-total { background: var(--surface-inset); }
.rail-total-label { color: var(--ink-faint); font-size: 9px; }
.rail-total strong { color: var(--ink-max); font-family: var(--font-display); font-size: 31px; font-weight: var(--weight-semibold); letter-spacing: -0.08em; line-height: 1; font-variant-numeric: tabular-nums; }
.rail-total-line { display: block; width: 100%; height: 2px; background: linear-gradient(90deg, var(--signal-deep), transparent); }

.warning-banner { position: relative; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: 14px; padding: 14px 16px; overflow: hidden; border: 1px solid color-mix(in srgb, var(--warn) 34%, var(--line-faint)); border-radius: var(--dashboard-radius); background: linear-gradient(90deg, var(--warn-wash), transparent 70%), var(--surface-raised); }
.warning-banner::after { position: absolute; right: 0; bottom: 0; left: 0; height: 2px; content: ''; background: linear-gradient(90deg, var(--warn), transparent 60%); opacity: 0.55; }
.warning-symbol { display: grid; width: 32px; height: 32px; place-items: center; border: 1px solid color-mix(in srgb, var(--warn) 40%, transparent); border-radius: 50%; color: var(--warn); }
.warning-title { color: var(--warn); font-size: var(--fn-sm); font-weight: var(--weight-semibold); }
.warning-desc { margin-top: 3px; overflow: hidden; color: var(--ink-muted); font-size: var(--fn-xs); text-overflow: ellipsis; white-space: nowrap; }

.metrics-section { display: flex; flex-direction: column; gap: 12px; }
.section-heading { display: flex; align-items: end; justify-content: space-between; gap: 16px; padding: 0 2px; }
.section-heading h2 { margin: 6px 0 0; color: var(--ink-max); font-size: var(--fn-lg); font-weight: var(--weight-semibold); letter-spacing: -0.02em; }
.section-aside { color: var(--ink-faint); font-size: 9px; }
.metrics-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }

.metric-card { position: relative; display: flex; min-height: 142px; flex-direction: column; gap: 14px; overflow: hidden; padding: 17px 18px 15px; border: 1px solid var(--line-faint); border-radius: var(--dashboard-radius); background: var(--surface-raised); box-shadow: var(--lift-1); transition: border-color var(--transition-fast), box-shadow var(--transition-bounce), transform var(--transition-bounce); }
.metric-card::before { position: absolute; top: 0; right: 0; left: 0; height: 2px; content: ''; background: var(--line); transition: background var(--transition-fast); }
.metric-card:hover { border-color: var(--line); box-shadow: var(--lift-2); transform: translateY(-4px); }
.metric-card.interactive { cursor: pointer; }
.metric-card-accounts::before, .metric-card-sign::before { background: var(--signal-deep); }
.metric-card-rewards::before { background: var(--warn); }
.metric-card-quota::before { background: var(--info); }
.metric-topline { justify-content: space-between; gap: 12px; }
.metric-label { color: var(--ink-faint); font-size: 10px; font-weight: var(--weight-semibold); }
.metric-icon { display: grid; width: 28px; height: 28px; place-items: center; border: 1px solid var(--line-faint); border-radius: 50%; color: var(--ink-muted); background: var(--surface-inset); }
.metric-card-accounts .metric-icon, .metric-card-sign .metric-icon { color: var(--signal-deep); }
.metric-card-rewards .metric-icon { color: var(--warn); }
.metric-card-quota .metric-icon { color: var(--info); }
.metric-value { color: var(--ink-max); font-family: var(--font-display); font-size: clamp(2rem, 3vw, 3.15rem); font-weight: var(--weight-semibold); letter-spacing: -0.09em; line-height: 0.9; font-variant-numeric: tabular-nums; }
.metric-value-rewards { font-size: clamp(1.55rem, 2.3vw, 2.3rem); letter-spacing: -0.07em; }
.metric-sub { margin-left: 3px; color: var(--ink-faint); font-size: 0.42em; font-weight: var(--weight-medium); letter-spacing: -0.03em; }
.metric-foot { align-self: stretch; gap: 8px; min-height: 16px; margin-top: auto; color: var(--ink-muted); font-size: var(--fn-xs); }
.account-status-foot { flex-wrap: wrap; }
.metric-sub-label { color: var(--ink-muted); font-size: var(--fn-xs); }
.metric-delta { display: inline-flex; align-items: center; gap: 3px; font-size: var(--fn-xs); font-weight: var(--weight-medium); font-variant-numeric: tabular-nums; }
.metric-delta.up { color: var(--ok); }
.metric-delta.down { color: var(--bad); }
.metric-bar { flex: 1; height: 3px; overflow: hidden; background: var(--line-faint); }
.metric-bar-fill { display: block; height: 100%; background: var(--signal-deep); box-shadow: 0 0 12px var(--signal-glow); transition: width var(--transition-slow); }
.metric-bar-text { color: var(--ink-strong); font-family: var(--font-mono); font-size: 10px; font-weight: var(--weight-semibold); font-variant-numeric: tabular-nums; }
.metric-index { position: absolute; right: 17px; bottom: 14px; color: var(--ink-ghost); font-size: 9px; }

.workspace { display: grid; grid-template-columns: minmax(0, 1.64fr) minmax(280px, 0.86fr); gap: var(--dashboard-gap); align-items: start; }
.workspace-main, .workspace-side { display: flex; min-width: 0; flex-direction: column; gap: var(--dashboard-gap); }
.workspace-side { padding-top: clamp(18px, 3vw, 38px); }
.panel { overflow: hidden; border: 1px solid var(--line-faint); border-radius: var(--dashboard-radius); background: var(--surface-raised); box-shadow: var(--lift-1); transition: border-color var(--transition-fast), box-shadow var(--transition-bounce); }
.panel:hover { border-color: var(--line); box-shadow: var(--lift-2); }
.panel-head { justify-content: space-between; gap: 14px; min-height: 62px; padding: 11px 17px; border-bottom: 1px solid var(--line-faint); }
.panel-heading { align-items: flex-start; flex-direction: column; gap: 5px; min-width: 0; }
.panel-code { color: var(--ink-faint); font-size: 9px; font-weight: var(--weight-semibold); }
.panel-title { color: var(--ink-max); font-size: var(--fn-md); font-weight: var(--weight-semibold); }
.panel-head-actions { justify-content: flex-end; gap: 6px; min-width: 0; }
.panel-signal { gap: 6px; color: var(--ok); font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: 0.08em; }
.panel-body { padding: 17px; }
.chart-body { min-height: 276px; }
.trend-panel .chart-body { min-height: 314px; padding: 20px 18px 14px; }
.quota-panel .chart-body { min-height: 276px; }
.platform-select { width: 140px; }
.panel-subhead { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 38px; padding: 9px 17px; border-bottom: 1px solid var(--line-faint); color: var(--ink-muted); font-family: var(--font-sans); font-size: var(--fn-xs); letter-spacing: 0; text-transform: none; }
.panel-subhead-count { flex-shrink: 0; color: var(--ink-faint); font-family: var(--font-mono); font-size: 10px; font-variant-numeric: tabular-nums; }
.account-rows, .activity-list, .endpoints-list { display: flex; flex-direction: column; }

.account-row { display: grid; grid-template-columns: 24px 34px minmax(0, 1fr) auto; align-items: center; gap: 12px; min-height: 66px; padding: 10px 17px; border-bottom: 1px solid var(--line-faint); cursor: pointer; transition: background var(--transition-fast), padding-left var(--transition-bounce); }
.account-row:last-child { border-bottom: none; }
.account-row:hover { padding-left: 22px; background: var(--surface-hover); }
.account-row.alert { background: linear-gradient(90deg, var(--bad-wash), transparent 70%); }
.account-row.alert:hover { background: linear-gradient(90deg, var(--bad-wash), var(--surface-hover) 72%); }
.row-index { color: var(--ink-ghost); font-family: var(--font-mono); font-size: 10px; font-variant-numeric: tabular-nums; }
.row-avatar { display: grid; width: 32px; height: 32px; place-items: center; border: 1px solid color-mix(in srgb, var(--signal-deep) 36%, var(--line-faint)); border-radius: 50%; background: var(--signal-wash); color: var(--signal-deep); font-family: var(--font-mono); font-size: var(--fn-xs); font-weight: var(--weight-semibold); }
.row-avatar.inactive { border-color: var(--line-faint); background: var(--surface-inset); color: var(--ink-faint); }
.row-main { min-width: 0; }
.row-title { display: flex; align-items: center; gap: 7px; overflow: hidden; color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-medium); text-overflow: ellipsis; white-space: nowrap; }
.row-status-dot { width: 6px; height: 6px; flex-shrink: 0; border-radius: 999px; }
.row-status-dot.success { background: var(--ok); box-shadow: 0 0 0 3px var(--ok-wash); }
.row-status-dot.error { background: var(--bad); box-shadow: 0 0 0 3px var(--bad-wash); }
.row-meta { flex-wrap: wrap; gap: 6px; margin-top: 5px; color: var(--ink-muted); font-size: var(--fn-xs); }
.row-quota { color: var(--ink-strong); font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
.row-quota.danger { color: var(--bad); }
.divider { color: var(--ink-ghost); }
.row-tag { display: inline-flex; align-items: center; min-height: 17px; padding: 0 5px; border: 1px solid var(--line-faint); border-radius: 999px; background: var(--surface-inset); color: var(--ink-muted); font-size: 9px; }
.row-tag.warning { border-color: color-mix(in srgb, var(--warn) 30%, var(--line-faint)); background: var(--warn-wash); color: var(--warn); }
.row-actions { gap: 2px; opacity: 0.65; transition: opacity var(--transition-fast); }
.account-row:hover .row-actions { opacity: 1; }
.row-empty { display: flex; align-items: center; justify-content: center; gap: 9px; min-height: 150px; padding: 24px; color: var(--ink-muted); font-size: var(--fn-sm); text-align: center; }

.activity-list, .endpoints-list { max-height: 320px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: var(--line-strong) transparent; }
.activity-item { display: grid; grid-template-columns: 7px minmax(0, 1fr) auto; align-items: start; gap: 11px; min-height: 58px; padding: 12px 17px; border-bottom: 1px solid var(--line-faint); transition: background var(--transition-fast); }
.activity-item:last-child { border-bottom: none; }
.activity-item:hover { background: var(--surface-hover); }
.activity-dot { width: 7px; height: 7px; margin-top: 5px; border-radius: 50%; }
.activity-dot.success { background: var(--ok); box-shadow: 0 0 0 4px var(--ok-wash); }
.activity-dot.error { background: var(--bad); box-shadow: 0 0 0 4px var(--bad-wash); }
.activity-main { min-width: 0; }
.activity-title { flex-wrap: wrap; gap: 5px 8px; color: var(--ink-muted); font-size: var(--fn-xs); }
.activity-title b { overflow: hidden; max-width: 160px; color: var(--ink-strong); font-weight: var(--weight-medium); text-overflow: ellipsis; white-space: nowrap; }
.activity-action.success { color: var(--ok); }
.activity-action.error { color: var(--bad); }
.activity-time { margin-top: 4px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 10px; }
.activity-arrow { color: var(--ink-ghost); opacity: 0; transition: opacity var(--transition-fast), transform var(--transition-fast); }
.activity-item:hover .activity-arrow { opacity: 1; transform: translateX(2px); }

.endpoint-row { display: grid; grid-template-columns: 8px minmax(0, 1fr) auto; gap: 11px; padding: 12px 17px; border-bottom: 1px solid var(--line-faint); }
.endpoint-row:last-child { border-bottom: none; }
.endpoint-row:hover { background: var(--surface-hover); }
.endpoint-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--info); box-shadow: 0 0 0 4px var(--info-wash); }
.endpoint-dot.green { background: var(--ok); box-shadow: 0 0 0 4px var(--ok-wash); }
.endpoint-dot.yellow { background: var(--warn); box-shadow: 0 0 0 4px var(--warn-wash); }
.endpoint-dot.red { background: var(--bad); box-shadow: 0 0 0 4px var(--bad-wash); }
.endpoint-dot.blue { background: var(--info); box-shadow: 0 0 0 4px var(--info-wash); }
.endpoint-main { min-width: 0; }
.endpoint-name { overflow: hidden; color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-medium); text-overflow: ellipsis; white-space: nowrap; }
.endpoint-url { margin-top: 4px; color: var(--ink-muted); font-size: 10px; }

.status-dot { width: 6px; height: 6px; flex-shrink: 0; border-radius: 50%; }
.status-dot.success { background: var(--ok); }
.status-dot.error { background: var(--bad); }
.status-dot.default { background: var(--ink-ghost); }
.status-dot.info { background: var(--info); }

@keyframes telemetry-pulse {
  0%, 100% { opacity: 0.7; transform: scale(0.92); }
  50% { opacity: 1; transform: scale(1.08); }
}

@keyframes orbit-drift {
  from { transform: rotate(0deg) rotate(34deg) skewX(-10deg); }
  to { transform: rotate(360deg) rotate(34deg) skewX(-10deg); }
}

@media (max-width: 1100px) {
  .hero-content { gap: 48px; }
  .workspace { grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.9fr); }
}

@media (max-width: 900px) {
  .hero-header { min-height: auto; }
  .hero-content { grid-template-columns: minmax(0, 1fr) minmax(210px, 0.58fr); }
  .metrics-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .status-rail { grid-template-columns: 1fr; }
  .rail-intro, .rail-total { flex-direction: row; align-items: center; }
  .rail-intro > span:last-child { margin-left: auto; }
  .rail-total { justify-content: flex-start; }
  .rail-total-line { flex: 1; }
}

@media (max-width: 720px) {
  .hero-topline, .hero-footer { align-items: flex-start; flex-direction: column; }
  .hero-content { display: flex; flex-direction: column; align-items: stretch; gap: 30px; padding-top: 48px; }
  .hero-readout { align-self: stretch; justify-self: stretch; width: auto; }
  .hero-orbit { right: -90px; bottom: 44px; width: 300px; opacity: 0.42; }
  .hero-actions { justify-content: flex-start; flex-wrap: wrap; }
  .workspace { grid-template-columns: 1fr; }
  .workspace-side { padding-top: 0; }
  .panel-head { align-items: flex-start; }
  .panel-head-actions { flex-wrap: wrap; }
  .warning-banner { grid-template-columns: auto minmax(0, 1fr); }
  .warning-banner :deep(.ui-btn) { grid-column: 2; justify-self: start; }
}

@media (max-width: 520px) {
  .hero-header { padding: 18px; }
  .hero-title { font-size: clamp(3.4rem, 20vw, 5.6rem); }
  .hero-description { margin-top: 18px; }
  .metrics-grid { grid-template-columns: 1fr; }
  .rail-items { grid-template-columns: 1fr; }
  .rail-item { min-height: 62px; }
  .account-row { grid-template-columns: 18px 30px minmax(0, 1fr); gap: 9px; padding-right: 12px; padding-left: 12px; }
  .account-row:hover { padding-left: 16px; }
  .row-actions { grid-column: 3; justify-self: start; margin-top: -2px; }
  .panel-head, .panel-subhead { padding-right: 12px; padding-left: 12px; }
  .activity-item, .endpoint-row { padding-right: 12px; padding-left: 12px; }
  .platform-select { width: 120px; }
  .section-heading { align-items: flex-start; flex-direction: column; gap: 5px; }
}

@media (prefers-reduced-motion: reduce) {
  .hero-live-dot, .orbit-ring-one, .orbit-ring-two { animation: none; }
  .metric-card, .rail-item, .account-row, .activity-arrow { transition: none; }
}
</style>
