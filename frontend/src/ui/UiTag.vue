<!--
  UiTag —— 替代 n-tag。

  仪器面板的状态标签：不用圆胖的胶囊，用近方角 + 语义色左侧竖条。
  竖条比整块着色更克制，密集表格里几十个标签也不会糊成一片。
-->
<template>
  <span :class="['ui-tag', `ui-tag--${size}`, `ui-tag--${type}`, { 'is-bordered': bordered, 'has-bar': bar }]">
    <span v-if="$slots.icon" class="ui-tag__icon"><slot name="icon" /></span>
    <slot />
  </span>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  type?: 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'
  size?: 'tiny' | 'small' | 'medium'
  bordered?: boolean
  /** 左侧语义色竖条。默认开，纯中性标签可关掉 */
  bar?: boolean
}>(), {
  type: 'default',
  size: 'small',
  bordered: true,
  bar: true,
})
</script>

<style scoped>
.ui-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border: 1px solid transparent;
  border-radius: var(--r-xs);
  font-weight: var(--weight-medium);
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

.ui-tag--tiny { height: 17px; padding: 0 5px; font-size: var(--fn-2xs); }
.ui-tag--small { height: 20px; padding: 0 6px; font-size: var(--fn-xs); }
.ui-tag--medium { height: 24px; padding: 0 8px; font-size: var(--fn-sm); }

.ui-tag.has-bar { border-left-width: 2px; padding-left: 5px; }

.ui-tag__icon { display: inline-flex; align-items: center; }

/* ── 语义 */

.ui-tag--default {
  background: var(--surface-sunken);
  color: var(--ink);
  border-color: var(--line-faint);
}

.ui-tag--default.has-bar { border-left-color: var(--ink-ghost); }

.ui-tag--primary { background: var(--signal-wash); color: var(--signal-deep); }
.ui-tag--primary.is-bordered { border-color: var(--signal-wash); }
.ui-tag--primary.has-bar { border-left-color: var(--signal-deep); }

.ui-tag--success { background: var(--ok-wash); color: var(--ok); }
.ui-tag--success.is-bordered { border-color: var(--ok-wash); }
.ui-tag--success.has-bar { border-left-color: var(--ok); }

.ui-tag--warning { background: var(--warn-wash); color: var(--warn); }
.ui-tag--warning.is-bordered { border-color: var(--warn-wash); }
.ui-tag--warning.has-bar { border-left-color: var(--warn); }

.ui-tag--error { background: var(--bad-wash); color: var(--bad); }
.ui-tag--error.is-bordered { border-color: var(--bad-wash); }
.ui-tag--error.has-bar { border-left-color: var(--bad); }

.ui-tag--info { background: var(--info-wash); color: var(--info); }
.ui-tag--info.is-bordered { border-color: var(--info-wash); }
.ui-tag--info.has-bar { border-left-color: var(--info); }
</style>
