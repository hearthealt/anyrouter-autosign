<template>
  <UiModal v-model:show="visible" bare :width="680" :mask-closable="false">
    <div class="modal-container tokens-modal">
      <div class="modal-header">
        <div class="modal-title-group">
          <div class="modal-icon">
            <KeyRound :size="18" />
          </div>
          <div>
            <span class="modal-code">ACCESS KEY / VAULT</span>
            <h3>API 令牌</h3>
            <span class="modal-subtitle">{{ account?.username }}</span>
          </div>
        </div>
        <UiButton text @click="close">
          <X :size="20" />
        </UiButton>
      </div>

      <div class="modal-body tokens-body">
        <div class="tokens-toolbar">
          <div class="tokens-stats">
            <span class="tokens-count">{{ tokens.length }}</span>
            <span class="tokens-label">个令牌</span>
          </div>
          <div class="tokens-actions">
            <UiButton size="small" type="primary" @click="openAddDrawer">
              <template #icon><Plus /></template>
              添加令牌
            </UiButton>
            <UiButton size="small" secondary @click="$emit('sync')" :loading="syncing">
              <template #icon><RefreshCw /></template>
              同步令牌
            </UiButton>
          </div>
        </div>

        <UiLoading :show="loading">
          <div v-if="tokens.length > 0" class="tokens-list">
            <div v-for="token in tokens" :key="token.id" class="token-card">
              <div class="token-header">
                <div class="token-name">{{ token.name || '未命名令牌' }}</div>
                <div class="token-quota">
                  <span class="quota-used">已用 {{ formatQuota(token.used_quota) }}</span>
                  <UiTag v-if="token.unlimited_quota" size="tiny" :bordered="false" type="success">无限</UiTag>
                  <UiTag v-else size="tiny" :bordered="false" type="info">{{ formatQuota(token.used_quota + token.remain_quota) }}</UiTag>
                </div>
              </div>
              <div v-if="token.model_limits" class="token-models">
                <UiTag
                  v-for="model in parseModels(token.model_limits)"
                  :key="model"
                  size="tiny"
                  :bordered="false"
                >
                  {{ model }}
                </UiTag>
              </div>
              <div class="token-key-row">
                <code class="token-key">{{ renderKey(token) }}</code>
                <div class="token-actions">
                  <UiButton size="tiny" quaternary :title="revealed.has(token.token_id) ? '隐藏' : '显示明文'" @click="toggleReveal(token)">
                    <template #icon>
                      <component :is="revealed.has(token.token_id) ? EyeOff : Eye" :size="14" />
                    </template>
                  </UiButton>
                  <UiButton size="tiny" quaternary @click="copyToken(token.key)">
                    <template #icon><Copy :size="14" /></template>
                  </UiButton>
                  <UiButton size="tiny" quaternary @click="openEditDrawer(token)">
                    <template #icon><Pencil :size="14" /></template>
                  </UiButton>
                  <UiConfirm @positive-click="$emit('delete', token)">
                    <template #trigger>
                      <UiButton size="tiny" quaternary :loading="deletingId === token.token_id" style="color: var(--error-color);">
                        <template #icon><Trash2 :size="14" /></template>
                      </UiButton>
                    </template>
                    确定删除该令牌吗？
                  </UiConfirm>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="tokens-empty">
            <div class="empty-icon">
              <KeyRound :size="40" />
            </div>
            <div class="empty-text">暂无 API 令牌</div>
            <div class="empty-hint">点击"同步令牌"从服务器获取</div>
          </div>
        </UiLoading>
      </div>

      <div class="modal-footer">
        <span class="modal-status"><i></i> ENCRYPTED SESSION</span>
        <UiButton @click="close">关闭</UiButton>
      </div>
    </div>
  </UiModal>

  <!-- 添加/编辑令牌抽屉 -->
  <UiDrawer v-model:show="showDrawer" :width="400" kicker="Token" :title="editingToken ? '编辑令牌' : '添加令牌'">
      <div class="token-form">
        <div class="form-item">
          <label class="form-label">令牌名称 <span class="required">*</span></label>
          <UiInput v-model:value="tokenForm.name" placeholder="请输入令牌名称" />
        </div>
        <div class="form-item">
          <label class="form-label">额度设置</label>
          <UiSwitch v-model:value="tokenForm.unlimited_quota">
            <template #checked>无限额度</template>
            <template #unchecked>限制额度</template>
          </UiSwitch>
        </div>
        <div class="form-item" v-if="!tokenForm.unlimited_quota">
          <label class="form-label">剩余额度</label>
          <UiNumberInput v-model:value="tokenForm.remain_quota" :min="0" :step="100000" style="width: 100%;">
            <template #suffix>（约 ${{ (tokenForm.remain_quota / 500000).toFixed(2) }}）</template>
          </UiNumberInput>
        </div>
        <div class="form-item">
          <label class="form-label">过期时间</label>
          <UiSelect
            v-model:value="tokenForm.expired_time"
            :options="expireOptions"
            placeholder="选择过期时间"
          />
        </div>
        <div class="form-item">
          <label class="form-label">模型限制</label>
          <UiSwitch v-model:value="tokenForm.model_limits_enabled">
            <template #checked>启用限制</template>
            <template #unchecked>不限制</template>
          </UiSwitch>
        </div>
        <div class="form-item" v-if="tokenForm.model_limits_enabled">
          <label class="form-label">可用模型</label>
          <UiSelect
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
          <UiSelect
            v-model:value="tokenForm.group"
            :options="tokenGroupOptions"
            :loading="loadingTokenGroups"
            placeholder="选择分组"
          />
        </div>
        <div class="form-item">
          <label class="form-label">IP 白名单（可选）</label>
          <UiInput v-model:value="tokenForm.allow_ips" placeholder="留空表示不限制，多个 IP 用逗号分隔" />
        </div>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <UiButton @click="showDrawer = false">取消</UiButton>
          <UiButton type="primary" @click="handleSaveToken" :loading="savingToken">
            {{ editingToken ? '保存修改' : '创建令牌' }}
          </UiButton>
        </div>
      </template>
  </UiDrawer>
</template>

<script setup lang="ts">
import { UiButton, UiConfirm, UiDrawer, UiInput, UiLoading, UiModal, UiNumberInput, UiSelect, UiSwitch, UiTag } from '../../ui'
import { ref, computed, watch } from 'vue'
import { Copy, Eye, EyeOff, KeyRound, Pencil, Plus, RefreshCw, Trash2, X } from 'lucide-vue-next'
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
  create: [data: CreateTokenParams, done: (success: boolean) => void]
  edit: [tokenId: number, data: CreateTokenParams, done: (success: boolean) => void]
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

const revealed = ref(new Set<number>())

const toggleReveal = (token: ApiToken) => {
  const next = new Set(revealed.value)
  if (next.has(token.token_id)) next.delete(token.token_id)
  else next.add(token.token_id)
  revealed.value = next
}

const renderKey = (token: ApiToken) => {
  const key = token.key || ''
  if (revealed.value.has(token.token_id)) return `sk-${key}`
  return `sk-${key.slice(0, 8)}...${key.slice(-4)}`
}

watch(() => props.show, (val) => {
  if (!val) revealed.value = new Set()
})

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
    remain_quota: token.remain_quota ?? 500000,
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
    const success = await new Promise<boolean>((resolve) => {
      if (editingToken.value) {
        emit('edit', editingToken.value.token_id, formData, resolve)
      } else {
        emit('create', formData, resolve)
      }
    })

    if (!success) {
      return
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
.modal-container { display: flex; width: 100%; min-width: 0; min-height: 0; max-height: inherit; flex-direction: column; overflow: hidden; border: 1px solid var(--line); border-radius: var(--r-xl); background: var(--surface-overlay); box-shadow: var(--lift-4); }
.tokens-modal { display: flex; min-width: 0; flex-direction: column; color: var(--ink-strong); }
.modal-header { display: flex; flex: 0 0 auto; align-items: center; justify-content: space-between; gap: var(--s4); padding: 16px 20px; border-bottom: 1px solid var(--line-faint); background: linear-gradient(to right, var(--grid-line) 1px, transparent 1px), var(--surface-inset); background-size: 18px 18px; }
.modal-title-group { display: flex; align-items: center; gap: 12px; min-width: 0; }
.modal-icon { display: grid; width: 34px; height: 34px; flex: 0 0 auto; place-items: center; border: 1px solid color-mix(in srgb, var(--signal-deep) 26%, transparent); border-radius: 50%; color: var(--signal-deep); background: var(--signal-wash); }
.modal-code, .modal-status { display: block; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: .1em; text-transform: uppercase; }
.modal-header h3 { margin: 4px 0 0; color: var(--ink-max); font-size: var(--fn-lg); font-weight: var(--weight-semibold); }
.modal-subtitle { display: block; margin-top: 3px; color: var(--ink-muted); font-size: var(--fn-xs); }
.modal-body { flex: 1; min-width: 0; min-height: 0; max-height: none; padding: 20px; overflow-y: auto; overscroll-behavior: contain; }
.modal-footer { display: flex; flex: 0 0 auto; align-items: center; justify-content: flex-end; gap: var(--s2); padding: 14px 20px; border-top: 1px solid var(--line-faint); background: var(--surface-inset); }
.modal-status { display: inline-flex; align-items: center; gap: 8px; margin-right: auto; color: var(--ok); }
.modal-status i { width: 5px; height: 5px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 10px color-mix(in srgb, var(--ok) 55%, transparent); }
.tokens-toolbar { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--s4); margin-bottom: 16px; }
.tokens-stats { display: flex; align-items: baseline; gap: 7px; }
.tokens-count { color: var(--ink-max); font-family: var(--font-display); font-size: clamp(2.4rem, 5vw, 4.4rem); font-weight: var(--weight-semibold); letter-spacing: -.08em; line-height: .82; }
.tokens-label { color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .1em; }
.tokens-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.tokens-list { display: flex; flex-direction: column; gap: 10px; }
.token-card { position: relative; padding: 14px 15px; overflow: hidden; border: 1px solid var(--line-faint); border-radius: var(--r-lg); background: var(--surface-raised); transition: border-color var(--transition-fast), transform var(--transition-bounce), box-shadow var(--transition-bounce); }
.token-card::before { position: absolute; top: 0; right: 0; left: 0; height: 2px; content: ''; background: linear-gradient(90deg, var(--signal-deep), transparent 62%); }
.token-card:hover { border-color: var(--line); box-shadow: var(--lift-2); transform: translateY(-2px); }
.token-header { display: flex; align-items: center; justify-content: space-between; gap: var(--s2); margin-bottom: 8px; }
.token-name { color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-semibold); }
.token-quota { display: inline-flex; align-items: center; gap: 7px; }
.quota-used { color: var(--ink-faint); font-family: var(--font-mono); font-size: 10px; }
.token-models { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 9px; }
.token-key-row { display: flex; align-items: center; justify-content: space-between; gap: var(--s2); padding-top: 10px; border-top: 1px solid var(--line-faint); }
.token-key { min-width: 0; overflow: hidden; color: var(--signal-deep); font-family: var(--font-mono); font-size: var(--fn-xs); text-overflow: ellipsis; white-space: nowrap; }
.token-actions { display: flex; flex: 0 0 auto; gap: 2px; }
.tokens-empty { display: flex; min-height: 250px; flex-direction: column; align-items: center; justify-content: center; gap: 8px; padding: var(--s8); border: 1px dashed var(--line); color: var(--ink-faint); background: var(--surface-inset); }
.empty-icon { color: var(--signal-deep); }
.empty-text { color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-semibold); }
.empty-hint { color: var(--ink-faint); font-size: var(--fn-xs); }
.token-form { display: flex; flex-direction: column; gap: 16px; }
.form-item { display: flex; flex-direction: column; gap: 7px; }
.form-label { color: var(--ink-muted); font-size: var(--fn-xs); font-weight: var(--weight-semibold); }
.required { margin-left: 2px; color: var(--bad); }
.drawer-footer { display: flex; justify-content: flex-end; gap: var(--s2); }
@media (max-width: 560px) {
  .modal-header, .modal-footer, .modal-body { padding-inline: 16px; }
  .tokens-toolbar { align-items: stretch; flex-direction: column; }
  .tokens-actions { display: grid; grid-template-columns: 1fr 1fr; }
  .token-header, .token-key-row { align-items: flex-start; flex-direction: column; }
  .token-actions { align-self: stretch; justify-content: flex-end; }
  .modal-status { display: none; }
}
</style>
