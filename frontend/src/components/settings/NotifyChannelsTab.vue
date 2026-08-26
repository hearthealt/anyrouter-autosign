<template>
  <div class="card settings-panel">
    <UiLoading :show="loading">
      <div class="channel-header">
        <div class="channel-header-info">
          <div class="channel-header-title">推送渠道</div>
          <div class="channel-header-desc">配置定时签到汇总与健康告警通知方式，支持多种推送渠道</div>
        </div>
        <UiButton type="primary" @click="showAddChannelModal">
          <template #icon><Plus /></template>
          添加渠道
        </UiButton>
      </div>

      <UiDivider style="margin: 16px 0;" />

      <div v-if="channels.length > 0" class="channel-grid">
        <div v-for="channel in channels" :key="channel.id" class="channel-card">
          <div class="channel-card-header">
            <div class="channel-icon" :class="channel.type">
              <component :is="getChannelIcon(channel.type)" :size="20" />
            </div>
            <div class="channel-status">
              <UiTag :type="channel.is_enabled ? 'success' : 'default'" size="small" :bordered="false">
                {{ channel.is_enabled ? '已启用' : '已禁用' }}
              </UiTag>
            </div>
          </div>
          <div class="channel-card-body">
            <div class="channel-name">{{ channel.name }}</div>
            <div class="channel-type-label">{{ getChannelTypeName(channel.type) }}</div>
          </div>
          <div class="channel-card-footer">
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
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">
          <Bell :size="48" />
        </div>
        <div class="empty-title">暂无推送渠道</div>
        <div class="empty-desc">添加推送渠道后，定时任务结果将自动通知到您</div>
        <UiButton type="primary" @click="showAddChannelModal" style="margin-top: 16px;">
          <template #icon><Plus /></template>
          添加第一个渠道
        </UiButton>
      </div>
    </UiLoading>
  </div>

  <UiModal v-model:show="showChannelModal" :mask-closable="false">
    <div class="modal-container">
      <div class="modal-header">
        <h3>{{ editingChannel ? '编辑渠道' : '添加渠道' }}</h3>
        <UiButton text @click="showChannelModal = false">
          <X :size="20" />
        </UiButton>
      </div>
      <div class="modal-body">
        <div class="form-item">
          <label>渠道名称</label>
          <UiInput v-model:value="channelForm.name" placeholder="给渠道起个名字" />
        </div>
        <div class="form-item">
          <label>渠道类型</label>
          <UiSelect v-model:value="channelForm.channel_type" :options="channelTypeOptions" :disabled="!!editingChannel" />
        </div>
        <div class="form-item">
          <label>启用状态</label>
          <UiSwitch v-model:value="channelForm.is_enabled" />
        </div>

        <template v-if="channelForm.channel_type === 'pushplus'">
          <div class="form-item">
            <label>Token</label>
            <UiInput v-model:value="channelForm.config.token" placeholder="PushPlus Token" />
          </div>
        </template>

        <template v-if="channelForm.channel_type === 'wechat_mp'">
          <div class="form-item">
            <label>AppID</label>
            <UiInput v-model:value="channelForm.config.app_id" placeholder="公众号 AppID" />
          </div>
          <div class="form-item">
            <label>AppSecret</label>
            <UiInput v-model:value="channelForm.config.app_secret" type="password" placeholder="公众号 AppSecret" />
          </div>
          <div class="form-item">
            <label>模板消息 ID</label>
            <UiInput v-model:value="channelForm.config.template_id" placeholder="模板消息 ID" />
          </div>
          <div class="form-item">
            <label>接收者 OpenID</label>
            <UiInput v-model:value="channelForm.config.openid" placeholder="接收消息的用户 OpenID" />
          </div>
        </template>

        <template v-if="channelForm.channel_type === 'wechat_work'">
          <div class="form-item">
            <label>Webhook URL</label>
            <UiInput v-model:value="channelForm.config.webhook_url" placeholder="企业微信机器人 Webhook" />
          </div>
        </template>

        <template v-if="channelForm.channel_type === 'dingtalk'">
          <div class="form-item">
            <label>Webhook URL</label>
            <UiInput v-model:value="channelForm.config.webhook_url" placeholder="钉钉机器人 Webhook" />
          </div>
          <div class="form-item">
            <label>签名密钥</label>
            <UiInput v-model:value="channelForm.config.secret" placeholder="可选" />
          </div>
        </template>

        <template v-if="channelForm.channel_type === 'feishu'">
          <div class="form-item">
            <label>Webhook URL</label>
            <UiInput v-model:value="channelForm.config.webhook_url" placeholder="飞书机器人 Webhook" />
          </div>
          <div class="form-item">
            <label>签名密钥</label>
            <UiInput v-model:value="channelForm.config.secret" placeholder="可选" />
          </div>
        </template>

        <template v-if="channelForm.channel_type === 'email'">
          <div class="form-item">
            <label>SMTP 服务器</label>
            <UiInput v-model:value="channelForm.config.smtp_host" placeholder="如 smtp.qq.com" />
          </div>
          <div class="form-item">
            <label>SMTP 端口</label>
            <UiNumberInput v-model:value="channelForm.config.smtp_port" :min="1" :max="65535" style="width: 100%;" />
          </div>
          <div class="form-item">
            <label>发件邮箱</label>
            <UiInput v-model:value="channelForm.config.username" placeholder="发件人邮箱" />
          </div>
          <div class="form-item">
            <label>邮箱密码</label>
            <UiInput v-model:value="channelForm.config.password" type="password" placeholder="密码或授权码" />
          </div>
          <div class="form-item">
            <label>使用 SSL</label>
            <UiSwitch v-model:value="channelForm.config.use_ssl" />
          </div>
        </template>
      </div>
      <div class="modal-footer">
        <UiButton @click="showChannelModal = false">取消</UiButton>
        <UiButton type="primary" @click="saveChannel" :loading="savingChannel">保存</UiButton>
      </div>
    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { UiButton, UiConfirm, UiDivider, UiInput, UiLoading, UiModal, UiNumberInput, UiSelect, UiSwitch, UiTag } from '../../ui'
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
.settings-panel :deep(.n-card__content) { padding: 0; }
.settings-panel :deep(.n-card) { background: transparent; border: none; box-shadow: none; }

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}

.channel-header-info { flex: 1; }
.channel-header-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: 2px;
}
.channel-header-desc { font-size: var(--text-xs); color: var(--text-tertiary); }

.channel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--spacing-3);
}

.channel-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  transition: border-color var(--transition-fast);
}
.channel-card:hover { border-color: var(--border-color); }

.channel-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2);
}

.channel-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  background: var(--primary-color-light);
  color: var(--primary-color);
}
.channel-icon.pushplus { background: var(--primary-color-light); color: var(--primary-color); }
.channel-icon.wechat_mp,
.channel-icon.wechat_work { background: var(--success-color-light); color: var(--success-color); }
.channel-icon.dingtalk { background: var(--info-color-light); color: var(--info-color); }
.channel-icon.feishu { background: var(--purple-light); color: var(--purple-color); }
.channel-icon.email { background: var(--error-color-light); color: var(--error-color); }

.channel-card-body { margin-bottom: var(--spacing-2); }
.channel-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
  margin-bottom: 2px;
}
.channel-type-label { font-size: var(--text-xs); color: var(--text-tertiary); }

.channel-card-footer {
  display: flex;
  gap: 2px;
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
}
.channel-card-footer .n-button { flex: 1; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-12) var(--spacing-5);
  gap: var(--spacing-2);
}
.empty-icon { margin-bottom: var(--spacing-2); }
.empty-title { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--text-primary); }
.empty-desc { font-size: var(--text-xs); color: var(--text-tertiary); }

.delete-btn:hover { color: var(--error-color) !important; }

.modal-container {
  width: min(480px, calc(100vw - 24px));
  background: var(--bg-modal);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}
.modal-header h3 { margin: 0; font-size: var(--text-md); font-weight: var(--font-semibold); }
.modal-body { padding: var(--spacing-4); max-height: 60vh; overflow-y: auto; }

.form-item { margin-bottom: var(--spacing-3); }
.form-item:last-child { margin-bottom: 0; }
.form-item label {
  display: block;
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

@media (max-width: 768px) {
  .channel-header { flex-direction: column; align-items: flex-start; gap: var(--spacing-2); }
  .channel-grid { grid-template-columns: 1fr; }
}
</style>
