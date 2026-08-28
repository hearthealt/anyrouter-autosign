<template>
  <UiLoading :show="loading">
    <div class="settings-pane">
      <div class="pane-head">
        <div class="pane-heading">
          <div class="pane-title"><Bell :size="15" />推送渠道</div>
          <div class="pane-desc">配置定时签到汇总与健康告警通知方式，支持多种推送渠道</div>
        </div>
        <div class="pane-actions">
          <UiButton type="primary" size="small" @click="showAddChannelModal">
            <template #icon><Plus /></template>
            添加渠道
          </UiButton>
        </div>
      </div>

      <div v-if="channels.length > 0" class="channel-grid">
        <article v-for="channel in channels" :key="channel.id" class="channel-card">
          <header class="channel-card-head">
            <span class="channel-icon" :class="channel.type">
              <component :is="getChannelIcon(channel.type)" :size="16" />
            </span>
            <div class="channel-card-heading">
              <span class="channel-name">{{ channel.name }}</span>
              <span class="channel-type-label">{{ getChannelTypeName(channel.type) }}</span>
            </div>
            <span class="channel-state" :class="channel.is_enabled ? 'is-on' : 'is-off'">
              {{ channel.is_enabled ? '已启用' : '已禁用' }}
            </span>
          </header>
          <footer class="channel-card-foot">
            <UiButton size="small" quaternary @click="testChannel(channel)" :loading="testingId === channel.id">
              <template #icon><Send /></template>
              测试
            </UiButton>
            <UiButton size="small" quaternary @click="editChannel(channel)">
              <template #icon><Pencil /></template>
              编辑
            </UiButton>
            <UiConfirm @positive-click="deleteChannel(channel.id)">
              <template #trigger>
                <UiButton size="small" quaternary class="delete-btn">
                  <template #icon><Trash2 /></template>
                  删除
                </UiButton>
              </template>
              确定删除此渠道？
            </UiConfirm>
          </footer>
        </article>
      </div>

      <div v-else class="empty-state">
        <Bell :size="40" class="empty-icon" />
        <div class="empty-title">暂无推送渠道</div>
        <div class="empty-desc">添加推送渠道后，定时任务结果将自动通知到您</div>
        <UiButton type="primary" size="small" @click="showAddChannelModal">
          <template #icon><Plus /></template>
          添加第一个渠道
        </UiButton>
      </div>
    </div>
  </UiLoading>

  <UiModal v-model:show="showChannelModal" bare :width="480" :mask-closable="false">
    <div class="modal-container">
      <div class="modal-header">
        <h3>{{ editingChannel ? '编辑渠道' : '添加渠道' }}</h3>
        <UiButton text @click="showChannelModal = false">
          <X :size="18" />
        </UiButton>
      </div>
      <div class="modal-body">
        <div class="modal-grid">
          <div class="form-item">
            <label>渠道名称</label>
            <UiInput v-model:value="channelForm.name" size="small" placeholder="给渠道起个名字" />
          </div>
          <div class="form-item">
            <label>渠道类型</label>
            <UiSelect v-model:value="channelForm.channel_type" :options="channelTypeOptions" size="small" :disabled="!!editingChannel" />
          </div>
          <div class="form-item form-item--row">
            <label>启用状态</label>
            <UiSwitch v-model:value="channelForm.is_enabled" size="small" />
          </div>
        </div>

        <div class="modal-grid modal-grid--config">
          <div class="pane-section-title">渠道配置</div>

          <template v-if="channelForm.channel_type === 'pushplus'">
            <div class="form-item">
              <label>Token</label>
              <UiInput v-model:value="channelForm.config.token" size="small" placeholder="PushPlus Token" />
            </div>
          </template>

          <template v-if="channelForm.channel_type === 'wechat_mp'">
            <div class="form-item">
              <label>AppID</label>
              <UiInput v-model:value="channelForm.config.app_id" size="small" placeholder="公众号 AppID" />
            </div>
            <div class="form-item">
              <label>AppSecret</label>
              <UiInput v-model:value="channelForm.config.app_secret" type="password" show-password-on="click" size="small" placeholder="公众号 AppSecret" />
            </div>
            <div class="form-item">
              <label>模板消息 ID</label>
              <UiInput v-model:value="channelForm.config.template_id" size="small" placeholder="模板消息 ID" />
            </div>
            <div class="form-item">
              <label>接收者 OpenID</label>
              <UiInput v-model:value="channelForm.config.openid" size="small" placeholder="接收消息的用户 OpenID" />
            </div>
          </template>

          <template v-if="channelForm.channel_type === 'wechat_work'">
            <div class="form-item">
              <label>Webhook URL</label>
              <UiInput v-model:value="channelForm.config.webhook_url" size="small" placeholder="企业微信机器人 Webhook" />
            </div>
          </template>

          <template v-if="channelForm.channel_type === 'dingtalk'">
            <div class="form-item">
              <label>Webhook URL</label>
              <UiInput v-model:value="channelForm.config.webhook_url" size="small" placeholder="钉钉机器人 Webhook" />
            </div>
            <div class="form-item">
              <label>签名密钥</label>
              <UiInput v-model:value="channelForm.config.secret" size="small" placeholder="可选" />
            </div>
          </template>

          <template v-if="channelForm.channel_type === 'feishu'">
            <div class="form-item">
              <label>Webhook URL</label>
              <UiInput v-model:value="channelForm.config.webhook_url" size="small" placeholder="飞书机器人 Webhook" />
            </div>
            <div class="form-item">
              <label>签名密钥</label>
              <UiInput v-model:value="channelForm.config.secret" size="small" placeholder="可选" />
            </div>
          </template>

          <template v-if="channelForm.channel_type === 'email'">
            <div class="form-row">
              <div class="form-item">
                <label>SMTP 服务器</label>
                <UiInput v-model:value="channelForm.config.smtp_host" size="small" placeholder="如 smtp.qq.com" />
              </div>
              <div class="form-item form-item--narrow">
                <label>端口</label>
                <UiNumberInput v-model:value="channelForm.config.smtp_port" :min="1" :max="65535" size="small" style="width: 100%;" />
              </div>
            </div>
            <div class="form-item">
              <label>发件邮箱</label>
              <UiInput v-model:value="channelForm.config.username" size="small" placeholder="发件人邮箱" />
            </div>
            <div class="form-item">
              <label>邮箱密码</label>
              <UiInput v-model:value="channelForm.config.password" type="password" show-password-on="click" size="small" placeholder="密码或授权码" />
            </div>
            <div class="form-item form-item--row">
              <label>使用 SSL</label>
              <UiSwitch v-model:value="channelForm.config.use_ssl" size="small" />
            </div>
          </template>
        </div>
      </div>
      <div class="modal-footer">
        <UiButton size="small" @click="showChannelModal = false">取消</UiButton>
        <UiButton size="small" type="primary" @click="saveChannel" :loading="savingChannel">保存</UiButton>
      </div>
    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { UiButton, UiConfirm, UiInput, UiLoading, UiModal, UiNumberInput, UiSelect, UiSwitch } from '../../ui'
import { ref, onMounted, watch } from 'vue'
import type { Component } from 'vue'
import { Bell, Mail, MessageCircle, MessageSquare, Pencil, Plus, Send, Trash2, X } from 'lucide-vue-next'
import { notifyApi } from '../../api'
import { channelTypes, getChannelTypeName } from '../../utils'
import { apiError } from '../../utils/apiError'

const emit = defineEmits<{
  (e: 'update:count', v: number): void
}>()

const getChannelIcon = (type: string): Component => {
  const icons: Record<string, Component> = {
    pushplus: Send,
    wechat_mp: MessageSquare,
    wechat_work: MessageSquare,
    dingtalk: MessageCircle,
    feishu: MessageCircle,
    email: Mail
  }
  return icons[type] || Bell
}

const loading = ref(false)
const channels = ref<any[]>([])
const testingId = ref<number | null>(null)
const showChannelModal = ref(false)
const editingChannel = ref<any>(null)
const savingChannel = ref(false)
const channelForm = ref({
  name: '',
  channel_type: 'pushplus',
  is_enabled: true,
  config: {} as Record<string, any>
})

const channelTypeOptions = Object.entries(channelTypes).map(([value, label]) => ({ value, label }))

watch(() => channels.value.length, v => emit('update:count', v))

const load = async () => {
  loading.value = true
  try {
    const res = await notifyApi.getChannels()
    channels.value = res.data || []
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    loading.value = false
  }
}

const showAddChannelModal = () => {
  editingChannel.value = null
  channelForm.value = { name: '', channel_type: 'pushplus', is_enabled: true, config: {} }
  showChannelModal.value = true
}

const editChannel = (channel: any) => {
  editingChannel.value = channel
  channelForm.value = {
    name: channel.name,
    channel_type: channel.type,
    is_enabled: channel.is_enabled,
    config: { ...channel.config }
  }
  showChannelModal.value = true
}

const saveChannel = async () => {
  if (!channelForm.value.name.trim()) {
    window.$notify('请输入渠道名称', 'warning')
    return
  }
  savingChannel.value = true
  try {
    const payload = {
      type: channelForm.value.channel_type,
      name: channelForm.value.name,
      config: channelForm.value.config,
      is_enabled: channelForm.value.is_enabled
    }
    if (editingChannel.value) {
      await notifyApi.updateChannel(editingChannel.value.id, payload)
      window.$notify('渠道更新成功', 'success')
    } else {
      await notifyApi.createChannel(payload)
      window.$notify('渠道添加成功', 'success')
    }
    showChannelModal.value = false
    load()
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    savingChannel.value = false
  }
}

const deleteChannel = async (id: number) => {
  try {
    await notifyApi.deleteChannel(id)
    window.$notify('渠道删除成功', 'success')
    load()
  } catch (e) {
    window.$notify(apiError(e), 'error')
  }
}

const testChannel = async (channel: any) => {
  testingId.value = channel.id
  try {
    await notifyApi.testChannel(channel.id)
    window.$notify('测试消息已发送', 'success')
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    testingId.value = null
  }
}

defineExpose({ load })

onMounted(load)
</script>

<style scoped>
.channel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(268px, 1fr));
  gap: var(--s3);
}

.channel-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-lg);
  background: var(--surface-raised);
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.channel-card:hover {
  border-color: var(--line);
  box-shadow: var(--lift-2);
}

.channel-card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 13px;
}

.channel-icon {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: var(--r-md);
  background: var(--signal-wash);
  color: var(--signal-deep);
}

.channel-icon.wechat_mp,
.channel-icon.wechat_work { background: var(--ok-wash); color: var(--ok); }
.channel-icon.dingtalk { background: var(--info-wash); color: var(--info); }
.channel-icon.feishu { background: var(--warn-wash); color: var(--warn); }
.channel-icon.email { background: var(--bad-wash); color: var(--bad); }

.channel-card-heading {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.channel-name {
  overflow: hidden;
  color: var(--ink-max);
  font-size: var(--fn-md);
  font-weight: var(--weight-semibold);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.channel-type-label {
  color: var(--ink-faint);
  font-size: var(--fn-xs);
}

/* 状态用一个小圆点 + 文字，比塞一枚 tag 更安静 */
.channel-state {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex: 0 0 auto;
  font-size: var(--fn-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-wide);
}

.channel-state::before {
  content: "";
  width: 5px;
  height: 5px;
  border-radius: var(--r-full);
}

.channel-state.is-on { color: var(--ok); }
.channel-state.is-on::before { background: var(--ok); box-shadow: 0 0 7px var(--ok); }
.channel-state.is-off { color: var(--ink-ghost); }
.channel-state.is-off::before { background: var(--ink-ghost); }

.channel-card-foot {
  display: flex;
  gap: 2px;
  padding: 6px;
  border-top: 1px solid var(--line-faint);
  background: var(--surface-inset);
  border-radius: 0 0 var(--r-lg) var(--r-lg);
}

.channel-card-foot > * { flex: 1; }
.channel-card-foot :deep(.ui-btn) { width: 100%; }

.empty-icon { color: var(--ink-ghost); }
.delete-btn:hover { color: var(--bad); }

/* ── 渠道编辑弹窗 */

.modal-container {
  display: flex;
  width: 100%;
  min-width: 0;
  min-height: 0;
  max-height: inherit;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
}

.modal-header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  padding: 14px var(--s5);
  border-bottom: 1px solid var(--line-faint);
  background: var(--surface-inset);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--fn-lg);
  font-weight: var(--weight-semibold);
}

.modal-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--s5);
  min-width: 0;
  min-height: 0;
  max-height: none;
  padding: var(--s5);
  overflow-y: auto;
  overscroll-behavior: contain;
}

.modal-grid {
  display: flex;
  flex-direction: column;
  gap: var(--s3);
}

.form-item { margin-bottom: 0; }

.form-item--row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s3);
}

.form-item--row label { margin-bottom: 0; }

.form-row {
  display: flex;
  gap: var(--s3);
}

.form-row > .form-item { flex: 1; min-width: 0; }
.form-row > .form-item--narrow { flex: 0 0 96px; }

.modal-footer {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: flex-end;
  gap: var(--s2);
  padding: 12px var(--s5);
  border-top: 1px solid var(--line-faint);
  background: var(--surface-inset);
}

@media (max-width: 560px) {
  .form-row { flex-direction: column; }
  .form-row > .form-item--narrow { flex: 1; }
}
</style>
