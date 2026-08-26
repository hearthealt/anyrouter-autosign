<!--
  UiBadge —— 替代 n-badge。

  两种形态：有内容时是数字胶囊（超过 max 显示 99+），无内容时是一个点。
  数字用等宽，避免计数变化时宽度跳动。
-->
<template>
  <span class="ui-badge-wrap">
    <slot />
    <span
      v-if="show"
      :class="['ui-badge', `ui-badge--${type}`, { 'is-dot': dot, 'is-standalone': !$slots.default }]"
    >
      <span v-if="!dot" class="tabular">{{ display }}</span>
    </span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  value?: number | string
  max?: number
  dot?: boolean
  type?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'
  /** 值为 0 时是否仍然显示 */
  showZero?: boolean
}>(), {
  max: 99,
  type: 'error',
})

const show = computed(() => {
  if (props.dot) return true
  if (props.value === undefined || props.value === null || props.value === '') return false
  if (typeof props.value === 'number' && props.value === 0) return props.showZero
  return true
})

const display = computed(() => {
  if (typeof props.value === 'number' && props.value > props.max) return `${props.max}+`
  return String(props.value ?? '')
})
</script>

<style scoped>
.ui-badge-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.ui-badge {
  position: absolute;
  top: -5px;
  right: -7px;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 15px;
  height: 15px;
  padding: 0 4px;
  border-radius: var(--r-full);
  /* 描边用页底色，让徽标从下层内容里"挖"出来 */
  box-shadow: 0 0 0 2px var(--surface-page);
  font-size: 9px;
  font-weight: var(--weight-bold);
  line-height: 1;
  letter-spacing: 0;
}

.ui-badge.is-standalone {
  position: static;
  box-shadow: none;
}

.ui-badge.is-dot {
  min-width: 6px;
  width: 6px;
  height: 6px;
  padding: 0;
  top: -1px;
  right: -1px;
}

.ui-badge--default { background: var(--ink-ghost); color: var(--ink-inverse); }
.ui-badge--primary { background: var(--signal); color: var(--signal-ink); }
.ui-badge--success { background: var(--ok); color: #fff; }
.ui-badge--warning { background: var(--warn); color: #fff; }
.ui-badge--error { background: var(--bad); color: #fff; }
.ui-badge--info { background: var(--info); color: #fff; }
</style>
