<!--
  UiNumberInput —— 替代 n-input-number。

  覆盖现有用法：v-model:value / min / max / step / size，以及右侧后缀插槽
  （TokensModal 用它放"额度"单位）。

  步进按钮做成上下叠放的细长条，比左右两个圆按钮占位更小，
  密集设置表单里更合适。
-->
<template>
  <div class="num" :class="[`num--${size}`, { 'is-disabled': disabled, 'is-focused': focused }]">
    <input
      ref="control"
      class="num__control"
      type="text"
      inputmode="numeric"
      :value="display"
      :disabled="disabled"
      :placeholder="placeholder"
      v-bind="$attrs"
      @input="onInput"
      @focus="focused = true"
      @blur="onBlur"
      @keydown.up.prevent="bump(step)"
      @keydown.down.prevent="bump(-step)"
    />

    <span v-if="$slots.suffix" class="num__suffix"><slot name="suffix" /></span>

    <span class="num__steps">
      <button
        class="num__step"
        type="button"
        aria-label="增加"
        :disabled="disabled || atMax"
        @click="bump(step)"
      >
        <ChevronUp :size="10" />
      </button>
      <button
        class="num__step"
        type="button"
        aria-label="减少"
        :disabled="disabled || atMin"
        @click="bump(-step)"
      >
        <ChevronDown :size="10" />
      </button>
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ChevronDown, ChevronUp } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  value?: number | null
  min?: number
  max?: number
  step?: number
  size?: 'tiny' | 'small' | 'medium'
  placeholder?: string
  disabled?: boolean
}>(), {
  step: 1,
  size: 'medium',
})

const emit = defineEmits<{ 'update:value': [value: number | null] }>()

defineOptions({ inheritAttrs: false })

const control = ref<HTMLInputElement | null>(null)
const focused = ref(false)
/** 聚焦期间保留用户的原始输入（可能是 "-" 或 "1." 这种中间态） */
const draft = ref<string | null>(null)

const display = computed(() => (draft.value !== null ? draft.value : props.value ?? ''))

const atMin = computed(() => props.min !== undefined && (props.value ?? 0) <= props.min)
const atMax = computed(() => props.max !== undefined && (props.value ?? 0) >= props.max)

function clamp(value: number): number {
  let next = value
  if (props.min !== undefined) next = Math.max(props.min, next)
  if (props.max !== undefined) next = Math.min(props.max, next)
  return next
}

function onInput(event: Event) {
  const raw = (event.target as HTMLInputElement).value
  draft.value = raw

  if (raw === '' || raw === '-') {
    emit('update:value', null)
    return
  }
  const parsed = Number(raw)
  if (!Number.isNaN(parsed)) emit('update:value', parsed)
}

/** 失焦时才钳位，否则输入 "5" 想打 "50" 会被 min=10 立刻改掉 */
function onBlur() {
  focused.value = false
  draft.value = null
  if (props.value === null || props.value === undefined) return
  const clamped = clamp(props.value)
  if (clamped !== props.value) emit('update:value', clamped)
}

function bump(delta: number) {
  if (props.disabled) return
  draft.value = null
  emit('update:value', clamp((props.value ?? 0) + delta))
}
</script>

<style scoped>
.num {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  background: var(--surface-inset);
  transition: border-color 0.14s ease, background-color 0.14s ease;
}

.num:hover:not(.is-disabled) { border-color: var(--line-strong); }

.num.is-focused {
  border-color: var(--signal-deep);
  background: var(--surface-raised);
}

.num.is-disabled { opacity: 0.5; }

.num--tiny { height: 24px; padding-left: 6px; font-size: var(--fn-xs); }
.num--small { height: 30px; padding-left: 8px; font-size: var(--fn-sm); }
.num--medium { height: 34px; padding-left: 10px; font-size: var(--fn-md); }

.num__control {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--ink-max);
  font: inherit;
  font-variant-numeric: tabular-nums;
}

.num__control:disabled { cursor: not-allowed; }
.num__control::placeholder { color: var(--ink-ghost); }

.num__suffix {
  flex-shrink: 0;
  color: var(--ink-faint);
  font-size: var(--fn-xs);
  white-space: nowrap;
}

.num__steps {
  display: grid;
  flex-shrink: 0;
  align-self: stretch;
  border-left: 1px solid var(--line-faint);
}

.num__step {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--ink-faint);
  transition: background-color 0.12s ease, color 0.12s ease;
}

.num__step:first-child { border-bottom: 1px solid var(--line-faint); }

.num__step:hover:not(:disabled) {
  background: var(--surface-hover);
  color: var(--signal-deep);
}

.num__step:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}
</style>
