<!--
  UiCheckbox —— 替代 n-checkbox。v-model:checked 对齐原 API。

  勾选标记用 SVG path 的 stroke-dashoffset 动画画出来，
  比直接显示图标更有"落笔"感，且能被动效开关关掉。
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
      <svg v-if="indeterminate" class="ui-check__mark" viewBox="0 0 16 16">
        <path d="M4 8 H12" />
      </svg>
      <svg v-else class="ui-check__mark" viewBox="0 0 16 16">
        <path d="M3.5 8.5 L6.5 11.5 L12.5 4.5" />
      </svg>
    </span>
    <span v-if="$slots.default" class="ui-check__label"><slot /></span>
  </label>
</template>

<script setup lang="ts">
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

/* 原生 input 保留在无障碍树里，只是视觉隐藏 */
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
  width: 100%;
  height: 100%;
  fill: none;
  stroke: var(--signal-ink);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  /* 未选中时把线段完全收起，选中时画出来 */
  stroke-dasharray: 18;
  stroke-dashoffset: 18;
  transition: stroke-dashoffset 0.2s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.ui-check.is-checked .ui-check__mark,
.ui-check__input:indeterminate + .ui-check__box .ui-check__mark {
  stroke-dashoffset: 0;
}

.ui-check__label {
  min-width: 0;
  line-height: var(--leading-tight);
}
</style>
