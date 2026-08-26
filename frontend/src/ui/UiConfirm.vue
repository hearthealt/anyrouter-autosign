<!--
  UiConfirm —— 替代 n-popconfirm（5 处删除确认都用它）。

  插槽约定与 Naive 完全一致，避免调用点改写：
  - `#trigger` 是触发器
  - **默认插槽是提示文本**（不是触发器）
  - 也支持 `content` prop 传纯文本

  确认按钮默认用 error 色调，因为这 5 处全是删除操作。
-->
<template>
  <UiPopover v-model:show="open" :placement="placement" trigger="click" :disabled="disabled">
    <template #trigger><slot name="trigger" /></template>

    <div class="ui-confirm">
      <div class="ui-confirm__body">
        <span class="ui-confirm__icon" :class="`is-${tone}`" aria-hidden="true">
          <AlertTriangle :size="14" />
        </span>
        <p class="ui-confirm__text"><slot>{{ content }}</slot></p>
      </div>
      <div class="ui-confirm__actions">
        <UiButton size="tiny" quaternary @click="cancel">{{ negativeText }}</UiButton>
        <UiButton size="tiny" :type="tone" :loading="loading" @click="confirm">{{ positiveText }}</UiButton>
      </div>
    </div>
  </UiPopover>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { AlertTriangle } from 'lucide-vue-next'
import UiButton from './UiButton.vue'
import UiPopover from './UiPopover.vue'
import type { Placement } from './useAnchoredLayer'

withDefaults(defineProps<{
  content?: string
  positiveText?: string
  negativeText?: string
  tone?: 'error' | 'warning' | 'primary'
  placement?: Placement
  loading?: boolean
  disabled?: boolean
}>(), {
  content: '确认执行此操作？',
  positiveText: '确认',
  negativeText: '取消',
  tone: 'error',
  placement: 'top-end',
})

const emit = defineEmits<{
  'positive-click': []
  'negative-click': []
}>()

const open = ref(false)

function confirm() {
  emit('positive-click')
  open.value = false
}

function cancel() {
  emit('negative-click')
  open.value = false
}
</script>

<style scoped>
.ui-confirm {
  display: grid;
  gap: var(--s3);
  min-width: 200px;
  max-width: 264px;
}

.ui-confirm__body {
  display: flex;
  align-items: flex-start;
  gap: 7px;
}

.ui-confirm__icon {
  display: inline-flex;
  flex-shrink: 0;
  margin-top: 1px;
}

.ui-confirm__icon.is-error { color: var(--bad); }
.ui-confirm__icon.is-warning { color: var(--warn); }
.ui-confirm__icon.is-primary { color: var(--signal-deep); }

.ui-confirm__text {
  color: var(--ink-strong);
  font-size: var(--fn-sm);
  line-height: var(--leading-normal);
}

.ui-confirm__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--s2);
}
</style>
