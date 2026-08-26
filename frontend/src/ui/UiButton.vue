<!--
  UiButton —— 替代 n-button。

  变体对齐现有调用点：默认描边、primary 实心、quaternary 无边平铺、
  text 纯文字、ghost 透明描边。size 支持 tiny/small/medium/large。

  primary 与 large 尺寸带磁吸悬停（3px）；tiny/text/quaternary 不带 ——
  密集工具栏里几十个按钮同时抖动会让界面显得廉价。
-->
<template>
  <button
    ref="root"
    :class="[
      'ui-btn',
      `ui-btn--${size}`,
      `ui-btn--${variant}`,
      type !== 'default' && `ui-btn--tone-${type}`,
      { 'is-loading': loading, 'is-block': block, 'is-circle': circle },
    ]"
    :disabled="disabled || loading"
    :type="nativeType"
    v-bind="$attrs"
  >
    <UiSpinner v-if="loading" :size="spinnerSize" class="ui-btn__spinner" />
    <span v-if="$slots.icon && !loading" class="ui-btn__icon"><slot name="icon" /></span>
    <span v-if="$slots.default" class="ui-btn__label"><slot /></span>
  </button>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { magnetic } from '../design/motion'
import UiSpinner from './UiSpinner.vue'

type Size = 'tiny' | 'small' | 'medium' | 'large'
type Tone = 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'

const props = withDefaults(defineProps<{
  size?: Size
  type?: Tone
  loading?: boolean
  disabled?: boolean
  /** 无边框平铺，悬停出底色。密集工具栏的默认选择 */
  quaternary?: boolean
  /** 纯文字，像链接 */
  text?: boolean
  /** 透明底 + 描边 */
  ghost?: boolean
  block?: boolean
  circle?: boolean
  nativeType?: 'button' | 'submit' | 'reset'
}>(), {
  size: 'medium',
  type: 'default',
  nativeType: 'button',
})

defineOptions({ inheritAttrs: false })

const root = ref<HTMLElement | null>(null)

const variant = computed(() => {
  if (props.text) return 'text'
  if (props.quaternary) return 'quaternary'
  if (props.ghost) return 'ghost'
  if (props.type === 'default') return 'outline'
  return 'solid'
})

const spinnerSize = computed(() => (props.size === 'tiny' ? 11 : props.size === 'large' ? 16 : 13))

// 只给"重"按钮加磁吸：实心/大尺寸。平铺和文字按钮不加
const wantsMagnet = computed(
  () => !props.disabled && (variant.value === 'solid' || props.size === 'large'),
)

let release: (() => void) | null = null

function bindMagnet() {
  release?.()
  release = null
  if (root.value && wantsMagnet.value) release = magnetic(root.value, 3)
}

onMounted(bindMagnet)
watch(wantsMagnet, bindMagnet)
onBeforeUnmount(() => release?.())
</script>

<style scoped>
.ui-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid transparent;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--ink-strong);
  font-family: var(--font-sans);
  font-weight: var(--weight-medium);
  white-space: nowrap;
  user-select: none;
  /* transform 交给磁吸动效，这里只过渡颜色 */
  transition: background-color 0.14s ease, border-color 0.14s ease, color 0.14s ease,
    box-shadow 0.14s ease;
}

.ui-btn:disabled {
  cursor: not-allowed;
  opacity: 0.44;
}

.ui-btn.is-block { width: 100%; }

.ui-btn.is-circle {
  padding: 0;
  aspect-ratio: 1;
  border-radius: var(--r-full);
}

/* ── 尺寸 */

.ui-btn--tiny {
  height: 24px;
  padding: 0 8px;
  font-size: var(--fn-xs);
}

.ui-btn--small {
  height: 30px;
  padding: 0 10px;
  font-size: var(--fn-sm);
}

.ui-btn--medium {
  height: 34px;
  padding: 0 14px;
  font-size: var(--fn-md);
}

.ui-btn--large {
  height: 44px;
  padding: 0 22px;
  font-size: var(--fn-lg);
  border-radius: var(--r-md);
  letter-spacing: var(--track-tight);
}

/* ── 描边（默认） */

.ui-btn--outline {
  border-color: var(--line);
  background: var(--surface-raised);
  color: var(--ink-strong);
}

.ui-btn--outline:hover:not(:disabled) {
  border-color: var(--line-strong);
  background: var(--surface-hover);
}

.ui-btn--outline:active:not(:disabled) { background: var(--surface-active); }

/* ── 实心：signal 色是唯一的强调填充 */

.ui-btn--solid {
  background: var(--signal);
  border-color: var(--signal);
  color: var(--signal-ink);
  font-weight: var(--weight-semibold);
}

.ui-btn--solid:hover:not(:disabled) {
  box-shadow: 0 0 24px -6px var(--signal-glow);
}

.ui-btn--solid:active:not(:disabled) { filter: brightness(0.94); }

/* 语义色实心：不用 signal，用对应语义色 */
.ui-btn--solid.ui-btn--tone-success { background: var(--ok); border-color: var(--ok); color: #fff; }
.ui-btn--solid.ui-btn--tone-warning { background: var(--warn); border-color: var(--warn); color: #fff; }
.ui-btn--solid.ui-btn--tone-error { background: var(--bad); border-color: var(--bad); color: #fff; }
.ui-btn--solid.ui-btn--tone-info { background: var(--info); border-color: var(--info); color: #fff; }

.ui-btn--solid.ui-btn--tone-success:hover:not(:disabled),
.ui-btn--solid.ui-btn--tone-warning:hover:not(:disabled),
.ui-btn--solid.ui-btn--tone-error:hover:not(:disabled),
.ui-btn--solid.ui-btn--tone-info:hover:not(:disabled) {
  box-shadow: none;
  filter: brightness(1.08);
}

/* ── 平铺 */

.ui-btn--quaternary { color: var(--ink); }

.ui-btn--quaternary:hover:not(:disabled) {
  background: var(--surface-hover);
  color: var(--ink-max);
}

.ui-btn--quaternary:active:not(:disabled) { background: var(--surface-active); }

.ui-btn--quaternary.ui-btn--tone-error { color: var(--bad); }
.ui-btn--quaternary.ui-btn--tone-error:hover:not(:disabled) { background: var(--bad-wash); }
.ui-btn--quaternary.ui-btn--tone-primary { color: var(--signal-deep); }
.ui-btn--quaternary.ui-btn--tone-primary:hover:not(:disabled) { background: var(--signal-wash); }

/* ── 文字 */

.ui-btn--text {
  height: auto;
  padding: 0;
  color: var(--ink-muted);
}

.ui-btn--text:hover:not(:disabled) { color: var(--ink-max); }
.ui-btn--text.ui-btn--tone-primary { color: var(--signal-deep); }
.ui-btn--text.ui-btn--tone-error { color: var(--bad); }

/* ── 透明描边 */

.ui-btn--ghost {
  border-color: var(--line);
  color: var(--ink-strong);
}

.ui-btn--ghost:hover:not(:disabled) {
  border-color: var(--signal-deep);
  color: var(--signal-deep);
}

.ui-btn--ghost.ui-btn--tone-error { border-color: var(--bad); color: var(--bad); }
.ui-btn--ghost.ui-btn--tone-error:hover:not(:disabled) { background: var(--bad-wash); }

/* ── 内部 */

.ui-btn__icon {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.ui-btn__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ui-btn__spinner { flex-shrink: 0; }
</style>
