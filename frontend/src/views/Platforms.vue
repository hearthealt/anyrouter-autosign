<template>
  <div class="platforms-page">
    <div class="workspace-toolbar">
      <div class="toolbar-summary">
        <div class="toolbar-label">平台 <span class="toolbar-count">{{ pagination.itemCount }}</span></div>
        <div class="toolbar-stats">
          <span class="toolbar-stat">默认 <strong>{{ defaultPlatform?.name || '未设置' }}</strong></span>
          <span class="toolbar-stat">关联账号 <strong>{{ totalAccounts }}</strong></span>
        </div>
      </div>
      <div class="toolbar-actions">
        <UiButton size="small" :loading="loading" @click="loadPlatforms(pagination.page)">
          <template #icon><RefreshCw :size="14" /></template>
          刷新
        </UiButton>
        <UiButton size="small" type="primary" @click="showCreateModal">
          <template #icon><Plus :size="14" /></template>
          添加平台
        </UiButton>
      </div>
    </div>

    <div class="control-strip">
      <div class="filter-strip">
      <UiInput
        v-model:value="searchKeyword"
        size="small"
        clearable
        placeholder="搜索平台名称或 Base URL"
        class="search-input"
        @keyup.enter="loadPlatforms(1)"
        @clear="loadPlatforms(1)"
      >
        <template #prefix><Search :size="14" /></template>
      </UiInput>
      <UiButton size="small" :loading="loading" @click="loadPlatforms(1)">查询</UiButton>
      </div>
    </div>

    <div class="platforms-card data-surface">
      <div v-if="loading || platforms.length > 0" class="table-wrap">
        <DataGrid
          :columns="columns"
          :data="platforms"
          :row-key="getPlatformRowKey"
          :loading="loading"
          :pagination="false"
          :single-line="false"
          size="small"
          :scroll-x="1020"
        />
      </div>
      <div v-else class="empty-state">
        <Server :size="32" />
        <div class="empty-title">还没有平台</div>
        <div class="empty-desc">可以添加 New API 兼容站点，或配置任意 HTTP 签到接口</div>
        <UiButton size="small" type="primary" @click="showCreateModal">
          <template #icon><Plus :size="14" /></template>
          创建平台
        </UiButton>
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

    <UiModal v-model:show="modalVisible" :mask-closable="false">
      <div class="edit-modal">
        <div class="modal-head">
          <h3>{{ editingPlatform ? '编辑平台' : '添加平台' }}</h3>
          <UiButton text @click="modalVisible = false">
            <X :size="16" />
          </UiButton>
        </div>

        <div class="modal-body">
          <div class="platform-form">
            <section class="form-section">
              <div class="form-section-title">基础信息</div>
              <div class="form-grid base-grid">
                <label class="field">
                  <span class="field-label">平台名称 <span class="required">*</span></span>
                  <UiInput v-model:value="formData.name" size="small" placeholder="如：示例签到站" />
                </label>
                <label class="field">
                  <span class="field-label">Base URL <span class="required">*</span></span>
                  <UiInput v-model:value="formData.base_url" size="small" placeholder="https://example.com" />
                </label>
                <label class="field">
                  <span class="field-label">适配器 <span class="required">*</span></span>
                  <UiSelect v-model:value="formData.adapter_type" size="small" :options="adapterOptions" />
                </label>
              </div>
              <div class="form-help">
                Base URL 仅填写协议和站点地址；接口必须使用以 <code>/</code> 开头的相对路径。
              </div>
            </section>

            <template v-if="formData.adapter_type === 'new_api'">
              <section class="form-section">
                <div class="form-section-title">New API 签到</div>
                <div class="form-grid endpoint-grid">
                  <label class="field">
                  <span class="field-label">签到方式</span>
                    <UiSelect v-model:value="formData.sign_mode" size="small" :options="signModeOptions" />
                  </label>
                  <label class="field">
                  <span class="field-label">签到接口</span>
                    <UiInput v-model:value="formData.sign_api" size="small" placeholder="/api/user/sign_in" />
                  </label>
                  <label class="field">
                  <span class="field-label">签到记录</span>
                    <UiInput v-model:value="formData.checkin_api" size="small" placeholder="/api/user/checkin" />
                  </label>
                  <label class="field">
                  <span class="field-label">验证码</span>
                    <UiInput v-model:value="formData.captcha_api" size="small" placeholder="可选" />
                  </label>
                  <label class="field">
                  <span class="field-label">用户信息</span>
                    <UiInput v-model:value="formData.user_api" size="small" placeholder="/api/user/self" />
                  </label>
                  <label class="field">
                  <span class="field-label">控制台</span>
                    <UiInput v-model:value="formData.console_url" size="small" placeholder="/console" />
                  </label>
                </div>
              </section>

              <section class="form-section">
                <div class="form-section-title">New API 扩展接口</div>
                <div class="form-grid endpoint-grid">
                  <label class="field">
                  <span class="field-label">模型列表</span>
                    <UiInput v-model:value="formData.models_api" size="small" placeholder="/api/user/models" />
                  </label>
                  <label class="field">
                  <span class="field-label">平台分组</span>
                    <UiInput v-model:value="formData.groups_api" size="small" placeholder="/api/user/self/groups" />
                  </label>
                  <label class="field">
                  <span class="field-label">Token</span>
                    <UiInput v-model:value="formData.token_api" size="small" placeholder="/api/token/" />
                  </label>
                  <label class="field">
                  <span class="field-label">系统状态</span>
                    <UiInput v-model:value="formData.status_api" size="small" placeholder="/api/status" />
                  </label>
                </div>
              </section>
            </template>

            <template v-else>
              <section class="form-section">
                <div class="form-section-title">HTTP 请求</div>
                <div class="form-grid request-grid">
                  <label class="field">
                  <span class="field-label">请求方法</span>
                    <UiSelect v-model:value="formData.http_method" size="small" :options="httpMethodOptions" />
                  </label>
                  <label class="field">
                  <span class="field-label">签到路径</span>
                    <UiInput v-model:value="formData.http_path" size="small" placeholder="/api/checkin" />
                  </label>
                  <label class="field">
                  <span class="field-label">请求体类型</span>
                    <UiSelect v-model:value="formData.http_body_type" size="small" :options="bodyTypeOptions" />
                  </label>
                  <label class="field">
                  <span class="field-label">超时（秒）</span>
                    <UiNumberInput v-model:value="formData.http_timeout" size="small" :min="1" :max="120" />
                  </label>
                  <label class="field">
                  <span class="field-label">最大重定向</span>
                    <UiNumberInput v-model:value="formData.http_max_redirects" size="small" :min="0" :max="5" :disabled="!formData.http_follow_redirects" />
                  </label>
                  <label class="field">
                  <span class="field-label">允许重定向</span>
                    <div class="switch-field">
                      <UiSwitch v-model:value="formData.http_follow_redirects" size="small" />
                      <span>{{ formData.http_follow_redirects ? '允许（携带凭证时禁止跨域）' : '禁止' }}</span>
                    </div>
                  </label>
                </div>

                <div class="form-grid json-grid">
                  <label class="field">
                  <span class="field-label">Headers JSON</span>
                    <UiInput v-model:value="formData.http_headers_json" type="textarea" :rows="4" size="small" placeholder='{"X-Client":"autosign"}' />
                  </label>
                  <label class="field">
                  <span class="field-label">Query JSON</span>
                    <UiInput v-model:value="formData.http_query_json" type="textarea" :rows="4" size="small" placeholder='{"uid":"{{account.external_user_id}}"}' />
                  </label>
                  <label class="field">
                  <span class="field-label">请求体</span>
                    <UiInput
                      v-model:value="formData.http_body_json"
                      type="textarea"
                      :rows="5"
                      size="small"
                      :placeholder="formData.http_body_type === 'raw' ? '原始文本，可使用模板变量' : 'JSON 请求体，例如 action=checkin'"
                      :disabled="formData.http_body_type === 'none'"
                    />
                  </label>
                </div>
                <div class="form-help">
                  配置值支持模板变量：<code v-pre>{{auth.token}}</code>、<code v-pre>{{account.external_user_id}}</code>、<code v-pre>{{account.username}}</code>。
                  Bearer、Cookie、Header、Basic 认证信息由账号配置自动注入。
                </div>
              </section>

              <section class="form-section">
                <div class="form-section-title">HTTP 响应判定</div>
                <div class="form-grid json-grid">
                  <label class="field">
                  <span class="field-label">成功规则 JSON</span>
                    <UiInput v-model:value="formData.http_success_rule_json" type="textarea" :rows="4" size="small" placeholder='留空则按 HTTP 2xx；或 {"path":"code","equals":0}' />
                  </label>
                  <label class="field">
                  <span class="field-label">已签到规则 JSON</span>
                    <UiInput v-model:value="formData.http_already_rule_json" type="textarea" :rows="4" size="small" placeholder='{"path":"message","contains":"已签到"}' />
                  </label>
                </div>
                <div class="form-grid response-grid">
                  <label class="field">
                  <span class="field-label">消息字段路径</span>
                    <UiInput v-model:value="formData.http_message_path" size="small" placeholder="message" />
                  </label>
                  <label class="field">
                  <span class="field-label">奖励字段路径</span>
                    <UiInput v-model:value="formData.http_reward_path" size="small" placeholder="data.points" />
                  </label>
                  <label class="field">
                  <span class="field-label">奖励显示字段路径</span>
                    <UiInput v-model:value="formData.http_reward_display_path" size="small" placeholder="可选，如 data.reward_text" />
                  </label>
                  <label class="field">
                  <span class="field-label">奖励单位</span>
                    <UiInput v-model:value="formData.http_reward_unit" size="small" placeholder="积分、金币、天" />
                  </label>
                  <label class="field">
                  <span class="field-label">奖励倍率</span>
                    <UiNumberInput v-model:value="formData.http_reward_multiplier" size="small" :min="0" />
                  </label>
                </div>
                <div class="form-help">
                  字段路径支持点号访问嵌套对象。规则支持 <code>equals</code>、<code>contains</code>、<code>exists</code>、<code>in</code>、<code>truthy</code> 等判定。
                </div>
              </section>
            </template>
          </div>
        </div>

        <div class="modal-foot">
          <UiButton size="small" @click="modalVisible = false">取消</UiButton>
          <UiButton size="small" type="primary" :loading="saving" @click="handleSave">保存</UiButton>
        </div>
      </div>
    </UiModal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { DataGrid, UiButton, UiConfirm, UiInput, UiModal, UiNumberInput, UiPagination, UiSelect, UiSwitch, type GridColumns } from '../ui'
import { Plus, RefreshCw, Search, Server, X } from 'lucide-vue-next'
import { platformApi } from '../api'
import { useViewRefresh } from '../composables'
import ExternalLink from '../components/common/ExternalLink.vue'
import type { Platform, PlatformAdapterType } from '../types'

type HttpBodyType = 'json' | 'form' | 'raw' | 'none'

type PlatformEndpointKey =
  | 'sign_api'
  | 'checkin_api'
  | 'user_api'
  | 'console_url'
  | 'models_api'
  | 'groups_api'
  | 'token_api'
  | 'status_api'
  | 'captcha_api'

interface PlatformForm {
  name: string
  base_url: string
  adapter_type: PlatformAdapterType
  sign_mode: 'api' | 'login'
  sign_api: string
  checkin_api: string
  user_api: string
  console_url: string
  models_api: string
  groups_api: string
  token_api: string
  status_api: string
  captcha_api: string
  http_method: string
  http_path: string
  http_body_type: HttpBodyType
  http_headers_json: string
  http_query_json: string
  http_body_json: string
  http_success_rule_json: string
  http_already_rule_json: string
  http_message_path: string
  http_reward_path: string
  http_reward_display_path: string
  http_reward_unit: string
  http_reward_multiplier: number
  http_follow_redirects: boolean
  http_max_redirects: number
  http_timeout: number
}

const createDefaultFormData = (): PlatformForm => ({
  name: '',
  base_url: '',
  adapter_type: 'new_api',
  sign_mode: 'api',
  sign_api: '/api/user/sign_in',
  checkin_api: '/api/user/checkin',
  user_api: '/api/user/self',
  console_url: '/console',
  models_api: '/api/user/models',
  groups_api: '/api/user/self/groups',
  token_api: '/api/token/',
  status_api: '/api/status',
  captcha_api: '',
  http_method: 'POST',
  http_path: '/api/checkin',
  http_body_type: 'json',
  http_headers_json: '{}',
  http_query_json: '{}',
  http_body_json: '{}',
  http_success_rule_json: '',
  http_already_rule_json: '',
  http_message_path: 'message',
  http_reward_path: '',
  http_reward_display_path: '',
  http_reward_unit: '',
  http_reward_multiplier: 1,
  http_follow_redirects: false,
  http_max_redirects: 3,
  http_timeout: 30,
})

const endpointKeys: PlatformEndpointKey[] = [
  'sign_api', 'checkin_api', 'user_api', 'status_api',
  'models_api', 'groups_api', 'token_api', 'console_url', 'captcha_api'
]

const adapterOptions = [
  { label: 'New API 兼容', value: 'new_api' },
  { label: '通用 HTTP', value: 'http' },
]
const signModeOptions = [
  { label: '调用签到接口', value: 'api' },
  { label: '登录即签到', value: 'login' }
]
const httpMethodOptions = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].map(value => ({ label: value, value }))
const bodyTypeOptions = [
  { label: 'JSON', value: 'json' },
  { label: 'Form', value: 'form' },
  { label: 'Raw', value: 'raw' },
  { label: '无请求体', value: 'none' },
]

const platforms = ref<Platform[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const modalVisible = ref(false)
const editingPlatform = ref<Platform | null>(null)
const saving = ref(false)
const formData = ref<PlatformForm>(createDefaultFormData())
const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  pageSizes: [10, 20, 50, 100]
})

const defaultPlatform = computed(() => platforms.value.find(platform => platform.is_default) ?? null)
const totalAccounts = computed(() => platforms.value.reduce((sum, platform) => sum + (platform.accounts_count ?? 0), 0))
const getPlatformRowKey = (platform: Platform) => platform.id

const getConfiguredPathCount = (platform: Platform) => endpointKeys.reduce((count, key) => {
  const value = String(platform[key] || '').trim()
  return count + (value ? 1 : 0)
}, 0)

const getAdapterLabel = (platform: Platform) => platform.adapter_type === 'http' ? 'HTTP' : 'New API'
const getSignModeLabel = (platform: Platform) => platform.sign_mode === 'login' ? '登录签到' : '接口签到'
const getHttpSummary = (platform: Platform) => {
  const request = platform.adapter_config?.request || {}
  return `${String(request.method || 'POST').toUpperCase()} ${request.path || '-'}`
}
const formatDateTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

const columns = computed<GridColumns<Platform>>(() => [
  {
    title: '平台',
    key: 'name',
    minWidth: 270,
    render: row => h('div', { class: 'platform-cell' }, [
      h('span', { class: 'platform-name', title: row.name }, row.name),
      h('span', { class: 'platform-tags' }, [
        h('span', { class: row.adapter_type === 'http' ? 'tag warning' : 'tag' }, getAdapterLabel(row)),
        row.is_default ? h('span', { class: 'tag primary' }, '默认') : h('span', { class: 'tag ghost' }, '普通')
      ])
    ])
  },
  {
    title: 'Base URL',
    key: 'base_url',
    minWidth: 280,
    render: row => h(ExternalLink, { href: row.base_url, mono: true })
  },
  {
    title: '账号',
    key: 'accounts_count',
    width: 80,
    align: 'right',
    render: row => String(row.accounts_count ?? 0)
  },
  {
    title: '签到配置',
    key: 'paths',
    minWidth: 150,
    render: row => row.adapter_type === 'http'
      ? h('span', { class: 'mono', title: getHttpSummary(row) }, getHttpSummary(row))
      : `${getSignModeLabel(row)} · ${getConfiguredPathCount(row)}/9`
  },
  {
    title: '更新时间',
    key: 'updated_at',
    width: 170,
    render: row => formatDateTime(row.updated_at)
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: row => h('div', { class: 'actions' }, [
      h(UiButton, { size: 'tiny', quaternary: true, onClick: () => editPlatform(row) }, { default: () => '编辑' }),
      h(UiConfirm, {
        onPositiveClick: () => deletePlatform(row), positiveText: '删除', negativeText: '取消',
      }, {
        trigger: () => h(UiButton, { size: 'tiny', quaternary: true, type: 'error' }, { default: () => '删除' }),
        default: () => `确定删除平台 "${row.name}"？删除前必须先迁移或删除关联账号。`
      })
    ])
  }
])

const prettyJson = (value: unknown, fallback = '{}') => {
  if (value == null || value === '') return fallback
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return fallback
  }
}

const parseJsonObject = (value: string, label: string, allowEmpty = false): Record<string, any> | undefined => {
  const text = value.trim()
  if (!text && allowEmpty) return undefined
  let parsed: unknown
  try {
    parsed = JSON.parse(text || '{}')
  } catch (error: any) {
    throw new Error(`${label}不是有效 JSON：${error.message}`)
  }
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') {
    throw new Error(`${label}必须是 JSON 对象`)
  }
  return parsed as Record<string, any>
}

const buildHttpAdapterConfig = () => {
  const headers = parseJsonObject(formData.value.http_headers_json, 'Headers JSON') || {}
  const query = parseJsonObject(formData.value.http_query_json, 'Query JSON') || {}
  const success = parseJsonObject(formData.value.http_success_rule_json, '成功规则 JSON', true)
  const alreadySigned = parseJsonObject(formData.value.http_already_rule_json, '已签到规则 JSON', true)

  let body: unknown = undefined
  if (formData.value.http_body_type === 'raw') {
    body = formData.value.http_body_json
  } else if (formData.value.http_body_type !== 'none') {
    body = parseJsonObject(formData.value.http_body_json, '请求体') || {}
  }

  const response: Record<string, any> = {}
  if (success) response.success = success
  if (alreadySigned) response.already_signed = alreadySigned
  if (formData.value.http_message_path.trim()) response.message_path = formData.value.http_message_path.trim()
  if (formData.value.http_reward_path.trim()) response.reward_path = formData.value.http_reward_path.trim()
  if (formData.value.http_reward_display_path.trim()) response.reward_display_path = formData.value.http_reward_display_path.trim()
  if (formData.value.http_reward_unit.trim()) response.reward_unit = formData.value.http_reward_unit.trim()
  response.reward_multiplier = formData.value.http_reward_multiplier || 1

  return {
    request: {
      method: formData.value.http_method,
      path: formData.value.http_path.trim(),
      body_type: formData.value.http_body_type,
      headers,
      query,
      ...(body !== undefined ? { body } : {}),
      follow_redirects: formData.value.http_follow_redirects,
      max_redirects: formData.value.http_max_redirects,
      timeout: formData.value.http_timeout,
    },
    response,
  }
}

const applyHttpConfig = (platform: Platform, form: PlatformForm) => {
  const request = platform.adapter_config?.request || {}
  const response = platform.adapter_config?.response || {}
  form.http_method = String(request.method || 'POST').toUpperCase()
  form.http_path = String(request.path || '/api/checkin')
  form.http_body_type = (request.body_type || 'json') as HttpBodyType
  form.http_headers_json = prettyJson(request.headers || {})
  form.http_query_json = prettyJson(request.query || {})
  form.http_body_json = form.http_body_type === 'raw'
    ? String(request.body ?? '')
    : prettyJson(request.body || {})
  form.http_success_rule_json = response.success ? prettyJson(response.success, '') : ''
  form.http_already_rule_json = response.already_signed ? prettyJson(response.already_signed, '') : ''
  form.http_message_path = String(response.message_path || '')
  form.http_reward_path = String(response.reward_path || '')
  form.http_reward_display_path = String(response.reward_display_path || '')
  form.http_reward_unit = String(response.reward_unit || '')
  form.http_reward_multiplier = Number(response.reward_multiplier ?? 1)
  form.http_follow_redirects = Boolean(request.follow_redirects)
  form.http_max_redirects = Number(request.max_redirects ?? 3)
  form.http_timeout = Number(request.timeout ?? 30)
}

const loadPlatforms = async (page = pagination.value.page) => {
  loading.value = true
  try {
    const params: { page: number; size: number; keyword?: string } = { page, size: pagination.value.pageSize }
    const keyword = searchKeyword.value.trim()
    if (keyword) params.keyword = keyword

    const res: any = await platformApi.getList(params)
    const data = res.data || {}
    platforms.value = (data.items || []) as Platform[]
    pagination.value.itemCount = data.total || 0
    pagination.value.page = data.page || page
  } catch (e: any) {
    window.$notify(e.message || '加载平台失败', 'error')
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => loadPlatforms(page)
const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  loadPlatforms(1)
}

const showCreateModal = () => {
  editingPlatform.value = null
  formData.value = createDefaultFormData()
  modalVisible.value = true
}

const editPlatform = (platform: Platform) => {
  editingPlatform.value = platform
  const form = createDefaultFormData()
  Object.assign(form, {
    name: platform.name,
    base_url: platform.base_url,
    adapter_type: platform.adapter_type || 'new_api',
    sign_mode: platform.sign_mode || 'api',
    sign_api: platform.sign_api || '/api/user/sign_in',
    checkin_api: platform.checkin_api || '/api/user/checkin',
    user_api: platform.user_api || '/api/user/self',
    console_url: platform.console_url || '/console',
    models_api: platform.models_api || '/api/user/models',
    groups_api: platform.groups_api || '/api/user/self/groups',
    token_api: platform.token_api || '/api/token/',
    status_api: platform.status_api || '/api/status',
    captcha_api: platform.captcha_api || '',
  })
  if (form.adapter_type === 'http') applyHttpConfig(platform, form)
  formData.value = form
  modalVisible.value = true
}

const handleSave = async () => {
  const name = formData.value.name.trim()
  const baseUrl = formData.value.base_url.trim()
  if (!name) {
    window.$notify('请输入平台名称', 'warning')
    return
  }
  if (!baseUrl) {
    window.$notify('请输入 Base URL', 'warning')
    return
  }

  let adapterConfig: Record<string, any> = {}
  try {
    if (formData.value.adapter_type === 'http') {
      if (!formData.value.http_path.trim()) throw new Error('请输入 HTTP 签到路径')
      adapterConfig = buildHttpAdapterConfig()
    }
  } catch (error: any) {
    window.$notify(error.message || 'HTTP 适配器配置无效', 'warning')
    return
  }

  const payload = {
    name,
    base_url: baseUrl,
    adapter_type: formData.value.adapter_type,
    adapter_config: adapterConfig,
    sign_mode: formData.value.sign_mode,
    sign_api: formData.value.sign_api.trim(),
    checkin_api: formData.value.checkin_api.trim(),
    user_api: formData.value.user_api.trim(),
    console_url: formData.value.console_url.trim(),
    models_api: formData.value.models_api.trim(),
    groups_api: formData.value.groups_api.trim(),
    token_api: formData.value.token_api.trim(),
    status_api: formData.value.status_api.trim(),
    captcha_api: formData.value.captcha_api.trim(),
  }

  saving.value = true
  try {
    if (editingPlatform.value) {
      await platformApi.update(editingPlatform.value.id, payload)
      window.$notify('平台更新成功', 'success')
    } else {
      await platformApi.create(payload)
      window.$notify('平台创建成功', 'success')
    }
    modalVisible.value = false
    await loadPlatforms(pagination.value.page)
  } catch (e: any) {
    window.$notify(e.message || '操作失败', 'error')
  } finally {
    saving.value = false
  }
}

const deletePlatform = async (platform: Platform) => {
  try {
    await platformApi.delete(platform.id)
    window.$notify('平台删除成功', 'success')
    await loadPlatforms(pagination.value.page)
  } catch (e: any) {
    window.$notify(e.message || '删除失败', 'error')
  }
}

onMounted(() => loadPlatforms(1))
watch(searchKeyword, value => { if (!value) loadPlatforms(1) })
useViewRefresh(() => loadPlatforms(pagination.value.page))
</script>

<style scoped>
.platforms-page { display: flex; flex-direction: column; gap: var(--spacing-3); }
.search-input { width: min(440px, 100%); }
.platforms-card { overflow: hidden; }
.table-wrap :deep(.n-data-table) { border: none; border-radius: 0; }
.pagination-wrap { display: flex; justify-content: flex-end; padding: var(--spacing-3) var(--spacing-4); border-top: 1px solid var(--border-color-light); background: var(--bg-card-hover); }
.empty-state { padding: var(--spacing-12) var(--spacing-5); }
.platforms-page :deep(.platform-cell) { display: grid; grid-template-columns: minmax(0, 1fr) 112px; align-items: center; gap: var(--spacing-3); width: 100%; min-width: 0; }
.platforms-page :deep(.platform-name) { min-width: 0; overflow: hidden; color: var(--text-primary); font-weight: var(--font-medium); text-overflow: ellipsis; white-space: nowrap; }
.platforms-page :deep(.platform-tags) { display: inline-grid; grid-template-columns: 70px 36px; gap: 6px; justify-content: end; }
.platforms-page :deep(.tag) { display: inline-flex; align-items: center; justify-content: center; height: 18px; padding: 0 6px; border-radius: var(--radius-xs); font-size: 10px; font-weight: var(--font-medium); background: var(--bg-secondary); color: var(--text-tertiary); }
.platforms-page :deep(.tag.primary) { background: var(--primary-color-light); color: var(--primary-color); }
.platforms-page :deep(.tag.warning) { background: rgba(245, 158, 11, 0.12); color: #d97706; }
.platforms-page :deep(.tag.ghost) { background: transparent; color: transparent; }
.platforms-page :deep(.mono) { font-family: var(--font-mono); font-size: var(--text-xs); color: var(--text-secondary); }
.platforms-page :deep(.actions) { display: flex; gap: 2px; }
.edit-modal { width: min(940px, calc(100vw - 24px)); background: var(--bg-modal); border: 1px solid var(--border-color-light); border-radius: var(--radius-md); box-shadow: var(--shadow-lg); overflow: hidden; }
.modal-head, .modal-foot { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-3) var(--spacing-4); }
.modal-head { border-bottom: 1px solid var(--border-color-light); }
.modal-head h3 { margin: 0; font-size: var(--text-md); font-weight: var(--font-semibold); }
.modal-body { padding: var(--spacing-3) var(--spacing-4); max-height: calc(100vh - 160px); overflow-y: auto; }
.modal-foot { justify-content: flex-end; gap: var(--spacing-2); border-top: 1px solid var(--border-color-light); background: var(--bg-card-hover); }
.platform-form { display: flex; flex-direction: column; gap: var(--spacing-3); }
.form-section { padding-bottom: var(--spacing-2); border-bottom: 1px solid var(--border-color-light); }
.form-section:last-child { padding-bottom: 0; border-bottom: none; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 var(--spacing-3); }
.base-grid { grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr) 180px; }
.endpoint-grid, .response-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.request-grid { grid-template-columns: 150px minmax(0, 1fr) 150px; }
.json-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.span-2 { grid-column: span 2; }
.form-section-title { font-size: var(--text-xs); font-weight: var(--font-semibold); color: var(--text-tertiary); text-transform: uppercase; margin-bottom: var(--spacing-2); }
.form-help { color: var(--text-tertiary); font-size: var(--text-xs); line-height: 1.6; margin: -2px 0 8px; }
.form-help code { color: var(--primary-color); background: var(--bg-secondary); padding: 1px 4px; border-radius: var(--radius-xs); }
.switch-field { display: flex; align-items: center; gap: var(--spacing-2); min-height: 28px; color: var(--text-tertiary); font-size: var(--text-xs); }
.platform-form :deep(.n-form-item) { --n-label-height: 20px; --n-blank-height: 0; margin-bottom: 8px; }
.platform-form :deep(.n-form-item-feedback-wrapper) { min-height: 0; }
.platform-form :deep(.n-input-number) { width: 100%; }
@media (max-width: 900px) {
  .base-grid, .endpoint-grid, .request-grid, .response-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .form-grid, .base-grid, .endpoint-grid, .request-grid, .response-grid, .json-grid { grid-template-columns: 1fr; }
  .span-2 { grid-column: auto; }
}
</style>
