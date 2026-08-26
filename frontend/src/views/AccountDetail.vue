<template>
  <div class="account-detail">
    <!-- 返回 + 标题 -->
    <div class="detail-head">
      <UiButton text size="small" @click="router.push('/accounts')">
        <template #icon><ArrowLeft :size="14" /></template>
        账号列表
      </UiButton>
      <div class="detail-actions">
        <UiButton size="small" @click="openEditModal">
          <template #icon><Pencil :size="14" /></template>
          编辑
        </UiButton>
        <UiButton size="small" :loading="refreshing" @click="handleRefreshInfo">
          <template #icon><RefreshCw :size="14" /></template>
          刷新
        </UiButton>
        <UiButton size="small" type="primary" :loading="signing" @click="handleSign">
          <template #icon><Zap :size="14" /></template>
          立即签到
        </UiButton>
      </div>
    </div>

    <UiLoading :show="loading">
      <!-- 账号概览 -->
      <div class="account-hero">
        <div class="hero-identity">
          <div class="hero-avatar" :class="{ inactive: !account?.is_active }">
            {{ (account?.username || 'U')[0].toUpperCase() }}
          </div>
          <div class="hero-main">
            <div class="hero-title">
              <h1>{{ account?.username || '账号详情' }}</h1>
              <span class="tag" :class="account?.is_active ? 'success' : 'default'">
                {{ account?.is_active ? '启用' : '已禁用' }}
              </span>
              <span v-if="account?.group" class="group-tag">
                <span class="dot" :style="{ background: getGroupColor(account.group.color) }"></span>
                {{ account.group.name }}
              </span>
            </div>
            <div class="hero-meta">
              <span class="mono">ID {{ account?.external_user_id || account?.anyrouter_user_id || '-' }}</span>
              <span class="divider">·</span>
              <ExternalLink
                :href="getPlatformUrl()"
                :label="getPlatformUrl() || account?.platform?.name || '—'"
              />
              <span class="divider">·</span>
              <span>创建于 {{ account ? formatDateTime(account.created_at) : '-' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 指标卡 -->
      <div class="stat-row">
        <div class="stat-card">
          <div class="stat-label">剩余额度</div>
          <div class="stat-value">{{ accountInfo?.quota_display || formatQuota(accountInfo?.quota || 0) }}</div>
          <div class="stat-bar">
            <div class="stat-bar-fill" :style="{ width: `${parseFloat(accountInfo?.quota_percent || '0')}%` }"></div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">已用额度</div>
          <div class="stat-value">{{ accountInfo?.used_quota_display || formatQuota(accountInfo?.used_quota || 0) }}</div>
          <div class="stat-foot">{{ accountInfo?.quota_percent || '0%' }} 剩余</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">总请求数</div>
          <div class="stat-value">{{ (accountInfo?.request_count || 0).toLocaleString() }}</div>
          <div class="stat-foot">累计调用</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">推广所得</div>
          <div class="stat-value">{{ accountInfo?.aff_history_quota_display || formatQuota(accountInfo?.aff_history_quota || 0) }}</div>
          <div class="stat-foot">{{ accountInfo?.aff_count || 0 }} 人推广</div>
        </div>
      </div>

      <div class="content-grid">
        <!-- 左：基本信息 + 推广 -->
        <div class="left-col">
          <div class="panel">
            <div class="panel-head">
              <div class="panel-title">基本信息</div>
            </div>
            <div class="info-list">
              <div class="info-row">
                <span class="info-label">用户名</span>
                <span class="info-value">{{ accountInfo?.username || account?.username || '—' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">显示名</span>
                <span class="info-value">{{ accountInfo?.display_name || account?.display_name || '—' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">用户 ID</span>
                <span class="info-value mono">{{ accountInfo?.id || account?.anyrouter_user_id || '—' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">用户组</span>
                <span class="info-value">{{ accountInfo?.group || '—' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">所属分组</span>
                <span class="info-value">
                  <span v-if="accountInfo?.local_group || account?.group" class="group-tag">
                    <span class="dot" :style="{ background: getGroupColor((accountInfo?.local_group || account?.group)?.color) }"></span>
                    {{ (accountInfo?.local_group || account?.group)?.name }}
                  </span>
                  <span v-else class="muted">未分组</span>
                </span>
              </div>
              <div class="info-row">
                <span class="info-label">平台</span>
                <span class="info-value">
                  <ExternalLink
                    :href="getPlatformUrl()"
                    :label="getPlatformUrl() || account?.platform?.name || '—'"
                    mono
                  />
                </span>
              </div>
              <div class="info-row">
                <span class="info-label">访问出口</span>
                <span class="info-value">
                  {{ getProxyModeLabel(account?.proxy_mode) }}
                  <span v-if="account?.proxy_mode === 'custom' && account?.proxy_url_masked" class="muted">
                    · {{ account.proxy_url_masked }}
                  </span>
                </span>
              </div>
              <div class="info-row">
                <span class="info-label">登录账号</span>
                <span class="info-value">{{ account?.login_username || '—' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">备注</span>
                <span class="info-value">{{ account?.note || '—' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">自动刷新</span>
                <span class="info-value">
                  <span class="tag" :class="account?.has_login_credentials ? 'success' : 'default'">
                    {{ account?.has_login_credentials ? '已启用' : '未启用' }}
                  </span>
                </span>
              </div>
              <div class="info-row">
                <span class="info-label">最后更新</span>
                <span class="info-value">{{ account ? formatDateTime(account.updated_at) : '—' }}</span>
              </div>
            </div>
          </div>

          <div v-if="accountInfo?.aff_code" class="panel">
            <div class="panel-head">
              <div class="panel-title">推广</div>
              <div class="panel-sub">
                {{ accountInfo?.aff_count || 0 }} 人 · {{ accountInfo?.aff_history_quota_display || '$0.00' }}
              </div>
            </div>
            <div class="aff-box">
              <div class="aff-label">推广链接</div>
              <div class="aff-row">
                <ExternalLink class="aff-link" :href="getAffLink()" mono wrap />
                <UiButton size="small" @click="copyAffLink">
                  <template #icon><Copy :size="14" /></template>
                  复制
                </UiButton>
              </div>
            </div>
          </div>
        </div>

        <!-- 右：签到记录 -->
        <div class="right-col">
          <div class="panel">
            <div class="panel-head">
              <div class="panel-title">签到记录</div>
              <div class="panel-sub">共 {{ pagination.itemCount }} 条</div>
            </div>

            <div class="mini-trend">
              <div class="mini-trend-head">
                <span>近 7 天签到</span>
                <span class="mini-trend-meta">{{ miniTrendSummary }}</span>
              </div>
              <div class="mini-trend-chart">
                <div
                  v-for="day in miniTrend"
                  :key="day.date"
                  class="mini-day"
                >
                  <UiTooltip trigger="hover">
                    <template #trigger>
                      <div
                        class="mini-bar"
                        :class="day.tone"
                        :style="{ height: `${day.height}%` }"
                      ></div>
                    </template>
                    {{ day.date }} · {{ day.label }}
                  </UiTooltip>
                  <span class="mini-label">{{ day.short }}</span>
                </div>
              </div>
            </div>

            <div v-if="!loadingLogs && signLogs.length > 0" class="log-list">
              <div v-for="log in signLogs" :key="log.id" class="log-item">
                <span class="log-dot" :class="log.success ? 'success' : 'error'"></span>
                <div class="log-main">
                  <div class="log-head">
                    <span class="log-status" :class="log.success ? 'success' : 'error'">
                      {{ log.success ? '签到成功' : '签到失败' }}
                    </span>
                    <span v-if="Number(log.reward_quota || 0)" class="log-reward">+{{ formatRewardAmount(log.reward_quota, log.reward_unit, log.reward_display) }}</span>
                  </div>
                  <div class="log-time">{{ formatDateTime(log.sign_time) }}</div>
                  <div v-if="log.message" class="log-msg">{{ log.message }}</div>
                </div>
              </div>
            </div>

            <div v-if="loadingLogs" class="log-loading">
              <UiLoading size="small" />
            </div>

            <div v-if="!loadingLogs && signLogs.length === 0" class="log-empty">
              <FileText :size="24" />
              <span>暂无签到记录</span>
              <UiButton size="tiny" type="primary" :loading="signing" @click="handleSign">立即签到</UiButton>
            </div>

            <div v-if="pagination.itemCount > pagination.pageSize" class="log-pagination">
              <UiPagination
                v-model:page="pagination.page"
                v-model:page-size="pagination.pageSize"
                :item-count="pagination.itemCount"
                :page-sizes="pagination.pageSizes"
                size="small"
                @update:page="handlePageChange"
                @update:page-size="handlePageSizeChange"
              />
            </div>
          </div>
        </div>
      </div>
    </UiLoading>

    <AccountModal
      ref="accountModalRef"
      v-model:show="showEditModal"
      :account="account"
      :groups="groups"
      @submit="handleAccountSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { UiButton, UiLoading, UiPagination, UiTooltip } from '../ui'
import { computed, ref, onMounted } from 'vue'
import { AccountModal } from '../components/dashboard'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Copy, FileText, Pencil, RefreshCw, Zap } from 'lucide-vue-next'

import { accountApi, signApi, groupsApi, notifyApi, platformApi } from '../api'
import { formatDateTime, formatQuota, formatRewardAmount, copyToClipboard } from '../utils'
import { useEventStream, useViewRefresh } from '../composables'
import ExternalLink from '../components/common/ExternalLink.vue'
import type { Account, AccountAuthType, AccountGroup, AccountProxyMode } from '../types'

const route = useRoute()
const router = useRouter()

const accountId = Number(route.params.id)
const loading = ref(false)
const refreshing = ref(false)
const signing = ref(false)
const loadingLogs = ref(false)
const account = ref<Account | null>(null)
const accountInfo = ref<any>(null)
const signLogs = ref<any[]>([])

const showEditModal = ref(false)
const accountModalRef = ref<InstanceType<typeof AccountModal> | null>(null)
const groups = ref<AccountGroup[]>([])
const miniTrend = ref<Array<{ date: string; short: string; tone: 'success' | 'error' | 'empty'; label: string; height: number }>>([])
const getProxyModeLabel = (mode?: AccountProxyMode) => {
  if (mode === 'custom') return '自定义代理'
  return '直连服务器出口'
}

const getPlatformUrl = () => account.value?.platform?.base_url || ''
const getAffLink = () => `${getPlatformUrl()}/register?aff=${accountInfo.value?.aff_code || ''}`

const getGroupColor = (color?: string) => {
  const colors: Record<string, string> = {
    default: '#737980',
    blue: '#0284c7',
    green: '#16a34a',
    red: '#dc2626',
    orange: '#d97706',
    purple: '#7c3aed',
    pink: '#db2777',
    cyan: '#0891b2'
  }
  return colors[color || 'default'] || colors.default
}

const pagination = ref({
  page: 1,
  pageSize: 15,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const miniTrendSummary = computed(() => {
  const successDays = miniTrend.value.filter(item => item.tone === 'success').length
  const failDays = miniTrend.value.filter(item => item.tone === 'error').length
  return `成功 ${successDays} 天 · 失败 ${failDays} 天`
})

const toLocalDateKey = (value: string | Date) => {
  const date = new Date(value)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const buildMiniTrend = (logs: any[]) => {
  const dateMap = new Map<string, { success: number; fail: number }>()
  logs.forEach(log => {
    const signDate = toLocalDateKey(log.sign_time)
    const current = dateMap.get(signDate) || { success: 0, fail: 0 }
    if (log.success) current.success += 1
    else current.fail += 1
    dateMap.set(signDate, current)
  })

  const days = Array.from({ length: 7 }).map((_, index) => {
    const date = new Date()
    date.setDate(date.getDate() - (6 - index))
    const dateKey = toLocalDateKey(date)
    const data = dateMap.get(dateKey)
    const tone: 'success' | 'error' | 'empty' = !data || (data.success === 0 && data.fail === 0)
      ? 'empty'
      : data.success >= data.fail ? 'success' : 'error'
    const height = !data ? 18 : data.success > 0 ? 100 : 42
    return {
      date: dateKey,
      short: `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`,
      tone,
      label: !data ? '无签到' : data.success > 0 ? `成功 ${data.success}` : `失败 ${data.fail}`,
      height
    }
  })

  miniTrend.value = days
}

const loadMiniTrend = async () => {
  try {
    const res = await accountApi.getSignLogs(accountId, 1, 60)
    buildMiniTrend(res.data?.items || [])
  } catch (e) {
    console.error('Failed to load mini trend:', e)
  }
}

const loadAccount = async () => {
  loading.value = true
  try {
    const res = await accountApi.get(accountId)
    account.value = res.data

  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loading.value = false
  }
}

const loadAccountInfo = async () => {
  try {
    const res = await accountApi.getCachedInfo(accountId)
    accountInfo.value = res.data
  } catch (e: any) {
    console.error('获取账号信息失败:', e.message)
  }
}

const loadSignLogs = async (page = 1) => {
  loadingLogs.value = true
  try {
    const res = await accountApi.getSignLogs(accountId, page, pagination.value.pageSize)
    signLogs.value = res.data?.items || []
    pagination.value.itemCount = res.data?.total || 0
    pagination.value.page = page
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loadingLogs.value = false
  }
}

const handlePageChange = (page: number) => loadSignLogs(page)
const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  loadSignLogs(1)
}

const handleRefreshInfo = async () => {
  refreshing.value = true
  try {
    const res = await accountApi.getInfo(accountId)
    accountInfo.value = res.data
    window.$notify('账号信息已刷新', 'success')
    await loadMiniTrend()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    refreshing.value = false
  }
}

const handleSign = async () => {
  signing.value = true
  try {
    const res = await signApi.sign(accountId)
    window.$notify(res.data?.message || '签到成功', 'success')
    accountApi.getInfo(accountId).then(r => { accountInfo.value = r.data }).catch(() => {})
    loadSignLogs(1)
    loadMiniTrend()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    signing.value = false
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
    const targetPlatform = data.platform_id == null ? null : (await platformApi.get(data.platform_id)).data
    const isHttpTarget = targetPlatform?.adapter_type === 'http'
    const updateData: any = { is_active: data.is_active }
    const platformChanged = data.platform_id !== account.value?.platform?.id
    if (data.platform_id) updateData.platform_id = data.platform_id

    if (isHttpTarget) {
      const externalUserId = data.external_user_id.trim()
      if (platformChanged || externalUserId !== (account.value?.external_user_id || '')) {
        updateData.external_user_id = externalUserId
      }
      if (data.username.trim() !== (account.value?.username || '')) updateData.username = data.username.trim()
      if (data.display_name.trim() !== (account.value?.display_name || '')) updateData.display_name = data.display_name.trim()
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
        const previousLoginUsername = account.value?.login_username?.trim() || ''
        const currentLoginUsername = data.login_username.trim()
        if (currentLoginUsername && currentLoginUsername !== previousLoginUsername) updateData.login_username = currentLoginUsername
        if (data.login_password) updateData.login_password = data.login_password
      }
    }

    if (data.note.trim() !== (account.value?.note || '')) updateData.note = data.note.trim()
    if (data.group_id !== account.value?.group_id) updateData.group_id = data.group_id || 0

    const previousProxyMode = account.value?.proxy_mode || 'direct'
    if (data.proxy_mode !== previousProxyMode) updateData.proxy_mode = data.proxy_mode
    if (data.proxy_mode === 'custom' && data.proxy_url.trim()) {
      updateData.proxy_mode = 'custom'
      updateData.proxy_url = data.proxy_url.trim()
    } else if (data.proxy_mode !== 'custom' && previousProxyMode === 'custom') {
      updateData.proxy_url = ''
    }

    await accountApi.update(accountId, updateData)
    await notifyApi.updateAccountNotify(accountId, {
      channels: data.notify_channel_ids.map((id: number) => ({
        channel_id: id,
        is_enabled: true,
        notify_config: {}
      }))
    })

    window.$notify('账号信息已更新', 'success')
    showEditModal.value = false
    await Promise.all([loadAccount(), loadAccountInfo(), loadSignLogs(pagination.value.page), loadMiniTrend()])
  } catch (e: any) {
    window.$notify(e.message || '更新失败', 'error')
  } finally {
    accountModalRef.value?.setSubmitting(false)
  }
}
const copyAffLink = () => {
  if (accountInfo.value?.aff_code) {
    const link = getAffLink()
    copyToClipboard(link).then(() => {
      window.$notify('推广链接已复制', 'success')
    }).catch(() => {
      window.$notify('复制失败', 'error')
    })
  }
}

const loadGroups = async () => {
  try {
    const res = await groupsApi.getList()
    groups.value = res.data || []
  } catch (e: any) {
    console.error('Failed to load groups:', e)
  }
}


const openEditModal = () => {
  showEditModal.value = true
}
onMounted(() => {
  loadAccount()
  loadAccountInfo()
  loadSignLogs()
  loadMiniTrend()
  loadGroups()
})

useEventStream((event) => {
  if (event.account_id !== accountId) return
  if (!['sign_completed', 'health_changed', 'account_changed'].includes(event.type)) return
  void Promise.all([loadAccount(), loadAccountInfo(), loadSignLogs(pagination.value.page), loadMiniTrend()])
})

useViewRefresh(async () => {
  await Promise.all([loadAccount(), loadAccountInfo(), loadSignLogs(pagination.value.page), loadMiniTrend()])
})
</script>

<style scoped>
.account-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.detail-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}

.detail-actions {
  display: flex;
  gap: var(--spacing-2);
}

/* Hero */
.account-hero {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
}

.hero-identity {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.hero-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: var(--primary-color-light);
  color: var(--primary-color);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero-avatar.inactive {
  background: var(--bg-secondary);
  color: var(--text-tertiary);
}

.hero-main {
  min-width: 0;
  flex: 1;
}

.hero-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.hero-title h1 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  letter-spacing: -0.01em;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* Tags */
.tag {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.tag.success {
  background: var(--success-color-light);
  color: var(--success-color);
}

.tag.default {
  background: var(--bg-secondary);
  color: var(--text-tertiary);
}

.group-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 20px;
  padding: 0 6px;
  background: var(--bg-secondary);
  color: var(--text-secondary);
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
}

.group-tag .dot {
  width: 5px;
  height: 5px;
  border-radius: 999px;
}

.divider {
  color: var(--text-quaternary);
}

.muted {
  color: var(--text-quaternary);
}

.mono {
  font-family: var(--font-mono);
}

/* 指标卡 */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.stat-card {
  padding: var(--spacing-4);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.stat-label {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-value {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  letter-spacing: -0.01em;
  line-height: 1;
  color: var(--text-primary);
}

.stat-foot {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.stat-bar {
  height: 3px;
  background: var(--border-color-light);
  border-radius: 999px;
  overflow: hidden;
}

.stat-bar-fill {
  height: 100%;
  background: var(--primary-color);
}

/* 内容区 */
.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
  gap: var(--spacing-3);
}

.left-col,
.right-col {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

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
  height: 40px;
  padding: 0 var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.panel-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.panel-sub {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

/* info list */
.info-list {
  display: flex;
  flex-direction: column;
}

.info-row {
  display: grid;
  grid-template-columns: 100px 1fr;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  font-size: var(--text-sm);
  border-bottom: 1px solid var(--border-color-light);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--text-tertiary);
}

.info-value {
  color: var(--text-primary);
  word-break: break-all;
}

/* aff box */
.aff-box {
  padding: var(--spacing-4);
}

.aff-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-2);
}

.aff-row {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
}

.aff-link {
  flex: 1;
  min-width: 0;
  padding: var(--spacing-2);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
}

/* 签到记录 */
.log-list {
  display: flex;
  flex-direction: column;
  max-height: 640px;
  overflow-y: auto;
}

.mini-trend {
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.mini-trend-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.mini-trend-meta {
  color: var(--text-tertiary);
}

.mini-trend-chart {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 8px;
  align-items: end;
  min-height: 70px;
}

.mini-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.mini-bar {
  width: 100%;
  min-height: 14px;
  border-radius: var(--radius-sm) var(--radius-sm) 3px 3px;
  background: var(--bg-secondary);
  transition: height var(--transition-slow);
}

.mini-bar.success {
  background: var(--success-color);
}

.mini-bar.error {
  background: var(--error-color);
}

.mini-bar.empty {
  background: var(--border-color-light);
}

.mini-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-tertiary);
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.log-item:last-child {
  border-bottom: none;
}

.log-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  margin-top: 7px;
  flex-shrink: 0;
}

.log-dot.success {
  background: var(--success-color);
}

.log-dot.error {
  background: var(--error-color);
}

.log-main {
  flex: 1;
  min-width: 0;
}

.log-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-2);
}

.log-status {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.log-status.success {
  color: var(--success-color);
}

.log-status.error {
  color: var(--error-color);
}

.log-reward {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--primary-color);
  font-weight: var(--font-semibold);
}

.log-time {
  margin-top: 2px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.log-msg {
  margin-top: 4px;
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.log-loading,
.log-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-8);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.log-pagination {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-3) var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

/* 编辑弹窗 */
.edit-modal {
  width: min(560px, calc(100vw - 24px));
  background: var(--bg-modal);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-head,
.modal-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) var(--spacing-4);
}

.modal-head {
  border-bottom: 1px solid var(--border-color-light);
}

.modal-head h3 {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
}

.modal-foot {
  justify-content: flex-end;
  gap: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.modal-body {
  padding: var(--spacing-4);
  max-height: 70vh;
  overflow-y: auto;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-3);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-full {
  grid-column: 1 / -1;
}

.field label {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

@media (max-width: 1000px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .stat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .detail-head {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-2);
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
