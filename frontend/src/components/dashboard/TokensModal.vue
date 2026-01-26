<template>
  <n-modal v-model:show="visible" :mask-closable="false">
    <div class="modal-container tokens-modal">
      <div class="modal-header">
        <div class="modal-title-group">
          <div class="modal-icon">
            <n-icon :size="18"><KeyOutline /></n-icon>
          </div>
          <div>
            <h3>API 令牌</h3>
            <span class="modal-subtitle">{{ account?.username }}</span>
          </div>
        </div>
        <n-button text @click="close">
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
            <n-button size="small" type="primary" @click="openAddDrawer">
              <template #icon><n-icon><AddOutline /></n-icon></template>
              添加令牌
            </n-button>
            <n-button size="small" secondary @click="$emit('sync')" :loading="syncing">
              <template #icon><n-icon><RefreshOutline /></n-icon></template>
              同步令牌
            </n-button>
          </div>
        </div>

        <n-spin :show="loading">
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
                  <n-button size="tiny" quaternary @click="openEditDrawer(token)">
                    <template #icon><n-icon :size="14"><CreateOutline /></n-icon></template>
                  </n-button>
                  <n-popconfirm @positive-click="$emit('delete', token)">
                    <template #trigger>
                      <n-button size="tiny" quaternary :loading="deletingId === token.token_id" style="color: var(--error-color);">
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
        <n-button @click="close">关闭</n-button>
      </div>
    </div>
  </n-modal>

  <!-- 添加/编辑令牌抽屉 -->
  <n-drawer v-model:show="showDrawer" :width="400" placement="right">
    <n-drawer-content :title="editingToken ? '编辑令牌' : '添加令牌'" closable>
      <div class="token-form">
        <div class="form-item">
          <label class="form-label">令牌名称 <span class="required">*</span></label>
          <n-input v-model:value="tokenForm.name" placeholder="请输入令牌名称" />
        </div>
        <div class="form-item">
          <label class="form-label">额度设置</label>
          <n-switch v-model:value="tokenForm.unlimited_quota">
            <template #checked>无限额度</template>
            <template #unchecked>限制额度</template>
          </n-switch>
        </div>
        <div class="form-item" v-if="!tokenForm.unlimited_quota">
          <label class="form-label">剩余额度</label>
          <n-input-number v-model:value="tokenForm.remain_quota" :min="0" :step="100000" style="width: 100%;">
            <template #suffix>（约 ${{ (tokenForm.remain_quota / 500000).toFixed(2) }}）</template>
          </n-input-number>
        </div>
        <div class="form-item">
          <label class="form-label">过期时间</label>
          <n-select
            v-model:value="tokenForm.expired_time"
            :options="expireOptions"
            placeholder="选择过期时间"
          />
        </div>
        <div class="form-item">
          <label class="form-label">模型限制</label>
          <n-switch v-model:value="tokenForm.model_limits_enabled">
            <template #checked>启用限制</template>
            <template #unchecked>不限制</template>
          </n-switch>
        </div>
        <div class="form-item" v-if="tokenForm.model_limits_enabled">
          <label class="form-label">可用模型</label>
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
          <label class="form-label">分组</label>
          <n-select
            v-model:value="tokenForm.group"
            :options="tokenGroupOptions"
            :loading="loadingTokenGroups"
            placeholder="选择分组"
          />
        </div>
        <div class="form-item">
          <label class="form-label">IP 白名单（可选）</label>
          <n-input v-model:value="tokenForm.allow_ips" placeholder="留空表示不限制，多个 IP 用逗号分隔" />
        </div>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <n-button @click="showDrawer = false">取消</n-button>
          <n-button type="primary" @click="handleSaveToken" :loading="savingToken">
            {{ editingToken ? '保存修改' : '创建令牌' }}
          </n-button>
        </div>
      </template>
    </n-drawer-content>
  </n-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  KeyOutline, CloseOutline, AddOutline, RefreshOutline,
  CopyOutline, CreateOutline, TrashOutline
} from '@vicons/ionicons5'
import { accountApi } from '../../api'
import { useClipboard, useFormat } from '../../composables'
import type { Account, ApiToken, SelectOption, CreateTokenParams } from '../../types'

const props = defineProps<{
  show: boolean
  account: Account | null
  tokens: ApiToken[]
  loading: boolean
  syncing: boolean
  deletingId: number | null
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  sync: []
  delete: [token: ApiToken]
  create: [data: CreateTokenParams]
  edit: [tokenId: number, data: CreateTokenParams]
}>()

const { copyToken: copyToClipboard } = useClipboard()
const { formatQuota } = useFormat()

const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

// 抽屉状态
const showDrawer = ref(false)
const editingToken = ref<ApiToken | null>(null)
const savingToken = ref(false)

// 表单数据
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

// 选项数据
const loadingModels = ref(false)
const loadingTokenGroups = ref(false)
const availableModelOptions = ref<SelectOption<string>[]>([])
const tokenGroupOptions = ref<SelectOption<string>[]>([])

const expireOptions = [
  { label: '永不过期', value: -1 },
  { label: '1 小时', value: 1 },
  { label: '1 天', value: 24 },
  { label: '7 天', value: 24 * 7 },
  { label: '30 天', value: 24 * 30 },
  { label: '90 天', value: 24 * 90 },
  { label: '365 天', value: 24 * 365 }
]

const close = () => {
  visible.value = false
}

const copyToken = (key: string) => {
  copyToClipboard(key)
}

const parseModels = (modelLimits: string): string[] => {
  if (!modelLimits) return []
  return modelLimits.split(',').map(m => m.trim()).filter(m => m)
}

// 加载可用模型
const loadAvailableModels = async () => {
  if (!props.account) return
  loadingModels.value = true
  try {
    const res = await accountApi.getAvailableModels(props.account.id)
    const models = res.data || []
    availableModelOptions.value = models.map((m: string) => ({ label: m, value: m }))
  } catch (e) {
    console.error('Failed to load models:', e)
  } finally {
    loadingModels.value = false
  }
}

// 加载令牌分组
const loadTokenGroups = async () => {
  if (!props.account) return
  loadingTokenGroups.value = true
  try {
    const res = await accountApi.getAccountGroups(props.account.id)
    const groupsData = res.data || {}
    tokenGroupOptions.value = Object.entries(groupsData).map(([key, val]: [string, any]) => ({
      label: `${key} - ${val.desc || ''}`,
      value: key
    }))
  } catch (e) {
    console.error('Failed to load token groups:', e)
  } finally {
    loadingTokenGroups.value = false
  }
}

// 重置表单
const resetForm = () => {
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

// 打开添加抽屉
const openAddDrawer = () => {
  resetForm()
  showDrawer.value = true
}

// 打开编辑抽屉
const openEditDrawer = (token: ApiToken) => {
  editingToken.value = token
  tokenForm.value = {
    name: token.name || '',
    remain_quota: token.remain_quota || 500000,
    expired_time: token.expired_time ?? -1,
    unlimited_quota: token.unlimited_quota || false,
    model_limits_enabled: token.model_limits_enabled || false,
    model_limits_array: token.model_limits ? token.model_limits.split(',').filter(m => m.trim()) : [],
    group: token.group || 'default',
    allow_ips: token.allow_ips || ''
  }
  showDrawer.value = true
}

// 保存令牌
const handleSaveToken = async () => {
  if (!tokenForm.value.name.trim()) {
    window.$notify('请输入令牌名称', 'warning')
    return
  }

  savingToken.value = true
  const formData: CreateTokenParams = {
    name: tokenForm.value.name,
    remain_quota: tokenForm.value.remain_quota,
    expired_time: tokenForm.value.expired_time,
    unlimited_quota: tokenForm.value.unlimited_quota,
    model_limits_enabled: tokenForm.value.model_limits_enabled,
    model_limits: tokenForm.value.model_limits_array.join(','),
    allow_ips: tokenForm.value.allow_ips,
    group: tokenForm.value.group
  }

  try {
    if (editingToken.value) {
      emit('edit', editingToken.value.token_id, formData)
    } else {
      emit('create', formData)
    }
    showDrawer.value = false
    resetForm()
  } finally {
    savingToken.value = false
  }
}

// 监听抽屉打开
watch(showDrawer, (val) => {
  if (val) {
    loadAvailableModels()
    loadTokenGroups()
  }
})
</script>

<style scoped>
.tokens-modal {
  width: 680px;
}

.modal-container {
  background: var(--bg-modal);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.modal-title-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.modal-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-subtitle {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.tokens-body {
  padding: 0;
}

.tokens-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-card-hover);
  border-bottom: 1px solid var(--border-color);
}

.tokens-stats {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-1);
}

.tokens-count {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
}

.tokens-label {
  font-size: var(--text-base);
  color: var(--text-tertiary);
}

.tokens-actions {
  display: flex;
  gap: var(--spacing-2);
}

.tokens-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-3);
  max-height: 420px;
  overflow-y: auto;
  padding: var(--spacing-3);
}

.token-card {
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  transition: all var(--transition-fast);
}

.token-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.token-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2);
}

.token-name {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

.token-quota {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-shrink: 0;
}

.quota-used {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.token-models {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-1);
  margin-bottom: var(--spacing-2);
  max-height: 48px;
  overflow-y: auto;
}

.token-models .n-tag {
  background: var(--info-color-light);
  color: var(--info-color);
  font-size: 10px;
}

.token-key-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-2);
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: var(--spacing-1) var(--spacing-1) var(--spacing-1) var(--spacing-2);
}

.token-key {
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  font-size: var(--text-xs);
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
  padding: var(--spacing-12) var(--spacing-5);
}

.empty-icon {
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-3);
}

.empty-text {
  font-size: var(--text-lg);
  font-weight: var(--font-medium);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-1);
}

.empty-hint {
  font-size: var(--text-base);
  color: var(--text-tertiary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--border-color);
  background: var(--bg-card-hover);
}

.token-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
}

@media (max-width: 768px) {
  .tokens-modal {
    width: 95vw;
    max-width: 680px;
  }

  .tokens-list {
    grid-template-columns: 1fr;
  }
}
</style>
