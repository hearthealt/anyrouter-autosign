<!--
  DataGrid —— 替代 n-data-table。

  列定义 API 刻意和 Naive 保持一致，让 5 处调用点的 columns 几乎原样保留：
    title / key / width / minWidth / align
    render(row, index)      返回 VNode 或字符串
    type: 'selection'       选择列
    sorter: 'default'       + sortOrder（受控远程排序）
    ellipsis: { tooltip }   截断并用 tooltip 显示全文

  视觉上按"分区艺术指导"的数据页标准做：等宽数字、极细分隔、
  行悬停时左缘亮起一条 signal 色，动效只做确认反馈不做装饰。
-->
<template>
  <div class="grid" :class="[`grid--${size}`, { 'is-loading': loading }]">
    <div ref="scroller" class="grid__scroll">
      <table class="grid__table" :style="{ minWidth: scrollX ? `${scrollX}px` : undefined }">
        <colgroup>
          <col v-for="(col, i) in normalized" :key="`c-${i}`" :style="colStyle(col)" />
        </colgroup>

        <thead class="grid__head">
          <tr>
            <th
              v-for="(col, i) in normalized"
              :key="`h-${i}`"
              :class="['grid__th', col.align && `is-${col.align}`, {
                'is-sortable': !!col.sorter,
                'is-sorted': !!col.sortOrder,
                'is-selection': col.type === 'selection',
              }]"
              :aria-sort="ariaSort(col)"
              @click="col.sorter && toggleSort(col)"
            >
              <UiCheckbox
                v-if="col.type === 'selection'"
                size="small"
                :checked="allChecked"
                :indeterminate="someChecked"
                :disabled="!data.length"
                @update:checked="toggleAll"
              />
              <template v-else>
                <span class="grid__th-label">{{ col.title }}</span>
                <span v-if="col.sorter" class="grid__sort" aria-hidden="true">
                  <ChevronUp v-if="col.sortOrder === 'ascend'" :size="12" />
                  <ChevronDown v-else-if="col.sortOrder === 'descend'" :size="12" />
                  <ChevronsUpDown v-else :size="12" class="grid__sort-idle" />
                </span>
              </template>
            </th>
          </tr>
        </thead>

        <tbody class="grid__body">
          <!-- 加载时用骨架行而不是遮罩转圈：布局不跳，也能看出会有几行 -->
          <template v-if="loading && !data.length">
            <tr v-for="n in skeletonRows" :key="`sk-${n}`" class="grid__row is-skeleton">
              <td v-for="i in normalized.length" :key="`sk-${n}-${i}`" class="grid__td">
                <UiSkeleton text :width="i === 1 ? '60%' : '80%'" />
              </td>
            </tr>
          </template>

          <tr
            v-for="(row, index) in data"
            :key="keyOf(row, index)"
            :class="['grid__row', rowClassName?.(row, index), {
              'is-checked': isChecked(keyOf(row, index)),
            }]"
          >
            <td
              v-for="(col, i) in normalized"
              :key="`${keyOf(row, index)}-${i}`"
              :class="['grid__td', col.align && `is-${col.align}`, {
                'is-selection': col.type === 'selection',
                'is-ellipsis': !!col.ellipsis,
              }]"
            >
              <UiCheckbox
                v-if="col.type === 'selection'"
                size="small"
                :checked="isChecked(keyOf(row, index))"
                @update:checked="value => toggleRow(keyOf(row, index), value)"
              />

              <UiTooltip v-else-if="col.ellipsis" :content="plainText(col, row, index)" placement="top">
                <span class="grid__clip"><RenderCell :node="cell(col, row, index)" /></span>
              </UiTooltip>

              <RenderCell v-else :node="cell(col, row, index)" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && !data.length" class="grid__empty">
      <slot name="empty">
        <p class="grid__empty-title">暂无数据</p>
        <p class="grid__empty-desc">调整筛选条件后重试</p>
      </slot>
    </div>

    <!-- 已有数据时的刷新：顶部一条进度轨，不遮挡内容 -->
    <span v-if="loading && data.length" class="grid__refresh" aria-hidden="true" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, type VNodeChild } from 'vue'
import { ChevronDown, ChevronsUpDown, ChevronUp } from 'lucide-vue-next'
import RenderCell from './RenderCell'
import UiCheckbox from './UiCheckbox.vue'
import UiSkeleton from './UiSkeleton.vue'
import UiTooltip from './UiTooltip.vue'

export type SortOrder = false | 'ascend' | 'descend'

export interface GridColumn<T = any> {
  title?: string
  key?: string
  type?: 'selection'
  width?: number | string
  minWidth?: number | string
  align?: 'left' | 'center' | 'right'
  sorter?: 'default' | boolean
  sortOrder?: SortOrder
  ellipsis?: boolean | { tooltip?: boolean }
  render?: (row: T, index: number) => VNodeChild
}

export interface GridSortState {
  columnKey: string
  order: SortOrder
}

/**
 * 列定义数组。对齐 Naive 的 `DataTableColumns<T>` 语义 ——
 * 那个类型名本身就是数组，调用点写 `computed<GridColumns<Account>>(...)` 才成立。
 */
export type GridColumns<T = any> = GridColumn<T>[]

const props = withDefaults(defineProps<{
  columns?: GridColumn[]
  data?: any[]
  rowKey?: (row: any) => string | number
  checkedRowKeys?: Array<string | number>
  loading?: boolean
  size?: 'small' | 'medium'
  scrollX?: number
  rowClassName?: (row: any, index: number) => string | undefined
  skeletonRows?: number
}>(), {
  columns: () => [],
  data: () => [],
  checkedRowKeys: () => [],
  size: 'small',
  skeletonRows: 6,
})

const emit = defineEmits<{
  'update:sorter': [sorter: GridSortState | null]
  'update:checkedRowKeys': [keys: Array<string | number>]
}>()

const scroller = ref<HTMLElement | null>(null)

const normalized = computed(() => props.columns.filter(Boolean))

function colStyle(col: GridColumn) {
  const width = col.width ?? col.minWidth
  if (width === undefined) return undefined
  const value = typeof width === 'number' ? `${width}px` : width
  return col.width !== undefined ? { width: value } : { minWidth: value }
}

function keyOf(row: any, index: number): string | number {
  return props.rowKey ? props.rowKey(row) : (row?.id ?? index)
}

function cell(col: GridColumn, row: any, index: number): VNodeChild {
  if (col.render) return col.render(row, index)
  return col.key ? (row?.[col.key] ?? '-') : ''
}

/** ellipsis 的 tooltip 需要纯文本。render 返回 VNode 时取不到，退回字段原值。 */
function plainText(col: GridColumn, row: any, index: number): string {
  if (col.key && row?.[col.key] !== undefined && row[col.key] !== null) return String(row[col.key])
  const rendered = col.render?.(row, index)
  return typeof rendered === 'string' || typeof rendered === 'number' ? String(rendered) : ''
}

/* ── 排序 */

function ariaSort(col: GridColumn): 'ascending' | 'descending' | 'none' | undefined {
  if (!col.sorter) return undefined
  if (col.sortOrder === 'ascend') return 'ascending'
  if (col.sortOrder === 'descend') return 'descending'
  return 'none'
}

/** 三态循环：无 → 升 → 降 → 无。和 Naive 的默认行为一致。 */
function toggleSort(col: GridColumn) {
  if (!col.key) return
  const next: SortOrder = col.sortOrder === 'ascend' ? 'descend' : col.sortOrder === 'descend' ? false : 'ascend'
  emit('update:sorter', next ? { columnKey: col.key, order: next } : null)
}

/* ── 选择 */

const checkedSet = computed(() => new Set(props.checkedRowKeys))

function isChecked(key: string | number) {
  return checkedSet.value.has(key)
}

const allKeys = computed(() => props.data.map((row, index) => keyOf(row, index)))

const allChecked = computed(() => allKeys.value.length > 0 && allKeys.value.every(k => checkedSet.value.has(k)))

const someChecked = computed(
  () => !allChecked.value && allKeys.value.some(k => checkedSet.value.has(k)),
)

function toggleRow(key: string | number, checked: boolean) {
  const next = new Set(props.checkedRowKeys)
  checked ? next.add(key) : next.delete(key)
  emit('update:checkedRowKeys', Array.from(next))
}

/** 全选只影响当前页：跨页保留其他页已勾选的行。 */
function toggleAll(checked: boolean) {
  const next = new Set(props.checkedRowKeys)
  for (const key of allKeys.value) checked ? next.add(key) : next.delete(key)
  emit('update:checkedRowKeys', Array.from(next))
}
</script>

<style scoped>
.grid {
  position: relative;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-md);
  background: var(--surface-raised);
  overflow: hidden;
}

.grid__scroll {
  overflow-x: auto;
  overscroll-behavior-x: contain;
}

.grid__table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  /* 数据表全域等宽数字：纵向对比数值的前提 */
  font-variant-numeric: tabular-nums;
}

/* ── 表头 */

.grid__head {
  position: sticky;
  top: 0;
  z-index: 2;
}

.grid__th {
  position: relative;
  padding: 0 var(--s3);
  height: 34px;
  border-bottom: 1px solid var(--line-faint);
  background: var(--surface-inset);
  color: var(--ink-faint);
  font-size: var(--fn-2xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-caps);
  text-transform: uppercase;
  text-align: left;
  white-space: nowrap;
  user-select: none;
}

.grid__th.is-center { text-align: center; }
.grid__th.is-right { text-align: right; }

.grid__th.is-selection {
  width: 40px;
  padding-inline: var(--s3);
}

.grid__th.is-sortable { cursor: pointer; }
.grid__th.is-sortable:hover { color: var(--ink); }
.grid__th.is-sorted { color: var(--signal-deep); }

.grid__th-label { vertical-align: middle; }

.grid__sort {
  display: inline-flex;
  align-items: center;
  margin-left: 3px;
  vertical-align: middle;
}

.grid__sort-idle { opacity: 0; transition: opacity 0.14s ease; }
.grid__th.is-sortable:hover .grid__sort-idle { opacity: 0.5; }

/* ── 行 */

.grid__row { position: relative; }

.grid__td {
  position: relative;
  padding: 0 var(--s3);
  height: 40px;
  border-bottom: 1px solid var(--line-faint);
  color: var(--ink-strong);
  font-size: var(--fn-sm);
  vertical-align: middle;
}

.grid--medium .grid__td { height: 48px; }

.grid__td.is-center { text-align: center; }
.grid__td.is-right { text-align: right; }
.grid__td.is-selection { width: 40px; }

.grid__body tr:last-child .grid__td { border-bottom: 0; }

/* 悬停：底色提亮 + 左缘 signal 色竖条。竖条用第一个 td 的伪元素画 */
.grid__row:hover .grid__td { background: var(--surface-hover); }

.grid__row .grid__td:first-child::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--signal);
  transform: scaleY(0);
  transform-origin: center;
  transition: transform 0.16s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.grid__row:hover .grid__td:first-child::before,
.grid__row.is-checked .grid__td:first-child::before {
  transform: scaleY(1);
}

.grid__row.is-checked .grid__td { background: var(--signal-wash); }

.grid__row.is-skeleton .grid__td { background: transparent; }

.grid__clip {
  display: block;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.grid__td.is-ellipsis { max-width: 0; }

/* ── 空态与刷新 */

.grid__empty {
  display: grid;
  justify-items: center;
  gap: 4px;
  padding: var(--s16) var(--s5);
  text-align: center;
}

.grid__empty-title {
  color: var(--ink-strong);
  font-size: var(--fn-md);
  font-weight: var(--weight-semibold);
}

.grid__empty-desc {
  color: var(--ink-muted);
  font-size: var(--fn-sm);
}

/* 刷新指示：顶缘一条来回扫描的 signal 色轨 */
.grid__refresh {
  position: absolute;
  top: 0;
  left: 0;
  height: 2px;
  width: 32%;
  background: linear-gradient(90deg, transparent, var(--signal), transparent);
  animation: grid-scan 1.1s ease-in-out infinite;
  z-index: 3;
}

@keyframes grid-scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(412%); }
}
</style>
