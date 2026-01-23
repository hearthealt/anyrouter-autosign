<template>
  <div class="dashboard">
    <!-- 快捷操作栏 -->
    <div class="quick-actions">
      <n-button type="primary" size="large" @click="handleBatchSign" :loading="batchSigning">
        <template #icon><n-icon><FlashOutline /></n-icon></template>
        一键签到
      </n-button>
      <n-button size="large" @click="refreshData" :loading="loading">
        <template #icon><n-icon><RefreshOutline /></n-icon></template>
        刷新数据
      </n-button>
      <n-button size="large" @click="showAddModal">
        <template #icon><n-icon><AddOutline /></n-icon></template>
        添加账号
      </n-button>
      <n-button size="large" @click="handleSyncEndpoints" :loading="syncingEndpoints">
        <template #icon><n-icon><SyncOutline /></n-icon></template>
        同步节点
      </n-button>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon accounts">
          <n-icon :size="28"><PeopleOutline /></n-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard?.account_count || 0 }}</div>
          <div class="stat-label">账号总数</div>
        </div>
        <div class="stat-trend" v-if="(dashboard?.unhealthy_account_count ?? 0) > 0">
          <span class="trend-badge error">{{ dashboard?.unhealthy_account_count }} 异常</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon sign">
          <n-icon :size="28"><CheckmarkCircleOutline /></n-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">
            {{ dashboard?.today_sign_success || 0 }}
            <span class="stat-sub">/{{ dashboard?.today_sign_count || 0 }}</span>
          </div>
          <div class="stat-label">今日签到</div>
        </div>
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

      <div class="stat-card">
        <div class="stat-icon reward">
          <n-icon :size="28"><GiftOutline /></n-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard?.month_reward_display || '$0.00' }}</div>
          <div class="stat-label">本月奖励</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon quota">
          <n-icon :size="28"><WalletOutline /></n-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ dashboard?.total_quota_display || '$0.00' }}</div>
          <div class="stat-label">总剩余额度</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-grid">
      <!-- 签到趋势图表 -->
      <div class="chart-card card">
        <div class="card-header">
          <h3 class="card-title">签到趋势</h3>
          <n-radio-group v-model:value="trendDays" size="small">
            <n-radio-button :value="7">7天</n-radio-button>
            <n-radio-button :value="30">30天</n-radio-button>
          </n-radio-group>
        </div>
        <div class="card-body">
          <TrendChart :data="dashboard?.daily_trend || []" :is-dark="isDarkMode" />
        </div>
      </div>

      <!-- 额度分布饼图 -->
      <div class="chart-card card">
        <div class="card-header">
          <h3 class="card-title">额度分布</h3>
        </div>
        <div class="card-body">
          <QuotaPieChart :accounts="accounts" :is-dark="isDarkMode" />
        </div>
      </div>
    </div>

    <!-- 下方区域 -->
    <div class="bottom-grid">
      <!-- 账号状态列表 -->
      <div class="status-card card">
        <div class="card-header">
          <h3 class="card-title">账号状态</h3>
          <n-button text size="small" @click="$router.push('/settings')">
            管理
            <template #icon><n-icon><ChevronForwardOutline /></n-icon></template>
          </n-button>
        </div>
        <div class="status-list">
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

        <!-- 账号快速列表 -->
        <div class="account-quick-list">
          <div
            v-for="account in displayAccounts.slice(0, 5)"
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
          <div v-if="accounts.length > 5" class="view-all" @click="showAllAccounts = true">
            查看全部 {{ accounts.length }} 个账号
          </div>
        </div>
      </div>

      <!-- 最近活动时间线 -->
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
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { TrendChart, AccountModal, QuotaPieChart } from '../components/dashboard'
import TokensModal from '../components/dashboard/TokensModal.vue'
import { accountApi, dashboardApi, notifyApi, apiEndpointsApi, groupsApi, signApi } from '../api'
import type { Account, AccountGroup, ApiToken, DashboardData, ApiEndpoint, CreateTokenParams } from '../types'
import {
  PeopleOutline,
  CheckmarkCircleOutline,
  GiftOutline,
  WalletOutline,
  FlashOutline,
  SyncOutline,
  CopyOutline,
  AddOutline,
  RefreshOutline,
  ChevronForwardOutline,
  TimeOutline,
  PulseOutline,
  KeyOutline
} from '@vicons/ionicons5'
import { useFormat } from '../composables'

const message = useMessage()
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
    message.success('已复制到剪贴板')
  } catch {
    message.error('复制失败')
  }
}

// 签到状态
const signingId = ref<number | null>(null)
const batchSigning = ref(false)
const checkingId = ref<number | null>(null)

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
    message.error(e.message)
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  loadData()
  loadEndpoints()
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

// 同步 API 节点
const handleSyncEndpoints = async () => {
  syncingEndpoints.value = true
  try {
    const res: any = await apiEndpointsApi.sync()
    message.success(res.message || '同步成功')
    loadEndpoints()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    syncingEndpoints.value = false
  }
}

// 账号操作
const showAddModal = () => {
  editingAccount.value = null
  showAccountModal.value = true
}

const handleAccountSubmit = async (data: any) => {
  try {
    if (editingAccount.value) {
      const updateData: any = { is_active: data.is_active }
      if (data.user_id.trim()) updateData.user_id = data.user_id.trim()
      if (data.session_cookie.trim()) updateData.session_cookie = data.session_cookie.trim()
      if (data.group_id !== editingAccount.value.group_id) {
        updateData.group_id = data.group_id || 0
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
      message.success('更新成功')
    } else {
      const res = await accountApi.create({
        session_cookie: data.session_cookie,
        user_id: data.user_id,
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
      message.success('账号添加成功')
    }

    showAccountModal.value = false
    loadData()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    accountModalRef.value?.setSubmitting(false)
  }
}

// 签到操作
const handleSign = async (account: Account) => {
  if (!account.is_active) {
    message.warning('该账号已禁用，无法签到')
    return
  }
  signingId.value = account.id
  try {
    const res = await signApi.sign(account.id)
    message.success(res.data?.message || '签到成功')
    loadData()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    signingId.value = null
  }
}

// 健康检查
const handleHealthCheck = async (account: Account) => {
  checkingId.value = account.id
  try {
    await accountApi.healthCheck(account.id)
    message.success('健康检查完成')
    loadData()
  } catch (e: any) {
    message.error(e.message)
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
    message.error(e.message)
  } finally {
    loadingTokens.value = false
  }
}

const handleBatchSign = async () => {
  batchSigning.value = true
  try {
    const res = await signApi.batchSign()
    message.success(`批量签到完成：成功 ${res.data.success_count}，失败 ${res.data.fail_count}`)
    loadData()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    batchSigning.value = false
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
    message.success('刷新成功')
  } catch (e: any) {
    message.error(e.message)
  } finally {
    syncingTokens.value = false
  }
}

const handleDeleteToken = async (token: ApiToken) => {
  if (!tokenAccount.value) return
  deletingTokenId.value = token.token_id
  try {
    await accountApi.deleteToken(tokenAccount.value.id, token.token_id)
    message.success('删除成功')
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
  } catch (e: any) {
    message.error(e.message)
  } finally {
    deletingTokenId.value = null
  }
}

const handleCreateToken = async (data: CreateTokenParams) => {
  if (!tokenAccount.value) return
  try {
    await accountApi.createToken(tokenAccount.value.id, data)
    message.success('令牌创建成功')
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    return true
  } catch (e: any) {
    message.error(e.message)
    return false
  }
}

const handleEditToken = async (tokenId: number, data: CreateTokenParams) => {
  if (!tokenAccount.value) return
  try {
    await accountApi.updateToken(tokenAccount.value.id, tokenId, data)
    message.success('令牌更新成功')
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    return true
  } catch (e: any) {
    message.error(e.message)
    return false
  }
}

onMounted(() => {
  loadData()
  loadGroups()
  loadEndpoints()
})
</script>

<style scoped>
.dashboard {

  margin: 0 auto;
}

/* 快捷操作栏 */
.quick-actions {
  display: flex;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-6);
  flex-wrap: wrap;
}

.quick-actions .n-button {
  border-radius: var(--radius-lg);
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.stat-card {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  padding: var(--spacing-5);
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-4);
  position: relative;
  box-shadow: var(--shadow-card);
  transition: all var(--transition-normal);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.accounts {
  background: var(--info-color-light);
  color: var(--info-color);
}

.stat-icon.sign {
  background: var(--success-color-light);
  color: var(--success-color);
}

.stat-icon.reward {
  background: var(--warning-color-light);
  color: var(--warning-color);
}

.stat-icon.quota {
  background: var(--purple-light);
  color: var(--purple-color);
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-sub {
  font-size: var(--text-lg);
  font-weight: var(--font-normal);
  color: var(--text-tertiary);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-top: var(--spacing-1);
}

.stat-trend {
  position: absolute;
  top: var(--spacing-4);
  right: var(--spacing-4);
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.stat-trend.up {
  color: var(--success-color);
}

.stat-trend.down {
  color: var(--error-color);
}

.trend-badge {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.trend-badge.error {
  background: var(--error-color-light);
  color: var(--error-color);
}

.stat-progress {
  position: absolute;
  bottom: var(--spacing-4);
  right: var(--spacing-4);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  width: 100px;
}

.progress-text {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
}

/* 图表区域 */
.charts-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-6);
}

.chart-card .card-body {
  padding: var(--spacing-4);
  min-height: 280px;
}

/* 下方区域 */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--spacing-6);
}

/* 账号状态卡片 */
.status-list {
  display: flex;
  gap: var(--spacing-4);
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
}

.status-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.status-group:hover {
  background: var(--bg-card-hover);
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-full);
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
  background: var(--text-tertiary);
}

.status-group.active {
  background: var(--primary-color-light);
}

.status-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.status-count {
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--text-primary);
}

/* 账号快速列表 */
.account-quick-list {
  padding: var(--spacing-3);
}

.account-quick-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.account-quick-item:hover {
  background: var(--bg-card-hover);
}

.account-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--primary-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-bold);
  font-size: var(--text-sm);
  flex-shrink: 0;
}

.account-avatar.inactive {
  background: linear-gradient(135deg, #9ca3af 0%, #d1d5db 100%);
}

.account-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  cursor: pointer;
}

.account-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.disabled-tag {
  font-size: var(--text-xs);
  padding: 1px 6px;
  background: var(--bg-tag);
  color: var(--text-tertiary);
  border-radius: var(--radius-sm);
  font-weight: var(--font-normal);
}

.account-meta-line {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--text-xs);
}

.account-quota {
  font-size: var(--text-xs);
  color: var(--success-color);
}

.meta-divider {
  color: var(--border-color);
}

.last-sign-time {
  color: var(--text-tertiary);
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
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
}

.account-status .status-indicator {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-full);
  display: block;
}

.account-status.healthy .status-indicator {
  background: var(--success-color);
}

.account-status.unhealthy .status-indicator {
  background: var(--error-color);
}

.account-status.unknown .status-indicator {
  background: var(--text-tertiary);
}

.account-status.disabled .status-indicator {
  background: var(--text-tertiary);
}

.view-all {
  text-align: center;
  padding: var(--spacing-3);
  font-size: var(--text-sm);
  color: var(--primary-color);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: background var(--transition-fast);
}

.view-all:hover {
  background: var(--primary-color-light);
}

/* 活动时间线 */
.activity-timeline {
  padding: var(--spacing-4) var(--spacing-5);
  max-height: 400px;
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  gap: var(--spacing-3);
  padding: var(--spacing-2) 0;
  position: relative;
}

.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 24px;
  bottom: -8px;
  width: 2px;
  background: var(--border-color-light);
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
  margin-top: 4px;
}

.timeline-dot.success {
  background: var(--success-color);
}

.timeline-dot.error {
  background: var(--error-color);
}

.timeline-dot.info {
  background: var(--info-color);
}

.timeline-content {
  flex: 1;
  min-width: 0;
}

.timeline-title {
  font-size: var(--text-sm);
  color: var(--text-primary);
  display: flex;
  gap: var(--spacing-2);
}

.activity-account {
  font-weight: var(--font-medium);
}

.activity-action {
  color: var(--text-secondary);
}

.timeline-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: 2px;
}

.timeline-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  gap: var(--spacing-2);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

/* API 节点 */
.endpoints-list {
  padding: var(--spacing-4) var(--spacing-5);
}

.endpoint-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) 0;
  border-bottom: 1px solid var(--border-color-light);
}

.endpoint-item:last-child {
  border-bottom: none;
}

.endpoint-status {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
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

.endpoint-status.gray {
  background: var(--text-tertiary);
}

.endpoint-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.endpoint-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.endpoint-url {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.endpoints-empty {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

/* 全部账号弹窗 */
.all-accounts-list {
  max-height: 400px;
  overflow-y: auto;
}

.account-list-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.account-list-item:hover {
  background: var(--bg-card-hover);
}

.account-details {
  flex: 1;
  min-width: 0;
}

.account-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: 2px;
}

.account-meta .divider {
  color: var(--border-color);
}

.account-meta .health.healthy {
  color: var(--success-color);
}

.account-meta .health.unhealthy {
  color: var(--error-color);
}

.account-meta .health.disabled {
  color: var(--text-tertiary);
}

.account-meta .sign-time {
  color: var(--text-tertiary);
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }

  .bottom-grid {
    grid-template-columns: 1fr 1fr;
  }

  .bottom-grid .endpoints-card {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .quick-actions {
    flex-direction: column;
  }

  .quick-actions .n-button {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    flex-direction: row;
    align-items: center;
  }

  .stat-progress {
    position: static;
    width: auto;
    margin-top: var(--spacing-2);
  }

  .stat-trend {
    position: static;
    margin-top: var(--spacing-2);
  }

  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .bottom-grid .endpoints-card {
    grid-column: span 1;
  }

  .status-list {
    flex-wrap: wrap;
  }
}
</style>
