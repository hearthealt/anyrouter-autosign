<template>
  <div class="account-detail-page">
    <!-- 顶部导航 -->
    <div class="page-nav">
      <n-button text @click="router.push('/accounts')">
        <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
        返回账号管理
      </n-button>
    </div>

    <!-- 账号头部卡片 -->
    <div class="hero-card">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="hero-left">
          <div class="account-avatar" :class="{ inactive: !account?.is_active }">
            {{ (account?.username || 'U')[0].toUpperCase() }}
          </div>
          <div class="account-info">
            <div class="account-name">
              <h1>{{ account?.username || '账号详情' }}</h1>
              <n-tag :type="account?.is_active ? 'success' : 'default'" size="small" :bordered="false">
                {{ account?.is_active ? '已启用' : '已禁用' }}
              </n-tag>
              <n-tag v-if="account?.group" size="small" :bordered="false" :style="{ background: getGroupColor(account.group.color), color: '#fff' }">
                {{ account.group.name }}
              </n-tag>
            </div>
            <div class="account-meta">
              <span><n-icon><PersonOutline /></n-icon> ID: {{ account?.anrouter_user_id || account?.anyrouter_user_id || '-' }}</span>
              <span><n-icon><TimeOutline /></n-icon> 创建于 {{ account ? formatDateTime(account.created_at) : '-' }}</span>
            </div>
            <div class="hero-quick-stats">
              <div class="quick-stat-pill">
                <n-icon><WalletOutline /></n-icon>
                <span>剩余额度 {{ accountInfo?.quota_display || formatQuota(accountInfo?.quota || 0) }}</span>
              </div>
              <div class="quick-stat-pill">
                <n-icon><PulseOutline /></n-icon>
                <span>请求 {{ (accountInfo?.request_count || 0).toLocaleString() }}</span>
              </div>
              <div class="quick-stat-pill">
                <n-icon><PeopleOutline /></n-icon>
                <span>推广 {{ accountInfo?.aff_count || 0 }} 人</span>
              </div>
            </div>
          </div>
        </div>
        <div class="hero-actions">
          <n-button @click="openEditModal" secondary>
            <template #icon><n-icon><CreateOutline /></n-icon></template>
            编辑
          </n-button>
          <n-button @click="handleRefreshInfo" :loading="refreshing" secondary>
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新
          </n-button>
          <n-button type="primary" @click="handleSign" :loading="signing">
            <template #icon><n-icon><FlashOutline /></n-icon></template>
            立即签到
          </n-button>
        </div>
      </div>
    </div>

    <n-spin :show="loading">
      <!-- 数据概览 -->
      <div class="stats-row">
        <div class="stat-card quota-card">
          <div class="stat-icon">
            <n-icon :size="28"><WalletOutline /></n-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value primary">{{ accountInfo?.quota_display || formatQuota(accountInfo?.quota || 0) }}</div>
            <div class="stat-label">剩余额度</div>
          </div>
          <div class="stat-extra">
            <n-progress
              type="circle"
              :percentage="parseFloat(accountInfo?.quota_percent || '0')"
              :stroke-width="10"
              :show-indicator="true"
              :color="'var(--primary-color)'"
              style="width: 56px; height: 56px;"
            />
          </div>
        </div>

        <div class="stat-card used-card">
          <div class="stat-icon used">
            <n-icon :size="28"><TrendingDownOutline /></n-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ accountInfo?.used_quota_display || formatQuota(accountInfo?.used_quota || 0) }}</div>
            <div class="stat-label">已用额度</div>
          </div>
        </div>

        <div class="stat-card request-card">
          <div class="stat-icon request">
            <n-icon :size="28"><PulseOutline /></n-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ (accountInfo?.request_count || 0).toLocaleString() }}</div>
            <div class="stat-label">总请求数</div>
          </div>
        </div>

        <div class="stat-card aff-card">
          <div class="stat-icon aff">
            <n-icon :size="28"><PeopleOutline /></n-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value warning">{{ accountInfo?.aff_history_quota_display || formatQuota(accountInfo?.aff_history_quota || 0) }}</div>
            <div class="stat-label">推广所得 ({{ accountInfo?.aff_count || 0 }}人)</div>
          </div>
        </div>
      </div>

      <!-- 双栏布局 -->
      <div class="content-grid">
        <!-- 左侧：账号详情 -->
        <div class="content-left">
          <!-- 基本信息 -->
          <div class="detail-card card">
            <div class="card-header">
              <h3 class="card-title">
                <n-icon><InformationCircleOutline /></n-icon>
                基本信息
              </h3>
            </div>
            <div class="detail-list">
              <div class="detail-item">
                <div class="detail-icon"><n-icon><PersonOutline /></n-icon></div>
                <div class="detail-content">
                  <span class="detail-label">用户名</span>
                  <span class="detail-value">{{ accountInfo?.username || account?.username || '-' }}</span>
                </div>
              </div>
              <div class="detail-item">
                <div class="detail-icon"><n-icon><TextOutline /></n-icon></div>
                <div class="detail-content">
                  <span class="detail-label">显示名</span>
                  <span class="detail-value">{{ accountInfo?.display_name || account?.display_name || '-' }}</span>
                </div>
              </div>
              <div class="detail-item">
                <div class="detail-icon"><n-icon><KeyOutline /></n-icon></div>
                <div class="detail-content">
                  <span class="detail-label">用户ID</span>
                  <span class="detail-value mono">{{ accountInfo?.id || account?.anrouter_user_id || account?.anyrouter_user_id || '-' }}</span>
                </div>
              </div>
              <div class="detail-item">
                <div class="detail-icon"><n-icon><ShieldCheckmarkOutline /></n-icon></div>
                <div class="detail-content">
                  <span class="detail-label">用户组</span>
                  <span class="detail-value">{{ accountInfo?.group || '-' }}</span>
                </div>
              </div>
              <div class="detail-item">
                <div class="detail-icon"><n-icon><FolderOutline /></n-icon></div>
                <div class="detail-content">
                  <span class="detail-label">所属分组</span>
                  <span class="detail-value">
                    <n-tag v-if="accountInfo?.local_group || account?.group" size="small" :bordered="false" :style="{ background: getGroupColor((accountInfo?.local_group || account?.group)?.color), color: '#fff' }">
                      {{ (accountInfo?.local_group || account?.group)?.name }}
                    </n-tag>
                    <span v-else class="text-muted">未分组</span>
                  </span>
                </div>
              </div>
              <div class="detail-item">
                <div class="detail-icon"><n-icon><CalendarOutline /></n-icon></div>
                <div class="detail-content">
                  <span class="detail-label">最后更新</span>
                  <span class="detail-value">{{ account ? formatDateTime(account.updated_at) : '-' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 推广信息 -->
          <div class="detail-card card" v-if="accountInfo?.aff_code">
            <div class="card-header">
              <h3 class="card-title">
                <n-icon><ShareSocialOutline /></n-icon>
                推广信息
              </h3>
            </div>
            <div class="aff-section">
              <div class="aff-stats">
                <div class="aff-stat">
                  <span class="aff-stat-value">{{ accountInfo?.aff_count || 0 }}</span>
                  <span class="aff-stat-label">推广人数</span>
                </div>
                <div class="aff-stat">
                  <span class="aff-stat-value warning">{{ accountInfo?.aff_history_quota_display || '$0.00' }}</span>
                  <span class="aff-stat-label">累计收益</span>
                </div>
              </div>
              <div class="aff-link-box">
                <span class="aff-link-label">推广链接</span>
                <div class="aff-link-row">
                  <code class="aff-link-code">{{ getAffLink() }}</code>
                  <n-button size="small" type="primary" @click="copyAffLink">
                    <template #icon><n-icon><CopyOutline /></n-icon></template>
                    复制
                  </n-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：签到记录 -->
        <div class="content-right">
          <div class="logs-card card sticky-card">
            <div class="card-header">
              <h3 class="card-title">
                <n-icon><DocumentTextOutline /></n-icon>
                签到记录
              </h3>
              <span class="logs-count">共 {{ pagination.itemCount }} 条</span>
            </div>

            <div class="logs-timeline" v-if="!loadingLogs && signLogs.length > 0">
              <div v-for="log in signLogs" :key="log.id" class="timeline-item" :class="{ success: log.success, fail: !log.success }">
                <div class="timeline-dot">
                  <n-icon :size="12">
                    <CheckmarkOutline v-if="log.success" />
                    <CloseOutline v-else />
                  </n-icon>
                </div>
                <div class="timeline-content">
                  <div class="timeline-header">
                    <span class="timeline-status" :class="log.success ? 'success' : 'fail'">
                      {{ log.success ? '签到成功' : '签到失败' }}
                    </span>
                    <span class="timeline-reward" v-if="log.reward_quota">+{{ formatQuota(log.reward_quota) }}</span>
                  </div>
                  <div class="timeline-time">{{ formatDateTime(log.sign_time) }}</div>
                  <div class="timeline-message" v-if="log.message">{{ log.message }}</div>
                </div>
              </div>
            </div>

            <div class="logs-loading" v-if="loadingLogs">
              <n-spin size="medium" />
            </div>

            <div class="logs-empty" v-if="!loadingLogs && signLogs.length === 0">
              <div class="empty-icon">📭</div>
              <div class="empty-text">暂无签到记录</div>
              <n-button size="small" type="primary" @click="handleSign" :loading="signing">立即签到</n-button>
            </div>

            <div class="logs-pagination" v-if="pagination.itemCount > pagination.pageSize">
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

    <!-- 编辑账号弹窗 -->
    <n-modal v-model:show="showEditModal" :mask-closable="false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>编辑账号</h3>
          <n-button text @click="showEditModal = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>平台</label>
            <n-select
              v-model:value="editForm.platform_id"
              :options="platformOptions"
              placeholder="选择平台"
              :loading="loadingPlatforms"
            />
          </div>
          <div class="form-item">
            <label>User ID (new-api-user)</label>
            <n-input v-model:value="editForm.user_id" placeholder="留空则不修改" />
          </div>
          <div class="form-item">
            <label>Session Cookie</label>
            <n-input v-model:value="editForm.session_cookie" type="textarea" :rows="4" placeholder="留空则不修改" />
          </div>
          <div class="form-row">
            <div class="form-item flex-1">
              <label>状态</label>
              <n-switch v-model:value="editForm.is_active" size="large">
                <template #checked>启用</template>
                <template #unchecked>禁用</template>
              </n-switch>
            </div>
            <div class="form-item flex-2">
              <label>所属分组</label>
              <n-select
                v-model:value="editForm.group_id"
                :options="groups.map(g => ({ label: g.name, value: g.id }))"
                placeholder="选择分组"
                clearable
              />
            </div>
          </div>
          <n-divider style="margin: 16px 0;" />
          <div class="form-item">
            <label>签到推送渠道</label>
            <n-select
              v-model:value="editForm.notify_channel_ids"
              multiple
              :options="channelOptions"
              placeholder="选择推送渠道（可多选）"
              clearable
              :loading="loadingChannels"
            />
            <div class="form-tip">
              <n-icon><NotificationsOutline /></n-icon>
              签到成功或失败后会通过选中的渠道发送通知
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" @click="handleUpdate" :loading="updating">保存修改</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  RefreshOutline, FlashOutline, CopyOutline, CreateOutline, ArrowBackOutline,
  CheckmarkOutline, CloseOutline, PersonOutline, TimeOutline, WalletOutline,
  TrendingDownOutline, PulseOutline, PeopleOutline, InformationCircleOutline,
  TextOutline, KeyOutline, ShieldCheckmarkOutline, FolderOutline, CalendarOutline,
  ShareSocialOutline, DocumentTextOutline, NotificationsOutline
} from '@vicons/ionicons5'
import { accountApi, signApi, groupsApi, notifyApi, platformApi } from '../api'
import { formatDateTime, formatQuota, copyToClipboard } from '../utils'

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

const getAffBaseUrl = () => account.value?.platform?.base_url || ''

const getAffLink = () => `${getAffBaseUrl()}/register?aff=${accountInfo.value?.aff_code || ''}`

const getGroupColor = (color: string) => {
  const colors: Record<string, string> = {
    default: '#8b8b8b',
    blue: '#2080f0',
    green: '#18a058',
    red: '#d03050',
    orange: '#f0a020',
    purple: '#8b5cf6',
    pink: '#ec4899',
    cyan: '#06b6d4'
  }
  return colors[color] || colors.default
}

const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const loadAccount = async () => {
  loading.value = true
  try {
    const res = await accountApi.get(accountId)
    account.value = res.data
    editForm.value.is_active = res.data.is_active
    editForm.value.platform_id = res.data.platform?.id || null
    editForm.value.group_id = res.data.group_id || null
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

const handlePageChange = (page: number) => {
  loadSignLogs(page)
}

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
    if (res.data?.message) {
      window.$notify(res.data.message, 'success')
    } else {
      window.$notify('签到成功', 'success')
    }
    accountApi.getInfo(accountId).then(r => {
      accountInfo.value = r.data
    }).catch(() => {})
    loadSignLogs(1)
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
    const data: any = {
      is_active: editForm.value.is_active
    }
    if (editForm.value.user_id.trim()) {
      data.user_id = editForm.value.user_id.trim()
    }
    if (editForm.value.session_cookie.trim()) {
      data.session_cookie = editForm.value.session_cookie.trim()
    }
    if (editForm.value.group_id !== account.value?.group_id) {
      data.group_id = editForm.value.group_id || 0
    }
    if (editForm.value.platform_id !== account.value?.platform?.id) {
      data.platform_id = editForm.value.platform_id
    }

    await accountApi.update(accountId, data)

    // 保存推送配置
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

// 加载推送渠道列表
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

// 加载账号推送配置
const loadAccountNotify = async () => {
  try {
    const res = await notifyApi.getAccountNotify(accountId)
    const enabledChannels = (res.data || []).filter((c: any) => c.is_enabled)
    editForm.value.notify_channel_ids = enabledChannels.map((c: any) => c.channel_id)
  } catch (e: any) {
    console.error('Failed to load account notify:', e)
  }
}

// 打开编辑弹窗时加载推送配置
const openEditModal = async () => {
  showEditModal.value = true
  editForm.value.user_id = ''
  editForm.value.session_cookie = ''
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
  loadGroups()
  loadPlatforms()
})
</script>

<style scoped>
.account-detail-page {
  max-width: 1460px;
  margin: 0 auto;
  padding: var(--spacing-6);
}

/* 顶部导航 */
.page-nav {
  margin-bottom: var(--spacing-4);
}

/* Hero 卡片 */
.hero-card {
  position: relative;
  border-radius: var(--radius-xl);
  overflow: hidden;
  margin-bottom: var(--spacing-6);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  box-shadow: var(--shadow-md);
}

.hero-bg {
  position: absolute;
  inset: 0 0 auto 0;
  height: 128px;
  background:
    radial-gradient(80% 120% at 10% 0%, rgba(255, 255, 255, 0.2) 0%, transparent 60%),
    linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color-hover) 100%);
}

.hero-content {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--spacing-6);
  padding: var(--spacing-6);
  padding-top: 64px;
}

.hero-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.account-avatar {
  width: 86px;
  height: 86px;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, #4573d2 0%, #56a7f6 100%);
  color: #fff;
  font-size: 34px;
  font-weight: var(--font-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid var(--bg-card);
  box-shadow: var(--shadow-md);
  flex-shrink: 0;
}

.account-avatar.inactive {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

.account-info {
  min-width: 0;
  display: grid;
  gap: var(--spacing-2);
}

.account-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.account-name h1 {
  margin: 0;
  font-size: clamp(24px, 3vw, 30px);
  line-height: 1.1;
  font-weight: var(--font-bold);
  color: var(--text-primary);
}

.account-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.account-meta span {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: 4px 10px;
  border-radius: var(--radius-md);
  background: var(--bg-card-hover);
}

.hero-quick-stats {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.quick-stat-pill {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-1);
  padding: 6px 10px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color-light);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.hero-actions :deep(.n-button) {
  min-width: 92px;
}

/* 数据概览 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  padding: var(--spacing-5);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-color-light);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: all var(--transition-normal);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--primary-color);
  opacity: 0.35;
}

.stat-card.used-card::before {
  background: var(--error-color);
}

.stat-card.request-card::before {
  background: var(--success-color);
}

.stat-card.aff-card::before {
  background: var(--warning-color);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
  background: linear-gradient(135deg, rgba(32, 128, 240, 0.12) 0%, rgba(32, 128, 240, 0.2) 100%);
}

.stat-icon.used {
  color: var(--error-color);
  background: linear-gradient(135deg, rgba(208, 48, 80, 0.12) 0%, rgba(208, 48, 80, 0.2) 100%);
}

.stat-icon.request {
  color: var(--success-color);
  background: linear-gradient(135deg, rgba(24, 160, 88, 0.12) 0%, rgba(24, 160, 88, 0.2) 100%);
}

.stat-icon.aff {
  color: var(--warning-color);
  background: linear-gradient(135deg, rgba(240, 160, 32, 0.12) 0%, rgba(240, 160, 32, 0.2) 100%);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: clamp(20px, 2.3vw, 24px);
  font-weight: var(--font-bold);
  line-height: 1.2;
  color: var(--text-primary);
}

.stat-value.primary {
  color: var(--primary-color);
}

.stat-value.warning {
  color: var(--warning-color);
}

.stat-label {
  margin-top: var(--spacing-1);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.stat-extra {
  flex-shrink: 0;
}

/* 双栏布局 */
.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(350px, 0.85fr);
  gap: var(--spacing-6);
  align-items: start;
}

.content-left {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-5);
}

.content-right {
  min-width: 0;
}

.sticky-card {
  position: sticky;
  top: var(--spacing-4);
}

.card {
  border: 1px solid var(--border-color-light);
  background: var(--bg-card);
}

/* 详情卡片 */
.detail-card {
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
}

.card-title {
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.detail-list {
  padding: var(--spacing-4) var(--spacing-5);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.detail-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-lg);
  background: var(--bg-card-hover);
}

.detail-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.detail-content {
  min-width: 0;
  display: grid;
  gap: 4px;
}

.detail-label {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.detail-value {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: var(--font-medium);
  word-break: break-word;
}

.detail-value.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.text-muted {
  color: var(--text-tertiary);
}

/* 推广信息 */
.aff-section {
  padding: var(--spacing-5);
  display: grid;
  gap: var(--spacing-4);
}

.aff-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.aff-stat {
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-lg);
  background: var(--bg-card-hover);
  padding: var(--spacing-3);
  display: grid;
  gap: 2px;
}

.aff-stat-value {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
}

.aff-stat-value.warning {
  color: var(--warning-color);
}

.aff-stat-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.aff-link-box {
  background: var(--bg-card-hover);
  border-radius: var(--radius-lg);
  border: 1px dashed var(--border-color-light);
  padding: var(--spacing-4);
}

.aff-link-label {
  display: block;
  margin-bottom: var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.aff-link-row {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.aff-link-code {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  word-break: break-all;
}

/* 签到日志卡片 */
.logs-card {
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  height: fit-content;
}

.logs-count {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* 时间线 */
.logs-timeline {
  padding: var(--spacing-4) var(--spacing-5);
  max-height: 520px;
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  gap: var(--spacing-3);
  padding: var(--spacing-2) 0;
}

.timeline-dot {
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 8px;
}

.timeline-item.success .timeline-dot {
  background: var(--success-color-light);
  color: var(--success-color);
}

.timeline-item.fail .timeline-dot {
  background: var(--error-color-light);
  color: var(--error-color);
}

.timeline-content {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-lg);
  background: var(--bg-card-hover);
  padding: var(--spacing-3);
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-1);
}

.timeline-status {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}

.timeline-status.success {
  color: var(--success-color);
}

.timeline-status.fail {
  color: var(--error-color);
}

.timeline-reward {
  font-size: var(--text-sm);
  color: var(--warning-color);
  font-weight: var(--font-medium);
}

.timeline-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.timeline-message {
  margin-top: var(--spacing-1);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

/* 加载和空状态 */
.logs-loading {
  display: flex;
  justify-content: center;
  padding: var(--spacing-10);
}

.logs-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-10);
  text-align: center;
}

.logs-empty .empty-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-3);
}

.logs-empty .empty-text {
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-4);
}

.logs-pagination {
  display: flex;
  justify-content: center;
  padding: var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
}

/* 弹窗 */
.modal-container {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  width: 480px;
  max-width: 90vw;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-5);
}

.form-item {
  margin-bottom: var(--spacing-4);
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  margin-bottom: var(--spacing-2);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.form-row {
  display: flex;
  gap: var(--spacing-4);
}

.flex-1 {
  flex: 1;
}

.flex-2 {
  flex: 2;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-top: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  padding: var(--spacing-5);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

/* 响应式 */
@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .sticky-card {
    position: static;
  }
}

@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .account-detail-page {
    padding: var(--spacing-4);
  }

  .hero-content {
    flex-direction: column;
    align-items: flex-start;
    padding-top: 72px;
  }

  .hero-left {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
  }

  .account-avatar {
    margin-top: -42px;
  }

  .account-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-actions {
    width: 100%;
  }

  .hero-actions :deep(.n-button) {
    flex: 1;
    min-width: 0;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .detail-list {
    grid-template-columns: 1fr;
  }

  .aff-stats {
    grid-template-columns: 1fr;
  }

  .aff-link-row {
    flex-direction: column;
    align-items: stretch;
  }

  .form-row {
    flex-direction: column;
  }
}
</style>
