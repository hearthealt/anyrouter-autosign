<template>
  <n-modal v-model:show="visible" :mask-closable="false">
    <div class="modal-container">
      <div class="modal-header">
        <h3>{{ isEdit ? '编辑账号' : '添加账号' }}</h3>
        <n-button text @click="close">
          <n-icon :size="20"><CloseOutline /></n-icon>
        </n-button>
      </div>
      <div class="modal-body">
        <div class="form-item" v-if="!isEdit">
          <label class="form-label">User ID <span class="required">*</span></label>
          <n-input v-model:value="form.user_id" placeholder="请求头 new-api-user 的值" />
        </div>
        <div class="form-item" v-if="isEdit">
          <label class="form-label">User ID</label>
          <n-input v-model:value="form.user_id" placeholder="留空则不修改" />
        </div>
        <div class="form-item">
          <label class="form-label">
            Session Cookie
            <span class="required" v-if="!isEdit">*</span>
          </label>
          <n-input
            v-model:value="form.session_cookie"
            type="textarea"
            :rows="3"
            :placeholder="isEdit ? '留空则不修改' : 'Cookie 中 session 的值'"
          />
        </div>
        <div class="form-item" v-if="isEdit">
          <label class="form-label">账号状态</label>
          <n-switch v-model:value="form.is_active">
            <template #checked>启用</template>
            <template #unchecked>禁用</template>
          </n-switch>
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
        <n-divider v-if="isEdit" style="margin: 16px 0;" />
        <div class="form-item">
          <label class="form-label">签到推送渠道{{ isEdit ? '' : '（可选）' }}</label>
          <n-select
            v-model:value="form.notify_channel_ids"
            multiple
            :options="channelOptions"
            placeholder="选择推送渠道（可多选）"
            clearable
            :loading="loadingChannels"
          />
        </div>
        <div class="form-tip">
          <n-icon><InformationCircleOutline /></n-icon>
          {{ isEdit ? '签到成功或失败后会通过选中的渠道发送通知' : '在浏览器 F12 开发者工具 Network 中获取' }}
        </div>
      </div>
      <div class="modal-footer">
        <n-button @click="close">取消</n-button>
        <n-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存' : '验证并添加' }}
        </n-button>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { CloseOutline, InformationCircleOutline } from '@vicons/ionicons5'
import { notifyApi } from '../../api'
import type { Account, AccountGroup, NotifyChannel, SelectOption } from '../../types'

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
    is_active?: boolean
    group_id: number | null
    notify_channel_ids: number[]
  }]
}>()

const message = useMessage()

const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const isEdit = computed(() => !!props.account)

const form = ref({
  user_id: '',
  session_cookie: '',
  is_active: true,
  group_id: null as number | null,
  notify_channel_ids: [] as number[]
})

const submitting = ref(false)
const loadingChannels = ref(false)
const channelOptions = ref<SelectOption<number>[]>([])

const groupOptions = computed(() =>
  props.groups.map(g => ({ label: g.name, value: g.id }))
)

// 加载推送渠道
const loadChannels = async () => {
  loadingChannels.value = true
  try {
    const res = await notifyApi.getChannels()
    channelOptions.value = (res.data || [])
      .filter((c: NotifyChannel) => c.is_enabled)
      .map((c: NotifyChannel) => ({ label: c.name, value: c.id }))
  } catch (e) {
    console.error('Failed to load channels:', e)
  } finally {
    loadingChannels.value = false
  }
}

// 加载账号推送配置
const loadAccountNotify = async (accountId: number) => {
  try {
    const res = await notifyApi.getAccountNotify(accountId)
    const enabledChannels = (res.data || []).filter((c: any) => c.is_enabled)
    form.value.notify_channel_ids = enabledChannels.map((c: any) => c.channel_id)
  } catch (e) {
    console.error('Failed to load account notify:', e)
  }
}

// 监听弹窗显示
watch(() => props.show, async (val) => {
  if (val) {
    loadChannels()
    if (props.account) {
      // 编辑模式
      form.value = {
        user_id: '',
        session_cookie: '',
        is_active: props.account.is_active,
        group_id: props.account.group_id || null,
        notify_channel_ids: []
      }
      await loadAccountNotify(props.account.id)
    } else {
      // 添加模式
      form.value = {
        user_id: '',
        session_cookie: '',
        is_active: true,
        group_id: null,
        notify_channel_ids: []
      }
    }
  }
})

const close = () => {
  visible.value = false
}

const handleSubmit = () => {
  if (!isEdit.value) {
    if (!form.value.user_id.trim()) {
      message.warning('请输入 User ID')
      return
    }
    if (!form.value.session_cookie.trim()) {
      message.warning('请输入 Session Cookie')
      return
    }
  }

  submitting.value = true
  emit('submit', { ...form.value })
}

// 暴露方法供父组件调用
defineExpose({
  setSubmitting: (val: boolean) => { submitting.value = val }
})
</script>

<style scoped>
.modal-container {
  width: 440px;
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

.modal-body {
  padding: var(--spacing-5);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--border-color);
  background: var(--bg-card-hover);
}

@media (max-width: 480px) {
  .modal-container {
    width: 95vw;
    max-width: 440px;
  }
}
</style>
