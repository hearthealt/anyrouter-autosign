<template>
  <div class="platforms-page">
    <section class="toolbar-card rise-1">
      <div class="toolbar-top">
        <div class="toolbar-copy">
        <h1>平台管理</h1>
          <p>直接查看和维护平台配置，减少首屏占用。</p>
        </div>

        <div class="toolbar-actions">
          <n-button quaternary @click="loadPlatforms" :loading="loading">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新平台
          </n-button>
          <n-button type="primary" @click="showCreateModal">
            <template #icon><n-icon><AddOutline /></n-icon></template>
            添加平台
          </n-button>
        </div>
      </div>

      <div class="toolbar-filters compact">
        <div class="filter-field search-span">
          <n-input
            v-model:value="searchKeyword"
            clearable
            placeholder="搜索平台名称或 Base URL"
          >
            <template #prefix><n-icon><SearchOutline /></n-icon></template>
          </n-input>
        </div>
      </div>

      <div class="toolbar-bottom">
        <div class="toolbar-metrics">
          <span class="metric-chip">平台 {{ formatNumber(platforms.length) }}</span>
          <span class="metric-chip">默认 {{ defaultPlatform?.name || '未设置' }}</span>
          <span class="metric-chip">账号 {{ formatNumber(totalAccounts) }}</span>
          <span class="metric-chip">接口 {{ averagePathCount }}/8</span>
        </div>
      </div>
    </section>

    <section class="workspace-shell rise-2">
      <div class="workspace-head compact">
        <div class="workspace-copy">
          <h2>平台列表</h2>
        </div>

        <div class="workspace-summary">
          <div class="summary-chip">
            <span>当前结果</span>
            <strong>{{ filteredPlatforms.length }}</strong>
          </div>
          <div class="summary-chip">
            <span>默认平台</span>
            <strong>{{ defaultPlatform ? 1 : 0 }}</strong>
          </div>
          <div class="summary-chip">
            <span>接口覆盖</span>
            <strong>{{ averagePathCount }}/8</strong>
          </div>
        </div>
      </div>

      <div v-if="loading || filteredPlatforms.length > 0" class="table-wrap">
        <n-data-table
          class="platform-table"
          :columns="columns"
          :data="filteredPlatforms"
          :row-key="getPlatformRowKey"
          :loading="loading"
          :pagination="false"
          :single-line="false"
          size="small"
          :scroll-x="1160"
        />
      </div>

      <div v-else class="empty-state">
        <div class="empty-state-mark">P</div>
        <h3>还没有平台配置</h3>
        <p>创建平台后，这里会展示 Base URL、接口数量、默认状态和账号归属信息。</p>
        <n-button type="primary" @click="showCreateModal">
          <template #icon><n-icon><AddOutline /></n-icon></template>
          创建平台
        </n-button>
      </div>
    </section>

    <n-modal v-model:show="modalVisible" :mask-closable="false">
      <div class="modal-shell">
        <div class="modal-hero">
          <div>
            <span class="modal-kicker">{{ editingPlatform ? 'Edit Platform' : 'Create Platform' }}</span>
            <h3>{{ editingPlatform ? '编辑平台' : '添加平台' }}</h3>
            <p>设置平台主地址以及签到、状态、模型、分组、Token 等接口路径映射。</p>
          </div>
          <n-button text @click="modalVisible = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>

        <div class="modal-body">
          <div class="modal-tip">
            <n-icon :size="18"><SparklesOutline /></n-icon>
            <span>Base URL 建议填写域名根路径，例如 `https://anyrouter.top`，接口字段保留相对路径即可。</span>
          </div>

          <n-form :model="formData" :rules="formRules" label-placement="top">
            <div class="form-grid">
              <n-form-item label="平台名称" path="name">
                <n-input v-model:value="formData.name" placeholder="如: AnyRouter" />
              </n-form-item>
              <n-form-item label="Base URL" path="base_url">
                <n-input v-model:value="formData.base_url" placeholder="https://example.com" />
              </n-form-item>
            </div>

            <div class="form-section">
              <div class="form-section-head">
                <div>
                  <span class="section-kicker">API Mapping</span>
                  <h4>接口路径</h4>
                </div>
                <span class="form-caption">默认值适配 AnyRouter 系列接口</span>
              </div>

              <div class="path-grid">
                <n-form-item label="签到接口">
                  <n-input v-model:value="formData.sign_api" placeholder="/api/user/sign_in" />
                </n-form-item>
                <n-form-item label="签到记录接口">
                  <n-input v-model:value="formData.checkin_api" placeholder="/api/user/checkin" />
                </n-form-item>
                <n-form-item label="用户信息接口">
                  <n-input v-model:value="formData.user_api" placeholder="/api/user/self" />
                </n-form-item>
                <n-form-item label="状态接口">
                  <n-input v-model:value="formData.status_api" placeholder="/api/status" />
                </n-form-item>
                <n-form-item label="模型接口">
                  <n-input v-model:value="formData.models_api" placeholder="/api/user/models" />
                </n-form-item>
                <n-form-item label="分组接口">
                  <n-input v-model:value="formData.groups_api" placeholder="/api/user/self/groups" />
                </n-form-item>
                <n-form-item label="Token 接口">
                  <n-input v-model:value="formData.token_api" placeholder="/api/token/" />
                </n-form-item>
                <n-form-item class="form-span-2" label="Console URL">
                  <n-input v-model:value="formData.console_url" placeholder="/console" />
                </n-form-item>
              </div>
            </div>
          </n-form>
        </div>

        <div class="modal-footer">
          <n-button @click="modalVisible = false">取消</n-button>
          <n-button type="primary" @click="handleSave" :loading="saving">
            {{ editingPlatform ? '保存平台' : '创建平台' }}
          </n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { NButton, NTag, type DataTableColumns } from 'naive-ui'
import {
  AddOutline,
  CloseOutline,
  RefreshOutline,
  SearchOutline,
  SparklesOutline,
} from '@vicons/ionicons5'
import { platformApi } from '../api'
import type { Platform } from '../types'

type PlatformEndpointKey =
  | 'sign_api'
  | 'checkin_api'
  | 'user_api'
  | 'console_url'
  | 'models_api'
  | 'groups_api'
  | 'token_api'
  | 'status_api'

interface PlatformForm {
  name: string
  base_url: string
  sign_api: string
  checkin_api: string
  user_api: string
  console_url: string
  models_api: string
  groups_api: string
  token_api: string
  status_api: string
}

interface EndpointDefinition {
  key: PlatformEndpointKey
  label: string
  hint: string
}

interface EndpointItem extends EndpointDefinition {
  path: string
  fullUrl: string
}

const createDefaultFormData = (): PlatformForm => ({
  name: '',
  base_url: '',
  sign_api: '/api/user/sign_in',
  checkin_api: '/api/user/checkin',
  user_api: '/api/user/self',
  console_url: '/console',
  models_api: '/api/user/models',
  groups_api: '/api/user/self/groups',
  token_api: '/api/token/',
  status_api: '/api/status'
})

const endpointDefinitions: EndpointDefinition[] = [
  { key: 'sign_api', label: '签到接口', hint: '执行签到' },
  { key: 'checkin_api', label: '签到记录', hint: '月度签到明细' },
  { key: 'user_api', label: '用户信息', hint: '获取资料' },
  { key: 'status_api', label: '状态接口', hint: '健康检查' },
  { key: 'models_api', label: '模型接口', hint: '模型列表' },
  { key: 'groups_api', label: '分组接口', hint: '用户分组' },
  { key: 'token_api', label: 'Token 接口', hint: '令牌管理' },
  { key: 'console_url', label: 'Console URL', hint: '控制台入口' }
]

const platforms = ref<Platform[]>([])
const loading = ref(false)
const searchKeyword = ref('')
const modalVisible = ref(false)
const editingPlatform = ref<Platform | null>(null)
const saving = ref(false)
const formData = ref<PlatformForm>(createDefaultFormData())

const defaultPlatform = computed(
  () => platforms.value.find(platform => platform.is_default) ?? platforms.value[0] ?? null
)
const totalAccounts = computed(() =>
  platforms.value.reduce((sum, platform) => sum + (platform.accounts_count ?? 0), 0)
)
const configuredPathsTotal = computed(() =>
  platforms.value.reduce((sum, platform) => sum + getConfiguredPathCount(platform), 0)
)
const averagePathCount = computed(() =>
  platforms.value.length > 0 ? (configuredPathsTotal.value / platforms.value.length).toFixed(1) : '0'
)

const filteredPlatforms = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  if (!keyword) {
    return platforms.value
  }

  return platforms.value.filter(platform =>
    [platform.name, platform.base_url]
      .filter(Boolean)
      .some(value => String(value).toLowerCase().includes(keyword))
  )
})

const getPlatformRowKey = (platform: Platform) => platform.id
const formatNumber = (value: number) => value.toLocaleString()

const formRules = {
  name: { required: true, message: '请输入平台名称', trigger: 'blur' },
  base_url: { required: true, message: '请输入 Base URL', trigger: 'blur' }
}

const buildEndpointUrl = (baseUrl: string, path?: string) => {
  const cleanBaseUrl = (baseUrl || '').trim().replace(/\/+$/, '')
  const cleanPath = (path || '').trim()

  if (!cleanPath) {
    return cleanBaseUrl
  }

  const normalizedPath = cleanPath.startsWith('/') ? cleanPath : `/${cleanPath}`
  return `${cleanBaseUrl}${normalizedPath}`
}

const getEndpointItems = (platform: Platform): EndpointItem[] =>
  endpointDefinitions.map(definition => {
    const path = String(platform[definition.key] || '')
    return {
      ...definition,
      path,
      fullUrl: buildEndpointUrl(platform.base_url, path)
    }
  })

const getConfiguredPathCount = (platform: Platform) =>
  endpointDefinitions.reduce((count, item) => {
    const value = String(platform[item.key] || '').trim()
    return count + (value ? 1 : 0)
  }, 0)

const formatDateTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('zh-CN', { hour12: false })
}

const renderPlatformExpand = (platform: Platform) =>
  h('div', { class: 'platform-expand' }, [
    h('div', { class: 'expand-summary' }, [
      h('div', { class: 'summary-item' }, [
        h('span', { class: 'summary-label' }, 'Base URL'),
        h('code', { class: 'summary-value mono' }, platform.base_url)
      ]),
      h('div', { class: 'summary-item' }, [
        h('span', { class: 'summary-label' }, '关联账号'),
        h('strong', { class: 'summary-value' }, `${platform.accounts_count ?? 0} 个`)
      ]),
      h('div', { class: 'summary-item' }, [
        h('span', { class: 'summary-label' }, '接口数量'),
        h('strong', { class: 'summary-value' }, `${getConfiguredPathCount(platform)}/8`)
      ]),
      h('div', { class: 'summary-item' }, [
        h('span', { class: 'summary-label' }, '最后更新'),
        h('span', { class: 'summary-value' }, formatDateTime(platform.updated_at))
      ])
    ]),
    h(
      'div',
      { class: 'endpoint-grid' },
      getEndpointItems(platform).map(item =>
        h('div', { class: 'endpoint-item' }, [
          h('div', { class: 'endpoint-head' }, [
            h('span', { class: 'endpoint-label' }, item.label),
            h('span', { class: 'endpoint-hint' }, item.hint)
          ]),
          h('code', { class: 'endpoint-path' }, item.path || '-'),
          h('div', { class: 'endpoint-url' }, item.fullUrl || platform.base_url)
        ])
      )
    )
  ])

const renderActions = (platform: Platform) =>
  h('div', { class: 'table-actions' }, [
    h(
      NButton,
      { size: 'small', quaternary: true, onClick: () => editPlatform(platform) },
      { default: () => '编辑' }
    ),
    h(
      NButton,
      { size: 'small', quaternary: true, type: 'error', onClick: () => deletePlatform(platform) },
      { default: () => '删除' }
    )
  ])

const columns = computed<DataTableColumns<Platform>>(() => [
  { type: 'expand', expandable: () => true, renderExpand: renderPlatformExpand },
  {
    title: '平台',
    key: 'name',
    minWidth: 180,
    render: row =>
      h('div', { class: 'name-cell' }, [
        h('span', { class: 'name-text' }, row.name),
        row.is_default
          ? h(NTag, { size: 'small', bordered: false, type: 'success', round: true }, { default: () => '默认' })
          : null
      ])
  },
  {
    title: 'Base URL',
    key: 'base_url',
    minWidth: 260,
    ellipsis: { tooltip: true },
    render: row => h('code', { class: 'mono-cell' }, row.base_url)
  },
  {
    title: '关联账号',
    key: 'accounts_count',
    width: 110,
    align: 'center',
    render: row => `${row.accounts_count ?? 0}`
  },
  {
    title: '接口数量',
    key: 'paths',
    width: 110,
    align: 'center',
    render: row => `${getConfiguredPathCount(row)}/8`
  },
  {
    title: '最后更新',
    key: 'updated_at',
    width: 180,
    render: row => formatDateTime(row.updated_at)
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render: row => renderActions(row)
  }
])

const loadPlatforms = async () => {
  loading.value = true
  try {
    const res: any = await platformApi.getList()
    platforms.value = (res.data || []) as Platform[]
  } catch (e: any) {
    window.$notify(e.message || '加载平台失败', 'error')
  } finally {
    loading.value = false
  }
}

const showCreateModal = () => {
  editingPlatform.value = null
  formData.value = createDefaultFormData()
  modalVisible.value = true
}

const editPlatform = (platform: Platform) => {
  editingPlatform.value = platform
  formData.value = {
    name: platform.name,
    base_url: platform.base_url,
    sign_api: platform.sign_api || '/api/user/sign_in',
    checkin_api: platform.checkin_api || '/api/user/checkin',
    user_api: platform.user_api || '/api/user/self',
    console_url: platform.console_url || '/console',
    models_api: platform.models_api || '/api/user/models',
    groups_api: platform.groups_api || '/api/user/self/groups',
    token_api: platform.token_api || '/api/token/',
    status_api: platform.status_api || '/api/status'
  }
  modalVisible.value = true
}

const handleSave = async () => {
  const payload = {
    ...formData.value,
    name: formData.value.name.trim(),
    base_url: formData.value.base_url.trim()
  }

  if (!payload.name) {
    window.$notify('请输入平台名称', 'warning')
    return
  }

  if (!payload.base_url) {
    window.$notify('请输入 Base URL', 'warning')
    return
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
    await loadPlatforms()
  } catch (e: any) {
    window.$notify(e.message || '操作失败', 'error')
  } finally {
    saving.value = false
  }
}

const deletePlatform = async (platform: Platform) => {
  if (!confirm(`确定删除平台 "${platform.name}" 吗？`)) {
    return
  }

  try {
    await platformApi.delete(platform.id)
    window.$notify('平台删除成功', 'success')
    await loadPlatforms()
  } catch (e: any) {
    window.$notify(e.message || '删除失败', 'error')
  }
}

onMounted(() => {
  loadPlatforms()
})
</script>

<style scoped>
.platforms-page {
  display: grid;
  gap: var(--spacing-5);
}

.platforms-hero,
.filters-shell,
.workspace-shell,
.modal-shell {
  position: relative;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}

.platforms-hero {
  padding: var(--spacing-6);
}

.platforms-hero::before,
.modal-shell::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 132px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.14) 0%, rgba(52, 211, 153, 0.08) 100%);
}

.hero-copy,
.hero-actions,
.hero-band,
.filters-head,
.filter-grid,
.scope-line,
.workspace-head,
.table-wrap,
.empty-state,
.modal-hero,
.modal-body,
.modal-footer {
  position: relative;
  z-index: 1;
}

.hero-copy {
  max-width: 720px;
}

.hero-kicker,
.section-kicker,
.modal-kicker {
  display: inline-flex;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--primary-color);
}

.hero-copy h1,
.modal-hero h3 {
  margin: 10px 0 8px;
  font-size: clamp(28px, 3.6vw, 40px);
  line-height: 1;
  letter-spacing: -0.04em;
  color: var(--text-primary);
}

.hero-copy p,
.filters-head p,
.workspace-copy p,
.modal-hero p,
.empty-state p {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.8;
  color: var(--text-secondary);
}

.hero-actions,
.workspace-summary,
.table-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.hero-actions {
  margin-top: var(--spacing-5);
}

.hero-band {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-3);
  margin-top: var(--spacing-5);
}

.band-metric,
.summary-chip,
.scope-chip,
.summary-item,
.endpoint-item,
.modal-tip {
  border: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.band-metric {
  padding: var(--spacing-4);
  border-radius: var(--radius-xl);
}

.band-label,
.filter-field label,
.summary-label {
  display: block;
  margin-bottom: 8px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.band-metric strong {
  display: block;
  font-size: clamp(20px, 2.4vw, 28px);
  line-height: 1.1;
  color: var(--text-primary);
}

.band-metric small,
.summary-value,
.endpoint-url {
  display: block;
  margin-top: 6px;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-secondary);
}

.filters-shell,
.workspace-shell {
  padding: var(--spacing-5);
}

.filters-head,
.workspace-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-4);
  align-items: end;
}

.filters-head h2,
.workspace-copy h2 {
  margin: 8px 0 6px;
  font-size: clamp(24px, 2.8vw, 30px);
  line-height: 1.05;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

.section-kicker.soft {
  color: var(--text-tertiary);
}

.filter-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-3);
  margin-top: var(--spacing-5);
}

.scope-line {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-top: var(--spacing-4);
}

.scope-chip,
.summary-chip {
  min-height: 40px;
  padding: 0 14px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.scope-chip strong,
.summary-chip strong {
  color: var(--text-primary);
}

.summary-chip {
  min-height: auto;
  padding: 12px 14px;
  border-radius: var(--radius-lg);
  display: block;
}

.summary-chip span {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.summary-chip strong {
  display: block;
  margin-top: 4px;
  font-size: 20px;
  line-height: 1;
}

.table-wrap {
  margin-top: var(--spacing-5);
  padding: 8px;
  border-radius: var(--radius-xl);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
}

.platform-table :deep(.n-data-table-wrapper) {
  border-radius: var(--radius-lg);
}

.platform-table :deep(.n-data-table-th) {
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  text-transform: uppercase;
}

.platform-table :deep(.n-data-table-tr:hover .n-data-table-td) {
  background: var(--bg-card-hover);
}

.name-cell,
.table-actions,
.modal-hero,
.form-section-head {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.name-text,
.summary-value,
.endpoint-label,
.form-section-head h4 {
  color: var(--text-primary);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
}

.mono-cell,
.summary-value.mono,
.endpoint-path {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.mono-cell {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.platform-expand {
  padding: 12px 6px 6px;
}

.expand-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}

.summary-item,
.endpoint-item {
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
}

.endpoint-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.endpoint-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
  margin-bottom: 8px;
}

.endpoint-hint,
.form-caption {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.endpoint-path {
  display: block;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: var(--text-xs);
  word-break: break-all;
}

.platform-table :deep(.platform-expand) {
  padding: 12px 6px 6px;
}

.platform-table :deep(.expand-summary) {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-3);
}

.platform-table :deep(.summary-item),
.platform-table :deep(.endpoint-item) {
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.platform-table :deep(.summary-label) {
  display: block;
  margin-bottom: 8px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.platform-table :deep(.summary-value),
.platform-table :deep(.endpoint-label) {
  color: var(--text-primary);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  line-height: 1.4;
  word-break: break-word;
}

.platform-table :deep(.endpoint-grid) {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.platform-table :deep(.endpoint-head) {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
  margin-bottom: 8px;
}

.platform-table :deep(.endpoint-hint) {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.platform-table :deep(.endpoint-path) {
  display: block;
  padding: 8px 10px;
  border-radius: var(--radius-md);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: var(--text-xs);
  word-break: break-all;
}

.platform-table :deep(.endpoint-url) {
  display: block;
  margin-top: 6px;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-secondary);
  word-break: break-all;
}

.modal-shell {
  width: min(780px, calc(100vw - 24px));
}

.modal-hero {
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
}

.modal-body {
  max-height: 72vh;
  overflow-y: auto;
  padding: var(--spacing-5);
}

.modal-tip {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  line-height: 1.7;
  color: var(--text-secondary);
}

.modal-tip .n-icon {
  color: var(--primary-color);
  margin-top: 2px;
}

.form-grid,
.path-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 16px;
}

.form-section {
  margin-top: var(--spacing-3);
}

.form-section-head {
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 8px;
}

.form-span-2 {
  grid-column: 1 / -1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.empty-state {
  display: grid;
  justify-items: center;
  gap: var(--spacing-3);
  padding: 56px 24px;
  text-align: center;
}

.empty-state-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 22px;
  background: var(--primary-gradient);
  color: #fff;
  font-size: 28px;
  font-weight: var(--font-bold);
  box-shadow: var(--shadow-md);
}

.empty-state h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: var(--text-xl);
}

.toolbar-card {
  position: relative;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--spacing-5);
}

.toolbar-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 72px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(52, 211, 153, 0.06) 100%);
}

.toolbar-top,
.toolbar-filters,
.toolbar-bottom {
  position: relative;
  z-index: 1;
}

.toolbar-top {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--spacing-4);
  align-items: center;
}

.toolbar-copy h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: clamp(24px, 2.8vw, 30px);
  line-height: 1.05;
  letter-spacing: -0.03em;
}

.toolbar-copy p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.toolbar-filters.compact {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-3);
  margin-top: var(--spacing-4);
}

.toolbar-bottom {
  margin-top: var(--spacing-4);
}

.toolbar-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
}

.metric-chip {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  white-space: nowrap;
}

.workspace-head.compact {
  align-items: center;
}

.workspace-head.compact .workspace-copy h2 {
  margin: 0;
}

.rise-1,
.rise-2,
.rise-3 {
  animation: rise-in 0.55s ease both;
}

.rise-2 {
  animation-delay: 0.06s;
}

.rise-3 {
  animation-delay: 0.12s;
}

@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1200px) {
  .hero-band,
  .expand-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .endpoint-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .platform-table :deep(.expand-summary) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .platform-table :deep(.endpoint-grid) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 980px) {
  .toolbar-top,
  .filters-head,
  .workspace-head {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .hero-band,
  .expand-summary,
  .endpoint-grid {
    grid-template-columns: 1fr;
  }

  .platform-table :deep(.expand-summary),
  .platform-table :deep(.endpoint-grid) {
    grid-template-columns: 1fr;
  }

  .workspace-summary {
    width: 100%;
  }

  .summary-chip {
    flex: 1 1 0;
  }

  .form-grid,
  .path-grid {
    grid-template-columns: 1fr;
  }

  .form-span-2 {
    grid-column: auto;
  }
}

@media (max-width: 640px) {
  .hero-actions,
  .toolbar-actions,
  .table-actions {
    width: 100%;
  }

  .hero-actions :deep(.n-button),
  .toolbar-actions :deep(.n-button),
  .table-actions :deep(.n-button) {
    flex: 1 1 calc(50% - 8px);
    min-width: 0;
  }

  .scope-chip,
  .summary-chip {
    width: 100%;
  }
}
</style>
