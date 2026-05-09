<template>
  <div class="platforms-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">平台</h1>
        <p class="page-subtitle">{{ platforms.length }} 个平台 · 默认 {{ defaultPlatform?.name || '未设置' }} · 关联 {{ totalAccounts }} 账号</p>
      </div>
      <div class="head-actions">
        <n-button size="small" :loading="loading" @click="loadPlatforms(pagination.page)">
          <template #icon><n-icon :size="14"><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
        <n-button size="small" type="primary" @click="showCreateModal">
          <template #icon><n-icon :size="14"><AddOutline /></n-icon></template>
          添加平台
        </n-button>
      </div>
    </div>

    <div class="filter-bar">
      <n-input
        v-model:value="searchKeyword"
        size="small"
        clearable
        placeholder="搜索平台名称或 Base URL"
        class="search-input"
        @keyup.enter="loadPlatforms(1)"
        @clear="loadPlatforms(1)"
      >
        <template #prefix><n-icon :size="14"><SearchOutline /></n-icon></template>
      </n-input>
      <n-button size="small" :loading="loading" @click="loadPlatforms(1)">
        查询
      </n-button>
    </div>

    <div class="platforms-card">
      <div v-if="loading || platforms.length > 0" class="table-wrap">
        <n-data-table
          :columns="columns"
          :data="platforms"
          :row-key="getPlatformRowKey"
          :loading="loading"
          :pagination="false"
          :single-line="false"
          size="small"
          :scroll-x="960"
        />
      </div>
      <div v-else class="empty-state">
        <n-icon :size="32" color="var(--text-quaternary)"><ServerOutline /></n-icon>
        <div class="empty-title">还没有平台</div>
        <div class="empty-desc">创建平台后，可统一管理 Base URL 和接口路径映射</div>
        <n-button size="small" type="primary" @click="showCreateModal">
          <template #icon><n-icon :size="14"><AddOutline /></n-icon></template>
          创建平台
        </n-button>
      </div>

      <div v-if="pagination.itemCount > 0" class="pagination-wrap">
        <n-pagination
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

    <n-modal v-model:show="modalVisible" :mask-closable="false">
      <div class="edit-modal">
        <div class="modal-head">
          <h3>{{ editingPlatform ? '编辑平台' : '添加平台' }}</h3>
          <n-button text @click="modalVisible = false">
            <n-icon :size="16"><CloseOutline /></n-icon>
          </n-button>
        </div>

        <div class="modal-body">
          <div class="tip">
            <n-icon :size="14"><SparklesOutline /></n-icon>
            <span>Base URL 填写域名根路径（如 <code>https://anyrouter.top</code>），接口保留相对路径</span>
          </div>

          <n-form :model="formData" :rules="formRules" label-placement="top">
            <div class="form-grid">
              <n-form-item label="平台名称" path="name">
                <n-input v-model:value="formData.name" size="small" placeholder="如: AnyRouter" />
              </n-form-item>
              <n-form-item label="Base URL" path="base_url">
                <n-input v-model:value="formData.base_url" size="small" placeholder="https://example.com" />
              </n-form-item>
              <n-form-item label="签到方式" path="sign_mode">
                <n-select
                  v-model:value="formData.sign_mode"
                  size="small"
                  :options="signModeOptions"
                />
              </n-form-item>
            </div>

            <div class="form-section-title">接口路径</div>

            <div class="form-grid">
              <n-form-item label="签到">
                <n-input v-model:value="formData.sign_api" size="small" placeholder="/api/user/sign_in" />
              </n-form-item>
              <n-form-item label="签到记录">
                <n-input v-model:value="formData.checkin_api" size="small" placeholder="/api/user/checkin" />
              </n-form-item>
              <n-form-item label="用户信息">
                <n-input v-model:value="formData.user_api" size="small" placeholder="/api/user/self" />
              </n-form-item>
              <n-form-item label="状态">
                <n-input v-model:value="formData.status_api" size="small" placeholder="/api/status" />
              </n-form-item>
              <n-form-item label="模型">
                <n-input v-model:value="formData.models_api" size="small" placeholder="/api/user/models" />
              </n-form-item>
              <n-form-item label="分组">
                <n-input v-model:value="formData.groups_api" size="small" placeholder="/api/user/self/groups" />
              </n-form-item>
              <n-form-item label="Token">
                <n-input v-model:value="formData.token_api" size="small" placeholder="/api/token/" />
              </n-form-item>
              <n-form-item label="Console URL">
                <n-input v-model:value="formData.console_url" size="small" placeholder="/console" />
              </n-form-item>
            </div>
          </n-form>
        </div>

        <div class="modal-foot">
          <n-button size="small" @click="modalVisible = false">取消</n-button>
          <n-button size="small" type="primary" :loading="saving" @click="handleSave">
            {{ editingPlatform ? '保存' : '创建' }}
          </n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { NButton, NPopconfirm, type DataTableColumns } from 'naive-ui'
import {
  AddOutline,
  CloseOutline,
  RefreshOutline,
  SearchOutline,
  ServerOutline,
  SparklesOutline,
} from '@vicons/ionicons5'
import { platformApi } from '../api'
import { useViewRefresh } from '../composables'
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
  sign_mode: 'api' | 'login'
  sign_api: string
  checkin_api: string
  user_api: string
  console_url: string
  models_api: string
  groups_api: string
  token_api: string
  status_api: string
}

const createDefaultFormData = (): PlatformForm => ({
  name: '',
  base_url: '',
  sign_mode: 'api',
  sign_api: '/api/user/sign_in',
  checkin_api: '/api/user/checkin',
  user_api: '/api/user/self',
  console_url: '/console',
  models_api: '/api/user/models',
  groups_api: '/api/user/self/groups',
  token_api: '/api/token/',
  status_api: '/api/status'
})

const endpointKeys: PlatformEndpointKey[] = [
  'sign_api', 'checkin_api', 'user_api', 'status_api',
  'models_api', 'groups_api', 'token_api', 'console_url'
]

const signModeOptions = [
  { label: '调用签到接口', value: 'api' },
  { label: '登录即签到', value: 'login' }
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

const defaultPlatform = computed(
  () => platforms.value.find(platform => platform.is_default) ?? null
)
const totalAccounts = computed(() =>
  platforms.value.reduce((sum, platform) => sum + (platform.accounts_count ?? 0), 0)
)

const getPlatformRowKey = (platform: Platform) => platform.id

const formRules = {
  name: { required: true, message: '请输入平台名称', trigger: 'blur' },
  base_url: { required: true, message: '请输入 Base URL', trigger: 'blur' }
}

const getConfiguredPathCount = (platform: Platform) =>
  endpointKeys.reduce((count, key) => {
    const value = String(platform[key] || '').trim()
    return count + (value ? 1 : 0)
  }, 0)

const getSignModeLabel = (platform: Platform) =>
  platform.sign_mode === 'login' ? '登录即签到' : '接口签到'

const formatDateTime = (value: string) => {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { hour12: false })
}

const columns = computed<DataTableColumns<Platform>>(() => [
  {
    title: '平台',
    key: 'name',
    minWidth: 260,
    render: row =>
      h('div', { class: 'platform-cell' }, [
        h('span', { class: 'platform-name', title: row.name }, row.name),
        h('span', { class: 'platform-tags' }, [
          h('span', { class: row.sign_mode === 'login' ? 'tag warning' : 'tag' }, getSignModeLabel(row)),
          row.is_default
            ? h('span', { class: 'tag primary' }, '默认')
            : h('span', { class: 'tag ghost' }, '普通')
        ])
      ])
  },
  {
    title: 'Base URL',
    key: 'base_url',
    minWidth: 280,
    ellipsis: { tooltip: true },
    render: row => h(
      'a',
      {
        class: 'mono link-url',
        href: row.base_url,
        target: '_blank',
        rel: 'noopener noreferrer'
      },
      row.base_url
    )
  },
  {
    title: '账号',
    key: 'accounts_count',
    width: 80,
    align: 'right',
    render: row => String(row.accounts_count ?? 0)
  },
  {
    title: '接口',
    key: 'paths',
    width: 80,
    align: 'right',
    render: row => `${getConfiguredPathCount(row)}/8`
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
    render: row =>
      h('div', { class: 'actions' }, [
        h(NButton, { size: 'tiny', quaternary: true, onClick: () => editPlatform(row) }, { default: () => '编辑' }),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => deletePlatform(row),
            positiveText: '删除',
            negativeText: '取消',
          },
          {
            trigger: () => h(NButton, { size: 'tiny', quaternary: true, type: 'error' }, { default: () => '删除' }),
            default: () => `确定删除平台 "${row.name}" ？删除后关联账号会失去平台配置。`
          }
        )
      ])
  }
])

const loadPlatforms = async (page = pagination.value.page) => {
  loading.value = true
  try {
    const params: { page: number; size: number; keyword?: string } = {
      page,
      size: pagination.value.pageSize
    }
    const keyword = searchKeyword.value.trim()
    if (keyword) {
      params.keyword = keyword
    }

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

const handlePageChange = (page: number) => {
  loadPlatforms(page)
}

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
  formData.value = {
    name: platform.name,
    base_url: platform.base_url,
    sign_mode: platform.sign_mode || 'api',
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

onMounted(() => {
  loadPlatforms(1)
})

watch(searchKeyword, value => {
  if (!value) {
    loadPlatforms(1)
  }
})

useViewRefresh(() => loadPlatforms(pagination.value.page))
</script>

<style scoped>
.platforms-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin: 0;
}

.page-subtitle {
  margin-top: 2px;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.head-actions {
  display: flex;
  gap: var(--spacing-2);
}

.filter-bar {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.search-input {
  max-width: 360px;
}

.platforms-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.table-wrap :deep(.n-data-table) {
  border: none;
  border-radius: 0;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-3) var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.empty-state {
  padding: var(--spacing-12) var(--spacing-5);
}

.platforms-page :deep(.platform-cell) {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 112px;
  align-items: center;
  gap: var(--spacing-3);
  width: 100%;
  min-width: 0;
}

.platforms-page :deep(.platform-name) {
  min-width: 0;
  overflow: hidden;
  color: var(--text-primary);
  font-weight: var(--font-medium);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.platforms-page :deep(.platform-tags) {
  display: inline-grid;
  grid-template-columns: 70px 36px;
  gap: 6px;
  justify-content: end;
}

.platforms-page :deep(.tag) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 18px;
  padding: 0 6px;
  border-radius: var(--radius-xs);
  font-size: 10px;
  font-weight: var(--font-medium);
  background: var(--bg-secondary);
  color: var(--text-tertiary);
}

.platforms-page :deep(.tag.primary) {
  background: var(--primary-color-light);
  color: var(--primary-color);
}

.platforms-page :deep(.tag.warning) {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.platforms-page :deep(.tag.ghost) {
  background: transparent;
  color: transparent;
}

.platforms-page :deep(.mono) {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.platforms-page :deep(.link-url) {
  text-decoration: none;
}

.platforms-page :deep(.link-url:hover) {
  color: var(--primary-color);
  text-decoration: underline;
}

.platforms-page :deep(.actions) {
  display: flex;
  gap: 2px;
}

/* 弹窗 */
.edit-modal {
  width: min(600px, calc(100vw - 24px));
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

.modal-body {
  padding: var(--spacing-4);
  max-height: 70vh;
  overflow-y: auto;
}

.modal-foot {
  justify-content: flex-end;
  gap: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.tip {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  margin-bottom: var(--spacing-3);
}

.tip code {
  font-family: var(--font-mono);
  background: transparent;
  color: var(--text-secondary);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 var(--spacing-3);
}

.form-section-title {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: var(--spacing-2) 0 var(--spacing-2);
}

@media (max-width: 900px) {
  .page-head {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
