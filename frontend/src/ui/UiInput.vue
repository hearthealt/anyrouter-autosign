<!--
  UiInput —— 替代 n-input。

  覆盖现有用法：text / password / textarea、size、rows、clearable、
  show-password-on、disabled、@keyup.enter。

  聚焦态不用外扩光圈（密集表单里会互相挤），改成底部 2px signal 色下划线 +
  边框提亮 —— 仪器面板的"通道激活"语言。
-->
<template>
  <div
    :class="['ui-input', `ui-input--${size}`, {
      'is-disabled': disabled,
      'is-focused': focused,
      'is-textarea': type === 'textarea',
    }]"
  >
    <span v-if="$slots.prefix" class="ui-input__affix"><slot name="prefix" /></span>

    <textarea
      v-if="type === 'textarea'"
      ref="control"
      class="ui-input__control"
      :value="value ?? ''"
      :rows="rows"
      :placeholder="placeholder"
      :disabled="disabled"
      :maxlength="maxlength"
      v-bind="$attrs"
      @input="onInput"
      @focus="focused = true"
      @blur="focused = false"
    />
    <input
      v-else
      ref="control"
      class="ui-input__control"
      :type="revealed ? 'text' : type"
      :value="value ?? ''"
      :placeholder="placeholder"
      :disabled="disabled"
      :maxlength="maxlength"
      v-bind="$attrs"
      @input="onInput"
      @focus="focused = true"
      @blur="focused = false"
    />

    <button
      v-if="clearable && hasValue && !disabled"
      class="ui-input__action"
      type="button"
      aria-label="清空"
      @mousedown.prevent
      @click="clear"
    >
      <X :size="13" />
    </button>

    <button
      v-if="type === 'password' && showPasswordOn"
      class="ui-input__action"
      type="button"
      :aria-label="revealed ? '隐藏密码' : '显示密码'"
      @mousedown.prevent
      @click="revealed = !revealed"
    >
      <component :is="revealed ? EyeOff : Eye" :size="13" />
    </button>

    <span v-if="$slots.suffix" class="ui-input__affix"><slot name="suffix" /></span>

    <span class="ui-input__rail" aria-hidden="true" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { Eye, EyeOff, X } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  value?: string | null
  type?: 'text' | 'password' | 'textarea' | 'email' | 'url'
  size?: 'tiny' | 'small' | 'medium' | 'large'
  placeholder?: string
  disabled?: boolean
  clearable?: boolean
  rows?: number
  maxlength?: number
  /** 对齐 n-input 的 API；给了值就显示眼睛按钮 */
  showPasswordOn?: 'click' | 'mousedown'
}>(), {
  type: 'text',
  size: 'medium',
  rows: 3,
})

const emit = defineEmits<{
  'update:value': [value: string]
}>()

defineOptions({ inheritAttrs: false })

const control = ref<HTMLInputElement | HTMLTextAreaElement | null>(null)
const focused = ref(false)
const revealed = ref(false)

const hasValue = computed(() => !!props.value)

function onInput(event: Event) {
  emit('update:value', (event.target as HTMLInputElement).value)
}

function clear() {
  emit('update:value', '')
  control.value?.focus()
}

defineExpose({
  focus: () => control.value?.focus(),
  blur: () => control.value?.blur(),
})
</script>

<style scoped>
.ui-input {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  background: var(--surface-inset);
  color: var(--ink-max);
  transition: border-color 0.14s ease, background-color 0.14s ease;
}

.ui-input:hover:not(.is-disabled) { border-color: var(--line-strong); }

.ui-input.is-focused {
  border-color: var(--line-strong);
  background: var(--surface-raised);
}

.ui-input.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ui-input.is-textarea { align-items: stretch; }

/* 激活轨：聚焦时从中间向两侧展开的 signal 色下划线 */
.ui-input__rail {
  position: absolute;
  inset-inline: 0;
  bottom: -1px;
  height: 2px;
  border-radius: var(--r-full);
  background: var(--signal);
  transform: scaleX(0);
  transition: transform 0.22s cubic-bezier(0.2, 0.9, 0.3, 1);
  pointer-events: none;
}

.ui-input.is-focused .ui-input__rail { transform: scaleX(1); }

/* ── 尺寸 */

.ui-input--tiny { min-height: 24px; padding: 0 6px; font-size: var(--fn-xs); }
.ui-input--small { min-height: 30px; padding: 0 8px; font-size: var(--fn-sm); }
.ui-input--medium { min-height: 34px; padding: 0 10px; font-size: var(--fn-md); }
.ui-input--large { min-height: 44px; padding: 0 14px; font-size: var(--fn-lg); }

.ui-input.is-textarea { padding-block: 7px; }

/* ── 控件本体 */

.ui-input__control {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: inherit;
  font: inherit;
  /* 输入框里的数字也要等宽，粘贴 token 时便于核对 */
  font-variant-numeric: tabular-nums;
}

.ui-input__control::placeholder {
  color: var(--ink-ghost);
  font-variant-numeric: normal;
}

.ui-input__control:disabled { cursor: not-allowed; }

textarea.ui-input__control {
  resize: vertical;
  line-height: var(--leading-normal);
  padding: 0;
}

/* ── 附加元素 */

.ui-input__affix {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  color: var(--ink-faint);
}

.ui-input__action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  padding: 0;
  border: 0;
  border-radius: var(--r-xs);
  background: transparent;
  color: var(--ink-faint);
  transition: color 0.14s ease, background-color 0.14s ease;
}

.ui-input__action:hover {
  background: var(--surface-active);
  color: var(--ink-max);
}
</style>
