<!--
  UiDateRange —— 替代 n-date-picker type="daterange"（SignLogs / Statistics / AuditLogs 三处）。

  值格式与 Naive 一致：[起始毫秒, 结束毫秒] | null。
  起始归零到 00:00:00，结束推到 23:59:59，这样调用方直接 toISOString().split('T')[0]
  取到的日期就是用户看到的那两天，不会因为时区偏移差一天。

  双月并排 + 左侧快捷区间。范围内的日期用 signal 色淡底连成一条，
  端点实心 —— 一眼能看出选了多长一段。
-->
<template>
  <div
    v-bind="rootAttrs"
    class="dr"
    :class="[{ 'is-disabled': disabled }, rootAttrs.class]"
    :style="rootAttrs.style"
  >
    <div
      ref="anchor"
      class="dr__field"
      :class="`dr__field--${size}`"
      role="button"
      :tabindex="disabled ? -1 : 0"
      :aria-expanded="open"
      @click="toggle"
      @keydown.enter.prevent="toggle"
      @keydown.space.prevent="toggle"
    >
      <CalendarDays :size="13" class="dr__icon" />
      <span v-if="value" class="dr__text tabular">{{ label }}</span>
      <span v-else class="dr__placeholder">{{ placeholder }}</span>
      <button
        v-if="clearable && value && !disabled"
        class="dr__clear"
        type="button"
        aria-label="清空日期"
        @click.stop="clear"
      >
        <X :size="12" />
      </button>
    </div>

    <Teleport to="body">
      <Transition name="ui-layer">
        <div
          v-if="open"
          ref="layer"
          class="dr__layer"
          :style="{ top: `${position.top}px`, left: `${position.left}px` }"
        >
          <aside class="dr__presets">
            <button
              v-for="preset in presets"
              :key="preset.label"
              class="dr__preset"
              type="button"
              @click="applyPreset(preset)"
            >{{ preset.label }}</button>
          </aside>

          <div class="dr__cals">
            <header class="dr__nav">
              <UiButton size="tiny" quaternary aria-label="上一月" @click="shiftMonth(-1)">
                <template #icon><ChevronLeft :size="14" /></template>
              </UiButton>
              <span class="dr__nav-label tabular">
                {{ viewYear }} 年 {{ viewMonth + 1 }} 月 — {{ nextView.year }} 年 {{ nextView.month + 1 }} 月
              </span>
              <UiButton size="tiny" quaternary aria-label="下一月" @click="shiftMonth(1)">
                <template #icon><ChevronRight :size="14" /></template>
              </UiButton>
            </header>

            <div class="dr__grids">
              <table v-for="(month, mi) in [{ year: viewYear, month: viewMonth }, nextView]" :key="mi" class="dr__grid">
                <thead>
                  <tr>
                    <th v-for="d in WEEKDAYS" :key="d" class="dr__wd">{{ d }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(week, wi) in monthMatrix(month.year, month.month)" :key="wi">
                    <td v-for="(day, di) in week" :key="di" class="dr__cell">
                      <button
                        v-if="day"
                        :class="['dr__day', {
                          'is-start': isStart(day),
                          'is-end': isEnd(day),
                          'is-inside': isInside(day),
                          'is-today': isToday(day),
                          'is-outside': day.getMonth() !== month.month,
                        }]"
                        type="button"
                        @click="pick(day)"
                        @mouseenter="hover = day.getTime()"
                      >{{ day.getDate() }}</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useAttrs, watch } from 'vue'
import { CalendarDays, ChevronLeft, ChevronRight, X } from 'lucide-vue-next'
import UiButton from './UiButton.vue'
import { useAnchoredLayer } from './useAnchoredLayer'
import { useEscapeKey, useOutsidePointer } from './useOverlay'

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

const props = withDefaults(defineProps<{
  value?: [number, number] | null
  size?: 'tiny' | 'small' | 'medium'
  placeholder?: string
  clearable?: boolean
  disabled?: boolean
}>(), {
  size: 'small',
  placeholder: '选择日期范围',
  clearable: true,
})

const emit = defineEmits<{ 'update:value': [value: [number, number] | null] }>()

defineOptions({ inheritAttrs: false })
const attrs = useAttrs()
const rootAttrs = computed(() => ({ class: attrs.class, style: attrs.style as import('vue').StyleValue }))

const anchor = ref<HTMLElement | null>(null)
const layer = ref<HTMLElement | null>(null)
const open = ref(false)
/** 只选了起点、等待第二次点击时的悬停预览 */
const pendingStart = ref<number | null>(null)
const hover = ref<number | null>(null)

const today = startOfDay(new Date())
const viewYear = ref(today.getFullYear())
const viewMonth = ref(today.getMonth())

const { position, track, untrack, update } = useAnchoredLayer(anchor, layer, {
  placement: 'bottom-start',
  offset: 5,
})

useEscapeKey(open, close)
useOutsidePointer(open, [anchor, layer], close)

/* ── 日期工具 */

function startOfDay(date: Date): Date {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

function endOfDayMs(date: Date): number {
  const d = new Date(date)
  d.setHours(23, 59, 59, 999)
  return d.getTime()
}

function fmt(ms: number): string {
  const d = new Date(ms)
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

const label = computed(() => (props.value ? `${fmt(props.value[0])} → ${fmt(props.value[1])}` : ''))

const nextView = computed(() => {
  const month = viewMonth.value + 1
  return month > 11 ? { year: viewYear.value + 1, month: 0 } : { year: viewYear.value, month }
})

/**
 * 生成 6×7 的日期矩阵，周一起始。
 * 首尾补上相邻月份的日期（用 is-outside 淡化），避免格子空缺造成的视觉断裂。
 */
function monthMatrix(year: number, month: number): Array<Array<Date | null>> {
  const first = new Date(year, month, 1)
  // JS 的 getDay() 周日是 0，这里换成周一为 0
  const lead = (first.getDay() + 6) % 7
  const start = new Date(year, month, 1 - lead)

  const weeks: Array<Array<Date | null>> = []
  const cursor = new Date(start)
  for (let w = 0; w < 6; w++) {
    const week: Array<Date | null> = []
    for (let d = 0; d < 7; d++) {
      week.push(new Date(cursor))
      cursor.setDate(cursor.getDate() + 1)
    }
    weeks.push(week)
  }
  return weeks
}

/* ── 选区状态 */

const range = computed<[number, number] | null>(() => {
  if (pendingStart.value !== null) {
    const other = hover.value ?? pendingStart.value
    return pendingStart.value <= other ? [pendingStart.value, other] : [other, pendingStart.value]
  }
  return props.value ?? null
})

function isStart(day: Date) {
  const r = range.value
  return !!r && startOfDay(day).getTime() === startOfDay(new Date(r[0])).getTime()
}

function isEnd(day: Date) {
  const r = range.value
  return !!r && startOfDay(day).getTime() === startOfDay(new Date(r[1])).getTime()
}

function isInside(day: Date) {
  const r = range.value
  if (!r) return false
  const t = startOfDay(day).getTime()
  return t > startOfDay(new Date(r[0])).getTime() && t < startOfDay(new Date(r[1])).getTime()
}

function isToday(day: Date) {
  return startOfDay(day).getTime() === today.getTime()
}

/* ── 交互 */

function pick(day: Date) {
  const t = startOfDay(day).getTime()

  if (pendingStart.value === null) {
    pendingStart.value = t
    hover.value = t
    return
  }

  const [from, to] = pendingStart.value <= t ? [pendingStart.value, t] : [t, pendingStart.value]
  emit('update:value', [from, endOfDayMs(new Date(to))])
  pendingStart.value = null
  hover.value = null
  close()
}

interface Preset { label: string; days: number }

const presets: Preset[] = [
  { label: '今天', days: 0 },
  { label: '近 7 天', days: 6 },
  { label: '近 14 天', days: 13 },
  { label: '近 30 天', days: 29 },
  { label: '近 90 天', days: 89 },
]

function applyPreset(preset: Preset) {
  const end = new Date()
  const start = startOfDay(new Date())
  start.setDate(start.getDate() - preset.days)
  emit('update:value', [start.getTime(), endOfDayMs(end)])
  pendingStart.value = null
  close()
}

function shiftMonth(delta: number) {
  const next = new Date(viewYear.value, viewMonth.value + delta, 1)
  viewYear.value = next.getFullYear()
  viewMonth.value = next.getMonth()
  update()
}

function clear() {
  emit('update:value', null)
  pendingStart.value = null
}

async function openLayer() {
  if (props.disabled) return
  open.value = true
  pendingStart.value = null
  hover.value = null
  // 打开时把视图对到已选区间的起始月，而不是永远停在当月
  if (props.value) {
    const d = new Date(props.value[0])
    viewYear.value = d.getFullYear()
    viewMonth.value = d.getMonth()
  }
  await nextTick()
  track()
  update()
}

function close() {
  if (!open.value) return
  open.value = false
  pendingStart.value = null
  hover.value = null
  untrack()
}

function toggle() {
  open.value ? close() : openLayer()
}

watch(() => props.value, () => { if (open.value) update() })
</script>

<style scoped>
.dr { position: relative; }

.dr__field {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  background: var(--surface-inset);
  color: var(--ink-max);
  cursor: pointer;
  white-space: nowrap;
  transition: border-color 0.14s ease;
}

.dr__field:hover { border-color: var(--line-strong); }
.dr.is-disabled .dr__field { opacity: 0.5; cursor: not-allowed; }

.dr__field--tiny { height: 24px; padding: 0 6px; font-size: var(--fn-xs); }
.dr__field--small { height: 30px; padding: 0 8px; font-size: var(--fn-sm); }
.dr__field--medium { height: 34px; padding: 0 10px; font-size: var(--fn-md); }

.dr__icon { flex-shrink: 0; color: var(--ink-faint); }
.dr__placeholder { color: var(--ink-ghost); }

.dr__clear {
  display: inline-flex;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--ink-faint);
}

.dr__clear:hover { color: var(--ink-max); }

/* ── 浮层 */

.dr__layer {
  position: fixed;
  z-index: var(--z-layer);
  display: flex;
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
  overflow: hidden;
}

.dr__presets {
  display: grid;
  align-content: start;
  gap: 1px;
  padding: var(--s2);
  border-right: 1px solid var(--line-faint);
  background: var(--surface-inset);
}

.dr__preset {
  padding: 5px 10px;
  border: 0;
  border-radius: var(--r-xs);
  background: transparent;
  color: var(--ink);
  font-size: var(--fn-xs);
  text-align: left;
  white-space: nowrap;
}

.dr__preset:hover {
  background: var(--signal-wash);
  color: var(--signal-deep);
}

.dr__cals { padding: var(--s3); }

.dr__nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s2);
  margin-bottom: var(--s2);
}

.dr__nav-label {
  color: var(--ink-strong);
  font-size: var(--fn-xs);
  font-weight: var(--weight-semibold);
}

.dr__grids {
  display: flex;
  gap: var(--s5);
}

.dr__grid { border-collapse: collapse; }

.dr__wd {
  width: 30px;
  padding-bottom: 4px;
  color: var(--ink-faint);
  font-size: var(--fn-2xs);
  font-weight: var(--weight-medium);
}

.dr__cell { padding: 0; }

.dr__day {
  position: relative;
  width: 30px;
  height: 27px;
  border: 0;
  background: transparent;
  color: var(--ink-strong);
  font-size: var(--fn-xs);
  font-variant-numeric: tabular-nums;
  transition: background-color 0.1s ease, color 0.1s ease;
}

.dr__day:hover { background: var(--surface-hover); }
.dr__day.is-outside { color: var(--ink-ghost); }

.dr__day.is-today::after {
  content: "";
  position: absolute;
  left: 50%;
  bottom: 3px;
  width: 3px;
  height: 3px;
  margin-left: -1.5px;
  border-radius: 50%;
  background: var(--signal-deep);
}

/* 区间内：淡底连成一条 */
.dr__day.is-inside {
  background: var(--signal-wash);
  color: var(--signal-deep);
}

/* 端点：实心，两端外侧圆角 */
.dr__day.is-start,
.dr__day.is-end {
  background: var(--signal);
  color: var(--signal-ink);
  font-weight: var(--weight-semibold);
}

.dr__day.is-start { border-radius: var(--r-sm) 0 0 var(--r-sm); }
.dr__day.is-end { border-radius: 0 var(--r-sm) var(--r-sm) 0; }
.dr__day.is-start.is-end { border-radius: var(--r-sm); }

.dr__day.is-start.is-end::after,
.dr__day.is-start::after,
.dr__day.is-end::after { background: var(--signal-ink); }

.ui-layer-enter-active,
.ui-layer-leave-active {
  transition: opacity 0.14s ease, transform 0.18s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.ui-layer-enter-from,
.ui-layer-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}

@media (max-width: 720px) {
  .dr__grids { flex-direction: column; gap: var(--s3); }
  .dr__presets { display: none; }
}
</style>
