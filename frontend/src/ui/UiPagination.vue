<!--
  UiPagination —— 替代 n-pagination（5 处列表都用）。

  页码用等宽数字并给固定最小宽度，翻页时按钮不会因为位数变化而抖动 ——
  这是密集表格底部最容易被忽略的细节。
-->
<template>
  <nav class="pager" :class="{ 'is-disabled': disabled }" aria-label="分页">
    <span v-if="showTotal" class="pager__total">
      共 <strong class="tabular">{{ itemCount }}</strong> 条
    </span>

    <div class="pager__controls">
      <UiButton
        size="tiny"
        quaternary
        aria-label="上一页"
        :disabled="disabled || page <= 1"
        @click="go(page - 1)"
      >
        <template #icon><ChevronLeft :size="14" /></template>
      </UiButton>

      <button
        v-for="(item, index) in pages"
        :key="`p-${index}-${item}`"
        :class="['pager__page', { 'is-current': item === page, 'is-gap': item === '…' }]"
        type="button"
        :disabled="disabled || item === '…'"
        :aria-current="item === page ? 'page' : undefined"
        @click="typeof item === 'number' && go(item)"
      >{{ item }}</button>

      <UiButton
        size="tiny"
        quaternary
        aria-label="下一页"
        :disabled="disabled || page >= pageCount"
        @click="go(page + 1)"
      >
        <template #icon><ChevronRight :size="14" /></template>
      </UiButton>
    </div>

    <UiSelect
      v-if="pageSizes?.length"
      class="pager__size"
      size="tiny"
      :value="pageSize"
      :options="sizeOptions"
      :disabled="disabled"
      @update:value="value => emit('update:pageSize', Number(value))"
    />
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import UiButton from './UiButton.vue'
import UiSelect from './UiSelect.vue'

const props = withDefaults(defineProps<{
  page?: number
  pageSize?: number
  itemCount?: number
  pageSizes?: number[]
  showTotal?: boolean
  disabled?: boolean
  /** 中间连续页码的最大个数，两端各留 1 个 */
  siblings?: number
}>(), {
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showTotal: true,
  siblings: 1,
})

const emit = defineEmits<{
  'update:page': [page: number]
  'update:pageSize': [size: number]
}>()

const pageCount = computed(() => Math.max(1, Math.ceil(props.itemCount / (props.pageSize || 1))))

const sizeOptions = computed(() => (props.pageSizes ?? []).map(n => ({ label: `${n} 条/页`, value: n })))

/**
 * 生成页码序列，形如 1 … 4 5 6 … 20。
 * 两端各固定 1 个，当前页两侧各 `siblings` 个，缺口用 '…' 占位。
 */
const pages = computed<Array<number | '…'>>(() => {
  const total = pageCount.value
  const current = props.page
  const span = props.siblings

  if (total <= 5 + span * 2) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const result: Array<number | '…'> = [1]
  const start = Math.max(2, current - span)
  const end = Math.min(total - 1, current + span)

  if (start > 2) result.push('…')
  for (let i = start; i <= end; i++) result.push(i)
  if (end < total - 1) result.push('…')
  result.push(total)

  return result
})

function go(next: number) {
  if (props.disabled) return
  const clamped = Math.min(Math.max(1, next), pageCount.value)
  if (clamped !== props.page) emit('update:page', clamped)
}
</script>

<style scoped>
.pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--s3);
  flex-wrap: wrap;
}

.pager.is-disabled { opacity: 0.5; }

.pager__total {
  margin-right: auto;
  color: var(--ink-muted);
  font-size: var(--fn-xs);
}

.pager__total strong {
  color: var(--ink-strong);
  font-weight: var(--weight-semibold);
}

.pager__controls {
  display: flex;
  align-items: center;
  gap: 2px;
}

.pager__page {
  /* 固定最小宽度：页码从 9 跳到 10 时按钮不变形 */
  min-width: 26px;
  height: 24px;
  padding: 0 5px;
  border: 1px solid transparent;
  border-radius: var(--r-xs);
  background: transparent;
  color: var(--ink-muted);
  font-size: var(--fn-xs);
  font-weight: var(--weight-medium);
  font-variant-numeric: tabular-nums;
  transition: background-color 0.12s ease, color 0.12s ease, border-color 0.12s ease;
}

.pager__page:hover:not(:disabled):not(.is-current) {
  background: var(--surface-hover);
  color: var(--ink-max);
}

.pager__page.is-current {
  border-color: var(--signal);
  background: var(--signal-wash);
  color: var(--signal-deep);
  font-weight: var(--weight-semibold);
}

.pager__page.is-gap {
  cursor: default;
  color: var(--ink-ghost);
}

.pager__size { width: 104px; }
</style>
