<!--
  UiSegment —— 一口吃掉 n-radio-group/n-radio-button 和 <n-tabs type="segment">。

  选中指示条用弹簧驱动位移和宽度，切换时会从上一个位置"滑"过去。
  这是全站复用最多的一个动效瞬间，所以值得用真弹簧而不是 CSS transition。
-->
<template>
  <div
    ref="root"
    :class="['ui-segment', `ui-segment--${size}`, { 'is-block': block }]"
    role="tablist"
  >
    <span ref="indicator" class="ui-segment__indicator" aria-hidden="true" />
    <button
      v-for="opt in options"
      :key="String(opt.value)"
      :ref="el => setItemRef(String(opt.value), el as HTMLElement | null)"
      :class="['ui-segment__item', { 'is-active': opt.value === value }]"
      type="button"
      role="tab"
      :aria-selected="opt.value === value"
      :disabled="opt.disabled"
      @click="pick(opt)"
    >
      <span v-if="opt.icon" class="ui-segment__icon"><component :is="opt.icon" :size="14" /></span>
      <span class="ui-segment__label">{{ opt.label }}</span>
      <span v-if="opt.count !== undefined" class="ui-segment__count tabular">{{ opt.count }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch, type Component } from 'vue'
import { spring, SPRING, type SpringHandle } from '../design/motion'

type SegmentValue = string | number

export interface SegmentOption {
  label: string
  value: SegmentValue
  disabled?: boolean
  icon?: Component
  count?: number
}

const props = withDefaults(defineProps<{
  value?: SegmentValue
  options?: SegmentOption[]
  size?: 'small' | 'medium'
  block?: boolean
}>(), {
  options: () => [],
  size: 'medium',
})

const emit = defineEmits<{ 'update:value': [value: SegmentValue] }>()

const root = ref<HTMLElement | null>(null)
const indicator = ref<HTMLElement | null>(null)
const items = new Map<string, HTMLElement>()

let sx: SpringHandle | null = null
let sw: SpringHandle | null = null
let observer: ResizeObserver | null = null
let x = 0
let w = 0

function setItemRef(key: string, el: HTMLElement | null) {
  if (el) items.set(key, el)
  else items.delete(key)
}

function write() {
  if (!indicator.value) return
  indicator.value.style.transform = `translate3d(${x.toFixed(2)}px, 0, 0)`
  indicator.value.style.width = `${w.toFixed(2)}px`
}

function measure(animate = true) {
  const active = items.get(String(props.value))
  if (!active || !root.value || !indicator.value) return

  const rootRect = root.value.getBoundingClientRect()
  const rect = active.getBoundingClientRect()
  const nextX = rect.left - rootRect.left
  const nextW = rect.width

  if (!animate || !sx || !sw) {
    x = nextX
    w = nextW
    sx?.jump(nextX)
    sw?.jump(nextW)
    indicator.value.style.opacity = '1'
    write()
    return
  }

  sx.set(nextX)
  sw.set(nextW)
}

onMounted(async () => {
  sx = spring(0, value => { x = value; write() }, SPRING.crisp)
  sw = spring(0, value => { w = value; write() }, SPRING.crisp)
  await nextTick()
  measure(false)

  // 容器尺寸变化（侧栏折叠、窗口缩放）要重新量
  if (typeof ResizeObserver !== 'undefined' && root.value) {
    observer = new ResizeObserver(() => measure(false))
    observer.observe(root.value)
  }
})

onBeforeUnmount(() => {
  observer?.disconnect()
  sx?.stop()
  sw?.stop()
})

watch(() => props.value, () => nextTick(() => measure(true)))
watch(() => props.options, () => nextTick(() => measure(false)), { deep: true })

function pick(opt: SegmentOption) {
  if (opt.disabled || opt.value === props.value) return
  emit('update:value', opt.value)
}
</script>

<style scoped>
.ui-segment {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-md);
  background: var(--surface-sunken);
}

.ui-segment.is-block { display: flex; width: 100%; }
.ui-segment.is-block .ui-segment__item { flex: 1; }

/* 指示条：绝对定位在容器内，靠 transform 移动 */
.ui-segment__indicator {
  position: absolute;
  top: 2px;
  left: 0;
  bottom: 2px;
  border-radius: var(--r-sm);
  background: var(--surface-raised);
  box-shadow: var(--lift-2);
  opacity: 0;
  pointer-events: none;
}

.ui-segment__item {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  border: 0;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--ink-muted);
  font-weight: var(--weight-medium);
  white-space: nowrap;
  transition: color 0.16s ease;
}

.ui-segment--small .ui-segment__item { height: 26px; padding: 0 10px; font-size: var(--fn-xs); }
.ui-segment--medium .ui-segment__item { height: 30px; padding: 0 14px; font-size: var(--fn-sm); }

.ui-segment__item:hover:not(:disabled):not(.is-active) { color: var(--ink-strong); }

.ui-segment__item.is-active {
  color: var(--ink-max);
  font-weight: var(--weight-semibold);
}

.ui-segment__item:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ui-segment__icon { display: inline-flex; align-items: center; }

.ui-segment__count {
  padding: 0 4px;
  border-radius: var(--r-xs);
  background: var(--surface-active);
  color: var(--ink-muted);
  font-size: var(--fn-2xs);
  font-weight: var(--weight-semibold);
}

.ui-segment__item.is-active .ui-segment__count {
  background: var(--signal-wash);
  color: var(--signal-deep);
}
</style>
