<template>
  <div class="account-detail">
    <!-- 返回 + 标题 -->
    <div class="detail-head">
      <n-button text size="small" @click="router.push('/accounts')">
        <template #icon><n-icon :size="14"><ArrowBackOutline /></n-icon></template>
        账号列表
      </n-button>
      <div class="detail-actions">
        <n-button size="small" @click="openEditModal">
          <template #icon><n-icon :size="14"><CreateOutline /></n-icon></template>
          编辑
        </n-button>
        <n-button size="small" :loading="refreshing" @click="handleRefreshInfo">
          <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
        <n-button size="small" type="primary" :loading="signing" @click="handleSign">
          <template #icon><n-icon :size="14"><FlashOutline /></n-icon></template>
          立即签到
        </n-button>
      </div>
    </div>

    <n-spin :show="loading">
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
              <span class="mono">UID {{ account?.anyrouter_user_id || '-' }}</span>
              <span class="divider">·</span>
              <span>{{ account?.platform?.name || '—' }}</span>
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
                <span class="info-value">{{ account?.platform?.name || '—' }}</span>
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
                <code class="aff-link">{{ getAffLink() }}</code>
                <n-button size="small" @click="copyAffLink">
                  <template #icon><n-icon :size="14"><CopyOutline /></n-icon></template>
                  复制
                </n-button>
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
                  <n-tooltip trigger="hover">
                    <template #trigger>
                      <div
                        class="mini-bar"
                        :class="day.tone"
                        :style="{ height: `${day.height}%` }"
                      ></div>
                    </template>
                    {{ day.date }} · {{ day.label }}
                  </n-tooltip>
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
                    <span v-if="log.reward_quota" class="log-reward">+{{ formatQuota(log.reward_quota) }}</span>
                  </div>
                  <div class="log-time">{{ formatDateTime(log.sign_time) }}</div>
                  <div v-if="log.message" class="log-msg">{{ log.message }}</div>
                </div>
              </div>
            </div>

            <div v-if="loadingLogs" class="log-loading">
              <n-spin size="small" />
            </div>

            <div v-if="!loadingLogs && signLogs.length === 0" class="log-empty">
              <n-icon :size="24" color="var(--text-quaternary)"><DocumentTextOutline /></n-icon>
              <span>暂无签到记录</span>
              <n-button size="tiny" type="primary" :loading="signing" @click="handleSign">立即签到</n-button>
            </div>

            <div v-if="pagination.itemCount > pagination.pageSize" class="log-pagination">
              <n-pagination
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
    </n-spin>

    <!-- 编辑弹窗 -->
    <n-modal v-model:show="showEditModal" :mask-closable="false">
      <div class="edit-modal">
        <div class="modal-head">
          <h3>编辑账号</h3>
          <n-button text @click="showEditModal = false">
            <n-icon :size="16"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="field">
              <label>平台</label>
              <n-select
                v-model:value="editForm.platform_id"
                :options="platformOptions"
                size="small"
                placeholder="选择平台"
                :loading="loadingPlatforms"
              />
            </div>
            <div class="field">
              <label>User ID</label>
              <n-input v-model:value="editForm.user_id" size="small" placeholder="留空则不修改" />
            </div>
            <div class="field field-full">
              <label>Session Cookie</label>
              <n-input
                v-model:value="editForm.session_cookie"
                type="textarea"
                :rows="3"
                size="small"
                placeholder="留空则不修改"
              />
            </div>
            <div class="field">
              <label>登录账号</label>
              <n-input
                v-model:value="editForm.login_username"
                size="small"
                :disabled="editForm.clear_login_credentials"
                placeholder="邮箱或用户名"
              />
            </div>
            <div class="field">
              <label>登录密码</label>
              <n-input
                v-model:value="editForm.login_password"
                type="password"
                show-password-on="click"
                size="small"
                :disabled="editForm.clear_login_credentials"
                placeholder="留空则不变"
              />
            </div>
            <div class="field field-full">
              <label>备注</label>
              <n-input
                v-model:value="editForm.note"
                type="textarea"
                :rows="2"
                maxlength="255"
                show-count
                size="small"
                placeholder="记录用途、来源或特殊说明"
              />
            </div>
            <div v-if="account?.has_login_credentials" class="field field-full">
              <n-checkbox v-model:checked="editForm.clear_login_credentials">
                清除已保存的登录凭证
              </n-checkbox>
            </div>
            <div class="field">
              <label>状态</label>
              <n-switch v-model:value="editForm.is_active">
                <template #checked>启用</template>
                <template #unchecked>禁用</template>
              </n-switch>
            </div>
            <div class="field">
              <label>分组</label>
              <n-select
                v-model:value="editForm.group_id"
                :options="groups.map(g => ({ label: g.name, value: g.id }))"
                size="small"
                placeholder="选择分组"
                clearable
              />
            </div>
            <div class="field field-full">
              <label>推送渠道</label>
              <n-select
                v-model:value="editForm.notify_channel_ids"
                multiple
                size="small"
                :options="channelOptions"
                placeholder="选择推送渠道（可多选）"
                clearable
                :loading="loadingChannels"
              />
            </div>
          </div>
        </div>
        <div class="modal-foot">
          <n-button size="small" @click="showEditModal = false">取消</n-button>
          <n-button size="small" type="primary" :loading="updating" @click="handleUpdate">
            保存
          </n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  RefreshOutline, FlashOutline, CopyOutline, CreateOutline, ArrowBackOutline,
  CloseOutline, DocumentTextOutline
} from '@vicons/ionicons5'
import { accountApi, signApi, groupsApi, notifyApi, platformApi } from '../api'
import { formatDateTime, formatQuota, copyToClipboard } from '../utils'
import { useEventStream, useViewRefresh } from '../composables'

const route = useRoute()
const router = useRouter()

const accountId = Number(route.params.id)
const loading = ref(false)
const refreshing = ref(false)
const signing = ref(false)
const loadingLogs = ref(false)
const updating = ref(false)

const account = ref<any>(null)
const accountInfo = ref<any>(null)
const signLogs = ref<any[]>([])

const showEditModal = ref(false)
const editForm = ref({
  user_id: '',
  session_cookie: '',
  login_username: '',
  login_password: '',
  note: '',
  clear_login_credentials: false,
  is_active: true,
  platform_id: null as number | null,
  group_id: null as number | null,
  notify_channel_ids: [] as number[]
})

const groups = ref<any[]>([])
const channelOptions = ref<{ label: string; value: number }[]>([])
const loadingChannels = ref(false)
const platformOptions = ref<{ label: string; value: number }[]>([])
const loadingPlatforms = ref(false)
const miniTrend = ref<Array<{ date: string; short: string; tone: 'success' | 'error' | 'empty'; label: string; height: number }>>([])

const getAffBaseUrl = () => account.value?.platform?.base_url || ''
const getAffLink = () => `${getAffBaseUrl()}/register?aff=${accountInfo.value?.aff_code || ''}`

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
    editForm.value.is_active = res.data.is_active
    editForm.value.platform_id = res.data.platform?.id || null
    editForm.value.group_id = res.data.group_id || null
    editForm.value.login_username = res.data.login_username || ''
    editForm.value.note = res.data.note || ''
    editForm.value.clear_login_credentials = false
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

const handleUpdate = async () => {
  updating.value = true
  try {
    if (!editForm.value.platform_id) {
      window.$notify('请选择平台', 'warning')
      return
    }
    const data: any = { is_active: editForm.value.is_active }
    if (editForm.value.user_id.trim()) data.user_id = editForm.value.user_id.trim()
    if (editForm.value.session_cookie.trim()) data.session_cookie = editForm.value.session_cookie.trim()
    if (editForm.value.note.trim() !== (account.value?.note || '')) data.note = editForm.value.note.trim()
    if (editForm.value.clear_login_credentials) {
      data.clear_login_credentials = true
    } else {
      const previousLoginUsername = account.value?.login_username?.trim() || ''
      const currentLoginUsername = editForm.value.login_username.trim()
      if (currentLoginUsername && currentLoginUsername !== previousLoginUsername) {
        data.login_username = currentLoginUsername
      }
      if (editForm.value.login_password) data.login_password = editForm.value.login_password
    }
    if (editForm.value.group_id !== account.value?.group_id) {
      data.group_id = editForm.value.group_id || 0
    }
    if (editForm.value.platform_id !== account.value?.platform?.id) {
      data.platform_id = editForm.value.platform_id
    }

    await accountApi.update(accountId, data)

    const notifyData = {
      channels: editForm.value.notify_channel_ids.map((id: number) => ({
        channel_id: id,
        is_enabled: true,
        notify_config: {}
      }))
    }
    await notifyApi.updateAccountNotify(accountId, notifyData)

    window.$notify('账号信息已更新', 'success')
    showEditModal.value = false
    editForm.value.user_id = ''
    editForm.value.session_cookie = ''
    editForm.value.login_password = ''
    editForm.value.clear_login_credentials = false
    loadAccount()
    loadAccountInfo()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    updating.value = false
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

const loadPlatforms = async () => {
  loadingPlatforms.value = true
  try {
    const res = await platformApi.getList()
    const platforms = res.data || []
    platformOptions.value = platforms.map((p: any) => ({
      label: `${p.name} (${p.base_url})`,
      value: p.id
    }))
    if (!editForm.value.platform_id && platforms.length > 0) {
      editForm.value.platform_id = platforms[0].id
    }
  } catch (e: any) {
    console.error('Failed to load platforms:', e)
  } finally {
    loadingPlatforms.value = false
  }
}

const loadChannels = async () => {
  loadingChannels.value = true
  try {
    const res = await notifyApi.getChannels()
    channelOptions.value = (res.data || [])
      .filter((c: any) => c.is_enabled)
      .map((c: any) => ({ label: c.name, value: c.id }))
  } catch (e: any) {
    console.error('Failed to load channels:', e)
  } finally {
    loadingChannels.value = false
  }
}

const loadAccountNotify = async () => {
  try {
    const res = await notifyApi.getAccountNotify(accountId)
    const enabledChannels = (res.data || []).filter((c: any) => c.is_enabled)
    editForm.value.notify_channel_ids = enabledChannels.map((c: any) => c.channel_id)
  } catch (e: any) {
    console.error('Failed to load account notify:', e)
  }
}

const openEditModal = async () => {
  showEditModal.value = true
  editForm.value.user_id = ''
  editForm.value.session_cookie = ''
  editForm.value.login_username = account.value?.login_username || ''
  editForm.value.login_password = ''
  editForm.value.note = account.value?.note || ''
  editForm.value.clear_login_credentials = false
  editForm.value.is_active = account.value?.is_active ?? true
  editForm.value.platform_id = account.value?.platform?.id || null
  editForm.value.group_id = account.value?.group_id || null
  editForm.value.notify_channel_ids = []

  await Promise.all([loadPlatforms(), loadChannels(), loadAccountNotify()])
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
  padding: var(--spacing-2);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  word-break: break-all;
  font-family: var(--font-mono);
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
