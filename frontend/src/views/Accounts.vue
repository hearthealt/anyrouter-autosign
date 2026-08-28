<template>
  <div class="accounts-page">
    <section class="page-toolbar accounts-toolbar" aria-label="账号操作">
      <div class="page-toolbar__summary">
        <span class="page-toolbar__label"><Activity :size="15" /> 账号池</span>
        <div class="filter-meta page-toolbar__meta">
          <span>健康度 <strong>{{ healthRatio }}%</strong></span>
          <span class="success">正常 <strong>{{ normalCount }}</strong></span>
          <span class="error">异常 <strong>{{ unhealthyCount }}</strong></span>
          <span>禁用 <strong>{{ disabledCount }}</strong></span>
        </div>
      </div>
      <div class="page-toolbar__actions">
        <UiButton size="small" :loading="loading" @click="handleRefresh">
          <template #icon><RefreshCw :size="14" /></template>
          刷新节点
        </UiButton>
        <UiButton size="small" :loading="batchChecking" @click="handleBatchHealthCheck">
          <template #icon><Activity :size="14" /></template>
          批量检查
        </UiButton>
        <UiButton size="small" :loading="batchSigning" @click="handleBatchSign">
          <template #icon><Zap :size="14" /></template>
          一键签到
        </UiButton>
        <UiButton size="small" @click="showBatchImportModal = true">
          <template #icon><Plus :size="14" /></template>
          批量导入
        </UiButton>
        <UiButton size="small" type="primary" @click="showAddModal">
          <template #icon><Plus :size="14" /></template>
          添加账号
        </UiButton>
      </div>
    </section>

    <section class="accounts-console control-strip">
      <div class="console-topline">
        <div>
          <span class="console-code mono">FILTER MATRIX / 02—A</span>
          <strong>节点筛选与状态切片</strong>
        </div>
        <span class="console-live"><span></span> {{ pagination.itemCount }} NODES INDEXED</span>
      </div>
      <div class="filter-strip accounts-filter">
        <UiInput
          v-model:value="searchKeyword"
          size="small"
          clearable
          placeholder="搜索用户名、平台或 User ID"
          class="filter-search search-input"
        >
          <template #prefix><Search :size="14" /></template>
        </UiInput>

        <UiSelect
          v-model:value="selectedPlatformId"
          :options="platformOptions"
          size="small"
          clearable
          placeholder="全部平台"
          class="filter-field filter-item"
        />

        <UiSelect
          v-model:value="selectedGroupId"
          :options="groupOptions"
          size="small"
          clearable
          placeholder="全部分组"
          class="filter-field filter-item"
        />

        <UiButton v-if="hasActiveFilters" size="small" quaternary @click="resetFilters">重置</UiButton>
      </div>

      <div class="status-tabs" role="group" aria-label="账号状态筛选">
        <button
          v-for="pill in quickStatusPills"
          :key="pill.key"
          class="status-tab"
          :class="{ active: (pill.value === null && selectedStatus === null) || selectedStatus === pill.value }"
          :aria-pressed="(pill.value === null && selectedStatus === null) || selectedStatus === pill.value"
          @click="setStatusFilter(pill.value)"
        >
          <span v-if="pill.value" class="status-dot" :class="pill.tone" aria-hidden="true"></span>
          {{ pill.label }} <b>{{ pill.count }}</b>
        </button>
      </div>
    </section>
    <div v-if="selectedAccounts.length > 0" class="bulk-bar">
      <div class="bulk-bar-info">
        已选择 <strong>{{ selectedAccounts.length }}</strong> 个账号
      </div>
      <div class="bulk-bar-actions">
        <UiButton size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'sign'" @click="handleSelectedSign">
          批量签到
        </UiButton>
        <UiButton size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'health'" @click="handleSelectedHealthCheck">
          健康检查
        </UiButton>
        <UiButton size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'enable'" @click="handleBulkToggleActive(true)">
          启用
        </UiButton>
        <UiButton size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'disable'" @click="handleBulkToggleActive(false)">
          禁用
        </UiButton>
        <UiSelect
          v-model:value="bulkTargetPlatformId"
          :options="platformOptions"
          size="small"
          placeholder="迁移平台"
          class="bulk-select"
          :disabled="bulkDisabled"
        />
        <UiButton size="small" :disabled="bulkDisabled || !bulkTargetPlatformId" :loading="bulkLoading === 'platform'" @click="handleBulkMovePlatform">
          应用平台
        </UiButton>
        <UiSelect
          v-model:value="bulkTargetGroupId"
          :options="groupOptions"
          size="small"
          clearable
          placeholder="加入分组"
          class="bulk-select"
          :disabled="bulkDisabled"
        />
        <UiButton size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'group'" @click="handleBulkAssignGroup">
          应用分组
        </UiButton>
        <UiConfirm
          positive-text="删除"
          negative-text="取消"
          @positive-click="handleBulkDelete"
        >
          <template #trigger>
            <UiButton size="small" type="error" ghost :disabled="bulkDisabled" :loading="bulkLoading === 'delete'">
              批量删除
            </UiButton>
          </template>
          确定删除选中的 {{ selectedAccounts.length }} 个账号？
        </UiConfirm>
        <UiButton size="small" quaternary :disabled="bulkDisabled" @click="clearSelection">
          清空选择
        </UiButton>
      </div>
    </div>

    <div class="accounts-card">
      <div v-if="initialLoading" class="loading-state" aria-busy="true" aria-label="正在加载账号">
        <UiLoading size="small" />
        <div class="loading-text">正在加载账号...</div>
      </div>

      <div v-else-if="loading || accounts.length > 0" class="table-wrap">
        <DataGrid
          :columns="columns"
          :data="accounts"
          :row-key="getAccountRowKey"
          :checked-row-keys="checkedRowKeys"
          :loading="loading"
          :pagination="false"
          :single-line="false"
          :remote="true"
          size="small"
          :scroll-x="1200"
          :row-class-name="getRowClassName"
          @update:checked-row-keys="handleCheckedRowKeysChange"
          @update:sorter="handleSorterChange"
        />
      </div>

      <div v-else-if="!loading" class="empty-state">
        <Users :size="32" />
        <div class="empty-title">{{ hasActiveFilters ? '没有匹配的账号' : '还没有账号' }}</div>
        <div class="empty-desc">
          {{ hasActiveFilters ? '当前筛选条件下没有结果，试试清空筛选或更换关键词。' : '先去平台页确认配置，再添加账号或批量导入，避免后续校验失败。' }}
        </div>
        <div class="empty-actions">
          <UiButton v-if="!hasActiveFilters" size="small" @click="router.push('/platforms')">
            去平台页检查配置
          </UiButton>
          <UiButton size="small" @click="showBatchImportModal = true">
            <template #icon><Plus :size="14" /></template>
            批量导入
          </UiButton>
          <UiButton size="small" type="primary" @click="showAddModal">
            <template #icon><Plus :size="14" /></template>
            添加账号
          </UiButton>
        </div>
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

    <AccountModal
      ref="accountModalRef"
      v-model:show="showAccountModal"
      :account="editingAccount"
      :groups="groups"
      @submit="handleAccountSubmit"
    />

    <BatchImportModal
      v-model:show="showBatchImportModal"
      :platforms="platforms"
      :groups="groups"
      @imported="handleBatchImported"
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
import { computed, h, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { DataGrid, UiButton, UiConfirm, UiInput, UiLoading, UiPagination, UiSelect, UiSwitch, UiTooltip, type GridColumns, type GridSortState, type SortOrder } from '../ui'
import { Activity, AlertCircle, FileText, Plus, RefreshCw, Search, Users, Zap } from 'lucide-vue-next'
import { AccountModal, BatchImportModal, ExternalLink, TokensModal } from '../components'
import { accountApi, groupsApi, notifyApi, platformApi, settingsApi, signApi } from '../api'
import { useEventStream, useFormat, useViewRefresh } from '../composables'
import type { Account, AccountAuthType, AccountGroup, AccountProxyMode, ApiToken, CreateTokenParams, Platform, SelectOption } from '../types'
import { getAccountStatus } from '../utils'

type StatusFilter = 'normal' | 'unhealthy' | 'disabled'
type SortKey = 'username' | 'platform' | 'group' | 'quota' | 'last_sign' | 'health'

const router = useRouter()
const { formatQuota, formatRelativeTime } = useFormat()

const accounts = ref<Account[]>([])
const groups = ref<AccountGroup[]>([])
const platforms = ref<Platform[]>([])
const initialLoading = ref(true)
const loading = ref(true)
const batchSigning = ref(false)
const batchChecking = ref(false)
const signingId = ref<number | null>(null)
const checkingId = ref<number | null>(null)
const togglingActiveId = ref<number | null>(null)
const searchKeyword = ref('')
const selectedPlatformId = ref<number | null>(null)
const selectedGroupId = ref<number | null>(null)
const selectedStatus = ref<StatusFilter | null>(null)
const checkedRowKeys = ref<number[]>([])
const bulkLoading = ref<'sign' | 'health' | 'enable' | 'disable' | 'platform' | 'group' | 'delete' | null>(null)
const bulkTargetPlatformId = ref<number | null>(null)
const bulkTargetGroupId = ref<number | null>(null)
const showAccountModal = ref(false)
const showBatchImportModal = ref(false)
const editingAccount = ref<Account | null>(null)
const accountModalRef = ref<InstanceType<typeof AccountModal> | null>(null)
const showTokensVisible = ref(false)
const tokenAccount = ref<Account | null>(null)
const tokens = ref<ApiToken[]>([])
const loadingTokens = ref(false)
const syncingTokens = ref(false)
const deletingTokenId = ref<number | null>(null)
const quotaWarningThreshold = ref(5)
const listSummary = ref({
  total: 0,
  active_count: 0,
  normal_count: 0,
  healthy_count: 0,
  unhealthy_count: 0,
  disabled_count: 0,
  pending_count: 0
})
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  pageSizes: [10, 20, 50, 100]
})
const sortState = ref<{ columnKey: SortKey | null; order: SortOrder }>({
  columnKey: null,
  order: false
})
let eventRefreshTimer: number | null = null
let searchDebounceTimer: number | null = null

const activeCount = computed(() => listSummary.value.active_count)
const normalCount = computed(() => listSummary.value.normal_count || listSummary.value.healthy_count)
const unhealthyCount = computed(() => listSummary.value.unhealthy_count)
const disabledCount = computed(() => listSummary.value.disabled_count)
const healthRatio = computed(() => (activeCount.value > 0 ? Math.round((normalCount.value / activeCount.value) * 100) : 0))

const platformOptions = computed<SelectOption<number>[]>(() =>
  platforms.value.map(platform => ({ label: platform.name, value: platform.id }))
)
const groupOptions = computed<SelectOption<number>[]>(() =>
  groups.value.map(group => ({ label: group.name, value: group.id }))
)
const selectedAccounts = computed(() =>
  accounts.value.filter(account => checkedRowKeys.value.includes(account.id))
)
const bulkDisabled = computed(() => !!bulkLoading.value)
const quotaWarningValue = computed(() => quotaWarningThreshold.value * 500000)
const hasActiveFilters = computed(() =>
  !!searchKeyword.value.trim() ||
  selectedPlatformId.value != null ||
  selectedGroupId.value != null ||
  selectedStatus.value != null
)

const quickStatusPills = computed(() => [
  { key: 'all', label: '全部', count: listSummary.value.total, value: null as StatusFilter | null, tone: 'default' },
  { key: 'normal', label: '正常', count: normalCount.value, value: 'normal' as StatusFilter, tone: 'success' },
  { key: 'unhealthy', label: '异常', count: unhealthyCount.value, value: 'unhealthy' as StatusFilter, tone: 'error' },
  { key: 'disabled', label: '禁用', count: disabledCount.value, value: 'disabled' as StatusFilter, tone: 'default' }
])

const getAccountRowKey = (account: Account) => account.id

const setStatusFilter = (status: StatusFilter | null) => {
  if (status === null) {
    selectedStatus.value = null
    return
  }
  selectedStatus.value = selectedStatus.value === status ? null : status
}

const resetFilters = () => {
  searchKeyword.value = ''
  selectedPlatformId.value = null
  selectedGroupId.value = null
  selectedStatus.value = null
}

const isNewApiAccount = (account: Account) => account.platform?.adapter_type !== 'http'
const getUserId = (account: Account) => account.external_user_id
  ?? (account.anyrouter_user_id != null ? String(account.anyrouter_user_id) : '-')
const getPlatformName = (account: Account) => account.platform?.name || '—'
const getPlatformUrl = (account: Account) => account.platform?.base_url || ''
const getGroupInfo = (account: Account) => account.group || groups.value.find(group => group.id === account.group_id)

const getHealthTone = (account: Account) => {
  const status = getAccountStatus(account)
  if (status === 'disabled') return 'default'
  if (status === 'unhealthy') return 'error'
  return 'success'
}

const getHealthLabel = (account: Account) => {
  const status = getAccountStatus(account)
  if (status === 'disabled') return '已禁用'
  if (status === 'unhealthy') return '异常'
  return '正常'
}

const getQuotaRatio = (account: Account) => {
  const ratio = Number.parseFloat(String(account.quota_percent || '0').replace('%', ''))
  if (Number.isNaN(ratio)) return 0
  return Math.max(0, Math.min(100, ratio))
}

const isLowQuota = (account: Account) => account.is_active
  && isNewApiAccount(account)
  && (account.cached_quota || 0) < quotaWarningValue.value

const getRowClassName = (account: Account) => {
  if (getAccountStatus(account) === 'unhealthy') return 'account-row-alert'
  if (isLowQuota(account)) return 'account-row-warning'
  return ''
}

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
    window.$notify('该账号已禁用，无法签到', 'warning', { route: `/account/${account.id}` })
    return
  }

  signingId.value = account.id
  try {
    const res: any = await signApi.sign(account.id)
    window.$notify(res.data?.message || '签到成功', 'success', { route: `/account/${account.id}` })
    await loadData()
  } catch (e: any) {
    window.$notify(e.message || '签到失败', 'error', { route: `/account/${account.id}` })
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
    window.$notify('健康检查完成', 'success', { route: `/account/${account.id}` })
    await loadData()
  } catch (e: any) {
    window.$notify(e.message || '健康检查失败', 'error', { route: `/account/${account.id}` })
  } finally {
    checkingId.value = null
  }
}

const handleToggleAccountActive = async (account: Account, active: boolean) => {
  if (togglingActiveId.value !== null || account.is_active === active) return

  const previousActive = account.is_active
  togglingActiveId.value = account.id
  account.is_active = active

  try {
    await accountApi.update(account.id, { is_active: active })
    window.$notify(`${active ? '启用' : '禁用'}成功`, 'success', { route: `/account/${account.id}` })
    await loadData(pagination.value.page)
  } catch (e: any) {
    account.is_active = previousActive
    window.$notify(e.message || `${active ? '启用' : '禁用'}失败`, 'error', { route: `/account/${account.id}` })
  } finally {
    togglingActiveId.value = null
  }
}

const handleBatchHealthCheck = async () => {
  batchChecking.value = true
  try {
    const res: any = await accountApi.healthCheckAll()
    const healthy = res.data?.healthy_count ?? 0
    const unhealthy = res.data?.unhealthy_count ?? 0
    const unknown = res.data?.unknown_count ?? 0
    window.$notify(`批量检查完成，正常 ${healthy}，异常 ${unhealthy}${unknown > 0 ? `，未检查 ${unknown}` : ''}`, unknown > 0 ? 'warning' : 'success')
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
        // 令牌凭证：切到 PAT / refresh 时下发 auth_type + auth_data；
        // 切回账号密码时下发 clear_auth_data 把旧令牌清掉
        const usesToken = data.auth_type === 'bearer' || data.auth_type === 'new_api_refresh'
        if (data.clear_auth_data) {
          updateData.clear_auth_data = true
        } else if (usesToken) {
          updateData.auth_type = data.auth_type
          if (data.auth_data) updateData.auth_data = data.auth_data
        }
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
      window.$notify('账号更新成功', 'success')
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
        // New API 平台也支持令牌凭证（PAT / refresh token），auth_type 为
        // none/cookie 时后端回落到旧的 session cookie 方案
        if (data.auth_type && data.auth_type !== 'none') {
          payload.auth_type = data.auth_type
          payload.auth_data = data.auth_data
        }
      }

      const res: any = await accountApi.create(payload)
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
    window.$notify(e.message || '保存失败', 'error')
  } finally {
    accountModalRef.value?.setSubmitting(false)
  }
}
const handleBatchImported = async () => {
  await loadData(1)
}

const clearSelection = () => {
  checkedRowKeys.value = []
}

const handleCheckedRowKeysChange = (keys: Array<string | number>) => {
  checkedRowKeys.value = keys.map(key => Number(key)).filter(key => !Number.isNaN(key))
}

const BULK_CONCURRENCY = 8

const runBulkActions = async (
  items: Account[],
  action: (account: Account) => Promise<unknown>
): Promise<PromiseSettledResult<unknown>[]> => {
  const results: PromiseSettledResult<unknown>[] = new Array(items.length)
  let nextIndex = 0

  const worker = async () => {
    while (nextIndex < items.length) {
      const currentIndex = nextIndex++
      try {
        results[currentIndex] = {
          status: 'fulfilled',
          value: await action(items[currentIndex])
        }
      } catch (reason) {
        results[currentIndex] = {
          status: 'rejected',
          reason
        }
      }
    }
  }

  const workerCount = Math.min(BULK_CONCURRENCY, items.length)
  await Promise.all(Array.from({ length: workerCount }, () => worker()))
  return results
}

const runBulkOperation = async (
  loadingKey: NonNullable<typeof bulkLoading.value>,
  items: Account[],
  action: (account: Account) => Promise<unknown>,
  successMessage: (successCount: number, failCount: number, skippedCount: number) => string,
  skippedPredicate?: (account: Account) => boolean
) => {
  if (items.length === 0) {
    window.$notify('请先选择账号', 'warning')
    return
  }

  bulkLoading.value = loadingKey
  try {
    const executable = skippedPredicate ? items.filter(account => !skippedPredicate(account)) : items
    const skippedCount = items.length - executable.length

    const results = await runBulkActions(executable, action)
    const successCount = results.filter(result => result.status === 'fulfilled').length
    const failCount = results.length - successCount

    window.$notify(
      successMessage(successCount, failCount, skippedCount),
      failCount > 0 ? 'warning' : 'success'
    )
    await loadData()
    if (loadingKey === 'delete') {
      clearSelection()
    }
  } catch (e: any) {
    window.$notify(e.message || '批量操作失败', 'error')
  } finally {
    bulkLoading.value = null
  }
}

const handleSelectedSign = async () => {
  await runBulkOperation(
    'sign',
    selectedAccounts.value,
    account => signApi.sign(account.id),
    (successCount, failCount, skippedCount) =>
      `批量签到完成，成功 ${successCount}，失败 ${failCount}${skippedCount > 0 ? `，跳过 ${skippedCount}` : ''}`,
    account => !account.is_active
  )
}

const handleSelectedHealthCheck = async () => {
  await runBulkOperation(
    'health',
    selectedAccounts.value,
    account => accountApi.healthCheck(account.id),
    (successCount, failCount) => `健康检查完成，成功 ${successCount}，失败 ${failCount}`
  )
}

const handleBulkToggleActive = async (active: boolean) => {
  await runBulkOperation(
    active ? 'enable' : 'disable',
    selectedAccounts.value,
    account => accountApi.update(account.id, { is_active: active }),
    (successCount, failCount) => `${active ? '启用' : '禁用'}完成，成功 ${successCount}，失败 ${failCount}`
  )
}

const handleBulkMovePlatform = async () => {
  if (!bulkTargetPlatformId.value) {
    window.$notify('请先选择目标平台', 'warning')
    return
  }

  await runBulkOperation(
    'platform',
    selectedAccounts.value,
    account => accountApi.update(account.id, { platform_id: bulkTargetPlatformId.value }),
    (successCount, failCount) => `平台迁移完成，成功 ${successCount}，失败 ${failCount}`
  )
}

const handleBulkAssignGroup = async () => {
  await runBulkOperation(
    'group',
    selectedAccounts.value,
    account => accountApi.update(account.id, { group_id: bulkTargetGroupId.value || 0 }),
    (successCount, failCount) => `分组更新完成，成功 ${successCount}，失败 ${failCount}`
  )
}

const handleBulkDelete = async () => {
  await runBulkOperation(
    'delete',
    selectedAccounts.value,
    account => accountApi.delete(account.id),
    (successCount, failCount) => `批量删除完成，成功 ${successCount}，失败 ${failCount}`
  )
}

const loadMeta = async () => {
  const [groupsRes, platformsRes, settingsRes] = await Promise.allSettled([
    groupsApi.getList(),
    platformApi.getList(),
    settingsApi.get()
  ])

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

  if (settingsRes.status === 'fulfilled') {
    quotaWarningThreshold.value = settingsRes.value.data?.quota_warning_threshold ?? 5
  } else {
    console.error('Failed to load settings:', settingsRes.reason)
  }
}

const loadData = async (page = pagination.value.page) => {
  loading.value = true
  try {
    const params: {
      page: number
      size: number
      keyword?: string
      platform_id?: number
      group_id?: number
      status?: StatusFilter
      sort_by?: SortKey
      sort_order?: 'asc' | 'desc'
    } = {
      page,
      size: pagination.value.pageSize
    }

    const keyword = searchKeyword.value.trim()
    if (keyword) {
      params.keyword = keyword
    }
    if (selectedPlatformId.value != null) {
      params.platform_id = selectedPlatformId.value
    }
    if (selectedGroupId.value != null) {
      params.group_id = selectedGroupId.value
    }
    if (selectedStatus.value) {
      params.status = selectedStatus.value
    }
    if (sortState.value.columnKey && sortState.value.order) {
      params.sort_by = sortState.value.columnKey
      params.sort_order = sortState.value.order === 'ascend' ? 'asc' : 'desc'
    }

    const res: any = await accountApi.getList(params)
    const responseData = res.data || {}
    const total = responseData.total || 0
    const totalPages = total > 0 ? Math.ceil(total / pagination.value.pageSize) : 0

    if (totalPages > 0 && page > totalPages) {
      await loadData(totalPages)
      return
    }

    accounts.value = responseData.items || []
    pagination.value.page = page
    pagination.value.itemCount = total
    listSummary.value = responseData.summary || {
      total: total,
      active_count: 0,
      normal_count: 0,
      healthy_count: 0,
      unhealthy_count: 0,
      disabled_count: 0,
      pending_count: 0
    }
  } catch (e: any) {
    window.$notify(e.message || '加载账号数据失败', 'error')
  } finally {
    loading.value = false
  }
}

const handleRefresh = async () => {
  await loadMeta()
  await loadData(pagination.value.page)
}

const handlePageChange = (page: number) => {
  void loadData(page)
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  void loadData(1)
}

const getSortOrder = (columnKey: SortKey): SortOrder =>
  sortState.value.columnKey === columnKey ? sortState.value.order : false

const handleSorterChange = (sorter: GridSortState | GridSortState[] | null) => {
  const nextSorter = Array.isArray(sorter) ? (sorter[0] ?? null) : sorter

  if (!nextSorter?.columnKey || !nextSorter.order) {
    sortState.value = { columnKey: null, order: false }
    void loadData(1)
    return
  }

  sortState.value = {
    columnKey: String(nextSorter.columnKey) as SortKey,
    order: nextSorter.order
  }
  void loadData(1)
}

const columns = computed<GridColumns<Account>>(() => [
  {
    type: 'selection',
    width: 44,
  },
  {
    title: '账号',
    key: 'username',
    width: 200,
    ellipsis: { tooltip: true },
    sorter: 'default',
    sortOrder: getSortOrder('username'),
    render: account =>
      h('div', { class: 'account-cell' }, [
        h('div', { class: 'account-avatar-mini', onClick: () => openAccountDetail(account) }, (account.username || 'U')[0].toUpperCase()),
        h('div', { class: 'account-info' }, [
          h('div', { class: 'account-name-row' }, [
            h('div', { class: 'account-name', onClick: () => openAccountDetail(account) }, account.username || '-'),
            account.note
              ? h(
                  UiTooltip,
                  null,
                  {
                    trigger: () =>
                      h('span', { class: 'note-badge' }, [
                        h(FileText, { size: 12 })
                      ]),
                    default: () => account.note
                  }
                )
              : null
          ]),
          h('div', { class: 'account-sub' }, `ID ${getUserId(account)}`)
        ])
      ])
  },
  {
    title: '平台',
    key: 'platform',
    width: 210,
    ellipsis: { tooltip: true },
    sorter: 'default',
    sortOrder: getSortOrder('platform'),
    render: account => h(ExternalLink, {
      href: getPlatformUrl(account),
      label: getPlatformUrl(account) || getPlatformName(account),
      mono: true
    })
  },
  {
    title: '分组',
    key: 'group',
    width: 100,
    ellipsis: { tooltip: true },
    sorter: 'default',
    sortOrder: getSortOrder('group'),
    render: account => {
      const group = getGroupInfo(account)
      return group
        ? h('span', { class: 'group-tag' }, group.name)
        : h('span', { class: 'muted' }, '—')
    }
  },
  {
    title: '额度',
    key: 'quota',
    width: 180,
    sorter: 'default',
    sortOrder: getSortOrder('quota'),
    render: account => {
      if (!isNewApiAccount(account)) return h('span', { class: 'muted' }, '不适用')
      return h('div', { class: 'quota-cell' }, [
        h('div', { class: 'quota-main' }, [
          isLowQuota(account)
            ? h(
                UiTooltip,
                null,
                {
                  trigger: () =>
                    h('span', { class: 'quota-alert-icon' }, [
                      h(AlertCircle, { size: 12 })
                    ]),
                  default: () => `低于告警阈值 $${quotaWarningThreshold.value.toFixed(2)}`
                }
              )
            : null,
          h('span', { class: ['quota-value', isLowQuota(account) ? 'danger' : ''] }, formatQuota(account.cached_quota || 0)),
          h('span', { class: 'quota-sub' }, `/${formatQuota((account.cached_quota || 0) + (account.cached_used_quota || 0))}`)
        ]),
        h('div', { class: 'quota-bar' }, [
          h('div', { class: ['quota-bar-fill', isLowQuota(account) ? 'danger' : ''], style: { width: `${getQuotaRatio(account)}%` } })
        ])
      ])
    }
  },
  {
    title: '最近签到',
    key: 'last_sign',
    width: 140,
    sorter: 'default',
    sortOrder: getSortOrder('last_sign'),
    render: account => {
      if (!account.last_sign) return h('span', { class: 'muted' }, '未签到')
      const tone = account.last_sign.success ? 'success' : 'error'
      return h('div', { class: 'sign-cell' }, [
        h('span', { class: `tag-dot ${tone}` }),
        h('span', {}, formatRelativeTime(account.last_sign.time))
      ])
    }
  },
  {
    title: '状态',
    key: 'health',
    width: 150,
    sorter: 'default',
    sortOrder: getSortOrder('health'),
    render: account =>
      h('div', { class: 'status-cell' }, [
        h('span', { class: `tag ${getHealthTone(account)}` }, getHealthLabel(account)),
        h(UiSwitch, {
          size: 'small',
          value: account.is_active,
          disabled: togglingActiveId.value !== null && togglingActiveId.value !== account.id,
          loading: togglingActiveId.value === account.id,
          onClick: (event: MouseEvent) => event.stopPropagation(),
          'onUpdate:value': (value: boolean) => handleToggleAccountActive(account, value)
        })
      ])
  },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    render: account =>
      h('div', { class: 'actions' }, [
        h(UiButton, { size: 'tiny', quaternary: true, onClick: () => openAccountDetail(account) }, { default: () => '详情' }),
        h(UiButton, { size: 'tiny', quaternary: true, onClick: () => showEditModal(account) }, { default: () => '编辑' }),
        isNewApiAccount(account)
          ? h(UiButton, { size: 'tiny', quaternary: true, onClick: () => showTokens(account) }, { default: () => 'Token' })
          : null,
        h(
          UiButton,
          {
            size: 'tiny',
            quaternary: true,
            class: 'action-button',
            disabled: !account.is_active,
            loading: signingId.value === account.id,
            onClick: () => handleSign(account)
          },
          { default: () => (signingId.value === account.id ? '' : '签到') }
        ),
        h(
          UiButton,
          {
            size: 'tiny',
            quaternary: true,
            class: 'action-button',
            loading: checkingId.value === account.id,
            onClick: () => handleHealthCheck(account)
          },
          { default: () => (checkingId.value === account.id ? '' : '检查') }
        ),
        h(
          UiConfirm,
          {
            onPositiveClick: () => handleDeleteAccount(account),
            positiveText: '删除',
            negativeText: '取消',
          },
          {
            trigger: () => h(UiButton, { size: 'tiny', quaternary: true, type: 'error' }, { default: () => '删除' }),
            default: () => `确定删除账号 "${account.username || '-'}" ？`
          }
        )
      ])
  }
])

onMounted(async () => {
  try {
    await Promise.all([loadMeta(), loadData(1)])
  } finally {
    initialLoading.value = false
  }
})

watch(accounts, (list) => {
  const validKeys = new Set(list.map(account => account.id))
  checkedRowKeys.value = checkedRowKeys.value.filter(key => validKeys.has(key))
}, { deep: true })

watch([selectedPlatformId, selectedGroupId, selectedStatus], () => {
  void loadData(1)
})

watch(searchKeyword, () => {
  if (searchDebounceTimer !== null) {
    window.clearTimeout(searchDebounceTimer)
  }

  searchDebounceTimer = window.setTimeout(() => {
    searchDebounceTimer = null
    void loadData(1)
  }, 250)
})

useEventStream((event) => {
  if (!['sign_completed', 'health_changed', 'account_changed'].includes(event.type)) return
  if (eventRefreshTimer !== null) return
  eventRefreshTimer = window.setTimeout(async () => {
    eventRefreshTimer = null
    await loadData(pagination.value.page)
  }, 600)
})

onUnmounted(() => {
  if (eventRefreshTimer !== null) {
    window.clearTimeout(eventRefreshTimer)
  }
  if (searchDebounceTimer !== null) {
    window.clearTimeout(searchDebounceTimer)
  }
})

useViewRefresh(() => handleRefresh())
</script>

<style scoped>
.accounts-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.accounts-filter {
  width: 100%;
}

.search-input {
  flex: 1;
  max-width: 360px;
  min-width: 200px;
}

.filter-item {
  width: 160px;
}

.status-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
}

.bulk-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  background: var(--bg-card);
}

.bulk-bar-info {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.bulk-bar-info strong {
  color: var(--text-primary);
  font-weight: var(--font-semibold);
}

.bulk-bar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  justify-content: flex-end;
}

.bulk-select {
  width: 144px;
}

.status-tab {
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

.status-tab:hover {
  border-color: var(--border-color);
  background: var(--bg-card-hover);
}

.status-tab.active {
  border-color: var(--primary-color);
  background: var(--primary-color-light);
  color: var(--primary-color);
}

.status-tab b {
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.status-tab.active b {
  color: var(--primary-color);
}

.accounts-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.loading-state {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  color: var(--text-tertiary);
}

.loading-text {
  font-size: var(--text-sm);
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

.empty-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  justify-content: center;
  margin-top: var(--spacing-2);
}

/* Cell styles */
.accounts-page :deep(.account-cell) {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: var(--spacing-2);
}

.accounts-page :deep(.account-avatar-mini) {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  background: var(--primary-color-light);
  color: var(--primary-color);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  cursor: pointer;
}

.accounts-page :deep(.account-info) {
  min-width: 0;
}

.accounts-page :deep(.account-name-row) {
  display: flex;
  align-items: center;
  min-width: 0;
  gap: 6px;
}

.accounts-page :deep(.account-name) {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
  font-weight: var(--font-medium);
  cursor: pointer;
}

.accounts-page :deep(.account-name:hover) {
  color: var(--primary-color);
}

.accounts-page :deep(.account-sub) {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  font-family: var(--font-mono);
}

.accounts-page :deep(.note-badge) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 999px;
  background: var(--bg-secondary);
  color: var(--text-tertiary);
}

.accounts-page :deep(.group-tag) {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 6px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
}

.accounts-page :deep(.muted) {
  color: var(--text-quaternary);
}

.accounts-page :deep(.quota-cell) {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.accounts-page :deep(.quota-main) {
  display: flex;
  align-items: baseline;
  gap: 2px;
}

.accounts-page :deep(.quota-alert-icon) {
  display: inline-flex;
  align-items: center;
  color: var(--error-color);
  margin-right: 2px;
}

.accounts-page :deep(.quota-value) {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.accounts-page :deep(.quota-value.danger) {
  color: var(--error-color);
}

.accounts-page :deep(.quota-sub) {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.accounts-page :deep(.quota-bar) {
  height: 2px;
  background: var(--border-color-light);
  border-radius: 999px;
  overflow: hidden;
}

.accounts-page :deep(.quota-bar-fill) {
  height: 100%;
  background: var(--primary-color);
  transition: width var(--transition-slow);
}

.accounts-page :deep(.quota-bar-fill.danger) {
  background: var(--error-color);
}

.accounts-page :deep(.sign-cell) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.accounts-page :deep(.tag-dot) {
  width: 6px;
  height: 6px;
  border-radius: 999px;
}

.accounts-page :deep(.tag-dot.success) {
  background: var(--success-color);
}

.accounts-page :deep(.tag-dot.error) {
  background: var(--error-color);
}

.accounts-page :deep(.tag) {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.accounts-page :deep(.tag.success) {
  background: var(--success-color-light);
  color: var(--success-color);
}

.accounts-page :deep(.tag.error) {
  background: var(--error-color-light);
  color: var(--error-color);
}

.accounts-page :deep(.tag.warning) {
  background: var(--warning-color-light);
  color: var(--warning-color);
}

.accounts-page :deep(.tag.default) {
  background: var(--bg-secondary);
  color: var(--text-tertiary);
}

.accounts-page :deep(.status-cell) {
  display: inline-grid;
  grid-template-columns: 56px 42px;
  align-items: center;
  gap: var(--spacing-2);
  min-width: 106px;
}

.accounts-page :deep(.status-cell .tag) {
  justify-content: center;
}

.accounts-page :deep(.actions) {
  display: flex;
  gap: 2px;
}

.accounts-page :deep(.action-button) {
  width: 42px;
}

.accounts-page :deep(.account-row-warning td) {
  background: rgba(217, 119, 6, 0.06);
}

.accounts-page :deep(.account-row-alert td) {
  background: rgba(220, 38, 38, 0.06);
}

@media (max-width: 900px) {
  .search-input {
    max-width: none;
  }

  .bulk-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .bulk-bar-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .accounts-filter {
    align-items: stretch;
    flex-direction: column;
  }

  .filter-item {
    width: 100%;
  }

  .bulk-select {
    width: 100%;
  }
}

/* ────────── account operations visual layer */
.accounts-page { gap: clamp(14px, 1.8vw, 24px); padding-bottom: 48px; }
.accounts-hero { position: relative; isolation: isolate; min-height: 310px; display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(220px, .55fr); gap: 28px; align-items: end; overflow: hidden; padding: clamp(24px, 4vw, 52px); border: 1px solid var(--line); border-radius: 26px; background: radial-gradient(circle at 90% 18%, var(--signal-wash), transparent 25%), linear-gradient(135deg, var(--surface-raised), var(--surface-inset)); box-shadow: var(--lift-3); }
.accounts-hero__grid { position: absolute; inset: 0; z-index: -1; opacity: .55; background-image: linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px); background-size: 40px 40px; mask-image: linear-gradient(to right, black 34%, transparent 100%); }
.accounts-hero::after { content: ''; position: absolute; right: 22%; top: -60%; z-index: -1; width: 340px; aspect-ratio: 1; border: 1px solid color-mix(in srgb, var(--signal) 28%, transparent); border-radius: 50%; box-shadow: 0 0 0 52px color-mix(in srgb, var(--signal) 5%, transparent), 0 0 0 104px color-mix(in srgb, var(--signal) 3%, transparent); }
.accounts-hero__copy { align-self: center; max-width: 720px; }
.eyebrow-line { display: flex; align-items: center; gap: 9px; color: var(--ink-muted); font-family: var(--font-mono); font-size: 10px; letter-spacing: .14em; }
.eyebrow-line .mono { margin-left: auto; color: var(--ink-faint); }
.live-pulse { width: 7px; height: 7px; flex: 0 0 auto; border-radius: 50%; background: var(--signal); box-shadow: 0 0 0 5px var(--signal-wash), 0 0 14px var(--signal-glow); }
.accounts-hero h2 { margin: 36px 0 16px; color: var(--ink-max); font-family: var(--font-display); font-size: clamp(38px, 5.1vw, 72px); font-weight: 470; line-height: .98; letter-spacing: -.065em; }
.accounts-hero h2 em { display: block; color: var(--signal-deep); font-style: normal; font-weight: 720; }
.accounts-hero p { max-width: 580px; margin: 0; color: var(--ink-muted); font-size: 13px; line-height: 1.85; }
.accounts-hero__actions { display: flex; align-items: center; gap: 16px; margin-top: 25px; }
.hero-link { display: inline-flex; align-items: center; gap: 7px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .12em; }
.accounts-hero__readout { align-self: center; padding: 22px; border: 1px solid var(--line); border-radius: 20px; background: color-mix(in srgb, var(--surface-overlay) 76%, transparent); backdrop-filter: blur(20px); }
.hero-readout__label { color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .16em; }
.hero-readout__value { margin: 16px 0 20px; color: var(--ink-max); font-family: var(--font-display); font-size: clamp(54px, 6vw, 78px); font-weight: 620; line-height: .85; letter-spacing: -.08em; }
.hero-readout__value small { margin-left: 4px; color: var(--signal-deep); font-family: var(--font-mono); font-size: 12px; letter-spacing: 0; }
.hero-readout__meta { display: flex; justify-content: space-between; gap: 12px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .1em; }
.hero-readout__meta strong { color: var(--ink-strong); font-size: 11px; }
.hero-readout__bar { height: 3px; margin: 12px 0 15px; overflow: hidden; border-radius: 99px; background: var(--line-faint); }
.hero-readout__bar span { display: block; height: 100%; border-radius: inherit; background: var(--signal); box-shadow: 0 0 12px var(--signal-glow); transition: width .5s; }
.hero-readout__counts { display: flex; flex-wrap: wrap; gap: 7px 12px; color: var(--ink-muted); font-family: var(--font-mono); font-size: 9px; }
.status-dot { display: inline-block; width: 6px; height: 6px; margin-right: 3px; border-radius: 50%; background: var(--line-strong); }
.status-dot.success { background: var(--ok); }
.status-dot.error { background: var(--bad); }
.status-dot.default { background: var(--ink-faint); }
.accounts-hero__actions-panel { grid-column: 1 / -1; display: flex; align-items: center; justify-content: space-between; gap: 18px; padding-top: 16px; border-top: 1px solid var(--line-faint); }
.accounts-hero__actions-panel > .mono { color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .16em; }
.accounts-hero__actions-panel .toolbar-actions { flex-wrap: wrap; }
.accounts-console { gap: 14px; padding: 17px; border-radius: 20px; background: linear-gradient(135deg, var(--surface-raised), var(--surface-inset)); box-shadow: var(--lift-2); }
.console-topline { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--line-faint); }
.console-topline > div { display: flex; align-items: baseline; gap: 13px; }
.console-code { color: var(--signal-deep); font-size: 9px; letter-spacing: .14em; }
.console-topline strong { color: var(--ink-strong); font-size: 12px; }
.console-live { display: inline-flex; align-items: center; gap: 7px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .09em; }
.console-live span { width: 5px; height: 5px; border-radius: 50%; background: var(--signal); box-shadow: 0 0 9px var(--signal-glow); }
.accounts-console .status-tabs { padding-top: 13px; border-top: 1px solid var(--line-faint); }
.status-tab { border-radius: 7px; font-family: var(--font-mono); font-size: 10px; letter-spacing: .02em; }
.status-tab.active { box-shadow: 0 0 0 1px var(--signal-glow); }
.bulk-bar { border-radius: 16px; border-color: var(--signal-glow); background: linear-gradient(90deg, var(--signal-wash), var(--surface-raised)); box-shadow: var(--lift-2); }
.accounts-card { border-color: var(--line); border-radius: 20px; box-shadow: var(--lift-2); }
.pagination-wrap { background: var(--surface-inset); border-color: var(--line-faint); }

@media (max-width: 920px) {
  .accounts-hero { grid-template-columns: 1fr; }
  .accounts-hero__readout { max-width: 420px; }
  .accounts-hero__actions-panel { align-items: flex-start; flex-direction: column; }
}
@media (max-width: 640px) {
  .accounts-hero { min-height: 0; padding: 22px; border-radius: 20px; }
  .eyebrow-line .mono { display: none; }
  .accounts-hero h2 { margin-top: 34px; font-size: clamp(40px, 12vw, 58px); }
  .accounts-hero__actions { align-items: flex-start; flex-direction: column; }
  .accounts-hero__actions-panel .toolbar-actions { align-items: stretch; flex-direction: column; width: 100%; }
  .accounts-hero__actions-panel .toolbar-actions :deep(.ui-button) { width: 100%; }
  .console-topline { align-items: flex-start; flex-direction: column; }
  .console-topline > div { align-items: flex-start; flex-direction: column; gap: 4px; }
  .accounts-console .accounts-filter { flex-direction: column; align-items: stretch; }
}</style>
