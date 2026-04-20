<template>
  <div class="dashboard">
    <!-- 页头 + 快捷操作 -->
    <div class="dashboard-head">
      <div class="head-main">
        <h1 class="page-title">概览</h1>
        <p class="page-subtitle">
          {{ accounts.length }} 个账号 ·
          健康 {{ healthyCount }} ·
          异常 {{ unhealthyCount }} ·
          待签到 {{ pendingCount }}
        </p>
      </div>
      <div class="head-actions">
        <n-button size="small" @click="showAddModal">
          <template #icon><n-icon :size="14"><AddOutline /></n-icon></template>
          添加账号
        </n-button>
        <n-button size="small" @click="refreshData" :loading="refreshing">
          <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
        <n-button size="small" type="primary" @click="handleBatchSign" :loading="batchSigning">
          <template #icon><n-icon :size="14"><FlashOutline /></n-icon></template>
          一键签到
        </n-button>
      </div>
    </div>

    <div v-if="lowQuotaAccounts.length > 0" class="warning-banner">
      <div class="warning-copy">
        <div class="warning-title">有 {{ lowQuotaAccounts.length }} 个账号低于额度告警阈值</div>
        <div class="warning-desc">
          阈值 ${{ quotaWarningThreshold.toFixed(2) }}，
          {{ lowQuotaAccounts.slice(0, 4).map(account => `${account.username || '未命名'} ${account.quota_display || '$0.00'}`).join(' · ') }}
        </div>
      </div>
      <n-button size="small" type="warning" @click="$router.push('/accounts')">
        去账号页处理
      </n-button>
    </div>

    <!-- 指标卡 -->
    <div class="metrics-grid" v-if="!initialLoading">
      <div class="metric-card interactive" @click="$router.push('/accounts')">
        <div class="metric-label">账号总数</div>
        <div class="metric-value">{{ dashboard?.account_count || 0 }}</div>
        <div class="metric-foot" v-if="(dashboard?.unhealthy_account_count ?? 0) > 0">
          <span class="metric-delta down">
            {{ dashboard?.unhealthy_account_count }} 异常
          </span>
        </div>
        <div class="metric-foot" v-else>
          <span class="metric-delta up">全部健康</span>
        </div>
      </div>

      <div class="metric-card interactive" @click="$router.push({ path: '/logs', query: { today: '1' } })">
        <div class="metric-label">今日签到</div>
        <div class="metric-value">
          {{ dashboard?.today_sign_success || 0 }}
          <span class="metric-sub">/ {{ dashboard?.today_sign_count || 0 }}</span>
        </div>
        <div class="metric-foot">
          <div class="metric-bar">
            <div class="metric-bar-fill" :style="{ width: `${dashboard?.success_rate || 0}%` }"></div>
          </div>
          <span class="metric-bar-text">{{ dashboard?.success_rate || 0 }}%</span>
        </div>
      </div>

      <div class="metric-card interactive" @click="$router.push('/statistics')">
        <div class="metric-label">本月奖励</div>
        <div class="metric-value">{{ dashboard?.month_reward_display || '$0.00' }}</div>
        <div class="metric-foot">
          <span class="metric-sub-label">累计签到所得</span>
        </div>
      </div>

      <div class="metric-card interactive" @click="$router.push('/accounts')">
        <div class="metric-label">总剩余额度</div>
        <div class="metric-value">{{ dashboard?.total_quota_display || '$0.00' }}</div>
        <div class="metric-foot">
          <span class="metric-sub-label">全部账号</span>
        </div>
      </div>
    </div>
    <div class="metrics-grid" v-else aria-busy="true" aria-label="加载中">
      <div v-for="i in 4" :key="i" class="metric-card">
        <n-skeleton text :width="64" :height="12" />
        <n-skeleton text :width="96" :height="28" style="margin-top: 12px" />
        <n-skeleton text :width="80" :height="12" style="margin-top: 12px" />
      </div>
    </div>

    <!-- 主工作区 -->
    <div class="workspace">
      <!-- 左列 -->
      <div class="workspace-main">
        <!-- 趋势图 -->
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">签到趋势</div>
            <n-radio-group v-model:value="trendDays" size="small">
              <n-radio-button :value="7">7 天</n-radio-button>
              <n-radio-button :value="30">30 天</n-radio-button>
              <n-radio-button :value="60">60 天</n-radio-button>
            </n-radio-group>
          </div>
          <div class="panel-body chart-body">
            <TrendChart :data="dashboard?.daily_trend || []" :is-dark="isDarkMode" />
          </div>
        </div>

        <!-- 账号列表 -->
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">账号状态</div>
            <n-button text size="small" @click="$router.push('/accounts')">
              全部账号
              <template #icon><n-icon :size="12"><ChevronForwardOutline /></n-icon></template>
            </n-button>
          </div>
          <div class="status-chips">
            <button
              class="status-chip"
              :class="{ active: statusFilter === 'healthy' }"
              :aria-pressed="statusFilter === 'healthy'"
              @click="filterByStatus('healthy')"
            >
              <span class="status-dot success" aria-hidden="true"></span>
              健康 <b>{{ healthyCount }}</b>
            </button>
            <button
              class="status-chip"
              :class="{ active: statusFilter === 'unhealthy' }"
              :aria-pressed="statusFilter === 'unhealthy'"
              @click="filterByStatus('unhealthy')"
            >
              <span class="status-dot error" aria-hidden="true"></span>
              异常 <b>{{ unhealthyCount }}</b>
            </button>
            <button
              class="status-chip"
              :class="{ active: statusFilter === 'pending' }"
              :aria-pressed="statusFilter === 'pending'"
              @click="filterByStatus('pending')"
            >
              <span class="status-dot warning" aria-hidden="true"></span>
              待签到 <b>{{ pendingCount }}</b>
            </button>
            <button
              v-if="disabledCount > 0"
              class="status-chip"
              :class="{ active: statusFilter === 'disabled' }"
              :aria-pressed="statusFilter === 'disabled'"
              @click="filterByStatus('disabled')"
            >
              <span class="status-dot default" aria-hidden="true"></span>
              已禁用 <b>{{ disabledCount }}</b>
            </button>
          </div>
          <div class="account-rows">
            <div
              v-for="account in displayAccounts.slice(0, 6)"
              :key="account.id"
              class="account-row"
              :class="{ alert: account.health_status === 'unhealthy' || isLowQuota(account) }"
              @click="$router.push(`/account/${account.id}`)"
            >
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
                      success: account.health_status === 'healthy',
                      error: account.health_status === 'unhealthy',
                      default: account.health_status === 'unknown'
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
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary :loading="signingId === account.id" :disabled="!account.is_active" @click="handleSign(account)">
                      <template #icon><n-icon :size="14"><FlashOutline /></n-icon></template>
                    </n-button>
                  </template>
                  签到
                </n-tooltip>
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary :loading="checkingId === account.id" @click="handleHealthCheck(account)">
                      <template #icon><n-icon :size="14"><PulseOutline /></n-icon></template>
                    </n-button>
                  </template>
                  健康检查
                </n-tooltip>
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary @click="showTokens(account)">
                      <template #icon><n-icon :size="14"><KeyOutline /></n-icon></template>
                    </n-button>
                  </template>
                  令牌
                </n-tooltip>
              </div>
            </div>
            <div v-if="displayAccounts.length === 0" class="row-empty">
              <n-icon :size="20" color="var(--text-quaternary)"><PeopleOutline /></n-icon>
              <span>{{ accounts.length === 0 ? '还没有账号，先确认平台配置再添加账号' : '暂无匹配账号' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右列 -->
      <div class="workspace-side">
        <!-- 额度分布 -->
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">额度分布</div>
          </div>
          <div class="panel-body chart-body">
            <QuotaPieChart :accounts="accounts" :is-dark="isDarkMode" />
          </div>
        </div>

        <!-- 最近活动 -->
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">最近活动</div>
            <n-button text size="small" @click="$router.push('/logs')">
              更多
              <template #icon><n-icon :size="12"><ChevronForwardOutline /></n-icon></template>
            </n-button>
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
            </div>
            <div v-if="recentActivities.length === 0" class="row-empty">
              <n-icon :size="20" color="var(--text-quaternary)"><TimeOutline /></n-icon>
              <span>暂无活动</span>
            </div>
          </div>
        </div>

        <!-- API 节点 -->
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">API 节点</div>
            <div class="panel-head-actions">
              <n-select
                v-model:value="selectedPlatformId"
                :options="platformOptions"
                size="tiny"
                placeholder="平台"
                :loading="loadingPlatforms"
                class="platform-select"
              />
              <n-button text size="small" :loading="syncingEndpoints" @click="handleSyncEndpoints">
                <template #icon><n-icon :size="12"><SyncOutline /></n-icon></template>
                同步
              </n-button>
            </div>
          </div>
          <div class="endpoints-list">
            <div v-for="ep in apiEndpoints" :key="ep.id" class="endpoint-row">
              <span class="endpoint-dot" :class="ep.color"></span>
              <div class="endpoint-main">
                <div class="endpoint-name">{{ ep.route }}</div>
                <div class="endpoint-url mono">{{ ep.url }}</div>
              </div>
              <n-button size="tiny" quaternary @click="copyEndpoint(ep.url)">
                <template #icon><n-icon :size="12"><CopyOutline /></n-icon></template>
              </n-button>
            </div>
            <div v-if="apiEndpoints.length === 0" class="row-empty">
              <span>{{ selectedPlatformId ? '暂无节点，点击同步' : '请先在平台管理页创建平台' }}</span>
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { TrendChart, AccountModal, QuotaPieChart, TokensModal } from '../components/dashboard'
import { accountApi, dashboardApi, notifyApi, apiEndpointsApi, groupsApi, signApi, statisticsApi, platformApi, settingsApi } from '../api'
import type { Account, AccountGroup, ApiToken, DashboardData, ApiEndpoint, CreateTokenParams, Platform, SelectOption } from '../types'
import {
  AddOutline,
  PeopleOutline,
  FlashOutline,
  RefreshOutline,
  SyncOutline,
  CopyOutline,
  ChevronForwardOutline,
  TimeOutline,
  PulseOutline,
  KeyOutline
} from '@vicons/ionicons5'
import { useEventStream, useFormat } from '../composables'
import { useClipboard } from '../composables/useClipboard'
import { useViewRefresh } from '../composables'
import type { SystemSettings } from '../types'

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
const statusFilter = ref<string | null>(null)
const quotaWarningThreshold = ref(5)
let eventRefreshTimer: number | null = null

const platformOptions = computed<SelectOption<number>[]>(() =>
  platforms.value.map(platform => ({
    label: platform.is_default ? `${platform.name} (默认)` : platform.name,
    value: platform.id
  }))
)

const healthyCount = computed(() => accounts.value.filter(a => a.is_active && a.health_status === 'healthy').length)
const unhealthyCount = computed(() => accounts.value.filter(a => a.is_active && a.health_status === 'unhealthy').length)
const pendingCount = computed(() => accounts.value.filter(a => a.is_active && (!a.last_sign || !isToday(a.last_sign.time))).length)
const disabledCount = computed(() => accounts.value.filter(a => !a.is_active).length)
const lowQuotaAccounts = computed(() =>
  accounts.value.filter(account => account.is_active && isLowQuota(account))
)

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

const isToday = (dateStr: string) => {
  const date = new Date(dateStr)
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

const filterByStatus = (status: string) => {
  statusFilter.value = statusFilter.value === status ? null : status
}

const isLowQuota = (account: Account) => (account.cached_quota || 0) < quotaWarningThreshold.value * 500000

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

const handleAccountSubmit = async (data: any) => {
  try {
    if (editingAccount.value) {
      const updateData: any = { is_active: data.is_active }
      if (data.user_id.trim()) updateData.user_id = data.user_id.trim()
      if (data.session_cookie.trim()) updateData.session_cookie = data.session_cookie.trim()
      if (data.note.trim() !== (editingAccount.value.note || '')) updateData.note = data.note.trim()
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
        user_id: data.user_id.trim() || undefined,
        login_username: data.login_username.trim() || undefined,
        login_password: data.login_password || undefined,
        note: data.note.trim() || undefined,
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
    await Promise.all([loadData(), loadEndpoints()])
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
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

/* 页头 */
.dashboard-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}

.head-main .page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin: 0;
}

.head-main .page-subtitle {
  margin-top: 2px;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.head-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-shrink: 0;
}

.warning-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid rgba(217, 119, 6, 0.24);
  border-radius: var(--radius-md);
  background: var(--warning-color-light);
}

.warning-title {
  color: var(--warning-color);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}

.warning-desc {
  margin-top: 2px;
  color: var(--text-secondary);
  font-size: var(--text-xs);
}

/* 指标卡 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.metric-card {
  padding: var(--spacing-4);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  transition: border-color var(--transition-fast);
}

.metric-card:hover {
  border-color: var(--border-color);
}

.metric-card.interactive {
  cursor: pointer;
}

.metric-label {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.metric-value {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  letter-spacing: -0.02em;
  line-height: 1;
  color: var(--text-primary);
}

.metric-sub {
  font-size: var(--text-md);
  font-weight: var(--font-medium);
  color: var(--text-tertiary);
  margin-left: 4px;
}

.metric-foot {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.metric-sub-label {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.metric-delta {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.metric-delta.up {
  color: var(--success-color);
}

.metric-delta.down {
  color: var(--error-color);
}

.metric-bar {
  flex: 1;
  height: 3px;
  background: var(--border-color-light);
  border-radius: 999px;
  overflow: hidden;
}

.metric-bar-fill {
  height: 100%;
  background: var(--success-color);
  transition: width var(--transition-slow);
}

.metric-bar-text {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-secondary);
  font-weight: var(--font-medium);
}

/* 工作区 */
.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  gap: var(--spacing-3);
}

.workspace-main,
.workspace-side {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

/* Panel 通用 */
.panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  height: 44px;
  padding: 0 var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.panel-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.panel-head-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.platform-select {
  width: 140px;
}

.panel-body {
  padding: var(--spacing-4);
}

.chart-body {
  min-height: 240px;
}

/* 状态筛选 chips */
.status-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 26px;
  padding: 0 var(--spacing-2);
  background: transparent;
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.status-chip:hover {
  border-color: var(--border-color);
  background: var(--bg-card-hover);
}

.status-chip.active {
  border-color: var(--primary-color);
  background: var(--primary-color-light);
  color: var(--primary-color);
}

.status-chip b {
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.status-chip.active b {
  color: var(--primary-color);
}

/* 账号行 */
.account-rows {
  display: flex;
  flex-direction: column;
}

.account-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  cursor: pointer;
  border-bottom: 1px solid var(--border-color-light);
  transition: background var(--transition-fast);
}

.account-row:last-child {
  border-bottom: none;
}

.account-row:hover {
  background: var(--bg-card-hover);
}

.account-row.alert {
  background: rgba(220, 38, 38, 0.04);
}

.row-avatar {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  background: var(--primary-color-light);
  color: var(--primary-color);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.row-avatar.inactive {
  background: var(--bg-secondary);
  color: var(--text-tertiary);
}

.row-main {
  min-width: 0;
}

.row-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.row-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  flex-shrink: 0;
}

.row-status-dot.success {
  background: var(--success-color);
}

.row-status-dot.error {
  background: var(--error-color);
}

.row-status-dot.default {
  background: var(--text-quaternary);
}

.row-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.row-quota {
  font-family: var(--font-mono);
  color: var(--text-secondary);
}

.row-quota.danger {
  color: var(--error-color);
}

.divider {
  color: var(--text-quaternary);
}

.row-tag {
  display: inline-flex;
  align-items: center;
  height: 16px;
  padding: 0 4px;
  font-size: 10px;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border-radius: var(--radius-xs);
}

.row-tag.warning {
  color: var(--warning-color);
  background: var(--warning-color-light);
}

.row-actions {
  display: flex;
  gap: 2px;
}

.row-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-2);
  padding: var(--spacing-8);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

/* 活动时间线 */
.activity-list {
  display: flex;
  flex-direction: column;
  max-height: 320px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  margin-top: 6px;
  flex-shrink: 0;
}

.activity-dot.success {
  background: var(--success-color);
}

.activity-dot.error {
  background: var(--error-color);
}

.activity-main {
  flex: 1;
  min-width: 0;
}

.activity-title {
  display: flex;
  gap: 6px;
  align-items: baseline;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.activity-title b {
  color: var(--text-primary);
  font-weight: var(--font-medium);
}

.activity-action.success {
  color: var(--success-color);
}

.activity-action.error {
  color: var(--error-color);
}

.activity-time {
  margin-top: 2px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* API 节点 */
.endpoints-list {
  display: flex;
  flex-direction: column;
  max-height: 320px;
  overflow-y: auto;
}

.endpoint-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.endpoint-row:last-child {
  border-bottom: none;
}

.endpoint-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--info-color);
}

.endpoint-dot.green {
  background: var(--success-color);
}

.endpoint-dot.yellow {
  background: var(--warning-color);
}

.endpoint-dot.red {
  background: var(--error-color);
}

.endpoint-dot.blue {
  background: var(--info-color);
}

.endpoint-main {
  min-width: 0;
}

.endpoint-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.endpoint-url {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-head {
    flex-direction: column;
    align-items: stretch;
  }

  .warning-banner {
    flex-direction: column;
    align-items: flex-start;
  }

  .head-actions {
    width: 100%;
  }

  .head-actions :deep(.n-button) {
    flex: 1 1 0;
  }

  .metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
