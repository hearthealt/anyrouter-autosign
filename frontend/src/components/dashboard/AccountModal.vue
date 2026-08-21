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
          <span>{{ hintText }}</span>
        </div>

        <div class="form-grid">
          <div class="field field-full">
            <label class="field-label">平台 <span class="required">*</span></label>
            <n-select
              v-model:value="form.platform_id"
              :options="platformOptions"
              size="small"
              placeholder="选择平台"
              :loading="loadingPlatforms"
            />
            <span v-if="currentPlatform" class="field-tip">
              {{ currentPlatform.adapter_type === 'http' ? '通用 HTTP 适配器' : 'New API 兼容适配器' }}
              <template v-if="currentPlatform.base_url">
                ·
                <ExternalLink :href="currentPlatform.base_url" />
              </template>
            </span>
          </div>

          <template v-if="isHttpPlatform">
            <div class="field">
              <label class="field-label">外部账号 ID</label>
              <n-input
                v-model:value="form.external_user_id"
                size="small"
                :placeholder="isEdit ? '留空则不修改/可不设置' : '可选，支持字符串 ID'"
              />
            </div>

            <div class="field">
              <label class="field-label">账号名称</label>
              <n-input
                v-model:value="form.username"
                size="small"
                :placeholder="isEdit ? '当前名称，留空时按已有值处理' : '可选，用于本地识别账号'"
              />
            </div>

            <div class="field">
              <label class="field-label">显示名称</label>
              <n-input v-model:value="form.display_name" size="small" placeholder="可选" />
            </div>

            <div class="field">
              <label class="field-label">认证方式 <span class="required">*</span></label>
              <n-select v-model:value="form.auth_type" :options="authTypeOptions" size="small" />
            </div>

            <div v-if="isEdit && props.account?.has_auth_data" class="field field-full saved-auth">
              <div>
                已保存 {{ getAuthTypeLabel(props.account.auth_type || 'custom') }} 认证信息。敏感内容不会从后端回显，以下认证字段留空表示保持不变。
              </div>
              <n-checkbox v-model:checked="form.clear_auth_data">清除已保存的认证信息</n-checkbox>
            </div>

            <template v-if="form.auth_type === 'bearer'">
              <div class="field field-full">
                <label class="field-label">Bearer Token</label>
                <n-input
                  v-model:value="form.auth_token"
                  type="password"
                  show-password-on="click"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('Token')"
                />
              </div>
            </template>

            <template v-else-if="form.auth_type === 'cookie'">
              <div class="field field-full">
                <label class="field-label">Cookie</label>
                <n-input
                  v-model:value="form.auth_cookie"
                  type="textarea"
                  :rows="3"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('完整 Cookie，例如 session=...; token=...')"
                />
              </div>
            </template>

            <template v-else-if="form.auth_type === 'header'">
              <div class="field field-full">
                <label class="field-label">Headers JSON</label>
                <n-input
                  v-model:value="form.auth_headers_json"
                  type="textarea"
                  :rows="4"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('Header JSON')"
                />
              </div>
            </template>

            <template v-else-if="form.auth_type === 'basic'">
              <div class="field">
                <label class="field-label">Basic 用户名</label>
                <n-input
                  v-model:value="form.auth_username"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('用户名')"
                />
              </div>
              <div class="field">
                <label class="field-label">Basic 密码</label>
                <n-input
                  v-model:value="form.auth_password"
                  type="password"
                  show-password-on="click"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('密码')"
                />
              </div>
            </template>

            <template v-else-if="form.auth_type === 'custom'">
              <div class="field field-full">
                <label class="field-label">自定义认证数据 JSON</label>
                <n-input
                  v-model:value="form.auth_custom_json"
                  type="textarea"
                  :rows="5"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('认证 JSON')"
                />
                <span class="field-tip">平台请求模板可通过 <code v-pre>{{auth.token}}</code> 等路径读取这里的数据。</span>
              </div>
            </template>
          </template>

          <template v-else>
            <div class="field">
              <label class="field-label">
                User ID
                <span v-if="!isEdit && !form.login_username.trim() && !form.login_password.trim()" class="required">*</span>
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
                <span v-if="!isEdit && !form.login_username.trim() && !form.login_password.trim()" class="required">*</span>
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
                <span v-if="!isEdit && (!form.session_cookie.trim() || !form.user_id.trim())" class="required">*</span>
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
                <span v-if="!isEdit && (!form.session_cookie.trim() || !form.user_id.trim())" class="required">*</span>
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
              <n-checkbox v-model:checked="form.clear_login_credentials">清除已保存的登录凭证</n-checkbox>
            </div>
          </template>

          <div class="field">
            <label class="field-label">分组</label>
            <n-select v-model:value="form.group_id" :options="groupOptions" size="small" placeholder="选择分组" clearable />
          </div>

          <div class="field">
            <label class="field-label">访问出口</label>
            <n-select v-model:value="form.proxy_mode" :options="proxyModeOptions" size="small" />
          </div>

          <div v-if="form.proxy_mode === 'custom'" class="field field-full">
            <label class="field-label">代理地址</label>
            <n-input v-model:value="form.proxy_url" size="small" placeholder="http://user:pass@host:port" />
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
          {{ isEdit ? '保存' : (isHttpPlatform ? '添加' : '验证并添加') }}
        </n-button>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CloseOutline, InformationCircleOutline } from '@vicons/ionicons5'
import { notifyApi, platformApi } from '../../api'
import ExternalLink from '../common/ExternalLink.vue'
import type {
  Account,
  AccountAuthType,
  AccountGroup,
  AccountProxyMode,
  NotifyChannel,
  Platform,
  SelectOption,
} from '../../types'

interface AccountFormSubmit {
  user_id: string
  external_user_id: string
  username: string
  display_name: string
  session_cookie: string
  login_username: string
  login_password: string
  auth_type: AccountAuthType
  auth_data?: Record<string, any>
  clear_auth_data: boolean
  note: string
  proxy_mode: AccountProxyMode
  proxy_url: string
  clear_login_credentials: boolean
  is_active?: boolean
  platform_id: number | null
  group_id: number | null
  notify_channel_ids: number[]
}

const props = defineProps<{
  show: boolean
  account?: Account | null
  groups: AccountGroup[]
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: [data: AccountFormSubmit]
}>()

const visible = computed({
  get: () => props.show,
  set: value => emit('update:show', value)
})
const isEdit = computed(() => !!props.account)

const createDefaultForm = () => ({
  user_id: '',
  external_user_id: '',
  username: '',
  display_name: '',
  session_cookie: '',
  login_username: '',
  login_password: '',
  auth_type: 'none' as AccountAuthType,
  auth_token: '',
  auth_cookie: '',
  auth_headers_json: '',
  auth_username: '',
  auth_password: '',
  auth_custom_json: '',
  clear_auth_data: false,
  note: '',
  proxy_mode: 'direct' as AccountProxyMode,
  proxy_url: '',
  clear_login_credentials: false,
  is_active: true,
  platform_id: null as number | null,
  group_id: null as number | null,
  notify_channel_ids: [] as number[]
})

const form = ref(createDefaultForm())
const submitting = ref(false)
const loadingChannels = ref(false)
const loadingPlatforms = ref(false)
const channelOptions = ref<SelectOption<number>[]>([])
const platforms = ref<Platform[]>([])
const platformOptions = ref<SelectOption<number>[]>([])

const currentPlatform = computed(() => platforms.value.find(platform => platform.id === form.value.platform_id) || null)
const isHttpPlatform = computed(() => currentPlatform.value?.adapter_type === 'http')
const hintText = computed(() => {
  if (isEdit.value) return '只更新你填写的字段；已保存的密码、Token、Cookie 等敏感内容不会回显。'
  if (isHttpPlatform.value) return '通用 HTTP 账号不要求整数 User ID，可按目标网站选择 Bearer、Cookie、Header、Basic 或自定义认证。'
  return 'New API 平台推荐填写登录账号密码，User ID 和 Session 会在登录后自动获取。'
})

const proxyModeOptions: SelectOption<AccountProxyMode>[] = [
  { label: '直连服务器出口', value: 'direct' },
  { label: '自定义代理', value: 'custom' }
]
const authTypeOptions: SelectOption<AccountAuthType>[] = [
  { label: '无认证', value: 'none' },
  { label: 'Bearer Token', value: 'bearer' },
  { label: 'Cookie', value: 'cookie' },
  { label: '自定义 Header', value: 'header' },
  { label: 'Basic Auth', value: 'basic' },
  { label: '自定义 JSON', value: 'custom' },
]
const groupOptions = computed(() => props.groups.map(group => ({ label: group.name, value: group.id })))

const getAuthTypeLabel = (type: AccountAuthType | string) => authTypeOptions.find(option => option.value === type)?.label || type
const secretPlaceholder = (content: string) => isEdit.value && props.account?.has_auth_data
  ? `留空保持已保存内容；填写则替换（${content}）`
  : content

const applyAccountToForm = (account?: Account | null) => {
  form.value = createDefaultForm()
  if (!account) return
  Object.assign(form.value, {
    user_id: '',
    external_user_id: account.external_user_id || (account.anyrouter_user_id != null ? String(account.anyrouter_user_id) : ''),
    username: account.username || '',
    display_name: account.display_name || '',
    login_username: account.login_username || '',
    auth_type: (account.auth_type || 'none') as AccountAuthType,
    note: account.note || '',
    proxy_mode: account.proxy_mode || 'direct',
    clear_auth_data: false,
    clear_login_credentials: false,
    is_active: account.is_active,
    platform_id: account.platform?.id || null,
    group_id: account.group_id || null,
  })
}

const loadPlatforms = async () => {
  loadingPlatforms.value = true
  try {
    const res: any = await platformApi.getList()
    const loaded = (Array.isArray(res.data) ? res.data : res.data?.items || []) as Platform[]
    platforms.value = [...loaded].sort((a, b) => a.is_default === b.is_default ? 0 : (a.is_default ? -1 : 1))
    platformOptions.value = platforms.value.map(platform => ({
      label: `${platform.name} · ${platform.adapter_type === 'http' ? 'HTTP' : 'New API'} (${platform.base_url})`,
      value: platform.id
    }))
    const defaultPlatform = platforms.value.find(platform => platform.is_default) ?? platforms.value[0]
    if (defaultPlatform && !form.value.platform_id) form.value.platform_id = defaultPlatform.id
  } catch (error) {
    console.error('Failed to load platforms:', error)
  } finally {
    loadingPlatforms.value = false
  }
}

const loadChannels = async () => {
  loadingChannels.value = true
  try {
    const res: any = await notifyApi.getChannels()
    channelOptions.value = (res.data || [])
      .filter((channel: NotifyChannel) => channel.is_enabled)
      .map((channel: NotifyChannel) => ({ label: channel.name, value: channel.id }))
  } catch (error) {
    console.error('Failed to load channels:', error)
  } finally {
    loadingChannels.value = false
  }
}

const loadAccountNotify = async (accountId: number) => {
  try {
    const res: any = await notifyApi.getAccountNotify(accountId)
    const enabledChannels = (res.data || []).filter((channel: any) => channel.is_enabled)
    form.value.notify_channel_ids = enabledChannels.map((channel: any) => channel.channel_id)
  } catch (error) {
    console.error('Failed to load account notify:', error)
  }
}

watch(() => props.show, async value => {
  if (!value) return
  applyAccountToForm(props.account)
  await Promise.all([loadPlatforms(), loadChannels()])
  if (props.account) await loadAccountNotify(props.account.id)
})

watch(() => form.value.auth_type, () => {
  if (form.value.auth_type !== 'none') form.value.clear_auth_data = false
})

const close = () => { visible.value = false }

const parseObject = (text: string, label: string): Record<string, any> => {
  let value: unknown
  try {
    value = JSON.parse(text)
  } catch (error: any) {
    throw new Error(`${label}不是有效 JSON：${error.message}`)
  }
  if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error(`${label}必须是 JSON 对象`)
  return value as Record<string, any>
}

const buildAuthData = (): Record<string, any> | undefined => {
  const type = form.value.auth_type
  const hasSavedSameType = isEdit.value && props.account?.has_auth_data && (props.account.auth_type || 'none') === type
  if (form.value.clear_auth_data || type === 'none') return undefined

  if (type === 'bearer') {
    const token = form.value.auth_token.trim()
    if (!token && hasSavedSameType) return undefined
    if (!token) throw new Error('请输入 Bearer Token')
    return { token }
  }
  if (type === 'cookie') {
    const cookie = form.value.auth_cookie.trim()
    if (!cookie && hasSavedSameType) return undefined
    if (!cookie) throw new Error('请输入 Cookie')
    return { cookie }
  }
  if (type === 'header') {
    const text = form.value.auth_headers_json.trim()
    if (!text && hasSavedSameType) return undefined
    if (!text) throw new Error('请输入 Headers JSON')
    const headers = parseObject(text, 'Headers JSON')
    if (!Object.keys(headers).length) throw new Error('Headers JSON 不能为空对象')
    return { headers }
  }
  if (type === 'basic') {
    const username = form.value.auth_username
    const password = form.value.auth_password
    if (!username && !password && hasSavedSameType) return undefined
    if (!username || !password) throw new Error('Basic 用户名和密码需要同时填写')
    return { username, password }
  }
  const text = form.value.auth_custom_json.trim()
  if (!text && hasSavedSameType) return undefined
  if (!text) throw new Error('请输入自定义认证数据 JSON')
  return parseObject(text, '自定义认证数据 JSON')
}

const validateNewApiForm = () => {
  const hasUserId = !!form.value.user_id.trim()
  const hasSessionCookie = !!form.value.session_cookie.trim()
  const hasLoginUsername = !!form.value.login_username.trim()
  const hasLoginPassword = !!form.value.login_password.trim()
  const isMigratingFromHttp = isEdit.value && props.account?.platform?.adapter_type === 'http'

  if (hasLoginUsername !== hasLoginPassword) throw new Error('登录账号和密码需要同时填写')

  // 从通用 HTTP 平台切换到 New API 时，旧账号没有可复用的 New API 凭证，
  // 必须在本次提交中提供一组完整凭证，避免生成无法签到的账号。
  if (!isEdit.value || isMigratingFromHttp) {
    if (!(hasLoginUsername && hasLoginPassword) && (!hasUserId || !hasSessionCookie)) {
      throw new Error('请填写登录账号和密码，或同时填写 User ID 和 Session Cookie')
    }
    return
  }

  if (!form.value.clear_login_credentials && (
    (hasLoginUsername && !hasLoginPassword && !props.account?.has_login_credentials) ||
    (!hasLoginUsername && hasLoginPassword)
  )) throw new Error('登录账号和密码需要同时填写')
}

const handleSubmit = () => {
  if (!form.value.platform_id || !currentPlatform.value) {
    window.$notify('请选择平台', 'warning')
    return
  }
  const currentProxyMode = props.account?.proxy_mode || 'direct'
  const canKeepExistingCustomProxy = isEdit.value && currentProxyMode === 'custom' && form.value.proxy_mode === 'custom'
  if (form.value.proxy_mode === 'custom' && !form.value.proxy_url.trim() && !canKeepExistingCustomProxy) {
    window.$notify('自定义代理模式需要填写代理地址', 'warning')
    return
  }

  let authData: Record<string, any> | undefined
  try {
    if (isHttpPlatform.value) authData = buildAuthData()
    else validateNewApiForm()
  } catch (error: any) {
    window.$notify(error.message || '账号配置无效', 'warning')
    return
  }

  submitting.value = true
  emit('submit', {
    user_id: form.value.user_id,
    external_user_id: form.value.external_user_id,
    username: form.value.username,
    display_name: form.value.display_name,
    session_cookie: form.value.session_cookie,
    login_username: form.value.login_username,
    login_password: form.value.login_password,
    auth_type: form.value.auth_type,
    auth_data: authData,
    clear_auth_data: form.value.clear_auth_data || (isHttpPlatform.value && form.value.auth_type === 'none' && !!props.account?.has_auth_data),
    note: form.value.note,
    proxy_mode: form.value.proxy_mode,
    proxy_url: form.value.proxy_url,
    clear_login_credentials: form.value.clear_login_credentials,
    is_active: form.value.is_active,
    platform_id: form.value.platform_id,
    group_id: form.value.group_id,
    notify_channel_ids: form.value.notify_channel_ids,
  })
}

defineExpose({ setSubmitting: (value: boolean) => { submitting.value = value } })
</script>

<style scoped>
.account-modal { width: min(680px, calc(100vw - 24px)); background: var(--bg-modal); border: 1px solid var(--border-color-light); border-radius: var(--radius-md); box-shadow: var(--shadow-lg); overflow: hidden; }
.modal-head, .modal-foot { display: flex; align-items: center; justify-content: space-between; padding: var(--spacing-3) var(--spacing-4); }
.modal-head { border-bottom: 1px solid var(--border-color-light); }
.modal-head h3 { margin: 0; font-size: var(--text-md); font-weight: var(--font-semibold); color: var(--text-primary); }
.modal-body { padding: var(--spacing-4); max-height: 72vh; overflow-y: auto; }
.modal-foot { justify-content: flex-end; gap: var(--spacing-2); border-top: 1px solid var(--border-color-light); background: var(--bg-card-hover); }
.hint { display: flex; align-items: flex-start; gap: var(--spacing-2); padding: var(--spacing-2) var(--spacing-3); background: var(--bg-secondary); border-radius: var(--radius-sm); color: var(--text-tertiary); font-size: var(--text-xs); line-height: var(--leading-relaxed); margin-bottom: var(--spacing-3); }
.hint .n-icon { margin-top: 2px; color: var(--primary-color); flex-shrink: 0; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-3); }
.field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.field-full { grid-column: 1 / -1; }
.field-label { font-size: var(--text-xs); font-weight: var(--font-medium); color: var(--text-secondary); }
.field-tip { color: var(--text-tertiary); font-size: 11px; line-height: 1.5; overflow-wrap: anywhere; }
.field-tip code { color: var(--primary-color); }
.required { color: var(--error-color); margin-left: 2px; }
.switch-wrap { display: flex; align-items: center; min-height: 28px; }
.saved-auth { padding: var(--spacing-2) var(--spacing-3); background: var(--bg-secondary); border: 1px solid var(--border-color-light); border-radius: var(--radius-sm); color: var(--text-tertiary); font-size: var(--text-xs); line-height: 1.6; }
@media (max-width: 560px) {
  .form-grid { grid-template-columns: 1fr; }
  .field-full { grid-column: auto; }
}
</style>
