<!--
  UiLoading —— 替代 n-spin 的"包裹内容 + 显示加载态"用法。

  不用居中转圈遮罩：那会把已有内容整块挡住，刷新时用户看不到自己原来在哪。
  改成顶缘一条扫描轨 + 内容轻微降透明度，和 DataGrid 的刷新指示是同一套语言。

  用法与 n-spin 一致：<UiLoading :show="loading">…</UiLoading>
-->
<template>
  <div class="load" :class="{ 'is-busy': show }">
    <span v-if="show" class="load__rail" aria-hidden="true" />
    <div class="load__body" :aria-busy="show">
      <slot />
    </div>
    <!-- 首次加载（内容还是空的）时给一个居中提示，否则页面看起来像坏了 -->
    <div v-if="show && empty" class="load__first">
      <UiSpinner :size="18" />
      <span class="load__first-text">{{ description }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import UiSpinner from './UiSpinner.vue'

withDefaults(defineProps<{
  show?: boolean
  /** 内容为空时才显示居中提示；有内容时只走顶部扫描轨 */
  empty?: boolean
  description?: string
}>(), { description: '加载中' })
</script>

<style scoped>
.load {
  position: relative;
  min-width: 0;
}

.load__rail {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 3;
  height: 2px;
  width: 30%;
  border-radius: var(--r-full);
  background: linear-gradient(90deg, transparent, var(--signal), transparent);
  animation: load-scan 1.1s ease-in-out infinite;
}

@keyframes load-scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(433%); }
}

.load__body { transition: opacity 0.18s ease; }

.load.is-busy .load__body { opacity: 0.55; }

.load__first {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: var(--s3);
  color: var(--ink-muted);
}

.load__first-text {
  font-size: var(--fn-xs);
  letter-spacing: var(--track-wide);
}
</style>
