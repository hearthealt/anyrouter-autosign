<!--
  UiSkeleton —— 替代 n-skeleton。

  不用左右扫光（那个已经很俗），改成整体呼吸式明暗 —— 更像仪器在等待读数。
-->
<template>
  <span
    class="ui-skeleton"
    :class="{ 'is-circle': circle, 'is-text': text }"
    :style="{ width: resolvedWidth, height: resolvedHeight, borderRadius: circle ? '50%' : undefined }"
    aria-hidden="true"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  width?: string | number
  height?: string | number
  circle?: boolean
  /** 文本占位：高度按行高走，宽度默认 100% */
  text?: boolean
}>()

const size = (value?: string | number) =>
  value === undefined ? undefined : typeof value === 'number' ? `${value}px` : value

const resolvedWidth = computed(() => size(props.width) ?? (props.text ? '100%' : undefined))
const resolvedHeight = computed(() => size(props.height) ?? (props.text ? '0.9em' : undefined))
</script>

<style scoped>
.ui-skeleton {
  display: block;
  border-radius: var(--r-xs);
  background: var(--surface-active);
  animation: ui-breathe 1.5s ease-in-out infinite;
}

.ui-skeleton.is-text { display: inline-block; vertical-align: middle; }

@keyframes ui-breathe {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.45; }
}
</style>
