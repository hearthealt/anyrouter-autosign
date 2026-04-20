<template>
  <div class="accounts-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">账号</h1>
        <p class="page-subtitle">{{ pagination.itemCount }} 个账号 · 健康率 {{ healthRatio }}% · 待签到 {{ pendingCount }}</p>
      </div>
      <div class="head-actions">
        <n-button size="small" :loading="loading" @click="handleRefresh">
          <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
        <n-button size="small" :loading="batchChecking" @click="handleBatchHealthCheck">
          <template #icon><n-icon :size="14"><PulseOutline /></n-icon></template>
          批量检查
        </n-button>
        <n-button size="small" :loading="batchSigning" @click="handleBatchSign">
          <template #icon><n-icon :size="14"><FlashOutline /></n-icon></template>
          一键签到
        </n-button>
        <n-button size="small" @click="showBatchImportModal = true">
          <template #icon><n-icon :size="14"><AddOutline /></n-icon></template>
          批量导入
        </n-button>
        <n-button size="small" type="primary" @click="showAddModal">
          <template #icon><n-icon :size="14"><AddOutline /></n-icon></template>
          添加账号
        </n-button>
      </div>
    </div>

    <div class="filter-bar">
      <n-input
        v-model:value="searchKeyword"
        size="small"
        clearable
        placeholder="搜索用户名、平台或 User ID"
        class="search-input"
      >
        <template #prefix><n-icon :size="14"><SearchOutline /></n-icon></template>
      </n-input>

      <n-select
        v-model:value="selectedPlatformId"
        :options="platformOptions"
        size="small"
        clearable
        placeholder="全部平台"
        class="filter-item"
      />

      <n-select
        v-model:value="selectedGroupId"
        :options="groupOptions"
        size="small"
        clearable
        placeholder="全部分组"
        class="filter-item"
      />
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

    <div v-if="selectedAccounts.length > 0" class="bulk-bar">
      <div class="bulk-bar-info">
        已选择 <strong>{{ selectedAccounts.length }}</strong> 个账号
      </div>
      <div class="bulk-bar-actions">
        <n-button size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'sign'" @click="handleSelectedSign">
          批量签到
        </n-button>
        <n-button size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'health'" @click="handleSelectedHealthCheck">
          健康检查
        </n-button>
        <n-button size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'enable'" @click="handleBulkToggleActive(true)">
          启用
        </n-button>
        <n-button size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'disable'" @click="handleBulkToggleActive(false)">
          禁用
        </n-button>
        <n-select
          v-model:value="bulkTargetPlatformId"
          :options="platformOptions"
          size="small"
          placeholder="迁移平台"
          class="bulk-select"
          :disabled="bulkDisabled"
        />
        <n-button size="small" :disabled="bulkDisabled || !bulkTargetPlatformId" :loading="bulkLoading === 'platform'" @click="handleBulkMovePlatform">
          应用平台
        </n-button>
        <n-select
          v-model:value="bulkTargetGroupId"
          :options="groupOptions"
          size="small"
          clearable
          placeholder="加入分组"
          class="bulk-select"
          :disabled="bulkDisabled"
        />
        <n-button size="small" :disabled="bulkDisabled" :loading="bulkLoading === 'group'" @click="handleBulkAssignGroup">
          应用分组
        </n-button>
        <n-popconfirm
          positive-text="删除"
          negative-text="取消"
          @positive-click="handleBulkDelete"
        >
          <template #trigger>
            <n-button size="small" type="error" ghost :disabled="bulkDisabled" :loading="bulkLoading === 'delete'">
              批量删除
            </n-button>
          </template>
          确定删除选中的 {{ selectedAccounts.length }} 个账号？
        </n-popconfirm>
        <n-button size="small" quaternary :disabled="bulkDisabled" @click="clearSelection">
          清空选择
        </n-button>
      </div>
    </div>

    <div class="accounts-card">
      <div v-if="loading || accounts.length > 0" class="table-wrap">
        <n-data-table
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

      <div v-else class="empty-state">
        <n-icon :size="32" color="var(--text-quaternary)"><PeopleOutline /></n-icon>
        <div class="empty-title">{{ hasActiveFilters ? '没有匹配的账号' : '还没有账号' }}</div>
        <div class="empty-desc">
          {{ hasActiveFilters ? '当前筛选条件下没有结果，试试清空筛选或更换关键词。' : '先去平台页确认配置，再添加账号或批量导入，避免后续校验失败。' }}
        </div>
        <div class="empty-actions">
          <n-button v-if="!hasActiveFilters" size="small" @click="router.push('/platforms')">
            去平台页检查配置
          </n-button>
          <n-button size="small" @click="showBatchImportModal = true">
            <template #icon><n-icon :size="14"><AddOutline /></n-icon></template>
            批量导入
          </n-button>
          <n-button size="small" type="primary" @click="showAddModal">
            <template #icon><n-icon :size="14"><AddOutline /></n-icon></template>
            添加账号
          </n-button>
        </div>
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
import {
  NButton,
  NIcon,
  NPopconfirm,
  NTooltip,
  type DataTableColumns,
  type DataTableSortOrder,
  type DataTableSortState
} from 'naive-ui'
import {
  AddOutline,
  AlertCircleOutline,
  DocumentTextOutline,
  FlashOutline,
  PeopleOutline,
  PulseOutline,
  RefreshOutline,
  SearchOutline,
} from '@vicons/ionicons5'
import { AccountModal, BatchImportModal, TokensModal } from '../components'
import { accountApi, groupsApi, notifyApi, platformApi, settingsApi, signApi } from '../api'
import { useEventStream, useFormat, useViewRefresh } from '../composables'
import type { Account, AccountGroup, ApiToken, CreateTokenParams, Platform, SelectOption } from '../types'

type StatusFilter = 'healthy' | 'unhealthy' | 'pending' | 'disabled'
type SortKey = 'username' | 'platform' | 'group' | 'quota' | 'last_sign' | 'health'

const router = useRouter()
const { formatQuota, formatRelativeTime } = useFormat()

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
const sortState = ref<{ columnKey: SortKey | null; order: DataTableSortOrder }>({
  columnKey: null,
  order: false
})
let eventRefreshTimer: number | null = null
let searchDebounceTimer: number | null = null

const activeCount = computed(() => listSummary.value.active_count)
const healthyCount = computed(() => listSummary.value.healthy_count)
const unhealthyCount = computed(() => listSummary.value.unhealthy_count)
const disabledCount = computed(() => listSummary.value.disabled_count)
const pendingCount = computed(() => listSummary.value.pending_count)
const healthRatio = computed(() => (activeCount.value > 0 ? Math.round((healthyCount.value / activeCount.value) * 100) : 0))

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
  { key: 'healthy', label: '健康', count: healthyCount.value, value: 'healthy' as StatusFilter, tone: 'success' },
  { key: 'unhealthy', label: '异常', count: unhealthyCount.value, value: 'unhealthy' as StatusFilter, tone: 'error' },
  { key: 'pending', label: '待签到', count: pendingCount.value, value: 'pending' as StatusFilter, tone: 'warning' },
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

const getUserId = (account: Account) => account.anyrouter_user_id ?? '-'
const getPlatformName = (account: Account) => account.platform?.name || '—'
const getGroupInfo = (account: Account) => account.group || groups.value.find(group => group.id === account.group_id)

const getHealthTone = (account: Account) => {
  if (!account.is_active) return 'default'
  if (account.health_status === 'healthy') return 'success'
  if (account.health_status === 'unhealthy') return 'error'
  return 'warning'
}

const getHealthLabel = (account: Account) => {
  if (!account.is_active) return '已禁用'
  if (account.health_status === 'healthy') return '健康'
  if (account.health_status === 'unhealthy') return '异常'
  return '未检查'
}

const getQuotaRatio = (account: Account) => {
  const ratio = Number.parseFloat(String(account.quota_percent || '0').replace('%', ''))
  if (Number.isNaN(ratio)) return 0
  return Math.max(0, Math.min(100, ratio))
}

const isLowQuota = (account: Account) => (account.cached_quota || 0) < quotaWarningValue.value

const getRowClassName = (account: Account) => {
  if (account.health_status === 'unhealthy') return 'account-row-alert'
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
  login_username: string
  login_password: string
  note: string
  clear_login_credentials: boolean
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
      window.$notify('账号更新成功', 'success')
    } else {
      const res: any = await accountApi.create({
        session_cookie: data.session_cookie.trim() || undefined,
        user_id: data.user_id.trim() || undefined,
        login_username: data.login_username.trim() || undefined,
        login_password: data.login_password || undefined,
        note: data.note.trim() || undefined,
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

const handleBatchImported = async () => {
  await loadData(1)
}

const clearSelection = () => {
  checkedRowKeys.value = []
}

const handleCheckedRowKeysChange = (keys: Array<string | number>) => {
  checkedRowKeys.value = keys.map(key => Number(key)).filter(key => !Number.isNaN(key))
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

    const results = await Promise.allSettled(executable.map(account => action(account)))
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

const getSortOrder = (columnKey: SortKey): DataTableSortOrder =>
  sortState.value.columnKey === columnKey ? sortState.value.order : false

const handleSorterChange = (sorter: DataTableSortState | DataTableSortState[] | null) => {
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

const columns = computed<DataTableColumns<Account>>(() => [
  {
    type: 'selection',
    width: 44,
  },
  {
    title: '账号',
    key: 'username',
    minWidth: 200,
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
                  NTooltip,
                  null,
                  {
                    trigger: () =>
                      h('span', { class: 'note-badge' }, [
                        h(NIcon, { size: 12 }, { default: () => h(DocumentTextOutline) })
                      ]),
                    default: () => account.note
                  }
                )
              : null
          ]),
          h('div', { class: 'account-sub' }, `UID ${getUserId(account)}`)
        ])
      ])
  },
  {
    title: '平台',
    key: 'platform',
    minWidth: 140,
    sorter: 'default',
    sortOrder: getSortOrder('platform'),
    render: account => getPlatformName(account)
  },
  {
    title: '分组',
    key: 'group',
    minWidth: 100,
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
    minWidth: 180,
    sorter: 'default',
    sortOrder: getSortOrder('quota'),
    render: account =>
      h('div', { class: 'quota-cell' }, [
        h('div', { class: 'quota-main' }, [
          isLowQuota(account)
            ? h(
                NTooltip,
                null,
                {
                  trigger: () =>
                    h('span', { class: 'quota-alert-icon' }, [
                      h(NIcon, { size: 12 }, { default: () => h(AlertCircleOutline) })
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
    width: 90,
    sorter: 'default',
    sortOrder: getSortOrder('health'),
    render: account =>
      h('span', { class: `tag ${getHealthTone(account)}` }, getHealthLabel(account))
  },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    render: account =>
      h('div', { class: 'actions' }, [
        h(NButton, { size: 'tiny', quaternary: true, onClick: () => openAccountDetail(account) }, { default: () => '详情' }),
        h(NButton, { size: 'tiny', quaternary: true, onClick: () => showEditModal(account) }, { default: () => '编辑' }),
        h(NButton, { size: 'tiny', quaternary: true, onClick: () => showTokens(account) }, { default: () => 'Token' }),
        h(NButton, { size: 'tiny', quaternary: true, disabled: !account.is_active, loading: signingId.value === account.id, onClick: () => handleSign(account) }, { default: () => '签到' }),
        h(NButton, { size: 'tiny', quaternary: true, loading: checkingId.value === account.id, onClick: () => handleHealthCheck(account) }, { default: () => '检查' }),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDeleteAccount(account),
            positiveText: '删除',
            negativeText: '取消',
          },
          {
            trigger: () => h(NButton, { size: 'tiny', quaternary: true, type: 'error' }, { default: () => '删除' }),
            default: () => `确定删除账号 "${account.username || '-'}" ？`
          }
        )
      ])
  }
])

onMounted(async () => {
  await loadMeta()
  await loadData(1)
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
  gap: var(--spacing-4);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin: 0;
}

.page-subtitle {
  margin-top: 2px;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.head-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.filter-bar {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
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
  gap: 6px;
}

.accounts-page :deep(.account-name) {
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

.accounts-page :deep(.actions) {
  display: flex;
  gap: 2px;
}

.accounts-page :deep(.account-row-warning td) {
  background: rgba(217, 119, 6, 0.06);
}

.accounts-page :deep(.account-row-alert td) {
  background: rgba(220, 38, 38, 0.06);
}

@media (max-width: 900px) {
  .page-head {
    flex-direction: column;
    align-items: stretch;
  }

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
  .filter-bar {
    flex-direction: column;
  }

  .filter-item {
    width: 100%;
  }

  .bulk-select {
    width: 100%;
  }
}
</style>
