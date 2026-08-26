<!--
  UiDivider —— 替代 n-divider。支持水平/垂直，以及带标题的分段线。
-->
<template>
  <div v-if="vertical" class="ui-divider ui-divider--v" role="separator" />
  <div v-else-if="$slots.default" class="ui-divider ui-divider--titled" role="separator">
    <span class="ui-divider__line" />
    <span class="ui-divider__title kicker"><slot /></span>
    <span class="ui-divider__line" />
  </div>
  <hr v-else class="ui-divider ui-divider--h" />
</template>

<script setup lang="ts">
defineProps<{ vertical?: boolean }>()
</script>

<style scoped>
.ui-divider--h {
  border: 0;
  border-top: 1px solid var(--line-faint);
  margin: var(--s4) 0;
}

.ui-divider--v {
  display: inline-block;
  width: 1px;
  height: 1em;
  margin: 0 var(--s2);
  background: var(--line-faint);
  vertical-align: middle;
}

.ui-divider--titled {
  display: flex;
  align-items: center;
  gap: var(--s3);
  margin: var(--s5) 0 var(--s4);
}

.ui-divider__line {
  flex: 1;
  height: 1px;
  background: var(--line-faint);
}

.ui-divider__title { flex-shrink: 0; }
</style>
