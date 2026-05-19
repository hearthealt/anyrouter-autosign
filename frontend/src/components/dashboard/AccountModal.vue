<template>
  <n-modal v-model:show="visible" :mask-closable="false">
    <div class="account-modal">
      <div class="modal-head">
        <h3>{{ isEdit ? '编辑账号' : '添加账号' }}</h3>
        <n-button text @click="close">
          <n-icon :size="16"><CloseOutline /></n-icon>
        </n-button>
      </div>

      <div class="modal-body">
        <div class="hint">
          <n-icon :size="14"><InformationCircleOutline /></n-icon>
          <span>
            {{ isEdit
              ? '只更新你填写的字段，未填写的内容保持原样'
              : '推荐直接填写登录账号密码，User ID 和 Session 会在登录后自动获取' }}
          </span>
        </div>

        <div class="form-grid">
          <div class="field">
            <label class="field-label">
              平台
              <span class="required">*</span>
            </label>
            <n-select
              v-model:value="form.platform_id"
              :options="platformOptions"
              size="small"
              placeholder="选择平台"
              :loading="loadingPlatforms"
            />
          </div>

          <div class="field">
            <label class="field-label">
              User ID
              <span
                v-if="!isEdit && !form.login_username.trim() && !form.login_password.trim()"
                class="required"
              >*</span>
            </label>
            <n-input
              v-model:value="form.user_id"
              size="small"
              :placeholder="isEdit ? '留空则不修改' : '可留空，登录后自动获取'"
            />
          </div>

          <div class="field field-full">
            <label class="field-label">
              Session Cookie
              <span
                v-if="!isEdit && !form.login_username.trim() && !form.login_password.trim()"
                class="required"
              >*</span>
            </label>
            <n-input
              v-model:value="form.session_cookie"
              type="textarea"
              :rows="3"
              size="small"
              :placeholder="isEdit ? '留空则不修改' : 'Cookie 中 session 的值，或留空自动登录获取'"
            />
          </div>

          <div class="field">
            <label class="field-label">
              登录账号
              <span
                v-if="!isEdit && (!form.session_cookie.trim() || !form.user_id.trim())"
                class="required"
              >*</span>
            </label>
            <n-input
              v-model:value="form.login_username"
              size="small"
              :disabled="isEdit && form.clear_login_credentials"
              placeholder="邮箱或用户名"
            />
          </div>

          <div class="field">
            <label class="field-label">
              登录密码
              <span
                v-if="!isEdit && (!form.session_cookie.trim() || !form.user_id.trim())"
                class="required"
              >*</span>
            </label>
            <n-input
              v-model:value="form.login_password"
              type="password"
              show-password-on="click"
              size="small"
              :disabled="isEdit && form.clear_login_credentials"
              :placeholder="isEdit ? '留空保持原密码' : '登录密码'"
            />
          </div>

          <div v-if="isEdit && props.account?.has_login_credentials" class="field field-full">
            <n-checkbox v-model:checked="form.clear_login_credentials">
              清除已保存的登录凭证
            </n-checkbox>
          </div>

          <div class="field">
            <label class="field-label">分组</label>
            <n-select
              v-model:value="form.group_id"
              :options="groupOptions"
              size="small"
              placeholder="选择分组"
              clearable
            />
          </div>

          <div class="field">
            <label class="field-label">访问出口</label>
            <n-select
              v-model:value="form.proxy_mode"
              :options="proxyModeOptions"
              size="small"
            />
          </div>

          <div v-if="form.proxy_mode === 'custom'" class="field field-full">
            <label class="field-label">代理地址</label>
            <n-input
              v-model:value="form.proxy_url"
              size="small"
              placeholder="http://user:pass@host:port"
            />
          </div>

          <div class="field field-full">
            <label class="field-label">备注</label>
            <n-input
              v-model:value="form.note"
              type="textarea"
              :rows="2"
              maxlength="255"
              show-count
              size="small"
              placeholder="记录账号用途、来源或特殊说明"
            />
          </div>

          <div v-if="isEdit" class="field">
            <label class="field-label">状态</label>
            <div class="switch-wrap">
              <n-switch v-model:value="form.is_active" size="small">
                <template #checked>启用</template>
                <template #unchecked>禁用</template>
              </n-switch>
            </div>
          </div>

          <div class="field field-full">
            <label class="field-label">健康告警渠道</label>
            <n-select
              v-model:value="form.notify_channel_ids"
              multiple
              size="small"
              :options="channelOptions"
              placeholder="仅用于定时健康检查告警"
              clearable
              :loading="loadingChannels"
            />
          </div>
        </div>
      </div>

      <div class="modal-foot">
        <n-button size="small" @click="close">取消</n-button>
        <n-button size="small" type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '验证并添加' }}
        </n-button>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CloseOutline, InformationCircleOutline } from '@vicons/ionicons5'
import { notifyApi, platformApi } from '../../api'
import type { Account, AccountGroup, AccountProxyMode, NotifyChannel, Platform, SelectOption } from '../../types'

const props = defineProps<{
  show: boolean
  account?: Account | null
  groups: AccountGroup[]
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: [data: {
    user_id: string
    session_cookie: string
    login_username: string
    login_password: string
    note: string
    proxy_mode: AccountProxyMode
    proxy_url: string
    clear_login_credentials: boolean
    is_active?: boolean
    platform_id: number | null
    group_id: number | null
    notify_channel_ids: number[]
  }]
}>()

const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const isEdit = computed(() => !!props.account)

const form = ref({
  user_id: '',
  session_cookie: '',
  login_username: '',
  login_password: '',
  note: '',
  proxy_mode: 'direct' as AccountProxyMode,
  proxy_url: '',
  clear_login_credentials: false,
  is_active: true,
  platform_id: null as number | null,
  group_id: null as number | null,
  notify_channel_ids: [] as number[]
})

const submitting = ref(false)
const loadingChannels = ref(false)
const loadingPlatforms = ref(false)
const channelOptions = ref<SelectOption<number>[]>([])
const platformOptions = ref<SelectOption<number>[]>([])
const proxyModeOptions: SelectOption<AccountProxyMode>[] = [
  { label: '直连服务器出口', value: 'direct' },
  { label: '自定义代理', value: 'custom' }
]

const groupOptions = computed(() =>
  props.groups.map(group => ({ label: group.name, value: group.id }))
)

const resetForm = () => {
  form.value = {
    user_id: '',
    session_cookie: '',
    login_username: '',
    login_password: '',
    note: '',
    proxy_mode: 'direct',
    proxy_url: '',
    clear_login_credentials: false,
    is_active: true,
    platform_id: null,
    group_id: null,
    notify_channel_ids: []
  }
}

const applyAccountToForm = (account?: Account | null) => {
  if (!account) {
    resetForm()
    return
  }

  form.value = {
    user_id: '',
    session_cookie: '',
    login_username: account.login_username || '',
    login_password: '',
    note: account.note || '',
    proxy_mode: account.proxy_mode || 'direct',
    proxy_url: '',
    clear_login_credentials: false,
    is_active: account.is_active,
    platform_id: account.platform?.id || null,
    group_id: account.group_id || null,
    notify_channel_ids: []
  }
}

const loadPlatforms = async () => {
  loadingPlatforms.value = true
  try {
    const res: any = await platformApi.getList()
    const loadedPlatforms = (res.data || []) as Platform[]
    const sortedPlatforms = [...loadedPlatforms].sort((a, b) => {
      if (a.is_default === b.is_default) return 0
      return a.is_default ? -1 : 1
    })

    platformOptions.value = sortedPlatforms.map((platform: Platform) => ({
      label: `${platform.name} (${platform.base_url})`,
      value: platform.id
    }))

    const defaultPlatform = sortedPlatforms.find(platform => platform.is_default) ?? sortedPlatforms[0]

    if (defaultPlatform && !form.value.platform_id) {
      form.value.platform_id = defaultPlatform.id
    }
  } catch (e) {
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
      .filter((channel: NotifyChannel) => channel.is_enabled)
      .map((channel: NotifyChannel) => ({ label: channel.name, value: channel.id }))
  } catch (e) {
    console.error('Failed to load channels:', e)
  } finally {
    loadingChannels.value = false
  }
}

const loadAccountNotify = async (accountId: number) => {
  try {
    const res = await notifyApi.getAccountNotify(accountId)
    const enabledChannels = (res.data || []).filter((channel: any) => channel.is_enabled)
    form.value.notify_channel_ids = enabledChannels.map((channel: any) => channel.channel_id)
  } catch (e) {
    console.error('Failed to load account notify:', e)
  }
}

watch(() => props.show, async (val) => {
  if (!val) return

  applyAccountToForm(props.account)
  await Promise.all([loadPlatforms(), loadChannels()])

  if (props.account) {
    await loadAccountNotify(props.account.id)
  }
})

const close = () => {
  visible.value = false
}

const handleSubmit = () => {
  if (!form.value.platform_id) {
    window.$notify('请选择平台', 'warning')
    return
  }

  const currentProxyMode = props.account?.proxy_mode || 'direct'
  const canKeepExistingCustomProxy = isEdit.value && currentProxyMode === 'custom' && form.value.proxy_mode === 'custom'

  if (form.value.proxy_mode === 'custom' && !form.value.proxy_url.trim() && !canKeepExistingCustomProxy) {
    window.$notify('自定义代理模式需要填写代理地址', 'warning')
    return
  }

  if (!isEdit.value) {
    const hasUserId = !!form.value.user_id.trim()
    const hasSessionCookie = !!form.value.session_cookie.trim()
    const hasLoginUsername = !!form.value.login_username.trim()
    const hasLoginPassword = !!form.value.login_password.trim()
    const hasLoginCredentials = hasLoginUsername && hasLoginPassword

    if ((hasLoginUsername && !hasLoginPassword) || (!hasLoginUsername && hasLoginPassword)) {
      window.$notify('登录账号和密码需要同时填写', 'warning')
      return
    }

    if (!hasLoginCredentials) {
      if (!hasUserId) {
        window.$notify('请填写登录账号和密码，或同时填写 User ID 和 Session Cookie', 'warning')
        return
      }
      if (!hasSessionCookie) {
        window.$notify('仅填写 User ID 时还需提供 Session Cookie', 'warning')
        return
      }
    }
  } else {
    const hasLoginUsername = !!form.value.login_username.trim()
    const hasLoginPassword = !!form.value.login_password.trim()

    if (!form.value.clear_login_credentials && ((hasLoginUsername && !hasLoginPassword && !props.account?.has_login_credentials) || (!hasLoginUsername && hasLoginPassword))) {
      window.$notify('登录账号和密码需要同时填写', 'warning')
      return
    }
  }

  submitting.value = true
  emit('submit', { ...form.value })
}

defineExpose({
  setSubmitting: (val: boolean) => { submitting.value = val }
})
</script>

<style scoped>
.account-modal {
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
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-4);
  max-height: 72vh;
  overflow-y: auto;
}

.modal-foot {
  justify-content: flex-end;
  gap: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.hint {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--spacing-3);
}

.hint .n-icon {
  margin-top: 2px;
  color: var(--primary-color);
  flex-shrink: 0;
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
  min-width: 0;
}

.field-full {
  grid-column: 1 / -1;
}

.field-label {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.required {
  color: var(--error-color);
  margin-left: 2px;
}

.switch-wrap {
  display: flex;
  align-items: center;
  min-height: 28px;
}

@media (max-width: 560px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .field-full {
    grid-column: auto;
  }
}
</style>
