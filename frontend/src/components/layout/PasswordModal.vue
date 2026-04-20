<template>
  <n-modal :show="show" :mask-closable="false" @update:show="(v: boolean) => emit('update:show', v)">
    <div class="password-modal">
      <div class="modal-header">
        <h3>修改密码</h3>
        <n-button text @click="emit('update:show', false)" aria-label="关闭">
          <n-icon :size="18"><CloseOutline /></n-icon>
        </n-button>
      </div>
      <div class="modal-body">
        <n-form ref="formRef" :model="form" :rules="rules">
          <n-form-item label="原密码" path="old_password">
            <n-input
              v-model:value="form.old_password"
              type="password"
              show-password-on="click"
              placeholder="请输入原密码"
            />
          </n-form-item>
          <n-form-item label="新密码" path="new_password">
            <n-input
              v-model:value="form.new_password"
              type="password"
              show-password-on="click"
              placeholder="至少 6 位"
            />
          </n-form-item>
          <n-form-item label="确认密码" path="confirm_password">
            <n-input
              v-model:value="form.confirm_password"
              type="password"
              show-password-on="click"
              placeholder="再次输入新密码"
            />
          </n-form-item>
        </n-form>
      </div>
      <div class="modal-footer">
        <n-button size="small" @click="emit('update:show', false)">取消</n-button>
        <n-button size="small" type="primary" @click="submit" :loading="submitting">
          确认修改
        </n-button>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NButton, NIcon, NForm, NFormItem, NInput } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { CloseOutline } from '@vicons/ionicons5'
import { authApi } from '../../api'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'changed'): void
}>()

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)
const form = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const rules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_: unknown, value: string) => value === form.value.new_password,
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

watch(() => props.show, (v) => {
  if (v) {
    form.value = { old_password: '', new_password: '', confirm_password: '' }
  }
})

const submit = async () => {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    await authApi.changePassword({
      old_password: form.value.old_password,
      new_password: form.value.new_password
    })
    window.$notify('密码修改成功，请重新登录', 'success')
    emit('update:show', false)
    emit('changed')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '修改失败'
    window.$notify(msg, 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.password-modal {
  width: min(92vw, 420px);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-4);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
}
</style>
