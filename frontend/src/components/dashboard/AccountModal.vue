<template>
  <UiModal v-model:show="visible" bare :width="700" :mask-closable="false">
    <div class="account-modal">
      <div class="modal-head">
        <div class="modal-title-block">
          <span class="modal-code">IDENTITY NODE / CONFIG</span>
          <h3>{{ isEdit ? '编辑账号' : '添加账号' }}</h3>
        </div>
        <UiButton text @click="close">
          <X :size="16" />
        </UiButton>
      </div>

      <div class="modal-body">
        <div class="hint">
          <Info :size="14" />
          <span>{{ hintText }}</span>
        </div>

        <!-- ① 平台：只留一行，其余身份字段都是可选的，收进「更多设置」 -->
        <div class="field field-platform">
          <label class="field-label">平台 <span class="required">*</span></label>
          <UiSelect
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

        <!-- ② 凭证：只展示当前凭证方式需要的输入 -->
        <section class="form-section">
          <div class="section-label">凭证方式 <span class="required">*</span></div>

          <!-- New API：三条路差异大，用卡片把取舍讲清楚 -->
          <div v-if="!isHttpPlatform" class="auth-picker">
            <button
              v-for="option in newApiAuthOptions"
              :key="String(option.value)"
              type="button"
              class="auth-option"
              :class="{ 'is-active': form.auth_type === option.value }"
              :aria-pressed="form.auth_type === option.value"
              @click="pickAuthType(option.value)"
            >
              <span class="auth-option-name">
                <Check v-if="form.auth_type === option.value" :size="12" />
                {{ option.label }}
              </span>
              <span class="auth-option-hint">{{ option.hint }}</span>
            </button>
          </div>

          <!-- 通用 HTTP：六种认证只是字段不同，下拉更紧凑 -->
          <div v-else class="form-grid">
            <div class="field field-full">
              <label class="field-label">认证方式</label>
              <UiSelect :value="form.auth_type" :options="authTypeOptions" size="small" @update:value="onAuthTypeSelect" />
            </div>
          </div>

          <div v-if="showSavedAuthNotice" class="saved-auth">
            <div>
              已保存 {{ getAuthTypeLabel(props.account?.auth_type || 'none') }} 凭证。
              敏感内容不会从后端回显，下方留空表示保持不变。
            </div>
            <UiCheckbox v-model:checked="form.clear_auth_data">清除已保存的凭证</UiCheckbox>
          </div>

          <div class="form-grid">
            <!-- ── 通用 HTTP 的认证字段 -->
            <template v-if="isHttpPlatform">
              <div v-if="form.auth_type === 'none'" class="field field-full">
                <span class="field-tip">该平台请求不携带任何认证信息。</span>
              </div>

              <div v-else-if="form.auth_type === 'bearer'" class="field field-full">
                <label class="field-label">Bearer Token</label>
                <UiInput
                  v-model:value="form.auth_token"
                  type="password"
                  show-password-on="click"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('Token')"
                />
              </div>

              <div v-else-if="form.auth_type === 'cookie'" class="field field-full">
                <label class="field-label">Cookie</label>
                <UiInput
                  v-model:value="form.auth_cookie"
                  type="textarea"
                  :rows="3"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('完整 Cookie，例如 session=...; token=...')"
                />
              </div>

              <div v-else-if="form.auth_type === 'header'" class="field field-full">
                <label class="field-label">Headers JSON</label>
                <UiInput
                  v-model:value="form.auth_headers_json"
                  type="textarea"
                  :rows="4"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('Header JSON')"
                />
              </div>

              <template v-else-if="form.auth_type === 'basic'">
                <div class="field">
                  <label class="field-label">Basic 用户名</label>
                  <UiInput
                    v-model:value="form.auth_username"
                    size="small"
                    :disabled="form.clear_auth_data"
                    :placeholder="secretPlaceholder('用户名')"
                  />
                </div>
                <div class="field">
                  <label class="field-label">Basic 密码</label>
                  <UiInput
                    v-model:value="form.auth_password"
                    type="password"
                    show-password-on="click"
                    size="small"
                    :disabled="form.clear_auth_data"
                    :placeholder="secretPlaceholder('密码')"
                  />
                </div>
              </template>

              <div v-else class="field field-full">
                <label class="field-label">自定义认证数据 JSON</label>
                <UiInput
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

            <!-- ── New API：系统访问令牌 -->
            <template v-else-if="form.auth_type === 'bearer'">
              <div class="field field-full">
                <label class="field-label">系统访问令牌 <span class="required">*</span></label>
                <UiInput
                  v-model:value="form.auth_token"
                  type="password"
                  show-password-on="click"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('站点「个人设置」里生成的访问令牌')"
                />
                <span class="field-tip">永不过期，无需账号密码。重新生成会让旧令牌立即失效。</span>
              </div>
            </template>

            <!-- ── New API：refresh token cookie -->
            <template v-else-if="form.auth_type === 'new_api_refresh'">
              <div class="field field-full">
                <label class="field-label">refresh token <span class="required">*</span></label>
                <UiInput
                  v-model:value="form.auth_refresh_token"
                  type="password"
                  show-password-on="click"
                  size="small"
                  :disabled="form.clear_auth_data"
                  :placeholder="secretPlaceholder('Cookie 中 new_api_refresh 的值，格式 <sid>.<secret>')"
                />
                <span class="field-tip warn">
                  每次刷新都会轮换，且与浏览器登录态互斥 —— 本站用了它，你的浏览器会被登出。
                  建议优先用账号密码或系统访问令牌。
                </span>
              </div>
            </template>

            <!-- ── New API：账号密码登录 -->
            <template v-else>
              <div class="field">
                <label class="field-label">
                  登录账号
                  <span v-if="loginRequired" class="required">*</span>
                </label>
                <UiInput
                  v-model:value="form.login_username"
                  size="small"
                  :disabled="isEdit && form.clear_login_credentials"
                  placeholder="邮箱或用户名"
                />
              </div>

              <div class="field">
                <label class="field-label">
                  登录密码
                  <span v-if="loginRequired" class="required">*</span>
                </label>
                <UiInput
                  v-model:value="form.login_password"
                  type="password"
                  show-password-on="click"
                  size="small"
                  :disabled="isEdit && form.clear_login_credentials"
                  :placeholder="isEdit ? '留空保持原密码' : '登录密码'"
                />
              </div>

              <div class="field field-full">
                <span class="field-tip">User ID 和 Session 会在登录后自动获取，不用手填。</span>
              </div>
            </template>
          </div>

          <!-- 账号密码方式的备用路径：手填 Session Cookie -->
          <div v-if="!isHttpPlatform && form.auth_type === 'none'" class="sub-panel">
            <button type="button" class="sub-toggle" @click="toggleManualSession">
              <ChevronRight :size="13" :class="{ 'is-open': showManualSession }" />
              手动填写 User ID + Session Cookie（可选，不想存密码时用）
            </button>
            <div v-if="showManualSession" class="form-grid sub-grid">
              <div class="field">
                <label class="field-label">
                  User ID
                  <span v-if="!isEdit && !!form.session_cookie.trim()" class="required">*</span>
                </label>
                <UiInput
                  v-model:value="form.user_id"
                  size="small"
                  :placeholder="isEdit ? '留空则不修改' : '手填 Session Cookie 时必需'"
                />
              </div>
              <div class="field field-full">
                <label class="field-label">
                  Session Cookie
                  <span v-if="!isEdit && !!form.user_id.trim()" class="required">*</span>
                </label>
                <UiInput
                  v-model:value="form.session_cookie"
                  type="textarea"
                  :rows="3"
                  size="small"
                  :placeholder="isEdit ? '留空则不修改' : 'Cookie 中 session 的值'"
                />
              </div>
            </div>
          </div>

          <!-- 令牌方式的兜底：令牌被吊销时用账号密码重新登录 -->
          <div v-if="usesNewApiToken" class="sub-panel">
            <button type="button" class="sub-toggle" @click="toggleFallbackLogin">
              <ChevronRight :size="13" :class="{ 'is-open': showFallbackLogin }" />
              兜底登录凭证（可选，令牌失效时自动改用账号密码）
            </button>
            <div v-if="showFallbackLogin" class="form-grid sub-grid">
              <div class="field">
                <label class="field-label">登录账号</label>
                <UiInput
                  v-model:value="form.login_username"
                  size="small"
                  :disabled="isEdit && form.clear_login_credentials"
                  placeholder="邮箱或用户名"
                />
              </div>
              <div class="field">
                <label class="field-label">登录密码</label>
                <UiInput
                  v-model:value="form.login_password"
                  type="password"
                  show-password-on="click"
                  size="small"
                  :disabled="isEdit && form.clear_login_credentials"
                  :placeholder="isEdit ? '留空保持原密码' : '登录密码'"
                />
              </div>
            </div>
          </div>

          <div v-if="isEdit && props.account?.has_login_credentials" class="saved-auth">
            <div>该账号已保存登录凭证，可作为凭证失效后的兜底。</div>
            <UiCheckbox v-model:checked="form.clear_login_credentials">清除已保存的登录凭证</UiCheckbox>
          </div>
        </section>

        <!-- ③ 剩下的都是可选项，默认收起 —— 新建账号只需要平台 + 凭证 -->
        <section class="more-section">
          <button type="button" class="more-toggle" @click="showMore = !showMore">
            <ChevronRight :size="13" :class="{ 'is-open': showMore }" />
            <span>更多设置</span>
            <span class="more-summary">{{ moreSummary }}</span>
          </button>

          <div v-if="showMore" class="form-grid more-grid">
            <template v-if="isHttpPlatform">
              <div class="field">
                <label class="field-label">外部账号 ID</label>
                <UiInput
                  v-model:value="form.external_user_id"
                  size="small"
                  :placeholder="isEdit ? '留空则不修改' : '可选，支持字符串 ID'"
                />
              </div>

              <div class="field">
                <label class="field-label">账号名称</label>
                <UiInput
                  v-model:value="form.username"
                  size="small"
                  :placeholder="isEdit ? '留空按已有值处理' : '可选，用于本地识别'"
                />
              </div>

              <div class="field">
                <label class="field-label">显示名称</label>
                <UiInput v-model:value="form.display_name" size="small" placeholder="可选" />
              </div>
            </template>

            <div class="field">
              <label class="field-label">分组</label>
              <UiSelect v-model:value="form.group_id" :options="groupOptions" size="small" placeholder="未分组" clearable />
            </div>

            <div class="field">
              <label class="field-label">访问出口</label>
              <UiSelect v-model:value="form.proxy_mode" :options="proxyModeOptions" size="small" />
            </div>

            <div v-if="form.proxy_mode === 'custom'" class="field field-full">
              <label class="field-label">代理地址</label>
              <UiInput v-model:value="form.proxy_url" size="small" placeholder="http://user:pass@host:port" />
            </div>

            <div v-if="isEdit" class="field">
              <label class="field-label">账号状态</label>
              <div class="switch-wrap">
                <UiSwitch v-model:value="form.is_active" size="small">
                  <template #checked>启用</template>
                  <template #unchecked>禁用</template>
                </UiSwitch>
              </div>
            </div>

            <div class="field field-full">
              <label class="field-label">健康告警渠道</label>
              <UiSelect
                v-model:value="form.notify_channel_ids"
                multiple
                size="small"
                :options="channelOptions"
                placeholder="仅用于定时健康检查告警"
                clearable
                :loading="loadingChannels"
              />
            </div>

            <div class="field field-full">
              <label class="field-label">备注</label>
              <UiInput
                v-model:value="form.note"
                type="textarea"
                :rows="2"
                :maxlength="255"
                size="small"
                placeholder="记录账号用途、来源或特殊说明"
              />
            </div>
          </div>
        </section>
      </div>

      <div class="modal-foot">
        <span class="modal-status"><i></i> SECURE CONFIG CHANNEL</span>
        <UiButton size="small" @click="close">取消</UiButton>
        <UiButton size="small" type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : (isHttpPlatform ? '添加' : '验证并添加') }}
        </UiButton>
      </div>
    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { UiButton, UiCheckbox, UiInput, UiModal, UiSelect, UiSwitch } from '../../ui'
import { computed, ref, watch } from 'vue'
import { Check, ChevronRight, Info, X } from 'lucide-vue-next'
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
  auth_refresh_token: '',
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

/** 账号密码方式下手填 Session Cookie 的备用路径，默认收起 */
const showManualSession = ref(false)
/** 令牌方式下的兜底登录凭证，默认收起 */
const showFallbackLogin = ref(false)
/** 分组、出口、备注、告警渠道这些可选项，默认收起 */
const showMore = ref(false)

const currentPlatform = computed(() => platforms.value.find(platform => platform.id === form.value.platform_id) || null)
const isHttpPlatform = computed(() => currentPlatform.value?.adapter_type === 'http')
const hintText = computed(() => {
  if (isEdit.value) return '只更新你填写的字段；已保存的密码、Token、Cookie 等敏感内容不会回显。'
  if (isHttpPlatform.value) return '通用 HTTP 账号不要求整数 User ID，可按目标网站选择 Bearer、Cookie、Header、Basic 或自定义认证。'
  if (usesNewApiToken.value) return '令牌方式下 User ID 会在校验时自动回填；建议同时填写登录账号密码作为令牌失效后的兜底。'
  return 'New API 平台推荐填写登录账号密码，User ID 和 Session 会在登录后自动获取。新版站点会自动识别并改用 JWT 凭证。'
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
// New API 平台的凭证方式。新版 new-api 已改用 JWT，面板凭证有三条路：
// 账号密码（自愈能力最强）、系统访问令牌（永不过期）、refresh cookie（会轮换）。
// hint 直接印在选择卡上 —— 三者的取舍不同，藏在文档里等于没写。
const newApiAuthOptions: (SelectOption<AccountAuthType> & { hint: string })[] = [
  { label: '账号密码', value: 'none', hint: '推荐：凭证过期能自动重新登录' },
  { label: '系统访问令牌', value: 'bearer', hint: '永不过期，不用存密码' },
  { label: 'refresh token', value: 'new_api_refresh', hint: '会轮换，且与浏览器登录态互斥' },
]
const usesNewApiToken = computed(
  () => !isHttpPlatform.value && (form.value.auth_type === 'bearer' || form.value.auth_type === 'new_api_refresh')
)
const groupOptions = computed(() => props.groups.map(group => ({ label: group.name, value: group.id })))

/** 新建 New API 账号且没手填 Session 时，账号密码是唯一可用凭证 */
const loginRequired = computed(
  () => !isEdit.value && !usesNewApiToken.value
    && (!form.value.session_cookie.trim() || !form.value.user_id.trim())
)

/** 已保存凭证的提示只在「当前方式确实会用到已存内容」时出现 */
const showSavedAuthNotice = computed(
  () => isEdit.value && !!props.account?.has_auth_data && (isHttpPlatform.value || usesNewApiToken.value)
)

/** 收起状态下也要能看出里面设了什么，否则「更多设置」等于一个黑盒 */
const moreSummary = computed(() => {
  const parts: string[] = []
  const group = props.groups.find(item => item.id === form.value.group_id)
  parts.push(group ? group.name : '未分组')
  parts.push(form.value.proxy_mode === 'custom' ? '自定义代理' : '直连出口')
  if (form.value.notify_channel_ids.length) parts.push(`${form.value.notify_channel_ids.length} 个告警渠道`)
  if (form.value.note.trim()) parts.push('有备注')
  if (isEdit.value && !form.value.is_active) parts.push('已禁用')
  return parts.join(' · ')
})

// 两份选项里都有 'bearer'，先按当前平台的那一份查，避免 New API 的令牌
// 被显示成通用 HTTP 的 "Bearer Token"
const getAuthTypeLabel = (type: AccountAuthType | string) => {
  const preferred = isHttpPlatform.value ? authTypeOptions : newApiAuthOptions
  const fallback = isHttpPlatform.value ? newApiAuthOptions : authTypeOptions
  return [...preferred, ...fallback].find(option => option.value === type)?.label || type
}
const secretPlaceholder = (content: string) => isEdit.value && props.account?.has_auth_data
  ? `留空保持已保存内容；填写则替换（${content}）`
  : content

const toggleManualSession = () => {
  showManualSession.value = !showManualSession.value
  // 收起时清空，否则隐藏的旧值仍会参与校验和提交
  if (!showManualSession.value) {
    form.value.user_id = ''
    form.value.session_cookie = ''
  }
}

const toggleFallbackLogin = () => {
  showFallbackLogin.value = !showFallbackLogin.value
  if (!showFallbackLogin.value) {
    form.value.login_username = ''
    form.value.login_password = ''
  }
}

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
  showManualSession.value = false
  // 编辑已存兜底凭证的账号时直接摊开，否则 login_username 有值却看不见
  showFallbackLogin.value = isEdit.value && !!props.account?.has_login_credentials
  showMore.value = false
  await Promise.all([loadPlatforms(), loadChannels()])
  if (props.account) await loadAccountNotify(props.account.id)
})

watch(() => form.value.auth_type, type => {
  if (type !== 'none') form.value.clear_auth_data = false
})

/**
 * 用户切换凭证方式时清掉另一条路径的输入。
 *
 * 只在点击/选择时做，不放在 watch 里 —— watch 也会被 applyAccountToForm
 * 和下面的平台归位触发，那会把刚从后端读出来的 login_username 一起抹掉。
 */
const pickAuthType = (type: AccountAuthType) => {
  if (form.value.auth_type === type) return
  form.value.auth_type = type
  showManualSession.value = false
  showFallbackLogin.value = false
  form.value.user_id = ''
  form.value.session_cookie = ''
  form.value.login_username = ''
  form.value.login_password = ''
  if (type !== 'bearer') form.value.auth_token = ''
  if (type !== 'new_api_refresh') form.value.auth_refresh_token = ''
}

/** UiSelect 的 update:value 是宽类型（含 null 和数组），这里收窄回 AccountAuthType */
const onAuthTypeSelect = (value: unknown) => {
  if (typeof value === 'string') pickAuthType(value as AccountAuthType)
}

// 可选的凭证方式由平台适配器决定：换平台后把不适用的值归位，
// 否则 New API 的 new_api_refresh 会留在 HTTP 的下拉里显示成空白
watch(isHttpPlatform, (isHttp, was) => {
  if (isHttp === was) return
  const allowed = (isHttp ? authTypeOptions : newApiAuthOptions).map(option => option.value)
  if (!allowed.includes(form.value.auth_type)) form.value.auth_type = 'none'
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

const buildNewApiAuthData = (): Record<string, any> | undefined => {
  const type = form.value.auth_type
  const hasSavedSameType = isEdit.value && props.account?.has_auth_data && (props.account.auth_type || 'none') === type
  if (form.value.clear_auth_data || !usesNewApiToken.value) return undefined

  if (type === 'bearer') {
    const token = form.value.auth_token.trim()
    if (!token && hasSavedSameType) return undefined
    if (!token) throw new Error('请输入系统访问令牌')
    return { token }
  }

  const refreshToken = form.value.auth_refresh_token.trim()
  if (!refreshToken && hasSavedSameType) return undefined
  if (!refreshToken) throw new Error('请输入 new_api_refresh cookie 的值')
  if (!refreshToken.includes('.')) throw new Error('refresh token 格式应为 <sid>.<secret>')
  return { refresh_token: refreshToken }
}

const validateNewApiForm = () => {
  const hasUserId = !!form.value.user_id.trim()
  const hasSessionCookie = !!form.value.session_cookie.trim()
  const hasLoginUsername = !!form.value.login_username.trim()
  const hasLoginPassword = !!form.value.login_password.trim()
  const isMigratingFromHttp = isEdit.value && props.account?.platform?.adapter_type === 'http'

  if (hasLoginUsername !== hasLoginPassword) throw new Error('登录账号和密码需要同时填写')

  // 直接提供了 PAT / refresh token 时不需要 User ID 或 Session Cookie，
  // 令牌本身就带身份，后端会用它拉一次用户信息来校验并回填 User ID。
  if (usesNewApiToken.value) return

  // 从通用 HTTP 平台切换到 New API 时，旧账号没有可复用的 New API 凭证，
  // 必须在本次提交中提供一组完整凭证，避免生成无法签到的账号。
  if (!isEdit.value || isMigratingFromHttp) {
    // User ID 只在手填 Session Cookie 时必需 —— cookie 本身不带身份。
    // 账号密码登录会从响应里拿到 ID，所以不用填。
    if (!(hasLoginUsername && hasLoginPassword) && !(hasUserId && hasSessionCookie)) {
      throw new Error('请填写登录账号和密码，或同时填写 User ID 和 Session Cookie')
    }
    return
  }

  if (hasSessionCookie && !hasUserId && !props.account?.anyrouter_user_id) {
    throw new Error('手填 Session Cookie 时需要同时填写 User ID')
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
    // 代理地址在收起的「更多设置」里，报错前先摊开，否则提示指向一个看不见的输入框
    showMore.value = true
    window.$notify('自定义代理模式需要填写代理地址', 'warning')
    return
  }

  let authData: Record<string, any> | undefined
  try {
    if (isHttpPlatform.value) {
      authData = buildAuthData()
    } else {
      validateNewApiForm()
      authData = buildNewApiAuthData()
    }
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
    clear_auth_data: form.value.clear_auth_data
      || (isHttpPlatform.value && form.value.auth_type === 'none' && !!props.account?.has_auth_data)
      // New API 账号从令牌方式切回账号密码时，必须清掉已保存的令牌，否则旧令牌会继续被使用
      || (!isHttpPlatform.value && !usesNewApiToken.value && !!props.account?.has_auth_data),
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
.account-modal { display: flex; width: 100%; min-width: 0; min-height: 0; max-height: inherit; flex-direction: column; overflow: hidden; border: 1px solid var(--line); border-radius: var(--r-xl); background: var(--surface-overlay); box-shadow: var(--lift-4); color: var(--ink-strong); }
.modal-head,
.modal-foot { display: flex; flex: 0 0 auto; align-items: center; gap: var(--s4); padding: 16px 20px; }
.modal-head { justify-content: space-between; border-bottom: 1px solid var(--line-faint); background: linear-gradient(to right, var(--grid-line) 1px, transparent 1px), var(--surface-inset); background-size: 18px 18px; }
.modal-title-block { min-width: 0; }
.modal-code,
.modal-status { display: block; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: .1em; text-transform: uppercase; }
.modal-head h3 { margin: 5px 0 0; color: var(--ink-max); font-size: var(--fn-lg); font-weight: var(--weight-semibold); }
.modal-body { display: flex; flex: 1; flex-direction: column; gap: var(--s5); min-width: 0; min-height: 0; max-height: none; padding: 20px; overflow-y: auto; overscroll-behavior: contain; }
.modal-foot { justify-content: flex-end; border-top: 1px solid var(--line-faint); background: var(--surface-inset); }
.modal-status { display: inline-flex; align-items: center; gap: 8px; margin-right: auto; color: var(--ok); }
.modal-status i { width: 5px; height: 5px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 10px color-mix(in srgb, var(--ok) 55%, transparent); }
.hint { display: flex; align-items: flex-start; gap: var(--s2); padding: 11px 13px; border: 1px solid var(--line-faint); border-left: 2px solid var(--signal-deep); border-radius: var(--r-md); background: var(--surface-inset); color: var(--ink-muted); font-size: var(--fn-xs); line-height: 1.65; }
.hint svg { margin-top: 2px; flex: 0 0 auto; color: var(--signal-deep); }

/* 分节：凭证是主角，可选项收进「更多设置」，弹窗默认只有三四行高 */
.form-section { display: flex; flex-direction: column; gap: var(--s3); min-width: 0; }
.section-label { display: flex; align-items: center; gap: var(--s2); color: var(--ink-faint); font-size: var(--fn-2xs); font-weight: var(--weight-semibold); letter-spacing: var(--track-caps); text-transform: uppercase; }
.section-label::after { content: ""; flex: 1; height: 1px; background: var(--line-faint); }

.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 16px; }
.form-grid:empty { display: none; }
.field { display: flex; min-width: 0; flex-direction: column; gap: 7px; }
.field-platform { padding-bottom: var(--s4); border-bottom: 1px solid var(--line-faint); }
.field-full { grid-column: 1 / -1; }
.field-label { color: var(--ink-muted); font-size: var(--fn-xs); font-weight: var(--weight-semibold); }
.field-tip { color: var(--ink-faint); font-size: 11px; line-height: 1.5; overflow-wrap: anywhere; }
.field-tip code { color: var(--signal-deep); }
.field-tip.warn { color: var(--warn); }
.required { margin-left: 2px; color: var(--bad); }
.switch-wrap { display: flex; min-height: 32px; align-items: center; }

/**
 * 凭证方式选择卡。三条路的取舍差别很大（会不会过期、会不会踢掉浏览器登录），
 * 下拉只给得出一个标签，卡片能把这句话直接摆在选项旁边。
 */
.auth-picker { display: grid; grid-template-columns: repeat(auto-fit, minmax(178px, 1fr)); gap: var(--s2); }
.auth-option { display: flex; flex-direction: column; gap: 4px; padding: 10px 12px; border: 1px solid var(--line-faint); border-radius: var(--r-md); background: var(--surface-inset); text-align: left; transition: border-color var(--transition-fast), background var(--transition-fast); }
.auth-option:hover { border-color: var(--line-strong); }
.auth-option.is-active { border-color: var(--signal-deep); background: var(--signal-wash); }
.auth-option-name { display: flex; align-items: center; gap: 5px; color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-semibold); }
.auth-option.is-active .auth-option-name { color: var(--signal-deep); }
.auth-option-hint { color: var(--ink-faint); font-size: 11px; line-height: 1.45; }

/* 可选路径：手填 Session / 兜底账号密码，默认收起 */
.sub-panel { display: flex; flex-direction: column; gap: var(--s3); padding: 10px 12px; border: 1px dashed var(--line); border-radius: var(--r-md); }
.sub-toggle { display: flex; align-items: center; gap: 6px; padding: 0; border: 0; background: none; color: var(--ink-muted); font-size: var(--fn-xs); font-weight: var(--weight-medium); text-align: left; }
.sub-toggle:hover { color: var(--ink-strong); }
.sub-toggle svg { flex: 0 0 auto; transition: transform var(--transition-fast); }
.sub-toggle svg.is-open { transform: rotate(90deg); }
.sub-grid { gap: 12px 16px; }

.saved-auth { display: flex; flex-direction: column; gap: var(--s2); padding: 11px 13px; border: 1px solid var(--line-faint); border-left: 2px solid var(--warn); border-radius: var(--r-md); background: var(--warn-wash); color: var(--ink-muted); font-size: var(--fn-xs); line-height: 1.65; }

/* 「更多设置」：收起时是一条摘要栏，展开才占高度 */
.more-section { display: flex; flex-direction: column; gap: var(--s4); padding-top: var(--s4); border-top: 1px solid var(--line-faint); }
.more-toggle { display: flex; align-items: center; gap: 7px; width: 100%; padding: 0; border: 0; background: none; color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-semibold); text-align: left; }
.more-toggle:hover { color: var(--signal-deep); }
.more-toggle svg { flex: 0 0 auto; color: var(--ink-faint); transition: transform var(--transition-fast); }
.more-toggle svg.is-open { transform: rotate(90deg); }
.more-summary { min-width: 0; margin-left: auto; overflow: hidden; color: var(--ink-faint); font-size: var(--fn-xs); font-weight: var(--weight-normal); text-overflow: ellipsis; white-space: nowrap; }

@media (max-width: 560px) {
  .modal-head, .modal-foot, .modal-body { padding-inline: 16px; }
  .form-grid { grid-template-columns: 1fr; }
  .field-full { grid-column: auto; }
  .modal-status { display: none; }
  .more-summary { display: none; }
}
</style>
