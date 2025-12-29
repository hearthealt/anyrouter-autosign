<template>
  <div>
    <n-tabs type="line">
      <!-- 基础设置 -->
      <n-tab-pane name="basic" tab="自动签到">
        <n-card>
          <n-spin :show="loadingSettings">
            <div class="setting-section">
              <div class="setting-item">
                <div class="setting-info">
                  <div class="setting-label">自动签到</div>
                  <div class="setting-desc">开启后将在指定时间自动为所有账号签到</div>
                </div>
                <n-switch v-model:value="settings.auto_sign_enabled" />
              </div>

              <div class="setting-item" v-if="settings.auto_sign_enabled">
                <div class="setting-info">
                  <div class="setting-label">签到时间</div>
                  <div class="setting-desc">每天在此时间执行自动签到</div>
                </div>
                <n-time-picker v-model:value="signTimeValue" format="HH:mm" style="width: 120px;" />
              </div>

              <div class="setting-item" v-if="settings.auto_sign_enabled && schedulerStatus.next_run">
                <div class="setting-info">
                  <div class="setting-label">下次签到</div>
                  <div class="setting-desc">系统将在此时间自动执行签到</div>
                </div>
                <n-tag type="info">{{ schedulerStatus.next_run }}</n-tag>
              </div>

              <div class="setting-tip" v-if="settings.auto_sign_enabled">
                <n-icon><InformationCircleOutline /></n-icon>
                签到推送渠道请在「控制台」编辑账号时配置
              </div>
            </div>

            <n-divider title-placement="left">健康检查</n-divider>

            <div class="setting-section">
              <div class="setting-item">
                <div class="setting-info">
                  <div class="setting-label">定时健康检查</div>
                  <div class="setting-desc">定期检查账号凭证是否有效，并更新额度缓存</div>
                </div>
                <n-switch v-model:value="settings.health_check_enabled" />
              </div>

              <div class="setting-item" v-if="settings.health_check_enabled">
                <div class="setting-info">
                  <div class="setting-label">检查间隔（小时）</div>
                  <div class="setting-desc">每隔多少小时执行一次健康检查</div>
                </div>
                <n-input-number v-model:value="settings.health_check_interval" :min="1" :max="24" style="width: 100px;" />
              </div>
            </div>

            <n-divider title-placement="left">失败重试</n-divider>

            <div class="setting-section">
              <div class="setting-item">
                <div class="setting-info">
                  <div class="setting-label">自动重试</div>
                  <div class="setting-desc">签到失败后自动重试</div>
                </div>
                <n-switch v-model:value="settings.sign_retry_enabled" />
              </div>

              <div class="setting-item" v-if="settings.sign_retry_enabled">
                <div class="setting-info">
                  <div class="setting-label">最大重试次数</div>
                  <div class="setting-desc">签到失败后最多重试的次数</div>
                </div>
                <n-input-number v-model:value="settings.sign_max_retries" :min="1" :max="10" style="width: 100px;" />
              </div>

              <div class="setting-item" v-if="settings.sign_retry_enabled">
                <div class="setting-info">
                  <div class="setting-label">重试间隔（分钟）</div>
                  <div class="setting-desc">每次重试之间的等待时间</div>
                </div>
                <n-input-number v-model:value="settings.sign_retry_interval" :min="5" :max="120" style="width: 100px;" />
              </div>
            </div>

            <n-divider />

            <div class="setting-actions">
              <n-button type="primary" @click="saveSettings" :loading="savingSettings">
                保存设置
              </n-button>
            </div>
          </n-spin>
        </n-card>
      </n-tab-pane>

      <!-- 推送渠道 -->
      <n-tab-pane name="notify" tab="推送渠道">
        <n-card>
          <n-spin :show="loadingChannels">
            <!-- 头部区域 -->
            <div class="channel-header">
              <div class="channel-header-info">
                <div class="channel-header-title">推送渠道</div>
                <div class="channel-header-desc">配置签到结果通知方式，支持多种推送渠道</div>
              </div>
              <n-button type="primary" @click="showAddChannelModal">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                添加渠道
              </n-button>
            </div>

            <n-divider style="margin: 16px 0;" />

            <!-- 渠道列表 -->
            <div v-if="channels.length > 0" class="channel-grid">
              <div v-for="channel in channels" :key="channel.id" class="channel-card">
                <div class="channel-card-header">
                  <div class="channel-icon" :class="channel.channel_type">
                    <n-icon :size="20">
                      <component :is="getChannelIcon(channel.channel_type)" />
                    </n-icon>
                  </div>
                  <div class="channel-status">
                    <n-tag :type="channel.is_enabled ? 'success' : 'default'" size="small" :bordered="false">
                      {{ channel.is_enabled ? '已启用' : '已禁用' }}
                    </n-tag>
                  </div>
                </div>
                <div class="channel-card-body">
                  <div class="channel-name">{{ channel.name }}</div>
                  <div class="channel-type-label">{{ getChannelTypeName(channel.channel_type) }}</div>
                </div>
                <div class="channel-card-footer">
                  <n-button size="small" quaternary @click="testChannel(channel)" :loading="testingId === channel.id">
                    <template #icon><n-icon><SendOutline /></n-icon></template>
                    测试
                  </n-button>
                  <n-button size="small" quaternary @click="editChannel(channel)">
                    <template #icon><n-icon><CreateOutline /></n-icon></template>
                    编辑
                  </n-button>
                  <n-popconfirm @positive-click="deleteChannel(channel.id)">
                    <template #trigger>
                      <n-button size="small" quaternary class="delete-btn">
                        <template #icon><n-icon><TrashOutline /></n-icon></template>
                        删除
                      </n-button>
                    </template>
                    确定删除此渠道？
                  </n-popconfirm>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-state">
              <div class="empty-icon">
                <n-icon :size="48" color="#ddd"><NotificationsOutline /></n-icon>
              </div>
              <div class="empty-title">暂无推送渠道</div>
              <div class="empty-desc">添加推送渠道后，签到结果将自动通知到您</div>
              <n-button type="primary" @click="showAddChannelModal" style="margin-top: 16px;">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                添加第一个渠道
              </n-button>
            </div>
          </n-spin>
        </n-card>
      </n-tab-pane>

      <!-- 数据备份 -->
      <n-tab-pane name="backup" tab="数据备份">
        <n-card>
          <n-spin :show="loadingBackupInfo">
            <div class="backup-section">
              <div class="backup-header">
                <div class="backup-header-info">
                  <div class="backup-header-title">数据备份</div>
                  <div class="backup-header-desc">导出或导入系统数据，用于迁移或恢复</div>
                </div>
              </div>

              <n-divider style="margin: 16px 0;" />

              <!-- 数据统计 -->
              <div class="backup-stats">
                <div class="stat-item">
                  <div class="stat-value">{{ backupInfo.account_count || 0 }}</div>
                  <div class="stat-label">账号数量</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ backupInfo.sign_log_count || 0 }}</div>
                  <div class="stat-label">签到日志</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ backupInfo.notify_channel_count || 0 }}</div>
                  <div class="stat-label">推送渠道</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ backupInfo.setting_count || 0 }}</div>
                  <div class="stat-label">配置项</div>
                </div>
              </div>

              <n-divider style="margin: 16px 0;" />

              <!-- 导出备份 -->
              <div class="backup-action-section">
                <div class="action-info">
                  <div class="action-title">导出备份</div>
                  <div class="action-desc">将账号、设置、推送渠道等数据导出为 JSON 文件</div>
                </div>
                <div class="action-controls">
                  <n-checkbox v-model:checked="exportIncludeLogs">包含签到日志（最近1000条）</n-checkbox>
                  <n-button type="primary" @click="handleExport" :loading="exporting">
                    <template #icon><n-icon><DownloadOutline /></n-icon></template>
                    导出备份
                  </n-button>
                </div>
              </div>

              <n-divider style="margin: 16px 0;" />

              <!-- 导入备份 -->
              <div class="backup-action-section">
                <div class="action-info">
                  <div class="action-title">导入备份</div>
                  <div class="action-desc">从备份文件恢复数据（支持 JSON 格式）</div>
                </div>
                <div class="action-controls">
                  <n-checkbox v-model:checked="importOverwrite">覆盖现有数据</n-checkbox>
                  <n-upload
                    :show-file-list="false"
                    accept=".json"
                    @change="handleImportFile"
                  >
                    <n-button :loading="importing">
                      <template #icon><n-icon><CloudUploadOutline /></n-icon></template>
                      选择文件导入
                    </n-button>
                  </n-upload>
                </div>
              </div>

              <div class="backup-tip">
                <n-icon><InformationCircleOutline /></n-icon>
                备份文件包含敏感信息（如 Session Cookie），请妥善保管
              </div>
            </div>
          </n-spin>
        </n-card>
      </n-tab-pane>

      <!-- 分组管理 -->
      <n-tab-pane name="groups" tab="分组管理">
        <n-card>
          <n-spin :show="loadingGroups">
            <!-- 头部区域 -->
            <div class="channel-header">
              <div class="channel-header-info">
                <div class="channel-header-title">账号分组</div>
                <div class="channel-header-desc">创建分组来组织和管理账号</div>
              </div>
              <n-button type="primary" @click="showAddGroupModal">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                新建分组
              </n-button>
            </div>

            <n-divider style="margin: 16px 0;" />

            <!-- 分组列表 -->
            <div v-if="groups.length > 0" class="group-grid">
              <div v-for="group in groups" :key="group.id" class="group-card">
                <div class="group-card-header">
                  <div class="group-color-dot" :style="{ background: getGroupColor(group.color) }"></div>
                  <div class="group-account-count">
                    <n-tag size="small" :bordered="false">{{ group.account_count }} 个账号</n-tag>
                  </div>
                </div>
                <div class="group-card-body">
                  <div class="group-name">{{ group.name }}</div>
                  <div class="group-desc">{{ group.description || '暂无描述' }}</div>
                </div>
                <div class="group-card-footer">
                  <n-button size="small" quaternary @click="editGroup(group)">
                    <template #icon><n-icon><CreateOutline /></n-icon></template>
                    编辑
                  </n-button>
                  <n-popconfirm @positive-click="deleteGroup(group.id)">
                    <template #trigger>
                      <n-button size="small" quaternary class="delete-btn">
                        <template #icon><n-icon><TrashOutline /></n-icon></template>
                        删除
                      </n-button>
                    </template>
                    删除分组后，账号将变为未分组状态
                  </n-popconfirm>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-state">
              <div class="empty-icon">
                <n-icon :size="48" color="#ddd"><FolderOpenOutline /></n-icon>
              </div>
              <div class="empty-title">暂无分组</div>
              <div class="empty-desc">创建分组来更好地组织和管理您的账号</div>
              <n-button type="primary" @click="showAddGroupModal" style="margin-top: 16px;">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                创建第一个分组
              </n-button>
            </div>
          </n-spin>
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <!-- 添加/编辑渠道弹窗 -->
    <n-modal v-model:show="showChannelModal" :mask-closable="false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>{{ editingChannel ? '编辑渠道' : '添加渠道' }}</h3>
          <n-button text @click="showChannelModal = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>渠道名称</label>
            <n-input v-model:value="channelForm.name" placeholder="给渠道起个名字" />
          </div>
          <div class="form-item">
            <label>渠道类型</label>
            <n-select v-model:value="channelForm.channel_type" :options="channelTypeOptions" :disabled="!!editingChannel" />
          </div>
          <div class="form-item">
            <label>启用状态</label>
            <n-switch v-model:value="channelForm.is_enabled" />
          </div>

          <!-- PushPlus -->
          <template v-if="channelForm.channel_type === 'pushplus'">
            <div class="form-item">
              <label>Token</label>
              <n-input v-model:value="channelForm.config.token" placeholder="PushPlus Token" />
            </div>
          </template>

          <!-- 微信公众号 -->
          <template v-if="channelForm.channel_type === 'wechat_mp'">
            <div class="form-item">
              <label>AppID</label>
              <n-input v-model:value="channelForm.config.app_id" placeholder="公众号 AppID" />
            </div>
            <div class="form-item">
              <label>AppSecret</label>
              <n-input v-model:value="channelForm.config.app_secret" type="password" placeholder="公众号 AppSecret" />
            </div>
            <div class="form-item">
              <label>模板消息 ID</label>
              <n-input v-model:value="channelForm.config.template_id" placeholder="模板消息 ID" />
            </div>
            <div class="form-item">
              <label>接收者 OpenID</label>
              <n-input v-model:value="channelForm.config.openid" placeholder="接收消息的用户 OpenID" />
            </div>
          </template>

          <!-- 企业微信 -->
          <template v-if="channelForm.channel_type === 'wechat_work'">
            <div class="form-item">
              <label>Webhook URL</label>
              <n-input v-model:value="channelForm.config.webhook_url" placeholder="企业微信机器人 Webhook" />
            </div>
          </template>

          <!-- 钉钉 -->
          <template v-if="channelForm.channel_type === 'dingtalk'">
            <div class="form-item">
              <label>Webhook URL</label>
              <n-input v-model:value="channelForm.config.webhook_url" placeholder="钉钉机器人 Webhook" />
            </div>
            <div class="form-item">
              <label>签名密钥</label>
              <n-input v-model:value="channelForm.config.secret" placeholder="可选" />
            </div>
          </template>

          <!-- 飞书 -->
          <template v-if="channelForm.channel_type === 'feishu'">
            <div class="form-item">
              <label>Webhook URL</label>
              <n-input v-model:value="channelForm.config.webhook_url" placeholder="飞书机器人 Webhook" />
            </div>
            <div class="form-item">
              <label>签名密钥</label>
              <n-input v-model:value="channelForm.config.secret" placeholder="可选" />
            </div>
          </template>

          <!-- 邮箱 -->
          <template v-if="channelForm.channel_type === 'email'">
            <div class="form-item">
              <label>SMTP 服务器</label>
              <n-input v-model:value="channelForm.config.smtp_host" placeholder="如 smtp.qq.com" />
            </div>
            <div class="form-item">
              <label>SMTP 端口</label>
              <n-input-number v-model:value="channelForm.config.smtp_port" :min="1" :max="65535" style="width: 100%;" />
            </div>
            <div class="form-item">
              <label>发件邮箱</label>
              <n-input v-model:value="channelForm.config.username" placeholder="发件人邮箱" />
            </div>
            <div class="form-item">
              <label>邮箱密码</label>
              <n-input v-model:value="channelForm.config.password" type="password" placeholder="密码或授权码" />
            </div>
            <div class="form-item">
              <label>使用 SSL</label>
              <n-switch v-model:value="channelForm.config.use_ssl" />
            </div>
          </template>
        </div>
        <div class="modal-footer">
          <n-button @click="showChannelModal = false">取消</n-button>
          <n-button type="primary" @click="saveChannel" :loading="savingChannel">保存</n-button>
        </div>
      </div>
    </n-modal>

    <!-- 添加/编辑分组弹窗 -->
    <n-modal v-model:show="showGroupModal" :mask-closable="false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>{{ editingGroup ? '编辑分组' : '新建分组' }}</h3>
          <n-button text @click="showGroupModal = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>分组名称</label>
            <n-input v-model:value="groupForm.name" placeholder="输入分组名称" />
          </div>
          <div class="form-item">
            <label>分组描述（可选）</label>
            <n-input v-model:value="groupForm.description" placeholder="输入分组描述" />
          </div>
          <div class="form-item">
            <label>分组颜色</label>
            <div class="color-picker">
              <div
                v-for="color in colorOptions"
                :key="color.value"
                class="color-option"
                :class="{ active: groupForm.color === color.value }"
                :style="{ background: color.hex }"
                @click="groupForm.color = color.value"
              >
                <n-icon v-if="groupForm.color === color.value" :size="14" color="#fff"><CheckmarkOutline /></n-icon>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <n-button @click="showGroupModal = false">取消</n-button>
          <n-button type="primary" @click="saveGroup" :loading="savingGroup">保存</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Component } from 'vue'
import { useMessage } from 'naive-ui'
import {
  AddOutline,
  CloseOutline,
  SendOutline,
  CreateOutline,
  TrashOutline,
  NotificationsOutline,
  LogoWechat,
  MailOutline,
  ChatbubbleOutline,
  PaperPlaneOutline,
  InformationCircleOutline,
  DownloadOutline,
  CloudUploadOutline,
  FolderOpenOutline,
  CheckmarkOutline
} from '@vicons/ionicons5'
import { settingsApi, notifyApi, backupApi, groupsApi } from '../api'
import { getToken } from '../utils/auth'
import { channelTypes, getChannelTypeName } from '../utils'

// 渠道图标映射
const getChannelIcon = (type: string): Component => {
  const icons: Record<string, Component> = {
    pushplus: PaperPlaneOutline,
    wechat_mp: LogoWechat,
    wechat_work: LogoWechat,
    dingtalk: ChatbubbleOutline,
    feishu: ChatbubbleOutline,
    email: MailOutline
  }
  return icons[type] || NotificationsOutline
}

const message = useMessage()

// 基础设置
const loadingSettings = ref(false)
const savingSettings = ref(false)
const settings = ref({
  auto_sign_enabled: false,
  auto_sign_time: '08:00',
  health_check_enabled: true,
  health_check_interval: 6,
  sign_retry_enabled: true,
  sign_max_retries: 3,
  sign_retry_interval: 30
})
const schedulerStatus = ref({
  next_run: null as string | null
})

const signTimeValue = computed({
  get: () => {
    if (!settings.value.auto_sign_time) return null
    const [h, m] = settings.value.auto_sign_time.split(':').map(Number)
    return new Date(2000, 0, 1, h, m).getTime()
  },
  set: (val: number | null) => {
    if (val) {
      const d = new Date(val)
      settings.value.auto_sign_time = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
    }
  }
})

// 推送渠道
const loadingChannels = ref(false)
const channels = ref<any[]>([])
const testingId = ref<number | null>(null)

// 渠道表单
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

// 数据备份
const loadingBackupInfo = ref(false)
const backupInfo = ref<any>({})
const exportIncludeLogs = ref(false)
const exporting = ref(false)
const importOverwrite = ref(false)
const importing = ref(false)

// 分组管理
const loadingGroups = ref(false)
const groups = ref<any[]>([])
const showGroupModal = ref(false)
const editingGroup = ref<any>(null)
const savingGroup = ref(false)
const groupForm = ref({
  name: '',
  description: '',
  color: 'default'
})

const colorOptions = [
  { value: 'default', hex: '#8b8b8b' },
  { value: 'blue', hex: '#2080f0' },
  { value: 'green', hex: '#18a058' },
  { value: 'red', hex: '#d03050' },
  { value: 'orange', hex: '#f0a020' },
  { value: 'purple', hex: '#8b5cf6' },
  { value: 'pink', hex: '#ec4899' },
  { value: 'cyan', hex: '#06b6d4' }
]

const getGroupColor = (color: string) => {
  const found = colorOptions.find(c => c.value === color)
  return found ? found.hex : '#8b8b8b'
}

const loadSettings = async () => {
  loadingSettings.value = true
  try {
    const [settingsRes, schedulerRes] = await Promise.all([
      settingsApi.get(),
      settingsApi.getScheduler()
    ])
    if (settingsRes.data) {
      settings.value = { ...settings.value, ...settingsRes.data }
    }
    if (schedulerRes.data) {
      schedulerStatus.value = schedulerRes.data
    }
  } catch (e: any) {
    message.error(e.message)
  } finally {
    loadingSettings.value = false
  }
}

const saveSettings = async () => {
  savingSettings.value = true
  try {
    await settingsApi.update(settings.value)
    message.success('设置保存成功')
    // 重新加载调度器状态
    const res = await settingsApi.getScheduler()
    if (res.data) {
      schedulerStatus.value = res.data
    }
  } catch (e: any) {
    message.error(e.message)
  } finally {
    savingSettings.value = false
  }
}

const loadChannels = async () => {
  loadingChannels.value = true
  try {
    const res = await notifyApi.getChannels()
    channels.value = res.data || []
  } catch (e: any) {
    message.error(e.message)
  } finally {
    loadingChannels.value = false
  }
}

const showAddChannelModal = () => {
  editingChannel.value = null
  channelForm.value = {
    name: '',
    channel_type: 'pushplus',
    is_enabled: true,
    config: {}
  }
  showChannelModal.value = true
}

const editChannel = (channel: any) => {
  editingChannel.value = channel
  channelForm.value = {
    name: channel.name,
    channel_type: channel.channel_type,
    is_enabled: channel.is_enabled,
    config: { ...channel.config }
  }
  showChannelModal.value = true
}

const saveChannel = async () => {
  if (!channelForm.value.name.trim()) {
    message.warning('请输入渠道名称')
    return
  }
  savingChannel.value = true
  try {
    // 转换字段名
    const payload = {
      type: channelForm.value.channel_type,
      name: channelForm.value.name,
      config: channelForm.value.config,
      is_enabled: channelForm.value.is_enabled
    }

    if (editingChannel.value) {
      await notifyApi.updateChannel(editingChannel.value.id, payload)
      message.success('渠道更新成功')
    } else {
      await notifyApi.createChannel(payload)
      message.success('渠道添加成功')
    }
    showChannelModal.value = false
    loadChannels()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    savingChannel.value = false
  }
}

const deleteChannel = async (id: number) => {
  try {
    await notifyApi.deleteChannel(id)
    message.success('渠道删除成功')
    loadChannels()
  } catch (e: any) {
    message.error(e.message)
  }
}

const testChannel = async (channel: any) => {
  testingId.value = channel.id
  try {
    await notifyApi.testChannel(channel.id)
    message.success('测试消息已发送')
  } catch (e: any) {
    message.error(e.message)
  } finally {
    testingId.value = null
  }
}

// 备份功能
const loadBackupInfo = async () => {
  loadingBackupInfo.value = true
  try {
    const res = await backupApi.getInfo()
    backupInfo.value = res.data || {}
  } catch (e: any) {
    console.error('Failed to load backup info:', e)
  } finally {
    loadingBackupInfo.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const token = getToken()
    const url = `/api/v1/backup/export?include_logs=${exportIncludeLogs.value}`

    // 使用 fetch 下载文件
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('导出失败')
    }

    const blob = await response.blob()
    const filename = `anyrouter_backup_${new Date().toISOString().slice(0, 10)}.json`

    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)

    message.success('备份导出成功')
  } catch (e: any) {
    message.error(e.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

const handleImportFile = async ({ file }: { file: { file: File } }) => {
  if (!file.file) return

  importing.value = true
  try {
    const res = await backupApi.import(file.file, importOverwrite.value)
    const data = res.data
    message.success(`导入成功: ${data.accounts} 个账号, ${data.notify_channels} 个渠道, ${data.settings} 个配置`)
    loadBackupInfo()
  } catch (e: any) {
    message.error(e.message || '导入失败')
  } finally {
    importing.value = false
  }
}

// 分组管理函数
const loadGroups = async () => {
  loadingGroups.value = true
  try {
    const res = await groupsApi.getList()
    groups.value = res.data || []
  } catch (e: any) {
    message.error(e.message)
  } finally {
    loadingGroups.value = false
  }
}

const showAddGroupModal = () => {
  editingGroup.value = null
  groupForm.value = {
    name: '',
    description: '',
    color: 'default'
  }
  showGroupModal.value = true
}

const editGroup = (group: any) => {
  editingGroup.value = group
  groupForm.value = {
    name: group.name,
    description: group.description || '',
    color: group.color || 'default'
  }
  showGroupModal.value = true
}

const saveGroup = async () => {
  if (!groupForm.value.name.trim()) {
    message.warning('请输入分组名称')
    return
  }
  savingGroup.value = true
  try {
    const payload = {
      name: groupForm.value.name,
      description: groupForm.value.description || undefined,
      color: groupForm.value.color
    }

    if (editingGroup.value) {
      await groupsApi.update(editingGroup.value.id, payload)
      message.success('分组更新成功')
    } else {
      await groupsApi.create(payload)
      message.success('分组创建成功')
    }
    showGroupModal.value = false
    loadGroups()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    savingGroup.value = false
  }
}

const deleteGroup = async (id: number) => {
  try {
    await groupsApi.delete(id)
    message.success('分组删除成功')
    loadGroups()
  } catch (e: any) {
    message.error(e.message)
  }
}

onMounted(() => {
  loadSettings()
  loadChannels()
  loadBackupInfo()
  loadGroups()
})
</script>

<style scoped>
.setting-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.setting-info {
  flex: 1;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.setting-desc {
  font-size: 12px;
  color: #999;
}

.setting-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #999;
  padding: 12px 0;
}

.setting-actions {
  display: flex;
  justify-content: flex-end;
}

/* 推送渠道 - 头部 */
.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.channel-header-info {
  flex: 1;
}

.channel-header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.channel-header-desc {
  font-size: 13px;
  color: #999;
}

/* 推送渠道 - 卡片网格 */
.channel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.channel-card {
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  border: 1px solid #eef0f3;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;
}

.channel-card:hover {
  border-color: #00b38a;
  box-shadow: 0 4px 12px rgba(0, 179, 138, 0.1);
}

.channel-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.channel-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: #00b38a;
}

.channel-icon.pushplus {
  background: linear-gradient(135deg, #00b38a 0%, #00a080 100%);
}

.channel-icon.wechat_mp {
  background: linear-gradient(135deg, #07c160 0%, #06ae56 100%);
}

.channel-icon.wechat_work {
  background: linear-gradient(135deg, #07c160 0%, #06ae56 100%);
}

.channel-icon.dingtalk {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
}

.channel-icon.feishu {
  background: linear-gradient(135deg, #3370ff 0%, #2b5fd9 100%);
}

.channel-icon.email {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
}

.channel-card-body {
  margin-bottom: 16px;
}

.channel-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.channel-type-label {
  font-size: 12px;
  color: #999;
}

.channel-card-footer {
  display: flex;
  gap: 4px;
  padding-top: 12px;
  border-top: 1px solid #eef0f3;
}

.channel-card-footer .n-button {
  flex: 1;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 20px;
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 13px;
  color: #999;
}

.delete-btn:hover {
  color: #e88080 !important;
}

/* Modal */
.modal-container {
  width: 480px;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.modal-body {
  padding: 20px;
  max-height: 60vh;
  overflow-y: auto;
}

.form-item {
  margin-bottom: 16px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #666;
  margin-bottom: 8px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

/* 数据备份 */
.backup-section {
  padding: 0;
}

.backup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.backup-header-info {
  flex: 1;
}

.backup-header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.backup-header-desc {
  font-size: 13px;
  color: #999;
}

.backup-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.backup-stats .stat-item {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.backup-stats .stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
}

.backup-stats .stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.backup-action-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.action-info {
  flex: 1;
}

.action-title {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.action-desc {
  font-size: 12px;
  color: #999;
}

.action-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.backup-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #999;
  padding: 12px;
  background: #fff8e6;
  border-radius: 8px;
  margin-top: 16px;
}

/* 分组管理 */
.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.group-card {
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
  border: 1px solid #eef0f3;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s ease;
}

.group-card:hover {
  border-color: #00b38a;
  box-shadow: 0 4px 12px rgba(0, 179, 138, 0.1);
}

.group-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.group-color-dot {
  width: 24px;
  height: 24px;
  border-radius: 6px;
}

.group-card-body {
  margin-bottom: 16px;
}

.group-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.group-desc {
  font-size: 12px;
  color: #999;
}

.group-card-footer {
  display: flex;
  gap: 4px;
  padding-top: 12px;
  border-top: 1px solid #eef0f3;
}

.group-card-footer .n-button {
  flex: 1;
}

/* 颜色选择器 */
.color-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.active {
  border-color: #fff;
  box-shadow: 0 0 0 2px currentColor;
}
</style>
