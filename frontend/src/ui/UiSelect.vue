<!--
  UiSelect —— 替代 n-select。

  覆盖现有用法：options / v-model:value / size / placeholder / clearable /
  loading / disabled / multiple / filterable / @update:value。

  定位、外部点击、Esc 全部走 ui/ 里共用的 composable，
  所以这里只管选项列表和键盘导航。
-->
<template>
  <div
    v-bind="rootAttrs"
    :class="['ui-select', `ui-select--${size}`, { 'is-disabled': disabled, 'is-open': open }, rootAttrs.class]"
    :style="rootAttrs.style"
  >
    <div
      ref="anchor"
      class="ui-select__field"
      role="combobox"
      :tabindex="disabled ? -1 : 0"
      :aria-expanded="open"
      :aria-disabled="disabled"
      aria-haspopup="listbox"
      @click="toggle"
      @keydown="onFieldKeydown"
    >
      <div class="ui-select__value">
        <template v-if="multiple">
          <span v-if="!selectedOptions.length" class="ui-select__placeholder">{{ placeholder }}</span>
          <span v-for="opt in selectedOptions" :key="String(opt.value)" class="ui-select__chip">
            {{ opt.label }}
            <button
              class="ui-select__chip-x"
              type="button"
              :aria-label="`移除 ${opt.label}`"
              @click.stop="deselect(opt.value)"
            >
              <X :size="10" />
            </button>
          </span>
        </template>

        <template v-else>
          <input
            v-if="filterable && open"
            ref="filterInput"
            v-model="query"
            class="ui-select__filter"
            :placeholder="selectedOptions[0]?.label ?? placeholder"
            @click.stop
          />
          <span v-else-if="selectedOptions.length" class="ui-select__label">{{ selectedOptions[0].label }}</span>
          <span v-else class="ui-select__placeholder">{{ placeholder }}</span>
        </template>
      </div>

      <UiSpinner v-if="loading" :size="12" class="ui-select__icon" />
      <button
        v-else-if="clearable && hasValue && !disabled"
        class="ui-select__clear"
        type="button"
        aria-label="清空"
        @click.stop="clear"
      >
        <X :size="12" />
      </button>
      <ChevronDown v-else :size="14" class="ui-select__icon ui-select__chevron" />
    </div>

    <Teleport to="body">
      <Transition name="ui-layer">
        <div
          v-if="open"
          ref="layer"
          class="ui-select__layer"
          role="listbox"
          :aria-multiselectable="multiple"
          :style="{
            top: `${position.top}px`,
            left: `${position.left}px`,
            minWidth: position.minWidth ? `${position.minWidth}px` : undefined,
          }"
        >
          <div v-if="!filtered.length" class="ui-select__empty">无匹配项</div>
          <button
            v-for="(opt, index) in filtered"
            :key="String(opt.value)"
            :class="['ui-select__option', {
              'is-selected': isSelected(opt.value),
              'is-active': index === activeIndex,
              'is-disabled': opt.disabled,
            }]"
            type="button"
            role="option"
            :aria-selected="isSelected(opt.value)"
            :disabled="opt.disabled"
            @click="pick(opt)"
            @mousemove="activeIndex = index"
          >
            <span class="ui-select__option-label">{{ opt.label }}</span>
            <Check v-if="isSelected(opt.value)" :size="13" class="ui-select__check" />
          </button>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useAttrs, watch } from 'vue'
import { Check, ChevronDown, X } from 'lucide-vue-next'
import UiSpinner from './UiSpinner.vue'
import { useAnchoredLayer } from './useAnchoredLayer'
import { useEscapeKey, useOutsidePointer } from './useOverlay'

// 布尔值也要支持：签到记录页用 true/false 做"成功/失败"筛选
type OptionValue = string | number | boolean | null

export interface SelectOptionItem {
  label: string
  value: OptionValue
  disabled?: boolean
}

const props = withDefaults(defineProps<{
  value?: OptionValue | OptionValue[]
  options?: SelectOptionItem[]
  size?: 'tiny' | 'small' | 'medium' | 'large'
  placeholder?: string
  disabled?: boolean
  clearable?: boolean
  loading?: boolean
  multiple?: boolean
  filterable?: boolean
}>(), {
  options: () => [],
  size: 'medium',
  placeholder: '请选择',
})

const emit = defineEmits<{
  'update:value': [value: OptionValue | OptionValue[] | null]
}>()

defineOptions({ inheritAttrs: false })
const attrs = useAttrs()
const rootAttrs = computed(() => ({ class: attrs.class, style: attrs.style as import('vue').StyleValue }))

const anchor = ref<HTMLElement | null>(null)
const layer = ref<HTMLElement | null>(null)
const filterInput = ref<HTMLInputElement | null>(null)
const open = ref(false)
const query = ref('')
const activeIndex = ref(-1)

const { position, track, untrack, update } = useAnchoredLayer(anchor, layer, {
  placement: 'bottom-start',
  offset: 5,
  matchWidth: true,
})

useEscapeKey(open, close)
useOutsidePointer(open, [anchor, layer], close)

const selectedValues = computed<OptionValue[]>(() => {
  if (props.value === undefined || props.value === null) return []
  return Array.isArray(props.value) ? props.value : [props.value]
})

const hasValue = computed(() => selectedValues.value.length > 0)

const selectedOptions = computed(() =>
  selectedValues.value
    .map(v => props.options.find(o => o.value === v) ?? { label: String(v), value: v })
    .filter(Boolean),
)

const filtered = computed(() => {
  if (!props.filterable || !query.value.trim()) return props.options
  const q = query.value.trim().toLowerCase()
  return props.options.filter(o => o.label.toLowerCase().includes(q))
})

function isSelected(value: OptionValue) {
  return selectedValues.value.includes(value)
}

async function openLayer() {
  if (props.disabled) return
  open.value = true
  query.value = ''
  // 打开时把高亮落在当前选中项上，键盘操作才有起点
  activeIndex.value = props.options.findIndex(o => isSelected(o.value))
  await nextTick()
  track()
  update()
  if (props.filterable) filterInput.value?.focus()
}

function close() {
  if (!open.value) return
  open.value = false
  query.value = ''
  activeIndex.value = -1
  untrack()
}

function toggle() {
  open.value ? close() : openLayer()
}

function pick(opt: SelectOptionItem) {
  if (opt.disabled) return
  if (props.multiple) {
    const next = isSelected(opt.value)
      ? selectedValues.value.filter(v => v !== opt.value)
      : [...selectedValues.value, opt.value]
    emit('update:value', next)
    // 多选保持展开，方便连续勾选
    query.value = ''
  } else {
    emit('update:value', opt.value)
    close()
  }
}

function deselect(value: OptionValue) {
  emit('update:value', selectedValues.value.filter(v => v !== value))
}

function clear() {
  emit('update:value', props.multiple ? [] : null)
  close()
}

function onFieldKeydown(event: KeyboardEvent) {
  if (props.disabled) return

  if (!open.value) {
    if (['Enter', ' ', 'ArrowDown', 'ArrowUp'].includes(event.key)) {
      event.preventDefault()
      openLayer()
    }
    return
  }

  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    const step = event.key === 'ArrowDown' ? 1 : -1
    const count = filtered.value.length
    if (!count) return
    // 跳过 disabled 项，最多绕一圈
    let next = activeIndex.value
    for (let i = 0; i < count; i++) {
      next = (next + step + count) % count
      if (!filtered.value[next]?.disabled) break
    }
    activeIndex.value = next
    return
  }

  if (event.key === 'Enter') {
    event.preventDefault()
    const opt = filtered.value[activeIndex.value]
    if (opt) pick(opt)
    return
  }

  if (event.key === 'Tab') close()
}

// 选项变了（比如异步加载完）要重新量一次，高度变化会影响翻面
watch(() => props.options, () => { if (open.value) update() })
</script>

<style scoped>
.ui-select { position: relative; width: 100%; }

.ui-select__field {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  background: var(--surface-inset);
  color: var(--ink-max);
  cursor: pointer;
  transition: border-color 0.14s ease, background-color 0.14s ease;
}

.ui-select__field:hover { border-color: var(--line-strong); }

.ui-select.is-open .ui-select__field {
  border-color: var(--signal-deep);
  background: var(--surface-raised);
}

.ui-select.is-disabled .ui-select__field {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-select--tiny .ui-select__field { min-height: 24px; padding: 0 6px; font-size: var(--fn-xs); }
.ui-select--small .ui-select__field { min-height: 30px; padding: 0 8px; font-size: var(--fn-sm); }
.ui-select--medium .ui-select__field { min-height: 34px; padding: 0 10px; font-size: var(--fn-md); }
.ui-select--large .ui-select__field { min-height: 44px; padding: 0 14px; font-size: var(--fn-lg); }

.ui-select__value {
  display: flex;
  flex: 1;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  min-width: 0;
  padding-block: 3px;
}

.ui-select__label {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.ui-select__placeholder {
  color: var(--ink-ghost);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ui-select__filter {
  flex: 1;
  min-width: 40px;
  border: 0;
  outline: none;
  background: transparent;
  color: inherit;
  font: inherit;
}

.ui-select__chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 4px 1px 6px;
  border-radius: var(--r-xs);
  background: var(--signal-wash);
  color: var(--signal-deep);
  font-size: var(--fn-xs);
  font-weight: var(--weight-medium);
}

.ui-select__chip-x {
  display: inline-flex;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  opacity: 0.6;
}

.ui-select__chip-x:hover { opacity: 1; }

.ui-select__icon,
.ui-select__clear {
  flex-shrink: 0;
  color: var(--ink-faint);
}

.ui-select__clear {
  display: inline-flex;
  padding: 0;
  border: 0;
  background: transparent;
}

.ui-select__clear:hover { color: var(--ink-max); }

.ui-select__chevron { transition: transform 0.18s cubic-bezier(0.2, 0.9, 0.3, 1); }
.ui-select.is-open .ui-select__chevron { transform: rotate(180deg); }

/* ── 浮层 */

.ui-select__layer {
  position: fixed;
  z-index: var(--z-layer);
  max-height: 288px;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
}

.ui-select__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  border: 0;
  border-radius: var(--r-xs);
  background: transparent;
  color: var(--ink-strong);
  font-size: var(--fn-sm);
  text-align: left;
}

.ui-select__option.is-active { background: var(--surface-hover); }

.ui-select__option.is-selected {
  color: var(--signal-deep);
  font-weight: var(--weight-medium);
}

.ui-select__option.is-disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ui-select__option-label {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.ui-select__check { flex-shrink: 0; }

.ui-select__empty {
  padding: 12px 8px;
  color: var(--ink-faint);
  font-size: var(--fn-sm);
  text-align: center;
}

/* 浮层进出：从锚点方向轻微展开 */
.ui-layer-enter-active,
.ui-layer-leave-active {
  transition: opacity 0.14s ease, transform 0.18s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.ui-layer-enter-from,
.ui-layer-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
</style>
