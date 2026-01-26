<template>
  <div class="account-detail-page">
    <!-- 顶部导航 -->
    <div class="page-nav">
      <n-button text @click="router.push('/')">
        <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
        返回仪表盘
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
              <span><n-icon><PersonOutline /></n-icon> ID: {{ account?.anyrouter_user_id || '-' }}</span>
              <span><n-icon><TimeOutline /></n-icon> 创建于 {{ account ? formatDateTime(account.created_at) : '-' }}</span>
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

        <div class="stat-card">
          <div class="stat-icon used">
            <n-icon :size="28"><TrendingDownOutline /></n-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ accountInfo?.used_quota_display || formatQuota(accountInfo?.used_quota || 0) }}</div>
            <div class="stat-label">已用额度</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon request">
            <n-icon :size="28"><PulseOutline /></n-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ (accountInfo?.request_count || 0).toLocaleString() }}</div>
            <div class="stat-label">总请求数</div>
          </div>
        </div>

        <div class="stat-card">
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
                  <span class="detail-value mono">{{ accountInfo?.id || account?.anyrouter_user_id || '-' }}</span>
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
                  <code class="aff-link-code">https://anyrouter.top/register?aff={{ accountInfo.aff_code }}</code>
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
          <div class="logs-card card">
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
import { accountApi, signApi, groupsApi, notifyApi } from '../api'
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
  group_id: null as number | null,
  notify_channel_ids: [] as number[]
})

const groups = ref<any[]>([])
const channelOptions = ref<{ label: string; value: number }[]>([])
const loadingChannels = ref(false)

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
    const link = `https://anyrouter.top/register?aff=${accountInfo.value.aff_code}`
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
  editForm.value.group_id = account.value?.group_id || null
  editForm.value.notify_channel_ids = []

  await Promise.all([loadChannels(), loadAccountNotify()])
}

onMounted(() => {
  loadAccount()
  loadAccountInfo()
  loadSignLogs()
  loadGroups()
})
</script>

<style scoped>
.account-detail-page {

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
  box-shadow: var(--shadow-lg);
}

.hero-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100px;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color-hover) 100%);
}

.hero-content {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: var(--spacing-6);
  padding-top: 60px;
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.hero-left {
  display: flex;
  align-items: flex-end;
  gap: var(--spacing-4);
}

.account-avatar {
  width: 80px;
  height: 80px;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 32px;
  font-weight: var(--font-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid var(--bg-card);
  box-shadow: var(--shadow-md);
}

.account-avatar.inactive {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
}

.account-info {
  padding-bottom: var(--spacing-2);
}

.account-name {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
  margin-bottom: var(--spacing-1);
}

.account-name h1 {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0;
}

.account-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.account-meta span {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.hero-actions {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

/* 数据概览 */
.stats-row {
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
  align-items: center;
  gap: var(--spacing-4);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card.quota-card {
  grid-column: span 1;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(99, 102, 241, 0.2) 100%);
  color: var(--primary-color);
}

.stat-icon.used {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.2) 100%);
  color: var(--error-color);
}

.stat-icon.request {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.2) 100%);
  color: var(--success-color);
}

.stat-icon.aff {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.2) 100%);
  color: var(--warning-color);
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-value.primary {
  color: var(--primary-color);
}

.stat-value.warning {
  color: var(--warning-color);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-top: var(--spacing-1);
}

.stat-extra {
  flex-shrink: 0;
}

/* 双栏布局 */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-6);
}

.content-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-5);
}

/* 详情卡片 */
.detail-card {
  background: var(--bg-card);
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
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0;
}

.detail-list {
  padding: var(--spacing-4) var(--spacing-5);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-3) 0;
  border-bottom: 1px solid var(--border-color-light);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  background: var(--bg-card-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.detail-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-width: 0;
}

.detail-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.detail-value {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: var(--font-medium);
}
.text-muted {
  color: var(--text-tertiary);
}

/* 推广信息 */
.aff-section {
  padding: var(--spacing-5);
}

.aff-stats {
  display: flex;
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-4);
}

.aff-stat {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
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
  padding: var(--spacing-4);
}

.aff-link-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-2);
  display: block;
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
  background: var(--bg-card);
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
  max-height: 500px;
  overflow-y: auto;
}

.timeline-item {
  display: flex;
  gap: var(--spacing-3);
  padding: var(--spacing-3) 0;
  position: relative;
}

.timeline-item:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 9px;
  top: 32px;
  bottom: -12px;
  width: 2px;
  background: var(--border-color-light);
}

.timeline-dot {
  width: 20px;
  height: 20px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
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
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
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
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-top: var(--spacing-1);
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
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0;
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
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-2);
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
@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .account-detail-page {
    padding: var(--spacing-4);
  }

  .hero-content {
    flex-direction: column;
    align-items: flex-start;
    padding-top: 70px;
  }

  .hero-left {
    flex-direction: column;
    align-items: flex-start;
  }

  .account-avatar {
    margin-top: -40px;
  }

  .hero-actions {
    width: 100%;
  }

  .hero-actions .n-button {
    flex: 1;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .stat-card {
    padding: var(--spacing-4);
  }

  .account-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-1);
  }

  .aff-stats {
    flex-direction: column;
    gap: var(--spacing-3);
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
