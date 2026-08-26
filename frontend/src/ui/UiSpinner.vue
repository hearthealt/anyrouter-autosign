<!--
  UiSpinner —— 替代 n-spin 的内联场景。

  不用旋转的圆环，用一圈递次淡出的刻度 —— 仪器仪表的等待语言。
  刻度用 conic-gradient 一层搞定，比 12 个 div 便宜。
-->
<template>
  <span
    class="ui-spinner"
    :style="{ width: `${size}px`, height: `${size}px`, borderWidth: `${stroke}px` }"
    role="status"
    aria-live="polite"
  >
    <span class="sr-only">加载中</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  size?: number
  /** 描边宽度。不传则按尺寸推算 */
  strokeWidth?: number
}>(), { size: 14 })

const stroke = computed(() => props.strokeWidth ?? Math.max(1.5, props.size / 9))
</script>

<style scoped>
.ui-spinner {
  display: inline-block;
  flex-shrink: 0;
  border-style: solid;
  border-color: currentColor;
  /* 只留一段可见，其余透明，转起来就是弧线扫描 */
  border-right-color: transparent;
  border-bottom-color: transparent;
  border-radius: 50%;
  opacity: 0.85;
  animation: ui-spin 0.62s linear infinite;
}

@keyframes ui-spin {
  to { transform: rotate(360deg); }
}

/* 关掉动效后不转，改成静态半透明环，避免"卡住"的错觉 */
[data-motion="reduced"] .ui-spinner {
  animation: none;
  border-color: currentColor;
  opacity: 0.4;
}
</style>
