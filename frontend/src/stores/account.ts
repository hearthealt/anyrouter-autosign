import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { accountApi, signApi } from '../api'
import type {
  Account,
  AccountGroup,
  GroupColor,
  ApiToken,
  SignResult,
  BatchSignResult,
  HealthCheckResult,
  BatchHealthCheckResult
} from '../types'

export const useAccountStore = defineStore('account', () => {
  // 状态
  const accounts = ref<Account[]>([])
  const groups = ref<AccountGroup[]>([])
  const loading = ref(false)
  const selectedGroupId = ref<number | null>(null)

  // 计算属性
  const filteredAccounts = computed(() => {
    if (selectedGroupId.value === null) {
      return accounts.value
    }
    return accounts.value.filter(a => a.group_id === selectedGroupId.value)
  })

  const healthyAccounts = computed(() =>
    accounts.value.filter(a => a.health_status === 'healthy')
  )

  const unhealthyAccounts = computed(() =>
    accounts.value.filter(a => a.health_status === 'unhealthy')
  )

  const activeAccounts = computed(() =>
    accounts.value.filter(a => a.is_active)
  )

  const accountCount = computed(() => accounts.value.length)

  const groupOptions = computed(() => [
    { label: '全部分组', value: null },
    ...groups.value.map(g => ({ label: g.name, value: g.id }))
  ])

  // 分组颜色映射
  const groupColors: Record<GroupColor, string> = {
    default: '#8b8b8b',
    blue: '#2080f0',
    green: '#18a058',
    red: '#d03050',
    orange: '#f0a020',
    purple: '#8b5cf6',
    pink: '#ec4899',
    cyan: '#06b6d4'
  }

  const getGroupColor = (color: GroupColor): string => {
    return groupColors[color] || groupColors.default
  }

  // 操作
  async function fetchAccounts() {
    loading.value = true
    try {
      const res = await accountApi.getList()
      accounts.value = res.data || []
      return accounts.value
    } finally {
      loading.value = false
    }
  }

  async function fetchGroups() {
    try {
      const res = await (await import('../api')).groupsApi.getList()
      groups.value = res.data || []
      return groups.value
    } catch (e) {
      console.error('Failed to load groups:', e)
      return []
    }
  }

  async function createAccount(data: {
    session_cookie: string
    user_id: string
    group_id?: number
  }): Promise<Account> {
    const res = await accountApi.create(data)
    await fetchAccounts()
    return res.data
  }

  async function updateAccount(
    id: number,
    data: {
      user_id?: string
      session_cookie?: string
      is_active?: boolean
      group_id?: number
    }
  ): Promise<Account> {
    const res = await accountApi.update(id, data)
    await fetchAccounts()
    return res.data
  }

  async function deleteAccount(id: number): Promise<void> {
    await accountApi.delete(id)
    await fetchAccounts()
  }

  async function getAccountById(id: number): Promise<Account | undefined> {
    return accounts.value.find(a => a.id === id)
  }

  // 签到相关
  async function signAccount(accountId: number): Promise<SignResult> {
    const res = await signApi.sign(accountId)
    await fetchAccounts()
    return res.data
  }

  async function batchSign(): Promise<BatchSignResult> {
    const res = await signApi.batchSign()
    await fetchAccounts()
    return res.data
  }

  // 健康检查
  async function healthCheck(accountId: number): Promise<HealthCheckResult> {
    const res = await accountApi.healthCheck(accountId)
    await fetchAccounts()
    return res.data
  }

  async function healthCheckAll(): Promise<BatchHealthCheckResult> {
    const res = await accountApi.healthCheckAll()
    await fetchAccounts()
    return res.data
  }

  // Token 相关
  async function getTokens(accountId: number): Promise<ApiToken[]> {
    const res = await accountApi.getTokens(accountId)
    return res.data || []
  }

  async function syncTokens(accountId: number): Promise<ApiToken[]> {
    await accountApi.syncTokens(accountId)
    return getTokens(accountId)
  }

  async function createToken(
    accountId: number,
    data: {
      name: string
      remain_quota: number
      expired_time: number
      unlimited_quota: boolean
      model_limits_enabled: boolean
      model_limits: string
      group: string
      allow_ips: string
    }
  ): Promise<ApiToken> {
    const res = await accountApi.createToken(accountId, data)
    return res.data
  }

  async function updateToken(
    accountId: number,
    tokenId: number,
    data: {
      name: string
      remain_quota: number
      expired_time: number
      unlimited_quota: boolean
      model_limits_enabled: boolean
      model_limits: string
      group: string
      allow_ips: string
    }
  ): Promise<ApiToken> {
    const res = await accountApi.updateToken(accountId, tokenId, data)
    return res.data
  }

  async function deleteToken(accountId: number, tokenId: number): Promise<void> {
    await accountApi.deleteToken(accountId, tokenId)
  }

  // 重置状态
  function $reset() {
    accounts.value = []
    groups.value = []
    loading.value = false
    selectedGroupId.value = null
  }

  return {
    // 状态
    accounts,
    groups,
    loading,
    selectedGroupId,

    // 计算属性
    filteredAccounts,
    healthyAccounts,
    unhealthyAccounts,
    activeAccounts,
    accountCount,
    groupOptions,

    // 方法
    getGroupColor,
    fetchAccounts,
    fetchGroups,
    createAccount,
    updateAccount,
    deleteAccount,
    getAccountById,
    signAccount,
    batchSign,
    healthCheck,
    healthCheckAll,
    getTokens,
    syncTokens,
    createToken,
    updateToken,
    deleteToken,
    $reset
  }
})
