<template>
  <div class="account-detail-page">
    <UiLoading :show="loading">
      <section class="page-toolbar account-profile-toolbar" aria-label="账号详情操作">
        <div class="account-toolbar__identity">
          <button class="account-toolbar__back" type="button" aria-label="返回账号池" @click="router.push('/accounts')">
            <ArrowLeft :size="15" />
          </button>
          <div class="account-toolbar__avatar" :class="{ inactive: !account?.is_active }">
            {{ (account?.username || 'U')[0].toUpperCase() }}
          </div>
          <div class="account-toolbar__copy">
            <div class="account-toolbar__title">
              <strong>{{ account?.username || '账号详情' }}</strong>
              <span class="status-tag status-tag--light" :class="account?.is_active ? 'success' : 'default'">
                <i></i>{{ account?.is_active ? '已启用' : '已禁用' }}
              </span>
              <span v-if="account?.group" class="group-tag">
                <span class="dot" :style="{ background: getGroupColor(account.group.color) }"></span>
                {{ account.group.name }}
              </span>
            </div>
            <div class="account-toolbar__meta">
              <ExternalLink
                :href="getPlatformUrl()"
                :label="account?.platform?.name || getPlatformUrl() || '未配置平台'"
                mono
              />
              <span class="mono">ID {{ account?.external_user_id || account?.anyrouter_user_id || '—' }}</span>
            </div>
          </div>
        </div>
        <div class="page-toolbar__actions detail-actions">
          <UiButton size="small" @click="openEditModal">
            <template #icon><Pencil :size="14" /></template>
            编辑节点
          </UiButton>
          <UiButton size="small" :loading="refreshing" @click="handleRefreshInfo">
            <template #icon><RefreshCw :size="14" /></template>
            刷新读数
          </UiButton>
          <UiButton size="small" type="primary" :loading="signing" @click="handleSign">
            <template #icon><Zap :size="14" /></template>
            立即签到
          </UiButton>
        </div>
      </section>

      <section class="metric-deck" aria-label="账号指标">
        <article class="metric-card metric-card--signal">
          <div class="metric-top"><span>01 / CAPACITY</span><Gauge :size="16" /></div>
          <div class="metric-label">剩余额度</div>
          <div class="metric-value metric-value--quota">{{ accountInfo?.quota_display || formatQuota(accountInfo?.quota || 0) }}</div>
          <div class="metric-foot"><span class="metric-dot"></span>{{ quotaPercent }}% 可用容量</div>
        </article>
        <article class="metric-card">
          <div class="metric-top"><span>02 / CONSUMED</span><Database :size="16" /></div>
          <div class="metric-label">已用额度</div>
          <div class="metric-value metric-value--quota">{{ accountInfo?.used_quota_display || formatQuota(accountInfo?.used_quota || 0) }}</div>
          <div class="metric-foot">平台累计消耗读数</div>
        </article>
        <article class="metric-card">
          <div class="metric-top"><span>03 / REQUESTS</span><Activity :size="16" /></div>
          <div class="metric-label">总请求数</div>
          <div class="metric-value">{{ (accountInfo?.request_count || 0).toLocaleString() }}</div>
          <div class="metric-foot">生命周期累计调用</div>
        </article>
        <article class="metric-card metric-card--dark">
          <div class="metric-top"><span>04 / AFFILIATE</span><Network :size="16" /></div>
          <div class="metric-label">推广所得</div>
          <div class="metric-value metric-value--quota">{{ accountInfo?.aff_history_quota_display || formatQuota(accountInfo?.aff_history_quota || 0) }}</div>
          <div class="metric-foot">{{ accountInfo?.aff_count || 0 }} 个关联节点</div>
        </article>
      </section>

      <section class="profile-workspace">
        <div class="workspace-main">
          <article class="instrument-panel profile-panel">
            <header class="instrument-head">
              <div class="instrument-identity">
                <span class="instrument-code">IDENTITY / 07—A</span>
                <div>
                  <h2>身份与路由参数</h2>
                  <p>账号、平台、分组与认证状态的统一索引</p>
                </div>
              </div>
              <ShieldCheck :size="18" />
            </header>

            <div class="info-matrix">
              <div class="info-cell">
                <span class="info-label">用户名</span>
                <strong class="info-value">{{ accountInfo?.username || account?.username || '—' }}</strong>
              </div>
              <div class="info-cell">
                <span class="info-label">显示名</span>
                <strong class="info-value">{{ accountInfo?.display_name || account?.display_name || '—' }}</strong>
              </div>
              <div class="info-cell">
                <span class="info-label">用户 ID</span>
                <strong class="info-value mono">{{ accountInfo?.id || account?.anyrouter_user_id || '—' }}</strong>
              </div>
              <div class="info-cell">
                <span class="info-label">用户组</span>
                <strong class="info-value">{{ accountInfo?.group || '—' }}</strong>
              </div>
              <div class="info-cell">
                <span class="info-label">所属分组</span>
                <span class="info-value">
                  <span v-if="accountInfo?.local_group || account?.group" class="group-tag">
                    <span class="dot" :style="{ background: getGroupColor((accountInfo?.local_group || account?.group)?.color) }"></span>
                    {{ (accountInfo?.local_group || account?.group)?.name }}
                  </span>
                  <span v-else class="muted">未分组</span>
                </span>
              </div>
              <div class="info-cell">
                <span class="info-label">平台</span>
                <span class="info-value">
                  <ExternalLink
                    :href="getPlatformUrl()"
                    :label="getPlatformUrl() || account?.platform?.name || '—'"
                    mono
                    wrap
                  />
                </span>
              </div>
              <div class="info-cell info-cell--wide">
                <span class="info-label">访问出口</span>
                <strong class="info-value">
                  {{ getProxyModeLabel(account?.proxy_mode) }}
                  <span v-if="account?.proxy_mode === 'custom' && account?.proxy_url_masked" class="muted">
                    / {{ account.proxy_url_masked }}
                  </span>
                </strong>
              </div>
              <div class="info-cell">
                <span class="info-label">登录账号</span>
                <strong class="info-value">{{ account?.login_username || '—' }}</strong>
              </div>
              <div class="info-cell">
                <span class="info-label">自动刷新</span>
                <span class="info-value">
                  <span class="status-tag status-tag--light" :class="account?.has_login_credentials ? 'success' : 'default'">
                    <i></i>{{ account?.has_login_credentials ? '已启用' : '未启用' }}
                  </span>
                </span>
              </div>
              <div class="info-cell info-cell--wide">
                <span class="info-label">备注</span>
                <strong class="info-value">{{ account?.note || '—' }}</strong>
              </div>
              <div class="info-cell info-cell--wide">
                <span class="info-label">最后更新</span>
                <strong class="info-value mono">{{ account ? formatDateTime(account.updated_at) : '—' }}</strong>
              </div>
            </div>
          </article>

          <article v-if="accountInfo?.aff_code" class="instrument-panel affiliate-panel">
            <header class="instrument-head">
              <div class="instrument-identity">
                <span class="instrument-code">AFFILIATE / 07—B</span>
                <div>
                  <h2>推广信号</h2>
                  <p>{{ accountInfo?.aff_count || 0 }} 个关联节点 / {{ accountInfo?.aff_history_quota_display || '$0.00' }} 历史回报</p>
                </div>
              </div>
              <Link2 :size="18" />
            </header>
            <div class="affiliate-body">
              <div class="affiliate-code">
                <span>REFERRAL ENDPOINT</span>
                <ExternalLink class="aff-link" :href="getAffLink()" mono wrap />
              </div>
              <UiButton size="small" type="primary" @click="copyAffLink">
                <template #icon><Copy :size="14" /></template>
                复制链接
              </UiButton>
            </div>
          </article>
        </div>

        <aside class="workspace-side">
          <article class="instrument-panel log-panel">
            <header class="instrument-head">
              <div class="instrument-identity">
                <span class="instrument-code">EVENT STREAM / 07—C</span>
                <div>
                  <h2>签到事件流</h2>
                  <p>{{ pagination.itemCount }} 条执行记录持续同步</p>
                </div>
              </div>
              <span class="stream-live"><i></i> LIVE</span>
            </header>

            <div class="mini-trend">
              <div class="mini-trend-head">
                <span><Activity :size="13" /> 近 7 天信号</span>
                <span class="mini-trend-meta">{{ miniTrendSummary }}</span>
              </div>
              <div class="mini-trend-chart">
                <div v-for="day in miniTrend" :key="day.date" class="mini-day">
                  <UiTooltip trigger="hover">
                    <template #trigger>
                      <div class="mini-bar-track">
                        <div class="mini-bar" :class="day.tone" :style="{ height: `${day.height}%` }"></div>
                      </div>
                    </template>
                    {{ day.date }} / {{ day.label }}
                  </UiTooltip>
                  <span class="mini-label">{{ day.short }}</span>
                </div>
              </div>
            </div>
            <div v-if="!loadingLogs && signLogs.length > 0" class="log-list">
              <div v-for="(log, index) in signLogs" :key="log.id" class="log-item">
                <div class="log-sequence">
                  <span>{{ String((pagination.page - 1) * pagination.pageSize + index + 1).padStart(2, '0') }}</span>
                  <i class="log-dot" :class="log.success ? 'success' : 'error'"></i>
                </div>
                <div class="log-main">
                  <div class="log-head">
                    <span class="log-status" :class="log.success ? 'success' : 'error'">
                      {{ log.success ? 'SIGN COMPLETED' : 'SIGN FAILED' }}
                    </span>
                    <span v-if="Number(log.reward_quota || 0)" class="log-reward">+{{ formatRewardAmount(log.reward_quota, log.reward_unit, log.reward_display) }}</span>
                  </div>
                  <div class="log-time"><Clock3 :size="12" /> {{ formatDateTime(log.sign_time) }}</div>
                  <div v-if="log.message" class="log-msg">{{ log.message }}</div>
                </div>
              </div>
            </div>

            <div v-if="loadingLogs" class="log-loading">
              <UiLoading size="small" />
              <span>SYNCING EVENT STREAM</span>
            </div>

            <div v-if="!loadingLogs && signLogs.length === 0" class="log-empty">
              <FileText :size="26" :stroke-width="1.5" />
              <strong>NO EVENT DATA</strong>
              <span>当前节点还没有签到记录</span>
              <UiButton size="tiny" type="primary" :loading="signing" @click="handleSign">立即签到</UiButton>
            </div>

            <div v-if="pagination.itemCount > pagination.pageSize" class="log-pagination">
              <span class="pagination-caption">PAGE {{ pagination.page }}</span>
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
          </article>
        </aside>
      </section>
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
import {
  Activity,
  ArrowLeft,
  Clock3,
  Copy,
  Database,
  FileText,
  Gauge,
  Link2,
  Network,
  Pencil,
  RefreshCw,
  ShieldCheck,
  Zap
} from 'lucide-vue-next'

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

const quotaPercent = computed(() => {
  const value = Number.parseFloat(String(accountInfo.value?.quota_percent || '0'))
  return Math.max(0, Math.min(100, Number.isFinite(value) ? Math.round(value) : 0))
})

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
.account-detail-page {
  --detail-radius: clamp(14px, 1.4vw, 22px);
  --detail-gap: clamp(12px, 1.5vw, 20px);
  position: relative;
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--detail-gap);
  isolation: isolate;
}

.account-profile-toolbar {
  align-items: center;
  padding: 10px 12px;
}

.account-toolbar__identity,
.account-toolbar__title,
.account-toolbar__meta {
  display: flex;
  align-items: center;
}

.account-toolbar__identity {
  flex: 1 1 360px;
  gap: 10px;
  min-width: 0;
}

.account-toolbar__back {
  display: inline-grid;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-sm);
  color: var(--ink-muted);
  background: var(--surface-inset);
  cursor: pointer;
  transition: border-color var(--transition-fast), color var(--transition-fast), transform var(--transition-fast);
}

.account-toolbar__back:hover {
  border-color: var(--signal-glow);
  color: var(--signal-deep);
  transform: translateX(-2px);
}

.account-toolbar__avatar {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid var(--signal-glow);
  border-radius: 50%;
  color: var(--signal-deep);
  background: var(--signal-wash);
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: var(--weight-bold);
}

.account-toolbar__avatar.inactive {
  border-color: var(--line);
  color: var(--ink-faint);
  background: var(--surface-inset);
}

.account-toolbar__copy { min-width: 0; }
.account-toolbar__title { flex-wrap: wrap; gap: 6px; min-width: 0; }
.account-toolbar__title > strong {
  max-width: min(34vw, 320px);
  overflow: hidden;
  color: var(--ink-max);
  font-size: var(--fn-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-toolbar__meta {
  gap: 10px;
  min-width: 0;
  margin-top: 3px;
  color: var(--ink-faint);
  font-size: var(--fn-2xs);
}

.account-toolbar__meta > * {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-detail-page::before {
  position: absolute;
  z-index: -1;
  top: -40px;
  right: -8%;
  left: -8%;
  height: 480px;
  content: '';
  pointer-events: none;
  opacity: 0.45;
  background-image:
    linear-gradient(to right, var(--grid-line) 1px, transparent 1px),
    linear-gradient(to bottom, var(--grid-line) 1px, transparent 1px);
  background-size: 48px 48px;
  mask-image: linear-gradient(to bottom, #000, transparent 94%);
}

.profile-hero {
  position: relative;
  min-height: 430px;
  overflow: hidden;
  padding: clamp(22px, 3vw, 42px);
  border: 1px solid var(--line-strong);
  border-radius: var(--detail-radius);
  background: var(--surface-inverse);
  color: var(--ink-inverse);
  box-shadow: var(--lift-4);
  isolation: isolate;
}

.hero-grid {
  position: absolute;
  z-index: -3;
  inset: 0;
  pointer-events: none;
  opacity: 0.54;
  background-image:
    linear-gradient(to right, color-mix(in srgb, var(--ink-inverse) 13%, transparent) 1px, transparent 1px),
    linear-gradient(to bottom, color-mix(in srgb, var(--ink-inverse) 13%, transparent) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: linear-gradient(118deg, #000 0%, rgba(0, 0, 0, 0.66) 50%, transparent 94%);
}

.hero-orbit {
  position: absolute;
  z-index: -2;
  border-radius: 50%;
  pointer-events: none;
}

.hero-orbit--a {
  top: -290px;
  right: -90px;
  width: 620px;
  height: 620px;
  border: 1px solid color-mix(in srgb, var(--signal) 62%, transparent);
  box-shadow:
    0 0 0 44px color-mix(in srgb, var(--signal) 5%, transparent),
    0 0 120px color-mix(in srgb, var(--signal) 17%, transparent);
}

.hero-orbit--b {
  right: 27%;
  bottom: -285px;
  width: 450px;
  height: 450px;
  border: 1px dashed color-mix(in srgb, var(--ink-inverse) 18%, transparent);
}

.hero-topline,
.hero-kicker,
.identity-lockup,
.identity-tags,
.readout-topline,
.quota-caption,
.hero-actions-bar,
.action-status,
.detail-actions,
.metric-top,
.metric-foot,
.instrument-head,
.instrument-identity,
.affiliate-body,
.mini-trend-head,
.log-head,
.log-time,
.log-pagination,
.stream-live,
.status-tag,
.group-tag {
  display: flex;
  align-items: center;
}

.hero-topline {
  position: relative;
  z-index: 2;
  justify-content: space-between;
  gap: var(--s4);
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  padding: 0;
  border: 0;
  color: color-mix(in srgb, var(--ink-inverse) 58%, transparent);
  background: transparent;
  font: inherit;
  letter-spacing: inherit;
  transition: color var(--transition-fast), transform var(--transition-bounce);
}

.back-link:hover {
  color: var(--signal-deep);
  transform: translateX(-3px);
}

.hero-live {
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: var(--signal-deep);
  font-weight: var(--weight-semibold);
}

.hero-live i,
.action-status::before,
.stream-live i,
.status-tag i,
.metric-dot {
  width: 7px;
  height: 7px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--signal);
  box-shadow: 0 0 0 5px color-mix(in srgb, var(--signal) 13%, transparent), 0 0 16px var(--signal);
}

.hero-layout {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(260px, 0.65fr);
  align-items: end;
  gap: clamp(36px, 8vw, 132px);
  padding: clamp(42px, 6vw, 76px) 0 34px;
}

.hero-copy { min-width: 0; }

.hero-kicker {
  gap: 10px;
  margin-bottom: 18px;
  color: var(--signal-deep);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: var(--weight-semibold);
  letter-spacing: 0.12em;
}

.hero-index {
  display: inline-grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--ink-inverse) 30%, transparent);
  border-radius: 50%;
  color: var(--signal-deep);
}

.identity-lockup {
  align-items: flex-end;
  gap: clamp(16px, 2.4vw, 30px);
}

.hero-avatar {
  display: grid;
  width: clamp(70px, 8vw, 104px);
  height: clamp(70px, 8vw, 104px);
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--signal) 56%, transparent);
  border-radius: 50%;
  color: var(--signal-deep);
  background:
    radial-gradient(circle at 32% 26%, color-mix(in srgb, var(--signal) 24%, transparent), transparent 48%),
    color-mix(in srgb, var(--surface-inverse) 84%, transparent);
  box-shadow: inset 0 0 0 9px color-mix(in srgb, var(--signal) 5%, transparent), 0 0 46px color-mix(in srgb, var(--signal) 13%, transparent);
  font-family: var(--font-display);
  font-size: clamp(2rem, 4vw, 4rem);
  font-weight: var(--weight-black);
  line-height: 1;
}

.hero-avatar.inactive {
  border-color: color-mix(in srgb, var(--ink-inverse) 25%, transparent);
  color: color-mix(in srgb, var(--ink-inverse) 36%, transparent);
  box-shadow: inset 0 0 0 9px color-mix(in srgb, var(--ink-inverse) 4%, transparent);
}

.identity-copy { min-width: 0; }

.identity-copy h1 {
  max-width: 11em;
  overflow: hidden;
  color: var(--ink-inverse);
  font-family: var(--font-display);
  font-size: clamp(3.1rem, 8vw, 8rem);
  font-weight: var(--weight-black);
  letter-spacing: -0.085em;
  line-height: 0.82;
  overflow-wrap: anywhere;
}

.identity-tags {
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}
.status-tag,
.group-tag {
  gap: 7px;
  width: fit-content;
  min-height: 23px;
  padding: 4px 8px;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-full);
  color: var(--ink-muted);
  background: var(--surface-inset);
  font-size: 10px;
  font-weight: var(--weight-semibold);
  letter-spacing: 0.06em;
}

.status-tag.success { color: var(--ok); background: var(--ok-wash); border-color: color-mix(in srgb, var(--ok) 26%, transparent); }
.status-tag.default { color: var(--ink-faint); }
.status-tag.success i { background: var(--ok); box-shadow: 0 0 10px color-mix(in srgb, var(--ok) 55%, transparent); }
.status-tag.default i { background: var(--ink-faint); box-shadow: none; }
.status-tag--light { min-height: 22px; padding-block: 3px; }

.group-tag--hero {
  border-color: color-mix(in srgb, var(--ink-inverse) 20%, transparent);
  color: color-mix(in srgb, var(--ink-inverse) 68%, transparent);
  background: color-mix(in srgb, var(--surface-inverse) 72%, transparent);
}

.group-tag .dot {
  width: 6px;
  height: 6px;
  flex: 0 0 auto;
  border-radius: 50%;
}

.hero-description {
  max-width: 620px;
  margin-top: 24px;
  color: color-mix(in srgb, var(--ink-inverse) 60%, transparent);
  font-size: var(--fn-md);
  line-height: 1.8;
}

.hero-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  max-width: 760px;
  margin-top: 30px;
  border: 1px solid color-mix(in srgb, var(--ink-inverse) 15%, transparent);
  background: color-mix(in srgb, var(--ink-inverse) 15%, transparent);
}

.hero-meta-item {
  min-width: 0;
  padding: 12px 14px;
  background: color-mix(in srgb, var(--surface-inverse) 87%, transparent);
}

.hero-meta-item > span {
  display: block;
  margin-bottom: 6px;
  color: color-mix(in srgb, var(--ink-inverse) 35%, transparent);
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.1em;
}

.hero-meta-item strong,
.hero-meta-item :deep(.external-link) {
  display: block;
  overflow: hidden;
  color: color-mix(in srgb, var(--ink-inverse) 76%, transparent);
  font-size: var(--fn-xs);
  font-weight: var(--weight-medium);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quota-readout {
  justify-self: end;
  width: min(100%, 318px);
  padding: 20px;
  border: 1px solid color-mix(in srgb, var(--ink-inverse) 23%, transparent);
  background: color-mix(in srgb, var(--surface-inverse) 76%, transparent);
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.24);
  backdrop-filter: blur(16px);
}

.readout-topline {
  justify-content: space-between;
  color: color-mix(in srgb, var(--ink-inverse) 46%, transparent);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: var(--weight-semibold);
  letter-spacing: 0.12em;
}

.readout-topline svg { color: var(--signal-deep); }

.quota-dial {
  position: relative;
  display: grid;
  width: 150px;
  height: 150px;
  margin: 24px auto 20px;
  place-items: center;
  border-radius: 50%;
  background: conic-gradient(var(--signal) var(--quota-progress), color-mix(in srgb, var(--ink-inverse) 12%, transparent) 0);
  box-shadow: 0 0 44px color-mix(in srgb, var(--signal) 10%, transparent);
}

.quota-dial::before {
  position: absolute;
  inset: 8px;
  border: 1px solid color-mix(in srgb, var(--ink-inverse) 18%, transparent);
  border-radius: inherit;
  background: var(--surface-inverse);
  content: '';
}

.quota-dial::after {
  position: absolute;
  inset: -13px;
  border: 1px dashed color-mix(in srgb, var(--ink-inverse) 19%, transparent);
  border-radius: inherit;
  content: '';
  animation: orbit-rotate 30s linear infinite;
}

.quota-dial__core {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: baseline;
  justify-content: center;
}

.quota-dial__core span {
  position: absolute;
  top: -18px;
  color: color-mix(in srgb, var(--ink-inverse) 38%, transparent);
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.1em;
}

.quota-dial__core strong {
  color: var(--ink-inverse);
  font-family: var(--font-display);
  font-size: 3.3rem;
  font-weight: var(--weight-light);
  letter-spacing: -0.1em;
  line-height: 1;
}

.quota-dial__core small { color: var(--signal-deep); font-size: var(--fn-sm); }
.quota-primary { margin-top: 16px; }
.quota-primary span { display: block; color: color-mix(in srgb, var(--ink-inverse) 38%, transparent); font-size: var(--fn-xs); }
.quota-primary strong { display: block; margin-top: 5px; overflow: hidden; color: var(--ink-inverse); font-family: var(--font-display); font-size: clamp(1.55rem, 3vw, 2.45rem); font-weight: var(--weight-semibold); letter-spacing: -0.06em; text-overflow: ellipsis; white-space: nowrap; }
.quota-progress { height: 3px; margin-top: 14px; overflow: hidden; background: color-mix(in srgb, var(--ink-inverse) 12%, transparent); }
.quota-progress span { display: block; height: 100%; background: var(--signal); box-shadow: 0 0 18px var(--signal); transition: width var(--transition-slow); }
.quota-caption { justify-content: space-between; margin-top: 9px; color: color-mix(in srgb, var(--ink-inverse) 35%, transparent); font-family: var(--font-mono); font-size: 8px; letter-spacing: 0.08em; }
.quota-caption span:last-child { color: var(--signal-deep); }

.hero-actions-bar {
  position: relative;
  z-index: 2;
  justify-content: space-between;
  gap: var(--s4);
  padding-top: 18px;
  border-top: 1px solid color-mix(in srgb, var(--ink-inverse) 18%, transparent);
}

.action-status {
  gap: 9px;
  color: color-mix(in srgb, var(--ink-inverse) 42%, transparent);
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.1em;
}

.action-status::before { width: 5px; height: 5px; }
.action-status svg { color: var(--signal-deep); }
.action-status strong { color: var(--signal-deep); }
.detail-actions { flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.metric-deck {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.metric-card {
  position: relative;
  display: flex;
  min-height: 150px;
  overflow: hidden;
  flex-direction: column;
  gap: 12px;
  padding: 17px 18px 16px;
  border: 1px solid var(--line-faint);
  border-radius: var(--detail-radius);
  background: var(--surface-raised);
  box-shadow: var(--lift-1);
  transition: transform var(--transition-bounce), border-color var(--transition-fast), box-shadow var(--transition-bounce);
}

.metric-card::before { position: absolute; top: 0; right: 0; left: 0; height: 2px; content: ''; background: var(--line); }
.metric-card:hover { border-color: var(--line); box-shadow: var(--lift-2); transform: translateY(-4px); }
.metric-card--signal::before { background: var(--signal-deep); }
.metric-card--dark { border-color: var(--surface-inverse); color: var(--ink-inverse); background: var(--surface-inverse); }
.metric-card--dark::before { background: var(--signal); }
.metric-top { justify-content: space-between; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: 0.1em; }
.metric-card--dark .metric-top { color: color-mix(in srgb, var(--ink-inverse) 42%, transparent); }
.metric-card--signal .metric-top svg,
.metric-card--dark .metric-top svg { color: var(--signal-deep); }
.metric-label { color: var(--ink-muted); font-size: var(--fn-xs); }
.metric-card--dark .metric-label { color: color-mix(in srgb, var(--ink-inverse) 52%, transparent); }
.metric-value { overflow: hidden; color: var(--ink-max); font-family: var(--font-display); font-size: clamp(2rem, 3.4vw, 3.45rem); font-weight: var(--weight-semibold); letter-spacing: -0.08em; line-height: 0.9; text-overflow: ellipsis; white-space: nowrap; font-variant-numeric: tabular-nums; }
.metric-value--quota { font-size: clamp(1.65rem, 2.5vw, 2.65rem); }
.metric-card--dark .metric-value { color: var(--ink-inverse); }
.metric-foot { gap: 8px; margin-top: auto; color: var(--ink-faint); font-size: var(--fn-xs); }
.metric-card--dark .metric-foot { color: color-mix(in srgb, var(--ink-inverse) 42%, transparent); }
.metric-dot { width: 5px; height: 5px; box-shadow: none; background: var(--signal-deep); }

.profile-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
  align-items: start;
  gap: var(--detail-gap);
}

.workspace-main,
.workspace-side {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--detail-gap);
}

.workspace-side { padding-top: clamp(20px, 4vw, 58px); }

.instrument-panel {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--line-faint);
  border-radius: var(--detail-radius);
  background: var(--surface-raised);
  box-shadow: var(--lift-1);
  transition: border-color var(--transition-fast), box-shadow var(--transition-bounce);
}

.instrument-panel::before {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: 2px;
  content: '';
  background: linear-gradient(90deg, var(--signal-deep), transparent 60%);
}

.instrument-panel:hover { border-color: var(--line); box-shadow: var(--lift-2); }

.instrument-head {
  justify-content: space-between;
  gap: var(--s4);
  min-height: 72px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--line-faint);
  background:
    linear-gradient(to right, var(--grid-line) 1px, transparent 1px),
    linear-gradient(to bottom, var(--grid-line) 1px, transparent 1px),
    var(--surface-inset);
  background-size: 18px 18px;
}

.instrument-head > svg { color: var(--signal-deep); }
.instrument-identity { align-items: flex-start; gap: 14px; min-width: 0; }
.instrument-code { flex: 0 0 auto; padding-top: 3px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: 0.1em; }
.instrument-identity h2 { color: var(--ink-max); font-size: var(--fn-lg); letter-spacing: -0.02em; }
.instrument-identity p { margin-top: 4px; color: var(--ink-muted); font-size: var(--fn-xs); }

.info-matrix {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  padding: 1px;
  background: var(--line-faint);
}

.info-cell {
  min-width: 0;
  min-height: 88px;
  padding: 16px 18px;
  background: var(--surface-raised);
}

.info-cell--wide { grid-column: 1 / -1; min-height: 72px; }
.info-label { display: block; margin-bottom: 9px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: 0.1em; text-transform: uppercase; }
.info-value { display: block; min-width: 0; color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-medium); line-height: 1.55; overflow-wrap: anywhere; }
.info-value :deep(.external-link) { color: var(--ink-strong); }
.muted { color: var(--ink-faint); font-weight: var(--weight-normal); }
.mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }

.affiliate-panel::before { background: linear-gradient(90deg, var(--info), transparent 60%); }
.affiliate-body { justify-content: space-between; gap: var(--s4); padding: 18px; }
.affiliate-code { min-width: 0; flex: 1; padding: 13px 14px; border: 1px solid var(--line-faint); background: var(--surface-inset); }
.affiliate-code > span { display: block; margin-bottom: 7px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.1em; }
.aff-link { color: var(--ink-strong); font-size: var(--fn-xs); }
.stream-live { gap: 8px; color: var(--ok); font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: 0.1em; }
.stream-live i { width: 5px; height: 5px; background: var(--ok); box-shadow: 0 0 10px color-mix(in srgb, var(--ok) 60%, transparent); }
.mini-trend { padding: 17px 18px 14px; border-bottom: 1px solid var(--line-faint); background: var(--surface-inset); }
.mini-trend-head { justify-content: space-between; gap: var(--s3); margin-bottom: 14px; color: var(--ink-muted); font-size: var(--fn-xs); }
.mini-trend-head > span:first-child { display: inline-flex; align-items: center; gap: 7px; color: var(--ink-strong); font-weight: var(--weight-medium); }
.mini-trend-head svg { color: var(--signal-deep); }
.mini-trend-meta { color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; }
.mini-trend-chart { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); align-items: end; gap: 8px; min-height: 94px; }
.mini-day { display: flex; min-width: 0; flex-direction: column; align-items: center; gap: 7px; }
.mini-bar-track { display: flex; width: 100%; height: 68px; align-items: flex-end; border-bottom: 1px solid var(--line); background-image: linear-gradient(to top, var(--grid-line) 1px, transparent 1px); background-size: 100% 17px; }
.mini-bar { width: 100%; min-height: 7px; background: var(--line); transition: height var(--transition-slow); }
.mini-bar.success { background: var(--signal-deep); box-shadow: 0 0 10px color-mix(in srgb, var(--signal) 22%, transparent); }
.mini-bar.error { background: var(--bad); }
.mini-bar.empty { background: var(--line); }
.mini-label { overflow: hidden; width: 100%; color: var(--ink-faint); font-family: var(--font-mono); font-size: 8px; text-align: center; text-overflow: clip; white-space: nowrap; }

.log-list { display: flex; max-height: 680px; overflow-y: auto; flex-direction: column; }
.log-item { display: grid; grid-template-columns: 38px minmax(0, 1fr); gap: 12px; padding: 15px 18px; border-bottom: 1px solid var(--line-faint); transition: background var(--transition-fast); }
.log-item:hover { background: var(--surface-hover); }
.log-item:last-child { border-bottom: 0; }
.log-sequence { display: flex; flex-direction: column; align-items: center; gap: 8px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 8px; }
.log-dot { width: 7px; height: 7px; border-radius: 50%; }
.log-dot.success { background: var(--ok); box-shadow: 0 0 9px color-mix(in srgb, var(--ok) 44%, transparent); }
.log-dot.error { background: var(--bad); box-shadow: 0 0 9px color-mix(in srgb, var(--bad) 38%, transparent); }
.log-main { min-width: 0; }
.log-head { justify-content: space-between; gap: var(--s2); }
.log-status { font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: 0.08em; }
.log-status.success { color: var(--ok); }
.log-status.error { color: var(--bad); }
.log-reward { color: var(--signal-deep); font-family: var(--font-mono); font-size: var(--fn-xs); font-weight: var(--weight-semibold); }
.log-time { gap: 6px; margin-top: 7px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; }
.log-time svg { flex: 0 0 auto; }
.log-msg { margin-top: 8px; color: var(--ink-muted); font-size: var(--fn-xs); line-height: 1.6; overflow-wrap: anywhere; }
.log-loading,
.log-empty { display: flex; min-height: 220px; flex-direction: column; align-items: center; justify-content: center; gap: 9px; padding: var(--s8); color: var(--ink-faint); text-align: center; }
.log-loading span,
.log-empty strong { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.1em; }
.log-empty > span { font-size: var(--fn-xs); }
.log-empty svg { color: var(--signal-deep); }
.log-pagination { justify-content: space-between; gap: var(--s4); padding: 12px 16px; border-top: 1px solid var(--line-faint); background: var(--surface-inset); }
.pagination-caption { color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.1em; }

@keyframes orbit-rotate { to { transform: rotate(360deg); } }

@media (max-width: 1180px) {
  .hero-layout { grid-template-columns: minmax(0, 1.15fr) minmax(250px, 0.85fr); gap: 34px; }
  .profile-workspace { grid-template-columns: 1fr; }
  .workspace-side { padding-top: 0; }
}

@media (max-width: 900px) {
  .hero-layout { grid-template-columns: 1fr; align-items: start; }
  .quota-readout { justify-self: stretch; width: 100%; display: grid; grid-template-columns: 160px minmax(0, 1fr); align-items: center; column-gap: 24px; }
  .readout-topline { grid-column: 1 / -1; }
  .quota-dial { grid-row: 2 / span 4; margin-block: 28px; }
  .quota-primary { margin-top: 28px; }
  .quota-progress,
  .quota-caption { grid-column: 2; }
  .metric-deck { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 700px) {
  .account-profile-toolbar { align-items: stretch; }
  .account-toolbar__identity { flex-basis: 100%; }
  .account-toolbar__title > strong { max-width: min(58vw, 320px); }
  .account-toolbar__meta { flex-wrap: wrap; }
  .profile-hero { min-height: 0; padding: 18px; }
  .hero-topline { align-items: flex-start; }
  .hero-live { max-width: 130px; justify-content: flex-end; text-align: right; }
  .hero-layout { gap: 28px; padding: 38px 0 24px; }
  .identity-lockup { align-items: flex-start; flex-direction: column; }
  .identity-copy h1 { font-size: clamp(3rem, 17vw, 5.6rem); }
  .hero-meta-grid { grid-template-columns: 1fr; }
  .hero-actions-bar { align-items: stretch; flex-direction: column; }
  .action-status { display: none; }
  .detail-actions { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .detail-actions :deep(.ui-button) { width: 100%; justify-content: center; }
  .quota-readout { display: block; }
  .quota-dial { margin: 25px auto 20px; }
  .quota-primary { margin-top: 16px; }
  .metric-deck { grid-template-columns: 1fr; }
  .metric-card { min-height: 132px; }
  .info-matrix { grid-template-columns: 1fr; }
  .info-cell--wide { grid-column: auto; }
  .affiliate-body { align-items: stretch; flex-direction: column; }
  .affiliate-body :deep(.ui-button) { width: 100%; justify-content: center; }
  .instrument-head { align-items: flex-start; }
  .instrument-identity { gap: 8px; flex-direction: column; }
  .instrument-code { padding-top: 0; }
  .mini-trend-chart { gap: 5px; }
  .mini-label { font-size: 7px; }
  .log-pagination { align-items: flex-start; flex-direction: column; }
}

@media (max-width: 480px) {
  .detail-actions { grid-template-columns: 1fr; }
  .hero-avatar { width: 68px; height: 68px; }
  .identity-tags { margin-top: 14px; }
  .profile-hero,
  .instrument-panel,
  .metric-card { border-radius: 14px; }
}
</style>
