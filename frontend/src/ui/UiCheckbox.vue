<!--
  UiCheckbox —— 替代 n-checkbox。v-model:checked 对齐原 API。
  勾选标记统一使用 Lucide，保持整套界面的图标语言一致。
-->
<template>
  <label :class="['ui-check', `ui-check--${size}`, { 'is-disabled': disabled, 'is-checked': checked }]">
    <input
      class="ui-check__input"
      type="checkbox"
      :checked="checked"
      :disabled="disabled"
      :indeterminate="indeterminate"
      v-bind="$attrs"
      @change="onChange"
    />
    <span class="ui-check__box" aria-hidden="true">
      <Minus v-if="indeterminate" class="ui-check__mark" :size="size === 'small' ? 11 : 13" :stroke-width="2.2" />
      <Check v-else class="ui-check__mark" :size="size === 'small' ? 11 : 13" :stroke-width="2.2" />
    </span>
    <span v-if="$slots.default" class="ui-check__label"><slot /></span>
  </label>
</template>

<script setup lang="ts">
import { Check, Minus } from 'lucide-vue-next'

withDefaults(defineProps<{
  checked?: boolean
  disabled?: boolean
  indeterminate?: boolean
  size?: 'small' | 'medium'
}>(), { size: 'medium' })

const emit = defineEmits<{ 'update:checked': [value: boolean] }>()

defineOptions({ inheritAttrs: false })

function onChange(event: Event) {
  emit('update:checked', (event.target as HTMLInputElement).checked)
}
</script>

<style scoped>
.ui-check {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  cursor: pointer;
  user-select: none;
  color: var(--ink-strong);
}

.ui-check.is-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ui-check--small { font-size: var(--fn-xs); }
.ui-check--medium { font-size: var(--fn-sm); }

.ui-check__input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.ui-check__box {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid var(--line-strong);
  border-radius: var(--r-xs);
  background: var(--surface-inset);
  transition: background-color 0.14s ease, border-color 0.14s ease;
}

.ui-check--small .ui-check__box { width: 14px; height: 14px; }
.ui-check--medium .ui-check__box { width: 16px; height: 16px; }

.ui-check:hover:not(.is-disabled) .ui-check__box { border-color: var(--signal-deep); }

.ui-check.is-checked .ui-check__box,
.ui-check__input:indeterminate + .ui-check__box {
  background: var(--signal);
  border-color: var(--signal);
}

.ui-check__input:focus-visible + .ui-check__box { box-shadow: var(--focus-ring); }

.ui-check__mark {
  color: var(--signal-ink);
  opacity: 0;
  transform: scale(0.55);
  transition: opacity 0.16s ease, transform 0.2s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.ui-check.is-checked .ui-check__mark,
.ui-check__input:indeterminate + .ui-check__box .ui-check__mark {
  opacity: 1;
  transform: scale(1);
}

.ui-check__label {
  min-width: 0;
  line-height: var(--leading-tight);
}
</style>
