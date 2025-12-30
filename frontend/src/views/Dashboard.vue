<template>
  <div>
    <!-- 统计卡片骨架屏 -->
    <div class="stats-row" v-if="loading && !dashboard">
      <div class="stat-card skeleton-card" v-for="i in 4" :key="i">
        <n-skeleton circle :width="48" :height="48" />
        <div class="stat-content">
          <n-skeleton text :width="80" :height="28" style="margin-bottom: 8px;" />
          <n-skeleton text :width="60" :height="16" />
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row" v-else>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(0,179,138,0.1); color: #00b38a;">
          <n-icon :size="20"><PeopleOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboard?.account_count || 0 }}</div>
          <div class="stat-label">账号总数</div>
        </div>
        <div class="stat-badge warning" v-if="dashboard?.unhealthy_account_count > 0">
          {{ dashboard.unhealthy_account_count }} 异常
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
        <div class="stat-badge success" v-if="dashboard?.success_rate">
          {{ dashboard.success_rate }}%
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(240,160,32,0.1); color: #f0a020;">
          <n-icon :size="20"><GiftOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboard?.month_reward_display || '$0.00' }}</div>
          <div class="stat-label">本月奖励</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: rgba(32,128,240,0.1); color: #2080f0;">
          <n-icon :size="20"><WalletOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ dashboard?.total_quota_display || '$0.00' }}</div>
          <div class="stat-label">总剩余额度</div>
        </div>
      </div>
    </div>

    <!-- 7天签到趋势 -->
    <div class="trend-section" v-if="dashboard?.daily_trend?.length > 0">
      <div class="section-header">
        <h3 class="section-title">近7天签到趋势</h3>
        <div class="trend-legend">
          <span class="legend-item"><span class="dot success"></span>成功</span>
          <span class="legend-item"><span class="dot fail"></span>失败</span>
        </div>
      </div>
      <div ref="trendChartRef" class="trend-chart-container"></div>
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
        <div class="section-title-row">
          <h3 class="section-title">账号管理</h3>
          <n-select
            v-model:value="selectedGroupId"
            :options="groupOptions"
            size="small"
            style="width: 140px; margin-left: 12px;"
            :consistent-menu-width="false"
          />
        </div>
        <div class="section-actions">
          <n-button size="small" @click="handleHealthCheckAll" :loading="healthChecking">
            <template #icon><n-icon><PulseOutline /></n-icon></template>
            健康检查
          </n-button>
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

      <!-- 账号列表骨架屏 -->
      <template v-if="loading && accounts.length === 0">
        <div class="skeleton-table">
          <div class="skeleton-row" v-for="i in 5" :key="i">
            <n-skeleton text :width="100" />
            <n-skeleton text :width="80" />
            <n-skeleton text :width="60" />
            <n-skeleton text :width="120" />
            <n-skeleton text :width="100" />
          </div>
        </div>
      </template>

      <!-- 账号表格 -->
      <template v-else>
        <n-data-table
          v-if="filteredAccounts.length > 0"
          :columns="accountColumns"
          :data="filteredAccounts"
          :pagination="accountPagination"
          :row-key="(row: any) => row.id"
        />
        <n-empty v-else description="暂无账号" style="padding: 60px 0;">
          <template #extra>
            <n-button size="small" @click="showAddModalVisible = true">添加账号</n-button>
          </template>
        </n-empty>
      </template>
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
            <label>User ID <span class="required">*</span></label>
            <n-input v-model:value="addForm.user_id" placeholder="请求头 new-api-user 的值" />
          </div>
          <div class="form-item">
            <label>Session Cookie <span class="required">*</span></label>
            <n-input v-model:value="addForm.session_cookie" type="textarea" :rows="3" placeholder="Cookie 中 session 的值" />
          </div>
          <div class="form-item">
            <label>分组（可选）</label>
            <n-select
              v-model:value="addForm.group_id"
              :options="groups.map(g => ({ label: g.name, value: g.id }))"
              placeholder="选择分组"
              clearable
            />
          </div>
          <div class="form-item">
            <label>签到推送渠道（可选）</label>
            <n-select
              v-model:value="addForm.notify_channel_ids"
              multiple
              :options="channelOptions"
              placeholder="选择推送渠道（可多选）"
              clearable
              :loading="loadingChannels"
            />
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
          <div class="form-item">
            <label>所属分组</label>
            <n-select
              v-model:value="editForm.group_id"
              :options="groups.map(g => ({ label: g.name, value: g.id }))"
              placeholder="选择分组"
              clearable
            />
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
            <div class="tokens-actions">
              <n-button size="small" type="primary" @click="showAddTokenDrawer = true">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                添加令牌
              </n-button>
              <n-button size="small" secondary @click="handleSyncTokens" :loading="syncingTokens">
                <template #icon><n-icon><RefreshOutline /></n-icon></template>
                同步令牌
              </n-button>
            </div>
          </div>
          <n-spin :show="loadingTokens">
            <div v-if="tokens.length > 0" class="tokens-list">
              <div v-for="token in tokens" :key="token.id" class="token-card">
                <div class="token-header">
                  <div class="token-name">{{ token.name || '未命名令牌' }}</div>
                  <div class="token-quota">
                    <span class="quota-used">已用 {{ formatQuota(token.used_quota) }}</span>
                    <n-tag v-if="token.unlimited_quota" size="tiny" :bordered="false" type="success">无限</n-tag>
                    <n-tag v-else size="tiny" :bordered="false" type="info">{{ formatQuota(token.used_quota + token.remain_quota) }}</n-tag>
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
                  <div class="token-actions">
                    <n-button size="tiny" quaternary @click="copyToken(token.key)">
                      <template #icon><n-icon :size="14"><CopyOutline /></n-icon></template>
                    </n-button>
                    <n-button size="tiny" quaternary @click="handleEditToken(token)">
                      <template #icon><n-icon :size="14"><CreateOutline /></n-icon></template>
                    </n-button>
                    <n-popconfirm @positive-click="handleDeleteToken(token)">
                      <template #trigger>
                        <n-button size="tiny" quaternary :loading="deletingTokenId === token.token_id" style="color: #d03050;">
                          <template #icon><n-icon :size="14"><TrashOutline /></n-icon></template>
                        </n-button>
                      </template>
                      确定删除该令牌吗？
                    </n-popconfirm>
                  </div>
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

    <!-- 添加/编辑令牌抽屉 -->
    <n-drawer v-model:show="showAddTokenDrawer" :width="400" placement="right">
      <n-drawer-content :title="editingToken ? '编辑令牌' : '添加令牌'" closable>
        <div class="token-form">
          <div class="form-item">
            <label>令牌名称 <span class="required">*</span></label>
            <n-input v-model:value="tokenForm.name" placeholder="请输入令牌名称" />
          </div>
          <div class="form-item">
            <label>额度设置</label>
            <n-switch v-model:value="tokenForm.unlimited_quota">
              <template #checked>无限额度</template>
              <template #unchecked>限制额度</template>
            </n-switch>
          </div>
          <div class="form-item" v-if="!tokenForm.unlimited_quota">
            <label>剩余额度</label>
            <n-input-number v-model:value="tokenForm.remain_quota" :min="0" :step="100000" style="width: 100%;">
              <template #suffix>（约 ${{ (tokenForm.remain_quota / 500000).toFixed(2) }}）</template>
            </n-input-number>
          </div>
          <div class="form-item">
            <label>过期时间</label>
            <n-select
              v-model:value="tokenForm.expired_time"
              :options="expireOptions"
              placeholder="选择过期时间"
            />
          </div>
          <div class="form-item">
            <label>模型限制</label>
            <n-switch v-model:value="tokenForm.model_limits_enabled">
              <template #checked>启用限制</template>
              <template #unchecked>不限制</template>
            </n-switch>
          </div>
          <div class="form-item" v-if="tokenForm.model_limits_enabled">
            <label>可用模型</label>
            <n-select
              v-model:value="tokenForm.model_limits_array"
              multiple
              filterable
              :options="availableModelOptions"
              :loading="loadingModels"
              placeholder="选择可用模型"
            />
          </div>
          <div class="form-item">
            <label>分组</label>
            <n-select
              v-model:value="tokenForm.group"
              :options="tokenGroupOptions"
              :loading="loadingTokenGroups"
              placeholder="选择分组"
            />
          </div>
          <div class="form-item">
            <label>IP 白名单（可选）</label>
            <n-input v-model:value="tokenForm.allow_ips" placeholder="留空表示不限制，多个 IP 用逗号分隔" />
          </div>
        </div>
        <template #footer>
          <div class="drawer-footer">
            <n-button @click="showAddTokenDrawer = false">取消</n-button>
            <n-button type="primary" @click="handleSaveToken" :loading="creatingToken">
              {{ editingToken ? '保存修改' : '创建令牌' }}
            </n-button>
          </div>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, watch, h, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, NTag, NButton, NIcon, NPopconfirm, NSpace, NTooltip, NDrawer, NDrawerContent, NInputNumber } from 'naive-ui'
import {
  PeopleOutline, CheckmarkCircleOutline, WalletOutline, GiftOutline,
  AddOutline, FlashOutline, CloseOutline, InformationCircleOutline,
  CreateOutline, OpenOutline, TrashOutline, KeyOutline, RefreshOutline, CopyOutline,
  SyncOutline, PulseOutline
} from '@vicons/ionicons5'
import { accountApi, signApi, dashboardApi, notifyApi, apiEndpointsApi, groupsApi } from '../api'
import { formatQuota, copyToClipboard } from '../utils'
import * as echarts from 'echarts'

const router = useRouter()
const message = useMessage()

const loading = ref(false)
const accounts = ref<any[]>([])
const dashboard = ref<any>(null)
const signingId = ref<number | null>(null)
const batchSigning = ref(false)

// ECharts 实例
const trendChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null

// 检测深色模式
const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
const handleThemeChange = (e: MediaQueryListEvent) => {
  isDarkMode.value = e.matches
  updateTrendChart()
}

// 获取图表主题配置
const getChartTheme = () => {
  return isDarkMode.value ? {
    backgroundColor: 'transparent',
    textColor: 'rgba(255, 255, 255, 0.85)',
    axisLineColor: 'rgba(255, 255, 255, 0.15)',
    splitLineColor: 'rgba(255, 255, 255, 0.08)',
    tooltipBg: 'rgba(30, 30, 46, 0.95)',
    tooltipBorder: 'rgba(255, 255, 255, 0.1)',
    successColor: '#00d4a0',
    failColor: '#ff6b6b'
  } : {
    backgroundColor: 'transparent',
    textColor: 'rgba(0, 0, 0, 0.65)',
    axisLineColor: 'rgba(0, 0, 0, 0.15)',
    splitLineColor: 'rgba(0, 0, 0, 0.06)',
    tooltipBg: 'rgba(255, 255, 255, 0.98)',
    tooltipBorder: 'rgba(0, 0, 0, 0.08)',
    successColor: '#00b38a',
    failColor: '#ee5a5a'
  }
}

// 推送渠道
const loadingChannels = ref(false)
const channelOptions = ref<{ label: string; value: number }[]>([])

// 添加账号
const showAddModalVisible = ref(false)
const adding = ref(false)
const addForm = ref({ session_cookie: '', user_id: '', group_id: null as number | null, notify_channel_ids: [] as number[] })

// 编辑账号
const showEditModalVisible = ref(false)
const editingAccount = ref<any>(null)
const updating = ref(false)
const editForm = ref({
  user_id: '',
  session_cookie: '',
  is_active: true,
  notify_channel_ids: [] as number[],
  group_id: null as number | null
})

// API 令牌
const showTokensVisible = ref(false)
const tokenAccount = ref<any>(null)
const tokens = ref<any[]>([])
const loadingTokens = ref(false)
const syncingTokens = ref(false)
const deletingTokenId = ref<number | null>(null)

// 添加令牌
const showAddTokenDrawer = ref(false)
const creatingToken = ref(false)
const editingToken = ref<any>(null)  // 编辑时存储原始令牌数据
const loadingModels = ref(false)
const loadingTokenGroups = ref(false)
const availableModelOptions = ref<{ label: string; value: string }[]>([])
const tokenGroupOptions = ref<{ label: string; value: string }[]>([])
const tokenForm = ref({
  name: '',
  remain_quota: 500000,
  expired_time: -1,
  unlimited_quota: false,
  model_limits_enabled: false,
  model_limits_array: [] as string[],
  group: 'default',
  allow_ips: ''
})
const expireOptions = [
  { label: '永不过期', value: -1 },
  { label: '1 小时', value: 1 },
  { label: '1 天', value: 24 },
  { label: '7 天', value: 24 * 7 },
  { label: '30 天', value: 24 * 30 },
  { label: '90 天', value: 24 * 90 },
  { label: '365 天', value: 24 * 365 }
]

// API 节点
const apiEndpoints = ref<any[]>([])
const syncingEndpoints = ref(false)

// 健康检查
const healthChecking = ref(false)
const healthCheckingId = ref<number | null>(null)

// 分组
const groups = ref<any[]>([])
const selectedGroupId = ref<number | null>(null)
const groupOptions = ref<{ label: string; value: number | null }[]>([{ label: '全部分组', value: null }])

// 根据分组筛选账号
const filteredAccounts = computed(() => {
  if (selectedGroupId.value === null) {
    return accounts.value
  }
  return accounts.value.filter(a => a.group_id === selectedGroupId.value)
})

// 监听分组变化，重置页码
watch(selectedGroupId, () => {
  accountPagination.page = 1
})

// 账号表格分页配置
const accountPagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    accountPagination.page = page
  },
  onUpdatePageSize: (pageSize: number) => {
    accountPagination.pageSize = pageSize
    accountPagination.page = 1
  }
})

// 账号表格列定义
const accountColumns = [
  {
    title: '账号',
    key: 'username',
    render: (row: any) => {
      return h('div', { style: 'display: flex; align-items: center; gap: 10px;' }, [
        h('div', {
          style: `width: 32px; height: 32px; border-radius: 6px; background: ${row.is_active ? 'linear-gradient(135deg, #00b38a, #00d4a0)' : 'linear-gradient(135deg, #aaa, #ccc)'}; color: white; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 12px; flex-shrink: 0;`
        }, (row.username || 'U')[0].toUpperCase()),
        h('div', { style: 'min-width: 0;' }, [
          h('div', { style: 'display: flex; align-items: center; gap: 6px;' }, [
            h('span', { style: 'font-weight: 600; font-size: 13px; color: var(--text-primary);' }, row.username || '-'),
            row.group ? h(NTag, { size: 'tiny', bordered: false, style: `background: ${getGroupColor(row.group.color)}; color: #fff;` }, { default: () => row.group.name }) : null
          ]),
          h('div', { style: 'font-size: 11px; color: var(--text-tertiary); margin-top: 2px;' }, `ID: ${row.anyrouter_user_id || '-'}`)
        ])
      ])
    }
  },
  {
    title: '剩余额度',
    key: 'quota_display',
    render: (row: any) => h('span', { style: 'font-weight: 500; color: #18a058;' }, row.quota_display || '$0.00')
  },
  {
    title: '剩余比例',
    key: 'quota_percent',
    render: (row: any) => h('span', { style: 'color: var(--text-secondary);' }, row.quota_percent || '0.00%')
  },
  {
    title: '健康',
    key: 'health_status',
    width: 80,
    render: (row: any) => h(NTag, {
      type: getHealthStatusType(row.health_status),
      size: 'small',
      bordered: false
    }, { default: () => getHealthStatusText(row.health_status) })
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row: any) => h('div', { style: 'display: flex; align-items: center; gap: 4px;' }, [
      h('span', { style: `width: 6px; height: 6px; border-radius: 50%; background: ${row.is_active ? '#00b38a' : 'var(--text-tertiary)'};` }),
      h('span', { style: 'font-size: 12px; color: var(--text-secondary);' }, row.is_active ? '启用' : '禁用')
    ])
  },
  {
    title: '最近签到',
    key: 'last_sign',
    render: (row: any) => {
      if (!row.last_sign) {
        return h('span', { style: 'color: var(--text-tertiary); font-size: 12px;' }, '暂无')
      }
      return h('div', { style: 'display: flex; align-items: center; gap: 6px;' }, [
        h(NTag, { type: row.last_sign.success ? 'success' : 'error', size: 'tiny', bordered: false }, { default: () => row.last_sign.success ? '成功' : '失败' }),
        h('span', { style: 'font-size: 11px; color: var(--text-tertiary);' }, formatTime(row.last_sign.time))
      ])
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right' as const,
    render: (row: any) => {
      return h(NSpace, { size: 4 }, {
        default: () => [
          h(NTooltip, {}, {
            trigger: () => h(NButton, {
              size: 'tiny',
              quaternary: true,
              loading: signingId.value === row.id,
              onClick: () => handleSign(row)
            }, { icon: () => h(NIcon, {}, { default: () => h(FlashOutline) }) }),
            default: () => '签到'
          }),
          h(NTooltip, {}, {
            trigger: () => h(NButton, {
              size: 'tiny',
              quaternary: true,
              loading: healthCheckingId.value === row.id,
              onClick: () => handleHealthCheck(row)
            }, { icon: () => h(NIcon, {}, { default: () => h(PulseOutline) }) }),
            default: () => '健康检查'
          }),
          h(NTooltip, {}, {
            trigger: () => h(NButton, {
              size: 'tiny',
              quaternary: true,
              onClick: () => showEditModalFn(row)
            }, { icon: () => h(NIcon, {}, { default: () => h(CreateOutline) }) }),
            default: () => '编辑'
          }),
          h(NTooltip, {}, {
            trigger: () => h(NButton, {
              size: 'tiny',
              quaternary: true,
              onClick: () => showTokensModal(row)
            }, { icon: () => h(NIcon, {}, { default: () => h(KeyOutline) }) }),
            default: () => 'API令牌'
          }),
          h(NTooltip, {}, {
            trigger: () => h(NButton, {
              size: 'tiny',
              quaternary: true,
              onClick: () => router.push(`/account/${row.id}`)
            }, { icon: () => h(NIcon, {}, { default: () => h(OpenOutline) }) }),
            default: () => '详情'
          }),
          h(NPopconfirm, {
            onPositiveClick: () => handleDelete(row.id)
          }, {
            trigger: () => h(NButton, {
              size: 'tiny',
              quaternary: true,
              style: 'color: #d03050;'
            }, { icon: () => h(NIcon, {}, { default: () => h(TrashOutline) }) }),
            default: () => '确定删除该账号吗？'
          })
        ]
      })
    }
  }
]

// 初始化签到趋势图表
const initTrendChart = () => {
  if (!trendChartRef.value) return

  trendChart = echarts.init(trendChartRef.value)
  updateTrendChart()

  window.addEventListener('resize', handleResize)
}

// 更新签到趋势图表
const updateTrendChart = () => {
  if (!trendChart || !dashboard.value?.daily_trend) return

  const theme = getChartTheme()
  const data = dashboard.value.daily_trend

  const option: echarts.EChartsOption = {
    backgroundColor: theme.backgroundColor,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      borderWidth: 1,
      padding: [10, 14],
      textStyle: {
        color: isDarkMode.value ? '#fff' : '#333',
        fontSize: 12
      },
      formatter: (params: any) => {
        const date = params[0]?.axisValue || ''
        let html = `<div style="font-weight: 600; margin-bottom: 6px;">${date}</div>`

        params.forEach((item: any) => {
          const color = item.seriesName === '成功' ? theme.successColor : theme.failColor
          html += `<div style="display: flex; align-items: center; gap: 8px; margin: 3px 0;">
            <span style="width: 8px; height: 8px; border-radius: 2px; background: ${color};"></span>
            <span>${item.seriesName}: <b>${item.value}</b></span>
          </div>`
        })

        return html
      }
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '12%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map((d: any) => d.date),
      axisLine: {
        lineStyle: {
          color: theme.axisLineColor
        }
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: theme.textColor,
        fontSize: 10,
        formatter: (value: string) => {
          const parts = value.split('-')
          return parts.length >= 3 ? `${parts[1]}/${parts[2]}` : value
        }
      }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: theme.textColor,
        fontSize: 10
      },
      splitLine: {
        lineStyle: {
          color: theme.splitLineColor,
          type: 'dashed'
        }
      }
    },
    series: [
      {
        name: '成功',
        type: 'bar',
        stack: 'total',
        barWidth: '50%',
        barMaxWidth: 24,
        data: data.map((d: any) => d.success),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#00d4a0' },
            { offset: 1, color: theme.successColor }
          ]),
          borderRadius: [0, 0, 0, 0]
        }
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        barWidth: '50%',
        barMaxWidth: 24,
        data: data.map((d: any) => d.fail),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ff8080' },
            { offset: 1, color: theme.failColor }
          ]),
          borderRadius: [3, 3, 0, 0]
        }
      }
    ]
  }

  trendChart.setOption(option)
}

// 处理窗口大小变化
const handleResize = () => {
  trendChart?.resize()
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
    const res = await accountApi.create({
      session_cookie: addForm.value.session_cookie,
      user_id: addForm.value.user_id,
      group_id: addForm.value.group_id || undefined
    })

    // 如果选择了通知渠道，保存配置
    if (addForm.value.notify_channel_ids.length > 0 && res.data?.id) {
      const notifyData = {
        channels: addForm.value.notify_channel_ids.map(id => ({
          channel_id: id,
          is_enabled: true,
          notify_config: {}
        }))
      }
      await notifyApi.updateAccountNotify(res.data.id, notifyData)
    }

    message.success('账号添加成功')
    showAddModalVisible.value = false
    addForm.value = { session_cookie: '', user_id: '', group_id: null, notify_channel_ids: [] }
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

const loadGroups = async () => {
  try {
    const res = await groupsApi.getList()
    groups.value = res.data || []
    groupOptions.value = [
      { label: '全部分组', value: null },
      ...groups.value.map((g: any) => ({ label: g.name, value: g.id }))
    ]
  } catch (e: any) {
    console.error('Failed to load groups:', e)
  }
}

const showEditModalFn = async (account: any) => {
  editingAccount.value = account
  editForm.value = {
    user_id: '',
    session_cookie: '',
    is_active: account.is_active,
    notify_channel_ids: [],
    group_id: account.group_id || null
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
    // 分组 ID (0 表示移除分组)
    if (editForm.value.group_id !== editingAccount.value.group_id) {
      data.group_id = editForm.value.group_id || 0
    }

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

const handleDeleteToken = async (token: any) => {
  if (!tokenAccount.value) return
  deletingTokenId.value = token.token_id
  try {
    await accountApi.deleteToken(tokenAccount.value.id, token.token_id)
    message.success('删除成功')
    // 刷新令牌列表
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
  } catch (e: any) {
    message.error(e.message)
  } finally {
    deletingTokenId.value = null
  }
}

// 加载可用模型列表
const loadAvailableModels = async () => {
  if (!tokenAccount.value) return
  loadingModels.value = true
  try {
    const res = await accountApi.getAvailableModels(tokenAccount.value.id)
    const models = res.data || []
    availableModelOptions.value = models.map((m: string) => ({ label: m, value: m }))
  } catch (e: any) {
    console.error('Failed to load models:', e)
  } finally {
    loadingModels.value = false
  }
}

// 加载令牌分组
const loadTokenGroups = async () => {
  if (!tokenAccount.value) return
  loadingTokenGroups.value = true
  try {
    const res = await accountApi.getAccountGroups(tokenAccount.value.id)
    const groupsData = res.data || {}
    tokenGroupOptions.value = Object.entries(groupsData).map(([key, val]: [string, any]) => ({
      label: `${key} - ${val.desc || ''}`,
      value: key
    }))
  } catch (e: any) {
    console.error('Failed to load token groups:', e)
  } finally {
    loadingTokenGroups.value = false
  }
}

// 重置令牌表单
const resetTokenForm = () => {
  editingToken.value = null
  tokenForm.value = {
    name: '',
    remain_quota: 500000,
    expired_time: -1,
    unlimited_quota: false,
    model_limits_enabled: false,
    model_limits_array: [],
    group: 'default',
    allow_ips: ''
  }
}

// 编辑令牌
const handleEditToken = (token: any) => {
  editingToken.value = token
  tokenForm.value = {
    name: token.name || '',
    remain_quota: token.remain_quota || 500000,
    expired_time: token.expired_time ?? -1,
    unlimited_quota: token.unlimited_quota || false,
    model_limits_enabled: token.model_limits_enabled || false,
    model_limits_array: token.model_limits ? token.model_limits.split(',').filter((m: string) => m.trim()) : [],
    group: token.group || 'default',
    allow_ips: token.allow_ips || ''
  }
  showAddTokenDrawer.value = true
}

// 保存令牌（创建或更新）
const handleSaveToken = async () => {
  if (!tokenAccount.value) return
  if (!tokenForm.value.name.trim()) {
    message.warning('请输入令牌名称')
    return
  }
  creatingToken.value = true
  try {
    const formData = {
      name: tokenForm.value.name,
      remain_quota: tokenForm.value.remain_quota,
      expired_time: tokenForm.value.expired_time,
      unlimited_quota: tokenForm.value.unlimited_quota,
      model_limits_enabled: tokenForm.value.model_limits_enabled,
      model_limits: tokenForm.value.model_limits_array.join(','),
      allow_ips: tokenForm.value.allow_ips,
      group: tokenForm.value.group
    }

    if (editingToken.value) {
      // 编辑模式：合并原始数据
      const updateData = {
        ...editingToken.value,
        ...formData
      }
      await accountApi.updateToken(tokenAccount.value.id, editingToken.value.token_id, updateData)
      message.success('令牌更新成功')
    } else {
      // 创建模式
      await accountApi.createToken(tokenAccount.value.id, formData)
      message.success('令牌创建成功')
    }

    showAddTokenDrawer.value = false
    resetTokenForm()
    // 刷新令牌列表
    const res = await accountApi.getTokens(tokenAccount.value.id)
    tokens.value = res.data || []
  } catch (e: any) {
    message.error(e.message)
    // 编辑模式下刷新列表（可能远程已删除导致本地被同步清理）
    if (editingToken.value && tokenAccount.value) {
      const res = await accountApi.getTokens(tokenAccount.value.id)
      tokens.value = res.data || []
      // 如果是远程不存在的错误，关闭抽屉
      if (e.message.includes('不存在')) {
        showAddTokenDrawer.value = false
        resetTokenForm()
      }
    }
  } finally {
    creatingToken.value = false
  }
}

// 监听抽屉打开，加载模型和分组数据
watch(showAddTokenDrawer, (val) => {
  if (val) {
    // 编辑模式下不重置表单（handleEditToken 已设置）
    if (!editingToken.value) {
      resetTokenForm()
    }
    loadAvailableModels()
    loadTokenGroups()
  }
})

const copyToken = (key: string) => {
  const fullKey = `sk-${key}`
  copyToClipboard(fullKey).then(() => {
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
  copyToClipboard(url).then(() => {
    message.success('已复制')
  }).catch(() => {
    message.error('复制失败')
  })
}

// 健康检查
const handleHealthCheck = async (account: any) => {
  healthCheckingId.value = account.id
  try {
    const res = await accountApi.healthCheck(account.id)
    const status = res.data?.health_status
    if (status === 'healthy') {
      message.success('账号状态正常')
    } else {
      message.warning(`账号异常: ${res.data?.health_message || '凭证验证失败'}`)
    }
    loadData()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    healthCheckingId.value = null
  }
}

const handleHealthCheckAll = async () => {
  healthChecking.value = true
  try {
    const res = await accountApi.healthCheckAll()
    const { healthy_count, unhealthy_count } = res.data
    if (unhealthy_count > 0) {
      message.warning(`健康检查完成: ${healthy_count} 个正常, ${unhealthy_count} 个异常`)
    } else {
      message.success(`健康检查完成: 所有 ${healthy_count} 个账号正常`)
    }
    loadData()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    healthChecking.value = false
  }
}

const getHealthStatusType = (status: string) => {
  if (status === 'healthy') return 'success'
  if (status === 'unhealthy') return 'error'
  return 'default'
}

const getHealthStatusText = (status: string) => {
  if (status === 'healthy') return '正常'
  if (status === 'unhealthy') return '异常'
  return '未知'
}

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

// 监听 dashboard 数据变化，初始化/更新图表
watch(() => dashboard.value?.daily_trend, (newVal) => {
  if (newVal && newVal.length > 0) {
    nextTick(() => {
      if (!trendChart) {
        initTrendChart()
      } else {
        updateTrendChart()
      }
    })
  }
}, { deep: true })

onMounted(() => {
  // 监听主题变化
  mediaQuery.addEventListener('change', handleThemeChange)

  loadData()
  loadChannels()
  loadEndpoints()
  loadGroups()
})

onUnmounted(() => {
  // 清理事件监听
  mediaQuery.removeEventListener('change', handleThemeChange)
  window.removeEventListener('resize', handleResize)

  // 销毁图表实例
  trendChart?.dispose()
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
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  position: relative;
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
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-sub {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-tertiary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.stat-badge {
  position: absolute;
  top: 10px;
  right: 12px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.stat-badge.warning {
  background: rgba(208,48,80,0.1);
  color: #d03050;
}

.stat-badge.success {
  background: rgba(24,160,88,0.1);
  color: #18a058;
}

/* 签到趋势 */
.trend-section {
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 24px;
  padding: 16px 20px;
}

.trend-legend {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-item .dot.success { background: #18a058; }
.legend-item .dot.fail { background: #d03050; }

/* ECharts 图表容器 */
.trend-chart-container {
  width: 100%;
  height: 100px;
  margin-top: 12px;
}

/* API 节点 */
.api-endpoints-section {
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
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
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.2s;
}

.endpoint-card:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-sm);
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
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.endpoint-url {
  font-size: 11px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.endpoints-empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 24px;
  color: var(--text-tertiary);
  font-size: 13px;
}

.account-section {
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.section-title-row {
  display: flex;
  align-items: center;
}

.section-actions {
  display: flex;
  gap: 8px;
}

/* Modal */
.modal-container {
  width: 440px;
  background: var(--bg-modal);
  border-radius: 12px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.modal-body {
  padding: 20px;
}

/* 骨架屏样式 */
.skeleton-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.skeleton-table {
  background: var(--bg-card);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid var(--border-color);
}

.skeleton-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-color-light);
}

.skeleton-row:last-child {
  border-bottom: none;
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
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.form-item label .required {
  color: #d03050;
  margin-left: 2px;
}

.form-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-card-hover);
  border-radius: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-card-hover);
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
  color: var(--text-tertiary);
}

.tokens-body {
  padding: 0;
}

.tokens-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--bg-card-hover);
  border-bottom: 1px solid var(--border-color);
}

.tokens-stats {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.tokens-stats .tokens-count {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.tokens-stats .tokens-label {
  font-size: 13px;
  color: var(--text-tertiary);
}

.tokens-actions {
  display: flex;
  gap: 8px;
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
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s;
}

.token-card:hover {
  border-color: var(--border-color);
  box-shadow: var(--shadow-sm);
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
  color: var(--text-primary);
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
  color: var(--text-tertiary);
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
  background: var(--border-color);
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
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 4px 4px 4px 8px;
}

.token-key {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: 11px;
  color: var(--text-secondary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.token-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.tokens-empty {
  text-align: center;
  padding: 48px 20px;
}

.empty-icon {
  color: var(--text-tertiary);
  margin-bottom: 12px;
}

.empty-text {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.empty-hint {
  font-size: 13px;
  color: var(--text-tertiary);
}

/* 添加令牌抽屉 */
.token-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.token-form .form-item {
  margin-bottom: 0;
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .endpoints-grid {
    grid-template-columns: 1fr;
  }

  .tokens-list {
    grid-template-columns: 1fr;
  }

  .tokens-modal {
    width: 95vw;
    max-width: 680px;
  }
}

@media (max-width: 600px) {
  .stats-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
  }

  .stat-value {
    font-size: 20px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .section-title-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .section-title-row .n-select {
    margin-left: 0 !important;
    width: 100% !important;
  }

  .section-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .section-actions .n-button {
    flex: 1;
    min-width: 80px;
  }

  .modal-container {
    width: 95vw;
    max-width: 440px;
  }

  .trend-section {
    display: none;
  }

  .api-endpoints-section {
    margin-bottom: 16px;
  }

  /* 表格在移动端改为卡片布局 */
  :deep(.n-data-table) {
    font-size: 13px;
  }

  :deep(.n-data-table-th),
  :deep(.n-data-table-td) {
    padding: 8px 12px !important;
  }
}
</style>
