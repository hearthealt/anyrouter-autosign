<template>
  <UiModal
    :show="show"
    kicker="Security"
    title="修改密码"
    size="sm"
    :mask-closable="false"
    @update:show="(v: boolean) => emit('update:show', v)"
  >
    <form class="pw" @submit.prevent="submit">
      <label v-for="field in fields" :key="field.key" class="pw__field">
        <span class="pw__label">
          {{ field.label }}
          <span class="pw__required">*</span>
        </span>
        <UiInput
          v-model:value="form[field.key]"
          type="password"
          show-password-on="click"
          :placeholder="field.placeholder"
          @update:value="() => (errors[field.key] = '')"
        />
        <span v-if="errors[field.key]" class="pw__error">{{ errors[field.key] }}</span>
      </label>
    </form>

    <template #footer>
      <UiButton size="small" @click="emit('update:show', false)">取消</UiButton>
      <UiButton size="small" type="primary" :loading="submitting" @click="submit">确认修改</UiButton>
    </template>
  </UiModal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { UiButton, UiInput, UiModal } from '../../ui'
import { authApi } from '../../api'

type FieldKey = 'old_password' | 'new_password' | 'confirm_password'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'changed'): void
}>()

const fields: Array<{ key: FieldKey; label: string; placeholder: string }> = [
  { key: 'old_password', label: '原密码', placeholder: '请输入原密码' },
  { key: 'new_password', label: '新密码', placeholder: '至少 6 位' },
  { key: 'confirm_password', label: '确认密码', placeholder: '再次输入新密码' },
]

const submitting = ref(false)
const form = ref<Record<FieldKey, string>>({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const errors = ref<Record<FieldKey, string>>({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

function reset() {
  form.value = { old_password: '', new_password: '', confirm_password: '' }
  errors.value = { old_password: '', new_password: '', confirm_password: '' }
}

watch(() => props.show, v => { if (v) reset() })

/**
 * 手动校验替代 n-form 的 rules。
 * 全站只有这一处用过 FormInst，为它保留一整套表单组件不值得；
 * 逐字段错误提示的信息量和原来一致。
 */
function validate(): boolean {
  const next: Record<FieldKey, string> = { old_password: '', new_password: '', confirm_password: '' }

  if (!form.value.old_password) next.old_password = '请输入原密码'

  if (!form.value.new_password) next.new_password = '请输入新密码'
  else if (form.value.new_password.length < 6) next.new_password = '密码长度至少 6 位'

  if (!form.value.confirm_password) next.confirm_password = '请确认新密码'
  else if (form.value.confirm_password !== form.value.new_password) {
    next.confirm_password = '两次输入的密码不一致'
  }

  errors.value = next
  return !Object.values(next).some(Boolean)
}

async function submit() {
  if (submitting.value || !validate()) return

  submitting.value = true
  try {
    await authApi.changePassword({
      old_password: form.value.old_password,
      new_password: form.value.new_password,
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
.pw {
  display: grid;
  gap: var(--s4);
}

.pw__field {
  display: grid;
  gap: 5px;
}

.pw__label {
  color: var(--ink);
  font-size: var(--fn-xs);
  font-weight: var(--weight-medium);
}

.pw__required {
  color: var(--bad);
  margin-left: 2px;
}

.pw__error {
  color: var(--bad);
  font-size: var(--fn-xs);
}
</style>
