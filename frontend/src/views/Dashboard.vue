<template>
  <div>
    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(0,179,138,0.1); color: #00b38a;">
          <n-icon :size="20"><PeopleOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboard?.account_count || 0 }}</div>
          <div class="stat-label">账号总数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(24,160,88,0.1); color: #18a058;">
          <n-icon :size="20"><CheckmarkCircleOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboard?.today_sign_success || 0 }}<span class="stat-sub">/{{ dashboard?.today_sign_count || 0 }}</span></div>
          <div class="stat-label">今日签到</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(240,160,32,0.1); color: #f0a020;">
          <n-icon :size="20"><WalletOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboard?.total_quota_display || '$0.00' }}</div>
          <div class="stat-label">总剩余额度</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(32,128,240,0.1); color: #2080f0;">
          <n-icon :size="20"><TrendingUpOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ formatNumber(dashboard?.total_request_count || 0) }}</div>
          <div class="stat-label">总请求数</div>
        </div>
      </div>
    </div>

    <!-- API 节点 -->
    <div class="api-endpoints-section">
      <div class="section-header">
        <h3 class="section-title">API 节点</h3>
        <n-button size="small" @click="handleSyncEndpoints" :loading="syncingEndpoints">
          <template #icon><n-icon><SyncOutline /></n-icon></template>
          同步节点
        </n-button>
      </div>
      <div class="endpoints-grid">
        <div v-for="ep in apiEndpoints" :key="ep.id" class="endpoint-card">
          <div class="endpoint-status" :class="ep.color"></div>
          <div class="endpoint-info">
            <div class="endpoint-name">{{ ep.route }}</div>
            <div class="endpoint-url">{{ ep.url }}</div>
          </div>
          <n-button size="tiny" quaternary @click="copyEndpoint(ep.url)">
            <template #icon><n-icon :size="14"><CopyOutline /></n-icon></template>
          </n-button>
        </div>
        <div v-if="apiEndpoints.length === 0" class="endpoints-empty">
          暂无节点，点击"同步节点"获取
        </div>
      </div>
    </div>

    <!-- 账号列表 -->
    <div class="account-section">
      <div class="section-header">
        <h3 class="section-title">账号管理</h3>
        <div class="section-actions">
          <n-button size="small" @click="handleBatchSign" :loading="batchSigning">
            <template #icon><n-icon><FlashOutline /></n-icon></template>
            批量签到
          </n-button>
          <n-button type="primary" size="small" @click="showAddModalVisible = true">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            添加账号
          </n-button>
        </div>
      </div>

      <n-spin :show="loading">
        <div class="account-table" v-if="accounts.length > 0">
          <div class="table-header">
            <div class="col-account">账号</div>
            <div class="col-status">状态</div>
            <div class="col-sign">最近签到</div>
            <div class="col-actions">操作</div>
          </div>
          <div class="table-body">
            <div v-for="account in accounts" :key="account.id" class="table-row">
              <div class="col-account">
                <div class="account-cell">
                  <div class="avatar" :class="{ disabled: !account.is_active }">
                    {{ (account.username || 'U')[0].toUpperCase() }}
                  </div>
                  <div class="account-info">
                    <div class="account-name">{{ account.username }}</div>
                    <div class="account-id">ID: {{ account.anyrouter_user_id }}</div>
                  </div>
                </div>
              </div>
              <div class="col-status">
                <span class="status-dot" :class="account.is_active ? 'active' : 'inactive'"></span>
                <span class="status-text">{{ account.is_active ? '正常' : '禁用' }}</span>
              </div>
              <div class="col-sign">
                <template v-if="account.last_sign">
                  <n-tag :type="account.last_sign.success ? 'success' : 'error'" size="small" :bordered="false">
                    {{ account.last_sign.success ? '成功' : '失败' }}
                  </n-tag>
                  <span class="sign-time">{{ formatTime(account.last_sign.time) }}</span>
                </template>
                <span v-else class="no-sign">未签到</span>
              </div>
              <div class="col-actions">
                <n-button
                  size="tiny"
                  type="primary"
                  @click="handleSign(account)"
                  :loading="signingId === account.id"
                  :disabled="!account.is_active"
                >
                  签到
                </n-button>
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary @click="showEditModalFn(account)">
                      <template #icon><n-icon><CreateOutline /></n-icon></template>
                    </n-button>
                  </template>
                  编辑
                </n-tooltip>
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary @click="showTokensModal(account)">
                      <template #icon><n-icon><KeyOutline /></n-icon></template>
                    </n-button>
                  </template>
                  API 令牌
                </n-tooltip>
                <n-tooltip trigger="hover">
                  <template #trigger>
                    <n-button size="tiny" quaternary @click="router.push(`/account/${account.id}`)">
                      <template #icon><n-icon><OpenOutline /></n-icon></template>
                    </n-button>
                  </template>
                  详情
                </n-tooltip>
                <n-popconfirm @positive-click="handleDelete(account.id)">
                  <template #trigger>
                    <n-tooltip trigger="hover">
                      <template #trigger>
                        <n-button size="tiny" quaternary class="delete-btn">
                          <template #icon><n-icon><TrashOutline /></n-icon></template>
                        </n-button>
                      </template>
                      删除
                    </n-tooltip>
                  </template>
                  确定删除此账号？
                </n-popconfirm>
              </div>
            </div>
          </div>
        </div>
        <n-empty v-else description="暂无账号" style="padding: 60px 0;">
          <template #extra>
            <n-button size="small" @click="showAddModalVisible = true">添加账号</n-button>
          </template>
        </n-empty>
      </n-spin>
    </div>

    <!-- 添加账号弹窗 -->
    <n-modal v-model:show="showAddModalVisible" :mask-closable="false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>添加账号</h3>
          <n-button text @click="showAddModalVisible = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>User ID</label>
            <n-input v-model:value="addForm.user_id" placeholder="请求头 new-api-user 的值" />
          </div>
          <div class="form-item">
            <label>Session Cookie</label>
            <n-input v-model:value="addForm.session_cookie" type="textarea" :rows="3" placeholder="Cookie 中 session 的值" />
          </div>
          <div class="form-tip">
            <n-icon><InformationCircleOutline /></n-icon>
            在浏览器 F12 开发者工具 Network 中获取
          </div>
        </div>
        <div class="modal-footer">
          <n-button @click="showAddModalVisible = false">取消</n-button>
          <n-button type="primary" @click="handleAdd" :loading="adding">验证并添加</n-button>
        </div>
      </div>
    </n-modal>

    <!-- 编辑账号弹窗 -->
    <n-modal v-model:show="showEditModalVisible" :mask-closable="false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>编辑账号</h3>
          <n-button text @click="showEditModalVisible = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>User ID</label>
            <n-input v-model:value="editForm.user_id" placeholder="留空则不修改" />
          </div>
          <div class="form-item">
            <label>Session Cookie</label>
            <n-input v-model:value="editForm.session_cookie" type="textarea" :rows="3" placeholder="留空则不修改" />
          </div>
          <div class="form-item">
            <label>账号状态</label>
            <n-switch v-model:value="editForm.is_active">
              <template #checked>启用</template>
              <template #unchecked>禁用</template>
            </n-switch>
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
          </div>
          <div class="form-tip" style="margin-top: 8px;">
            <n-icon><InformationCircleOutline /></n-icon>
            签到成功或失败后会通过选中的渠道发送通知
          </div>
        </div>
        <div class="modal-footer">
          <n-button @click="showEditModalVisible = false">取消</n-button>
          <n-button type="primary" @click="handleUpdate" :loading="updating">保存</n-button>
        </div>
      </div>
    </n-modal>

    <!-- API 令牌弹窗 -->
    <n-modal v-model:show="showTokensVisible" :mask-closable="false">
      <div class="modal-container tokens-modal">
        <div class="modal-header">
          <div class="modal-title-group">
            <div class="modal-icon">
              <n-icon :size="18"><KeyOutline /></n-icon>
            </div>
            <div>
              <h3>API 令牌</h3>
              <span class="modal-subtitle">{{ tokenAccount?.username }}</span>
            </div>
          </div>
          <n-button text @click="showTokensVisible = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body tokens-body">
          <div class="tokens-toolbar">
            <div class="tokens-stats">
              <span class="tokens-count">{{ tokens.length }}</span>
              <span class="tokens-label">个令牌</span>
            </div>
            <n-button size="small" secondary @click="handleSyncTokens" :loading="syncingTokens">
              <template #icon><n-icon><RefreshOutline /></n-icon></template>
              同步令牌
            </n-button>
          </div>
          <n-spin :show="loadingTokens">
            <div v-if="tokens.length > 0" class="tokens-list">
              <div v-for="token in tokens" :key="token.id" class="token-card">
                <div class="token-header">
                  <div class="token-name">{{ token.name || '未命名令牌' }}</div>
                  <div class="token-quota">
                    <span class="quota-used">已用 {{ formatQuota(token.used_quota) }}</span>
                    <n-tag v-if="token.unlimited_quota" size="tiny" :bordered="false" type="success">无限</n-tag>
                  </div>
                </div>
                <div v-if="token.model_limits" class="token-models">
                  <n-tag
                    v-for="model in parseModels(token.model_limits)"
                    :key="model"
                    size="tiny"
                    :bordered="false"
                  >
                    {{ model }}
                  </n-tag>
                </div>
                <div class="token-key-row">
                  <code class="token-key">sk-{{ token.key.slice(0, 8) }}...{{ token.key.slice(-4) }}</code>
                  <n-button size="tiny" quaternary @click="copyToken(token.key)">
                    <template #icon><n-icon :size="14"><CopyOutline /></n-icon></template>
                  </n-button>
                </div>
              </div>
            </div>
            <div v-else class="tokens-empty">
              <div class="empty-icon">
                <n-icon :size="40"><KeyOutline /></n-icon>
              </div>
              <div class="empty-text">暂无 API 令牌</div>
              <div class="empty-hint">点击"同步令牌"从服务器获取</div>
            </div>
          </n-spin>
        </div>
        <div class="modal-footer">
          <n-button @click="showTokensVisible = false">关闭</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  PeopleOutline, CheckmarkCircleOutline, WalletOutline, TrendingUpOutline,
  AddOutline, FlashOutline, CloseOutline, InformationCircleOutline,
  CreateOutline, OpenOutline, TrashOutline, KeyOutline, RefreshOutline, CopyOutline,
  SyncOutline
} from '@vicons/ionicons5'
import { accountApi, signApi, dashboardApi, notifyApi, apiEndpointsApi } from '../api'
import { formatQuota } from '../utils'

const router = useRouter()
const message = useMessage()

const loading = ref(false)
const accounts = ref<any[]>([])
const dashboard = ref<any>(null)
const signingId = ref<number | null>(null)
const batchSigning = ref(false)

// 推送渠道
const loadingChannels = ref(false)
const channelOptions = ref<{ label: string; value: number }[]>([])

// 添加账号
const showAddModalVisible = ref(false)
const adding = ref(false)
const addForm = ref({ session_cookie: '', user_id: '' })

// 编辑账号
const showEditModalVisible = ref(false)
const editingAccount = ref<any>(null)
const updating = ref(false)
const editForm = ref({
  user_id: '',
  session_cookie: '',
  is_active: true,
  notify_channel_ids: [] as number[]
})

// API 令牌
const showTokensVisible = ref(false)
const tokenAccount = ref<any>(null)
const tokens = ref<any[]>([])
const loadingTokens = ref(false)
const syncingTokens = ref(false)

// API 节点
const apiEndpoints = ref<any[]>([])
const syncingEndpoints = ref(false)

const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toLocaleString()
}

const formatTime = (time: string) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 172800000) return '昨天'

  return (date.getMonth() + 1) + '/' + date.getDate()
}

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

const handleAdd = async () => {
  if (!addForm.value.user_id.trim()) {
    message.warning('请输入 User ID')
    return
  }
  if (!addForm.value.session_cookie.trim()) {
    message.warning('请输入 Session Cookie')
    return
  }
  adding.value = true
  try {
    await accountApi.create({
      session_cookie: addForm.value.session_cookie,
      user_id: addForm.value.user_id
    })
    message.success('账号添加成功')
    showAddModalVisible.value = false
    addForm.value = { session_cookie: '', user_id: '' }
    loadData()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    adding.value = false
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

const showEditModalFn = async (account: any) => {
  editingAccount.value = account
  editForm.value = {
    user_id: '',
    session_cookie: '',
    is_active: account.is_active,
    notify_channel_ids: []
  }
  showEditModalVisible.value = true

  // 加载账号的推送配置
  try {
    const res = await notifyApi.getAccountNotify(account.id)
    const enabledChannels = (res.data || []).filter((c: any) => c.is_enabled)
    editForm.value.notify_channel_ids = enabledChannels.map((c: any) => c.channel_id)
  } catch (e: any) {
    console.error('Failed to load account notify:', e)
  }
}

const handleUpdate = async () => {
  if (!editingAccount.value) return
  updating.value = true
  try {
    const data: any = { is_active: editForm.value.is_active }
    if (editForm.value.user_id.trim()) data.user_id = editForm.value.user_id.trim()
    if (editForm.value.session_cookie.trim()) data.session_cookie = editForm.value.session_cookie.trim()

    await accountApi.update(editingAccount.value.id, data)

    // 保存推送配置
    const notifyData = {
      channels: editForm.value.notify_channel_ids.map(id => ({
        channel_id: id,
        is_enabled: true,
        notify_config: {}
      }))
    }
    await notifyApi.updateAccountNotify(editingAccount.value.id, notifyData)

    message.success('更新成功')
    showEditModalVisible.value = false
    loadData()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    updating.value = false
  }
}

const handleSign = async (account: any) => {
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

const handleDelete = async (id: number) => {
  try {
    await accountApi.delete(id)
    message.success('删除成功')
    loadData()
  } catch (e: any) {
    message.error(e.message)
  }
}

const showTokensModal = async (account: any) => {
  tokenAccount.value = account
  tokens.value = []
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

const copyToken = (key: string) => {
  const fullKey = `sk-${key}`
  navigator.clipboard.writeText(fullKey).then(() => {
    message.success('已复制到剪贴板')
  }).catch(() => {
    message.error('复制失败')
  })
}

const parseModels = (modelLimits: string): string[] => {
  if (!modelLimits) return []
  return modelLimits.split(',').map(m => m.trim()).filter(m => m)
}

const loadEndpoints = async () => {
  try {
    const res = await apiEndpointsApi.getList()
    apiEndpoints.value = res.data || []
  } catch (e: any) {
    console.error('Failed to load endpoints:', e)
  }
}

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

const copyEndpoint = (url: string) => {
  navigator.clipboard.writeText(url).then(() => {
    message.success('已复制')
  }).catch(() => {
    message.error('复制失败')
  })
}

onMounted(() => {
  loadData()
  loadChannels()
  loadEndpoints()
})
</script>

<style scoped>
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
}

.stat-sub {
  font-size: 14px;
  font-weight: 400;
  color: #999;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

/* API 节点 */
.api-endpoints-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  margin-bottom: 24px;
}

.endpoints-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  padding: 16px;
}

.endpoint-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #f8f9fa;
  border: 1px solid #eee;
  border-radius: 8px;
  transition: all 0.2s;
}

.endpoint-card:hover {
  border-color: #ddd;
  box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}

.endpoint-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.endpoint-status.green { background: #18a058; }
.endpoint-status.blue { background: #2080f0; }
.endpoint-status.yellow { background: #f0a020; }
.endpoint-status.red { background: #d03050; }

.endpoint-info {
  flex: 1;
  min-width: 0;
}

.endpoint-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.endpoint-url {
  font-size: 11px;
  color: #999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.endpoints-empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 24px;
  color: #999;
  font-size: 13px;
}

.account-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.account-table {
  width: 100%;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 100px 160px 180px;
  padding: 12px 20px;
  background: #fafafa;
  font-size: 12px;
  font-weight: 500;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-body {
  padding: 0;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 100px 160px 180px;
  padding: 14px 20px;
  align-items: center;
  border-bottom: 1px solid #f5f5f5;
  transition: background 0.15s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: #fafafa;
}

.account-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, #00b38a, #00d4a0);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.avatar.disabled {
  background: linear-gradient(135deg, #aaa, #ccc);
}

.account-info {
  min-width: 0;
}

.account-name {
  font-weight: 600;
  font-size: 14px;
  color: #1a1a2e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.account-id {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.col-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot.active {
  background: #00b38a;
}

.status-dot.inactive {
  background: #ccc;
}

.status-text {
  font-size: 13px;
  color: #666;
}

.col-sign {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sign-time {
  font-size: 12px;
  color: #999;
}

.no-sign {
  font-size: 13px;
  color: #ccc;
}

.col-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: flex-end;
}

.col-actions .delete-btn:hover {
  color: #e88080;
}

/* Modal */
.modal-container {
  width: 440px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.modal-body {
  padding: 20px;
}

.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #999;
  margin-top: 16px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

/* Tokens Modal */
.tokens-modal {
  width: 680px;
}

.modal-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-subtitle {
  font-size: 12px;
  color: #999;
}

.tokens-body {
  padding: 0;
}

.tokens-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.tokens-stats {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.tokens-stats .tokens-count {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
}

.tokens-stats .tokens-label {
  font-size: 13px;
  color: #999;
}

.tokens-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  max-height: 420px;
  overflow-y: auto;
  padding: 12px;
}

.token-card {
  background: #f8f9fa;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s;
}

.token-card:hover {
  border-color: #ddd;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.token-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.token-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.token-quota {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.quota-used {
  font-size: 11px;
  color: #999;
}

.token-models {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 8px;
  max-height: 48px;
  overflow-y: auto;
}

.token-models::-webkit-scrollbar {
  width: 3px;
}

.token-models::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 2px;
}

.token-models .n-tag {
  background: #e8f4f8;
  color: #0d7377;
  font-size: 10px;
  padding: 0 6px;
  height: 18px;
}

.token-key-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 4px 4px 4px 8px;
}

.token-key {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 11px;
  color: #666;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tokens-empty {
  text-align: center;
  padding: 48px 20px;
}

.empty-icon {
  color: #ddd;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 15px;
  font-weight: 500;
  color: #999;
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 13px;
  color: #bbb;
}

@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .table-header,
  .table-row {
    grid-template-columns: 1fr 80px 120px 140px;
  }
}
</style>
