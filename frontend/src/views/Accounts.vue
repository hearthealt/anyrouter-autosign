<template>
  <div class="accounts-page">
    <section class="toolbar-card rise-1">
      <div class="toolbar-top">
        <div class="toolbar-copy">
        <h1>账号管理</h1>
          <p>直接查看、筛选和操作账号，顶部只保留高频动作。</p>
        </div>

        <div class="toolbar-actions">
          <n-button quaternary @click="loadData" :loading="loading">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新数据
          </n-button>
          <n-button secondary @click="handleBatchHealthCheck" :loading="batchChecking">
            <template #icon><n-icon><PulseOutline /></n-icon></template>
            批量检查
          </n-button>
          <n-button secondary @click="handleBatchSign" :loading="batchSigning">
            <template #icon><n-icon><FlashOutline /></n-icon></template>
            一键签到
          </n-button>
          <n-button type="primary" @click="showAddModal">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            添加账号
          </n-button>
        </div>
      </div>

      <div class="toolbar-filters">
        <div class="filter-field search-span">
          <n-input
            v-model:value="searchKeyword"
            clearable
            placeholder="搜索用户名、显示名、平台或 User ID"
          >
            <template #prefix><n-icon><SearchOutline /></n-icon></template>
          </n-input>
        </div>

        <div class="filter-field">
          <n-select
            v-model:value="selectedPlatformId"
            :options="platformOptions"
            clearable
            placeholder="全部平台"
          />
        </div>

        <div class="filter-field">
          <n-select
            v-model:value="selectedGroupId"
            :options="groupOptions"
            clearable
            placeholder="全部分组"
          />
        </div>
      </div>

      <div class="toolbar-bottom">
        <div class="toolbar-metrics">
          <span class="metric-chip">账号 {{ formatNumber(accounts.length) }}</span>
          <span class="metric-chip">健康率 {{ healthRatio }}%</span>
          <span class="metric-chip">待签到 {{ formatNumber(pendingCount) }}</span>
          <span class="metric-chip">剩余 {{ formatQuota(totalQuota) }}</span>
        </div>

        <div class="status-rail compact">
          <button
            v-for="pill in quickStatusPills"
            :key="pill.key"
            type="button"
            class="status-pill"
            :class="[pill.tone, { active: (pill.value === null && selectedStatus === null) || selectedStatus === pill.value }]"
            @click="setStatusFilter(pill.value)"
          >
            <span class="pill-label">{{ pill.label }}</span>
            <strong>{{ pill.count }}</strong>
          </button>
        </div>
      </div>
    </section>

    <section class="workspace-shell rise-2">
      <div class="workspace-head compact">
        <div class="workspace-copy">
          <h2>账号列表</h2>
        </div>

        <div class="workspace-summary">
          <div class="summary-chip">
            <span>当前结果</span>
            <strong>{{ filteredAccounts.length }}</strong>
          </div>
          <div class="summary-chip">
            <span>异常账号</span>
            <strong>{{ unhealthyCount }}</strong>
          </div>
          <div class="summary-chip">
            <span>禁用账号</span>
            <strong>{{ disabledCount }}</strong>
          </div>
        </div>
      </div>

      <div v-if="loading || filteredAccounts.length > 0" class="table-wrap">
        <n-data-table
          class="accounts-table"
          :columns="columns"
          :data="filteredAccounts"
          :row-key="getAccountRowKey"
          :loading="loading"
          :pagination="false"
          :single-line="false"
          size="small"
          :scroll-x="1420"
        />
      </div>

      <div v-else class="empty-state">
        <div class="empty-state-mark">A</div>
        <h3>没有匹配的账号</h3>
        <p>当前筛选条件下没有结果。可以放宽筛选范围，或者直接添加新的接入账号。</p>
        <n-button type="primary" @click="showAddModal">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          添加账号
        </n-button>
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
import { computed, h, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, type DataTableColumns } from 'naive-ui'
import {
  AddOutline,
  CreateOutline,
  EyeOutline,
  FlashOutline,
  KeyOutline,
  PulseOutline,
  RefreshOutline,
  SearchOutline,
  TrashOutline
} from '@vicons/ionicons5'
import { AccountModal, TokensModal } from '../components'
import { accountApi, groupsApi, notifyApi, platformApi, signApi } from '../api'
import { useFormat } from '../composables'
import type { Account, AccountGroup, ApiToken, CreateTokenParams, Platform, SelectOption } from '../types'

type StatusFilter = 'healthy' | 'unhealthy' | 'pending' | 'disabled'

const router = useRouter()
const { formatDateTime, formatQuota, formatRelativeTime, formatNumber } = useFormat()

const groupColors: Record<string, string> = {
  default: '#8f877a',
  blue: '#2f6de1',
  green: '#23735d',
  red: '#c24d3c',
  orange: '#cf7a2a',
  purple: '#7852d7',
  pink: '#c75883',
  cyan: '#1f8f99'
}

const accounts = ref<Account[]>([])
const groups = ref<AccountGroup[]>([])
const platforms = ref<Platform[]>([])
const loading = ref(false)
const batchSigning = ref(false)
const batchChecking = ref(false)
const signingId = ref<number | null>(null)
const checkingId = ref<number | null>(null)
const searchKeyword = ref('')
const selectedPlatformId = ref<number | null>(null)
const selectedGroupId = ref<number | null>(null)
const selectedStatus = ref<StatusFilter | null>(null)
const showAccountModal = ref(false)
const editingAccount = ref<Account | null>(null)
const accountModalRef = ref<InstanceType<typeof AccountModal> | null>(null)
const showTokensVisible = ref(false)
const tokenAccount = ref<Account | null>(null)
const tokens = ref<ApiToken[]>([])
const loadingTokens = ref(false)
const syncingTokens = ref(false)
const deletingTokenId = ref<number | null>(null)

const activeCount = computed(() => accounts.value.filter(account => account.is_active).length)
const healthyCount = computed(() => accounts.value.filter(account => account.is_active && account.health_status === 'healthy').length)
const unhealthyCount = computed(() => accounts.value.filter(account => account.is_active && account.health_status === 'unhealthy').length)
const disabledCount = computed(() => accounts.value.filter(account => !account.is_active).length)
const pendingCount = computed(() => accounts.value.filter(account => account.is_active && (!account.last_sign || !isToday(account.last_sign.time))).length)
const totalQuota = computed(() => accounts.value.reduce((sum, account) => sum + (account.cached_quota || 0), 0))
const healthRatio = computed(() => (activeCount.value > 0 ? Math.round((healthyCount.value / activeCount.value) * 100) : 0))

const platformOptions = computed<SelectOption<number>[]>(() =>
  platforms.value.map(platform => ({ label: platform.name, value: platform.id }))
)
const groupOptions = computed<SelectOption<number>[]>(() =>
  groups.value.map(group => ({ label: group.name, value: group.id }))
)

const quickStatusPills = computed(() => [
  { key: 'all', label: '全部', count: accounts.value.length, value: null as StatusFilter | null, tone: 'all' },
  { key: 'healthy', label: '健康', count: healthyCount.value, value: 'healthy' as StatusFilter, tone: 'healthy' },
  { key: 'unhealthy', label: '异常', count: unhealthyCount.value, value: 'unhealthy' as StatusFilter, tone: 'unhealthy' },
  { key: 'pending', label: '待签到', count: pendingCount.value, value: 'pending' as StatusFilter, tone: 'pending' },
  { key: 'disabled', label: '禁用', count: disabledCount.value, value: 'disabled' as StatusFilter, tone: 'disabled' }
])

const filteredAccounts = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()

  return accounts.value.filter(account => {
    const matchesKeyword =
      !keyword ||
      [account.username, account.display_name, getPlatformName(account), String(getUserId(account))]
        .filter(Boolean)
        .some(value => String(value).toLowerCase().includes(keyword))

    const matchesPlatform = selectedPlatformId.value == null || account.platform?.id === selectedPlatformId.value
    const matchesGroup = selectedGroupId.value == null || account.group_id === selectedGroupId.value
    const matchesStatus =
      selectedStatus.value == null ||
      (selectedStatus.value === 'healthy' && account.is_active && account.health_status === 'healthy') ||
      (selectedStatus.value === 'unhealthy' && account.is_active && account.health_status === 'unhealthy') ||
      (selectedStatus.value === 'pending' && account.is_active && (!account.last_sign || !isToday(account.last_sign.time))) ||
      (selectedStatus.value === 'disabled' && !account.is_active)

    return matchesKeyword && matchesPlatform && matchesGroup && matchesStatus
  })
})

const getAccountRowKey = (account: Account) => account.id

const setStatusFilter = (status: StatusFilter | null) => {
  if (status === null) {
    selectedStatus.value = null
    return
  }
  selectedStatus.value = selectedStatus.value === status ? null : status
}

const isToday = (value: string) => {
  const date = new Date(value)
  const today = new Date()
  return date.toDateString() === today.toDateString()
}

const getUserId = (account: Account) => account.anrouter_user_id ?? account.anyrouter_user_id ?? '-'
const getPlatformName = (account: Account) => account.platform?.name || '未分配平台'
const getGroupInfo = (account: Account) => account.group || groups.value.find(group => group.id === account.group_id)
const getGroupName = (account: Account) => getGroupInfo(account)?.name || '未分组'
const getGroupColor = (color?: string) => groupColors[color || 'default'] || groupColors.default

const getHealthTone = (account: Account) => {
  if (!account.is_active) return 'disabled'
  if (account.health_status === 'healthy') return 'healthy'
  if (account.health_status === 'unhealthy') return 'unhealthy'
  return 'pending'
}

const getHealthLabel = (account: Account) => {
  if (!account.is_active) return '已禁用'
  if (account.health_status === 'healthy') return '健康'
  if (account.health_status === 'unhealthy') return '异常'
  return '待检查'
}

const getQuotaRatio = (account: Account) => {
  const ratio = Number.parseFloat(String(account.quota_percent || '0').replace('%', ''))
  if (Number.isNaN(ratio)) return 0
  return Math.max(0, Math.min(100, ratio))
}

const getLastSignTone = (account: Account) => {
  if (!account.last_sign) return 'pending'
  if (account.last_sign.success && isToday(account.last_sign.time)) return 'healthy'
  if (account.last_sign.success) return 'pending'
  return 'unhealthy'
}

const getLastSignCell = (account: Account) => {
  if (!account.last_sign) return '未签到'
  return account.last_sign.success ? `成功 · ${formatRelativeTime(account.last_sign.time)}` : `失败 · ${formatRelativeTime(account.last_sign.time)}`
}

const getLastSignDetail = (account: Account) => {
  if (!account.last_sign) return '暂无签到记录。'
  if (account.last_sign.message) return account.last_sign.message
  return account.last_sign.success ? '最近一次签到成功。' : '最近一次签到失败。'
}

const getHealthDetail = (account: Account) =>
  account.health_message || (account.health_status === 'healthy' ? '最近一次健康检查正常。' : '暂无健康检查备注。')

const openAccountDetail = (account: Account) => {
  router.push(`/account/${account.id}`)
}

const showAddModal = () => {
  editingAccount.value = null
  showAccountModal.value = true
}

const showEditModal = (account: Account) => {
  editingAccount.value = account
  showAccountModal.value = true
}

const handleDeleteAccount = async (account: Account) => {
  if (!confirm(`确定删除账号 "${account.username}" 吗？`)) {
    return
  }

  try {
    await accountApi.delete(account.id)
    window.$notify('账号删除成功', 'success')
    await loadData()
  } catch (e: any) {
    window.$notify(e.message || '删除失败', 'error')
  }
}

const handleSign = async (account: Account) => {
  if (!account.is_active) {
    window.$notify('该账号已禁用，无法签到', 'warning')
    return
  }

  signingId.value = account.id
  try {
    const res: any = await signApi.sign(account.id)
    window.$notify(res.data?.message || '签到成功', 'success')
    await loadData()
  } catch (e: any) {
    window.$notify(e.message || '签到失败', 'error')
  } finally {
    signingId.value = null
  }
}

const handleBatchSign = async () => {
  batchSigning.value = true
  try {
    const res: any = await signApi.batchSign()
    window.$notify(res.message || '批量签到完成', 'success')
    await loadData()
  } catch (e: any) {
    window.$notify(e.message || '批量签到失败', 'error')
  } finally {
    batchSigning.value = false
  }
}

const handleHealthCheck = async (account: Account) => {
  checkingId.value = account.id
  try {
    await accountApi.healthCheck(account.id)
    window.$notify('健康检查完成', 'success')
    await loadData()
  } catch (e: any) {
    window.$notify(e.message || '健康检查失败', 'error')
  } finally {
    checkingId.value = null
  }
}

const handleBatchHealthCheck = async () => {
  batchChecking.value = true
  try {
    const res: any = await accountApi.healthCheckAll()
    const healthy = res.data?.healthy_count ?? 0
    const unhealthy = res.data?.unhealthy_count ?? 0
    window.$notify(`批量检查完成，正常 ${healthy}，异常 ${unhealthy}`, 'success')
    await loadData()
  } catch (e: any) {
    window.$notify(e.message || '批量检查失败', 'error')
  } finally {
    batchChecking.value = false
  }
}

const showTokens = async (account: Account) => {
  tokenAccount.value = account
  showTokensVisible.value = true
  loadingTokens.value = true
  try {
    const res: any = await accountApi.getTokens(account.id)
    tokens.value = res.data || []
  } catch (e: any) {
    window.$notify(e.message || '加载令牌失败', 'error')
  } finally {
    loadingTokens.value = false
  }
}

const handleSyncTokens = async () => {
  if (!tokenAccount.value) return
  syncingTokens.value = true
  try {
    await accountApi.syncTokens(tokenAccount.value.id)
    const res: any = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    window.$notify('令牌同步成功', 'success')
  } catch (e: any) {
    window.$notify(e.message || '同步失败', 'error')
  } finally {
    syncingTokens.value = false
  }
}

const handleDeleteToken = async (token: ApiToken) => {
  if (!tokenAccount.value) return
  deletingTokenId.value = token.token_id
  try {
    await accountApi.deleteToken(tokenAccount.value.id, token.token_id)
    const res: any = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    window.$notify('令牌删除成功', 'success')
  } catch (e: any) {
    window.$notify(e.message || '删除失败', 'error')
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
    const res: any = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    window.$notify('令牌创建成功', 'success')
    done?.(true)
    return true
  } catch (e: any) {
    window.$notify(e.message || '创建失败', 'error')
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
    const res: any = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
    window.$notify('令牌更新成功', 'success')
    done?.(true)
    return true
  } catch (e: any) {
    window.$notify(e.message || '更新失败', 'error')
    done?.(false)
    return false
  }
}

const handleAccountSubmit = async (data: {
  user_id: string
  session_cookie: string
  is_active?: boolean
  platform_id: number | null
  group_id: number | null
  notify_channel_ids: number[]
}) => {
  try {
    if (editingAccount.value) {
      const updateData: any = { is_active: data.is_active }

      if (data.user_id.trim()) updateData.user_id = data.user_id.trim()
      if (data.session_cookie.trim()) updateData.session_cookie = data.session_cookie.trim()
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
      window.$notify('账号更新成功', 'success')
    } else {
      const res: any = await accountApi.create({
        session_cookie: data.session_cookie,
        user_id: data.user_id,
        platform_id: data.platform_id as number,
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
    await loadData()
  } catch (e: any) {
    window.$notify(e.message || '保存失败', 'error')
  } finally {
    accountModalRef.value?.setSubmitting(false)
  }
}

const loadData = async () => {
  loading.value = true
  try {
    const [accountsRes, groupsRes, platformsRes] = await Promise.allSettled([
      accountApi.getList(),
      groupsApi.getList(),
      platformApi.getList()
    ])

    if (accountsRes.status === 'fulfilled') {
      accounts.value = accountsRes.value.data || []
    } else {
      accounts.value = []
      window.$notify(accountsRes.reason?.message || '加载账号数据失败', 'error')
    }

    if (groupsRes.status === 'fulfilled') {
      groups.value = groupsRes.value.data || []
    } else {
      groups.value = []
      console.error('Failed to load groups:', groupsRes.reason)
    }

    if (platformsRes.status === 'fulfilled') {
      platforms.value = platformsRes.value.data || []
    } else {
      platforms.value = []
      console.error('Failed to load platforms:', platformsRes.reason)
    }
  } catch (e: any) {
    window.$notify(e.message || '加载账号数据失败', 'error')
  } finally {
    loading.value = false
  }
}

const renderAccountNameCell = (account: Account) =>
  h('div', { class: 'simple-cell' }, [
    h('strong', { class: 'simple-name' }, account.username || '-')
  ])

const renderPlatformCell = (account: Account) =>
  h('div', { class: 'simple-cell' }, [
    h('span', { class: 'simple-text' }, getPlatformName(account))
  ])

const renderGroupCell = (account: Account) => {
  const group = getGroupInfo(account)
  if (!group) {
    return h('div', { class: 'simple-cell' }, [
      h('span', { class: 'simple-text muted' }, '未分组')
    ])
  }

  return h('div', { class: 'simple-cell' }, [
    h(
      'span',
      { class: 'group-pill', style: { '--group-color': getGroupColor(group.color) } },
      group.name
    )
  ])
}

const renderQuotaCell = (account: Account) =>
  h('div', { class: 'quota-cell' }, [
    h('strong', { class: 'quota-primary' }, formatQuota(account.cached_quota || 0)),
    h('span', { class: 'quota-secondary' }, `已用 ${formatQuota(account.cached_used_quota || 0)} · 请求 ${formatNumber(account.cached_request_count || 0)}`),
    h('div', { class: 'quota-rail' }, [
      h('span', { class: 'quota-fill', style: { width: `${getQuotaRatio(account)}%` } })
    ])
  ])

const renderLastSignCell = (account: Account) =>
  h('div', { class: 'sign-cell' }, [
    h('span', { class: ['sign-badge', getLastSignTone(account)] }, getLastSignCell(account)),
    h('span', { class: 'sign-caption' }, getLastSignDetail(account))
  ])

const renderHealthCell = (account: Account) =>
  h('div', { class: 'health-cell' }, [
    h('span', { class: ['health-badge', getHealthTone(account)] }, getHealthLabel(account)),
    h('span', { class: 'health-caption' }, account.last_health_check ? `${formatRelativeTime(account.last_health_check)} 检查` : '尚未执行检查')
  ])

const renderAccountExpand = (account: Account) =>
  h('div', { class: 'account-expand' }, [
    h('div', { class: 'expand-grid' }, [
      h('div', { class: 'expand-card' }, [
        h('span', { class: 'expand-label' }, '平台归属'),
        h('strong', { class: 'expand-value' }, getPlatformName(account)),
        h('small', { class: 'expand-note' }, '在账号详情页查看完整平台链路')
      ]),
      h('div', { class: 'expand-card' }, [
        h('span', { class: 'expand-label' }, '本地分组'),
        h('strong', { class: 'expand-value' }, getGroupName(account)),
        h('small', { class: 'expand-note' }, `远端组: ${account.cached_user_group || '-'}`)
      ]),
      h('div', { class: 'expand-card' }, [
        h('span', { class: 'expand-label' }, '额度更新时间'),
        h('strong', { class: 'expand-value' }, account.quota_updated_at ? formatDateTime(account.quota_updated_at) : '暂无缓存'),
        h('small', { class: 'expand-note' }, `推广码 ${account.cached_aff_code || '-'}`)
      ]),
      h('div', { class: 'expand-card' }, [
        h('span', { class: 'expand-label' }, '创建时间'),
        h('strong', { class: 'expand-value' }, formatDateTime(account.created_at)),
        h('small', { class: 'expand-note' }, `最近更新 ${formatDateTime(account.updated_at)}`)
      ])
    ]),
    h('div', { class: 'expand-narrative' }, [
      h('div', { class: 'narrative-block' }, [
        h('span', { class: 'narrative-kicker' }, '签到备注'),
        h('p', getLastSignDetail(account))
      ]),
      h('div', { class: 'narrative-block' }, [
        h('span', { class: 'narrative-kicker' }, '健康备注'),
        h('p', getHealthDetail(account))
      ])
    ]),
    h('div', { class: 'expand-actions' }, [
      h(NButton, { size: 'small', quaternary: true, onClick: () => openAccountDetail(account) }, { icon: () => h(EyeOutline), default: () => '详情' }),
      h(NButton, { size: 'small', quaternary: true, onClick: () => showEditModal(account) }, { icon: () => h(CreateOutline), default: () => '编辑' }),
      h(NButton, { size: 'small', quaternary: true, onClick: () => showTokens(account) }, { icon: () => h(KeyOutline), default: () => 'Token' }),
      h(NButton, { size: 'small', quaternary: true, disabled: !account.is_active, loading: signingId.value === account.id, onClick: () => handleSign(account) }, { icon: () => h(FlashOutline), default: () => '签到' }),
      h(NButton, { size: 'small', quaternary: true, loading: checkingId.value === account.id, onClick: () => handleHealthCheck(account) }, { icon: () => h(PulseOutline), default: () => '检查' }),
      h(NButton, { size: 'small', quaternary: true, type: 'error', onClick: () => handleDeleteAccount(account) }, { icon: () => h(TrashOutline), default: () => '删除' })
    ])
  ])

const renderActions = (account: Account) =>
  h('div', { class: 'table-actions' }, [
    h(NButton, { size: 'small', quaternary: true, onClick: () => openAccountDetail(account) }, { default: () => '详情' }),
    h(NButton, { size: 'small', quaternary: true, onClick: () => showEditModal(account) }, { default: () => '编辑' }),
    h(NButton, { size: 'small', quaternary: true, onClick: () => showTokens(account) }, { default: () => 'Token' }),
    h(NButton, { size: 'small', quaternary: true, disabled: !account.is_active, loading: signingId.value === account.id, onClick: () => handleSign(account) }, { default: () => '签到' })
  ])

const columns = computed<DataTableColumns<Account>>(() => [
  { type: 'expand', expandable: () => true, renderExpand: renderAccountExpand },
  { title: '账号', key: 'username', minWidth: 180, render: row => renderAccountNameCell(row) },
  { title: '平台名', key: 'platform_name', minWidth: 180, render: row => renderPlatformCell(row) },
  { title: '分组', key: 'group_name', minWidth: 140, render: row => renderGroupCell(row) },
  { title: '额度', key: 'quota', minWidth: 260, render: row => renderQuotaCell(row) },
  { title: '最近签到', key: 'last_sign', minWidth: 240, render: row => renderLastSignCell(row) },
  { title: '健康状态', key: 'health_status', width: 150, render: row => renderHealthCell(row) },
  { title: '操作', key: 'actions', width: 250, render: row => renderActions(row) }
])

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.accounts-page {
  display: grid;
  gap: var(--spacing-5);
}

.accounts-hero,
.filters-shell,
.workspace-shell {
  position: relative;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}

.accounts-hero {
  padding: var(--spacing-6);
}

.accounts-hero::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 132px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.14) 0%, rgba(52, 211, 153, 0.08) 100%);
}

.hero-copy,
.hero-actions,
.hero-band,
.filters-head,
.filter-grid,
.scope-line,
.workspace-head,
.table-wrap,
.empty-state {
  position: relative;
  z-index: 1;
}

.hero-copy {
  max-width: 720px;
}

.hero-kicker,
.section-kicker {
  display: inline-flex;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--primary-color);
}

.hero-copy h1 {
  margin: 10px 0 8px;
  font-size: clamp(28px, 3.6vw, 40px);
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--text-primary);
}

.hero-copy p,
.filters-head p,
.workspace-copy p,
.empty-state p {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.8;
  color: var(--text-secondary);
}

.hero-actions,
.workspace-summary,
.table-actions,
.expand-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.hero-actions {
  margin-top: var(--spacing-5);
}

.hero-band {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--spacing-3);
  margin-top: var(--spacing-5);
}

.band-metric,
.summary-chip,
.scope-chip,
.status-pill,
.expand-card,
.narrative-block {
  border: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.band-metric {
  padding: var(--spacing-4);
  border-radius: var(--radius-xl);
}

.band-label,
.filter-field label,
.expand-label,
.narrative-kicker {
  display: block;
  margin-bottom: 8px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.band-metric strong {
  display: block;
  font-size: clamp(20px, 2.4vw, 28px);
  line-height: 1.1;
  color: var(--text-primary);
}

.band-metric small,
.identity-meta,
.scope-caption,
.quota-secondary,
.sign-caption,
.health-caption,
.expand-note {
  display: block;
  margin-top: 6px;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-secondary);
}

.filters-shell,
.workspace-shell {
  padding: var(--spacing-5);
}

.filters-head,
.workspace-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-4);
  align-items: end;
}

.filters-head h2,
.workspace-copy h2 {
  margin: 8px 0 6px;
  font-size: clamp(24px, 2.8vw, 30px);
  line-height: 1.05;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

.section-kicker.soft {
  color: var(--text-tertiary);
}

.status-rail {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--spacing-2);
}

.status-pill {
  min-width: 96px;
  padding: 12px 14px;
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  display: grid;
  gap: 4px;
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.status-pill:hover,
.summary-chip:hover,
.scope-chip:hover,
.expand-card:hover {
  box-shadow: var(--shadow-sm);
}

.status-pill strong {
  font-size: 20px;
  line-height: 1;
  color: var(--text-primary);
}

.status-pill.active {
  border-color: rgba(16, 185, 129, 0.25);
  box-shadow: var(--shadow-md);
}

.status-pill.healthy.active {
  background: var(--success-color-light);
}

.status-pill.unhealthy.active {
  background: var(--error-color-light);
}

.status-pill.pending.active {
  background: var(--warning-color-light);
}

.status-pill.disabled.active {
  background: rgba(148, 163, 184, 0.14);
}

.pill-label {
  font-size: var(--text-sm);
}

.filter-grid {
  display: grid;
  grid-template-columns: 1.4fr 0.7fr 0.7fr;
  gap: var(--spacing-3);
  margin-top: var(--spacing-5);
}

.scope-line {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-top: var(--spacing-4);
}

.scope-chip,
.summary-chip {
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.scope-chip strong,
.summary-chip strong {
  color: var(--text-primary);
}

.summary-chip {
  min-height: auto;
  padding: 12px 14px;
  border-radius: var(--radius-lg);
  display: block;
}

.summary-chip span {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.summary-chip strong {
  display: block;
  margin-top: 4px;
  font-size: 20px;
  line-height: 1;
}

.table-wrap {
  margin-top: var(--spacing-5);
  padding: 8px;
  border-radius: var(--radius-xl);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
}

.accounts-table :deep(.n-data-table-wrapper) {
  border-radius: var(--radius-lg);
}

.accounts-table :deep(.n-data-table-th) {
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
}

.accounts-table :deep(.n-data-table-tr:hover .n-data-table-td) {
  background: var(--bg-card-hover);
}

.identity-cell,
.scope-cell,
.quota-cell,
.sign-cell,
.health-cell {
  display: grid;
  gap: 6px;
}

.identity-cell {
  grid-template-columns: 44px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.account-mark {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: var(--primary-gradient);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: var(--font-bold);
  box-shadow: var(--shadow-sm);
}

.account-mark.inactive {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

.identity-copy,
.scope-cell {
  min-width: 0;
}

.identity-line {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.identity-name,
.scope-title,
.quota-primary,
.expand-value {
  color: var(--text-primary);
  font-size: var(--text-md);
  line-height: 1.4;
  word-break: break-word;
}

.identity-display {
  display: inline-flex;
  align-items: center;
  min-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: var(--primary-color-light);
  color: var(--primary-color);
  font-size: var(--text-xs);
}

.identity-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.group-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  min-height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: var(--text-xs);
  color: var(--group-color);
  background: color-mix(in srgb, var(--group-color) 14%, var(--bg-card));
}

.simple-cell {
  display: flex;
  align-items: center;
  min-height: 32px;
}

.simple-name {
  color: var(--text-primary);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  line-height: 1.4;
}

.simple-text {
  color: var(--text-primary);
  font-size: var(--text-sm);
  line-height: 1.5;
}

.simple-text.muted {
  color: var(--text-tertiary);
}

.quota-primary {
  font-size: 18px;
}

.quota-rail {
  position: relative;
  width: 100%;
  height: 8px;
  overflow: hidden;
  border-radius: 999px;
  background: var(--border-color-light);
}

.quota-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
  background: var(--primary-gradient);
}

.sign-badge,
.health-badge {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  min-height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.sign-badge.healthy,
.health-badge.healthy {
  background: var(--success-color-light);
  color: var(--success-color);
}

.sign-badge.unhealthy,
.health-badge.unhealthy {
  background: var(--error-color-light);
  color: var(--error-color);
}

.sign-badge.pending,
.health-badge.pending {
  background: var(--warning-color-light);
  color: var(--warning-color);
}

.health-badge.disabled {
  background: rgba(148, 163, 184, 0.14);
  color: #64748b;
}

.account-expand {
  padding: 12px 6px 6px;
}

.expand-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.expand-card,
.narrative-block {
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
}

.narrative-block {
  border-style: dashed;
}

.expand-narrative {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
  margin-top: var(--spacing-3);
}

.narrative-block p {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 1.7;
}

.accounts-table :deep(.account-expand) {
  padding: 12px 6px 6px;
}

.accounts-table :deep(.expand-grid) {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.accounts-table :deep(.expand-card),
.accounts-table :deep(.narrative-block) {
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.accounts-table :deep(.narrative-block) {
  border-style: dashed;
}

.accounts-table :deep(.expand-label),
.accounts-table :deep(.narrative-kicker) {
  display: block;
  margin-bottom: 8px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.accounts-table :deep(.expand-value) {
  color: var(--text-primary);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  line-height: 1.4;
  word-break: break-word;
}

.accounts-table :deep(.expand-note) {
  display: block;
  margin-top: 6px;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-secondary);
}

.accounts-table :deep(.expand-narrative) {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
  margin-top: var(--spacing-3);
}

.accounts-table :deep(.narrative-block p) {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 1.7;
}

.accounts-table :deep(.expand-actions) {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-top: var(--spacing-3);
}

.empty-state {
  display: grid;
  justify-items: center;
  gap: var(--spacing-3);
  padding: 56px 24px;
  text-align: center;
}

.empty-state-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 22px;
  background: var(--primary-gradient);
  color: #fff;
  font-size: 28px;
  font-weight: var(--font-bold);
  box-shadow: var(--shadow-md);
}

.empty-state h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--text-xl);
}

.toolbar-card {
  position: relative;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-5);
}

.toolbar-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 72px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(52, 211, 153, 0.06) 100%);
}

.toolbar-top,
.toolbar-filters,
.toolbar-bottom {
  position: relative;
  z-index: 1;
}

.toolbar-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-4);
  align-items: center;
}

.toolbar-copy h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: clamp(24px, 2.8vw, 30px);
  line-height: 1.05;
  letter-spacing: -0.03em;
}

.toolbar-copy p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.toolbar-filters {
  display: grid;
  grid-template-columns: 1.4fr 0.7fr 0.7fr;
  gap: var(--spacing-3);
  margin-top: var(--spacing-4);
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.toolbar-bottom {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--spacing-3);
  align-items: start;
  margin-top: var(--spacing-4);
}

.toolbar-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.metric-chip {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  white-space: nowrap;
}

.status-rail.compact {
  justify-content: flex-end;
}

.status-rail.compact .status-pill {
  min-width: 78px;
  padding: 10px 12px;
}

.workspace-head.compact {
  align-items: center;
}

.workspace-head.compact .workspace-copy h2 {
  margin: 0;
}

.rise-1,
.rise-2,
.rise-3 {
  animation: rise-in 0.55s ease both;
}

.rise-2 {
  animation-delay: 0.06s;
}

.rise-3 {
  animation-delay: 0.12s;
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1200px) {
  .hero-band,
  .expand-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .expand-narrative {
    grid-template-columns: 1fr;
  }

  .accounts-table :deep(.expand-grid) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .accounts-table :deep(.expand-narrative) {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 980px) {
  .toolbar-top,
  .toolbar-bottom,
  .filters-head,
  .workspace-head,
  .filter-grid,
  .toolbar-filters {
    grid-template-columns: 1fr;
  }

  .status-rail.compact,
  .status-rail {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .hero-band {
    grid-template-columns: 1fr;
  }

  .workspace-summary {
    width: 100%;
  }

  .summary-chip {
    flex: 1 1 0;
  }
}

@media (max-width: 640px) {
  .toolbar-actions,
  .expand-actions,
  .table-actions {
    width: 100%;
  }

  .toolbar-actions :deep(.n-button),
  .expand-actions :deep(.n-button),
  .table-actions :deep(.n-button) {
    flex: 1 1 calc(50% - 8px);
    min-width: 0;
  }

  .status-pill,
  .scope-chip,
  .summary-chip {
    width: 100%;
  }

  .expand-grid {
    grid-template-columns: 1fr;
  }

  .identity-cell {
    grid-template-columns: 1fr;
    justify-items: start;
  }

  .accounts-table :deep(.expand-grid) {
    grid-template-columns: 1fr;
  }
}
</style>
