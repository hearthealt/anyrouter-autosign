<template>
  <a
    v-if="safeHref"
    class="external-link"
    :class="{ wrap }"
    :href="safeHref"
    :title="tooltip"
    target="_blank"
    rel="noopener noreferrer"
    @click.stop
  >
    <span class="link-text" :class="{ mono }">{{ text }}</span>
  </a>
  <span v-else class="external-link is-plain" :class="{ wrap }" :title="tooltip">
    <span class="link-text" :class="{ mono }">{{ text }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { normalizeExternalUrl } from '../../utils'

const props = defineProps<{
  /** 目标地址，非 http/https 时自动降级为不可点击的纯文本 */
  href?: string | null
  /** 显示文本，默认直接显示 href */
  label?: string | null
  /** 使用等宽字体 */
  mono?: boolean
  /** 允许折行显示完整地址（默认单行截断） */
  wrap?: boolean
  /** 悬浮提示，默认取 href */
  title?: string | null
}>()

const safeHref = computed(() => normalizeExternalUrl(props.href))
const text = computed(() => props.label?.trim() || props.href?.trim() || '—')
const tooltip = computed(() => props.title?.trim() || props.href?.trim() || undefined)
</script>

<style scoped>
/* 默认沿用常规文本配色，仅悬浮时才变主色 —— 避免整张表变成一片蓝链接。 */
.external-link {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  max-width: 100%;
  color: var(--text-secondary);
  text-decoration: none;
}

.external-link.is-plain {
  cursor: default;
}

.external-link:not(.is-plain):hover,
.external-link:not(.is-plain):hover .link-text {
  color: var(--primary-color);
  text-decoration: underline;
}

.link-text {
  max-width: 100%;
  overflow: hidden;
  color: inherit;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mono {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.external-link.wrap {
  display: block;
}

.external-link.wrap .link-text {
  overflow: visible;
  text-overflow: clip;
  white-space: normal;
  word-break: break-all;
}
</style>
