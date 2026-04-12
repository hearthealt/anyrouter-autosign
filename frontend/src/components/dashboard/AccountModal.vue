<template>
  <n-modal v-model:show="visible" :mask-closable="false">
    <div class="account-modal">
      <div class="modal-hero">
        <div>
          <span class="modal-kicker">{{ isEdit ? 'Edit Account' : 'Create Account' }}</span>
          <h3>{{ isEdit ? '编辑账号' : '添加账号' }}</h3>
          <p>{{ isEdit ? '只更新你填写的凭证和配置字段，未填写的内容保持原样。' : '录入平台、User ID 和 Session Cookie 后即可验证并添加账号。' }}</p>
        </div>
        <n-button text @click="close">
          <n-icon :size="20"><CloseOutline /></n-icon>
        </n-button>
      </div>

      <div class="modal-body">
        <div class="guide-grid">
          <div class="guide-card">
            <span class="guide-kicker">Capture</span>
            <p>{{ isEdit ? '可继续手动维护 Session，也可以保存登录账号和密码，让系统在 Session 失效后自动登录刷新。' : '新增时可二选一：直接填写 Session Cookie，或填写登录账号和密码自动获取 Session。User ID 仍填写请求头 `new-api-user` 的值。' }}</p>
          </div>
          <div class="guide-card subtle">
            <span class="guide-kicker">Notify</span>
            <p>勾选通知渠道后，签到成功或失败都会按所选渠道发送推送。</p>
          </div>
        </div>

        <div class="form-shell">
          <div class="form-grid">
            <div class="form-item">
              <label class="form-label">平台 <span class="required">*</span></label>
              <n-select
                v-model:value="form.platform_id"
                :options="platformOptions"
                placeholder="选择平台"
                :loading="loadingPlatforms"
              />
            </div>

            <div class="form-item">
              <label class="form-label">User ID <span class="required" v-if="!isEdit">*</span></label>
              <n-input
                v-model:value="form.user_id"
                :placeholder="isEdit ? '留空则不修改' : '请求头 new-api-user 的值'"
              />
            </div>

            <div class="form-item form-span-2">
              <label class="form-label">
                Session Cookie
                <span class="required" v-if="!isEdit && !form.login_username.trim() && !form.login_password.trim()">*</span>
              </label>
              <n-input
                v-model:value="form.session_cookie"
                type="textarea"
                :rows="4"
                :placeholder="isEdit ? '留空则不修改' : 'Cookie 中 session 的值；如已填写登录账号密码，可留空自动获取'"
              />
            </div>

            <div class="form-item">
              <label class="form-label">
                登录账号
                <span class="required" v-if="!isEdit && !form.session_cookie.trim()">*</span>
              </label>
              <n-input
                v-model:value="form.login_username"
                :disabled="isEdit && form.clear_login_credentials"
                placeholder="邮箱或用户名，可选"
              />
            </div>

            <div class="form-item">
              <label class="form-label">
                登录密码
                <span class="required" v-if="!isEdit && !form.session_cookie.trim()">*</span>
              </label>
              <n-input
                v-model:value="form.login_password"
                type="password"
                show-password-on="click"
                :disabled="isEdit && form.clear_login_credentials"
                :placeholder="isEdit ? '留空则保持原密码不变' : '登录密码，可选'"
              />
            </div>

            <div class="form-item" v-if="isEdit && props.account?.has_login_credentials">
              <label class="form-label">自动刷新</label>
              <div class="switch-shell clear-credentials-shell">
                <n-checkbox v-model:checked="form.clear_login_credentials">
                  清除已保存的登录凭证
                </n-checkbox>
              </div>
            </div>

            <div class="form-item">
              <label class="form-label">{{ isEdit ? '所属分组' : '分组（可选）' }}</label>
              <n-select
                v-model:value="form.group_id"
                :options="groupOptions"
                placeholder="选择分组"
                clearable
              />
            </div>

            <div class="form-item" v-if="isEdit">
              <label class="form-label">账号状态</label>
              <div class="switch-shell">
                <n-switch v-model:value="form.is_active">
                  <template #checked>启用</template>
                  <template #unchecked>禁用</template>
                </n-switch>
              </div>
            </div>
          </div>

          <div class="notify-shell">
            <div class="notify-head">
              <div>
                <span class="notify-kicker">Sign Notify</span>
                <h4>签到推送渠道</h4>
              </div>
              <span class="notify-caption">可多选</span>
            </div>

            <n-select
              v-model:value="form.notify_channel_ids"
              multiple
              :options="channelOptions"
              placeholder="选择推送渠道（可多选）"
              clearable
              :loading="loadingChannels"
            />

            <div class="form-tip">
              <n-icon><InformationCircleOutline /></n-icon>
              {{ isEdit ? '保存后立即更新该账号的签到推送配置。' : '如暂时不需要通知，可留空，后续再补充。' }}
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <n-button @click="close">取消</n-button>
        <n-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存修改' : '验证并添加' }}
        </n-button>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { CloseOutline, InformationCircleOutline } from '@vicons/ionicons5'
import { notifyApi, platformApi } from '../../api'
import type { Account, AccountGroup, NotifyChannel, Platform, SelectOption } from '../../types'

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

const groupOptions = computed(() =>
  props.groups.map(group => ({ label: group.name, value: group.id }))
)

const resetForm = () => {
  form.value = {
    user_id: '',
    session_cookie: '',
    login_username: '',
    login_password: '',
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
  if (!val) {
    return
  }

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

  if (!isEdit.value) {
    if (!form.value.user_id.trim()) {
      window.$notify('请输入 User ID', 'warning')
      return
    }
    const hasSessionCookie = !!form.value.session_cookie.trim()
    const hasLoginUsername = !!form.value.login_username.trim()
    const hasLoginPassword = !!form.value.login_password.trim()

    if (!hasSessionCookie && !(hasLoginUsername && hasLoginPassword)) {
      window.$notify('请填写 Session Cookie，或同时填写登录账号和密码', 'warning')
      return
    }

    if ((hasLoginUsername && !hasLoginPassword) || (!hasLoginUsername && hasLoginPassword)) {
      window.$notify('登录账号和密码需要同时填写', 'warning')
      return
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
  width: min(720px, calc(100vw - 24px));
  position: relative;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}

.account-modal::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 128px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.14) 0%, rgba(52, 211, 153, 0.08) 100%);
}

.modal-hero,
.modal-body,
.modal-footer {
  position: relative;
  z-index: 1;
}

.modal-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-4);
  padding: var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
}

.modal-kicker,
.guide-kicker,
.notify-kicker {
  display: inline-flex;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--primary-color);
}

.modal-hero h3 {
  margin: 8px 0 6px;
  font-size: clamp(26px, 3vw, 32px);
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--text-primary);
}

.modal-hero p,
.guide-card p,
.form-tip {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.7;
  color: var(--text-secondary);
}

.modal-body {
  max-height: 72vh;
  overflow-y: auto;
  padding: var(--spacing-5);
}

.guide-grid,
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.guide-card,
.form-shell,
.notify-shell,
.switch-shell {
  border: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.guide-card {
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
}

.guide-card p {
  margin-top: 8px;
}

.guide-card.subtle {
  background: var(--bg-card);
}

.form-shell {
  margin-top: var(--spacing-4);
  padding: var(--spacing-4);
  border-radius: var(--radius-xl);
}

.form-item {
  min-width: 0;
}

.form-span-2 {
  grid-column: 1 / -1;
}

.form-label {
  display: block;
  margin-bottom: 10px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.required {
  color: var(--error-color);
}

.switch-shell {
  display: flex;
  align-items: center;
  min-height: 40px;
  padding: 0 12px;
  border-radius: var(--radius-lg);
}

.clear-credentials-shell {
  justify-content: flex-start;
}

.notify-shell {
  margin-top: var(--spacing-4);
  padding: var(--spacing-4);
  border-radius: var(--radius-lg);
  border-style: dashed;
}

.notify-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--spacing-3);
  margin-bottom: 12px;
}

.notify-head h4 {
  margin: 8px 0 0;
  font-size: var(--text-lg);
  color: var(--text-primary);
}

.notify-caption {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.form-tip {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 12px;
}

.form-tip .n-icon {
  color: var(--primary-color);
  margin-top: 2px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

@media (max-width: 768px) {
  .guide-grid,
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-span-2 {
    grid-column: auto;
  }
}

@media (max-width: 640px) {
  .account-modal {
    width: min(100vw - 16px, 720px);
  }

  .modal-footer {
    flex-wrap: wrap;
  }

  .modal-footer :deep(.n-button) {
    flex: 1 1 calc(50% - 8px);
    min-width: 0;
  }
}
</style>
