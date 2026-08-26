<!--
  UiModal —— 替代 n-modal（含 preset="dialog" 的两处用法）。

  两种模式：
  - 默认：header / default / footer 三个插槽自己排
  - preset="dialog"：直接给 title / content / positive-text / negative-text

  遮罩不用糊成一片的黑，用低透明度 + backdrop-filter 的轻度模糊，
  让底层界面仍然可辨识 —— 运维工具里"我刚才在哪一行"很重要。
-->
<template>
  <Teleport to="body">
    <Transition name="ui-mask" @after-leave="onClosed">
      <div v-if="show" class="ui-modal-mask" @pointerdown.self="onMaskDown">
        <div
          ref="panel"
          :class="['ui-modal', `ui-modal--${size}`]"
          :style="width ? { maxWidth: typeof width === 'number' ? `${width}px` : width } : undefined"
          role="dialog"
          aria-modal="true"
          :aria-label="title || undefined"
          tabindex="-1"
        >
          <header v-if="title || $slots.header" class="ui-modal__head">
            <div class="ui-modal__titles">
              <slot name="header">
                <span v-if="kicker" class="kicker">{{ kicker }}</span>
                <h2 class="ui-modal__title">{{ title }}</h2>
              </slot>
            </div>
            <button v-if="closable" class="ui-modal__x" type="button" aria-label="关闭" @click="close">
              <X :size="15" />
            </button>
          </header>

          <div class="ui-modal__body">
            <slot>
              <p v-if="content" class="ui-modal__content">{{ content }}</p>
            </slot>
          </div>

          <footer v-if="isDialog || $slots.footer" class="ui-modal__foot">
            <slot name="footer">
              <UiButton v-if="negativeText" size="small" @click="onNegative">{{ negativeText }}</UiButton>
              <UiButton
                v-if="positiveText"
                size="small"
                :type="positiveTone"
                :loading="positiveLoading"
                @click="onPositive"
              >{{ positiveText }}</UiButton>
            </slot>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import UiButton from './UiButton.vue'
import { springIn } from '../design/motion'
import { useEscapeKey, useFocusTrap, useScrollLock } from './useOverlay'

const props = withDefaults(defineProps<{
  show?: boolean
  title?: string
  kicker?: string
  content?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  /** 覆盖 size 给出的最大宽度。数字按 px，也可传 'min(820px, 92vw)' 这类表达式 */
  width?: number | string
  closable?: boolean
  maskClosable?: boolean
  closeOnEsc?: boolean
  /** 对齐 n-modal 的 preset；给 'dialog' 时自动渲染确认/取消页脚 */
  preset?: 'dialog' | 'card'
  positiveText?: string
  negativeText?: string
  positiveTone?: 'primary' | 'error' | 'warning'
  positiveLoading?: boolean
}>(), {
  size: 'md',
  closable: true,
  maskClosable: true,
  closeOnEsc: true,
  positiveTone: 'primary',
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  'positive-click': []
  'negative-click': []
  closed: []
}>()

const panel = ref<HTMLElement | null>(null)
const showRef = computed(() => !!props.show)

const isDialog = computed(() => props.preset === 'dialog' || !!props.positiveText || !!props.negativeText)

useFocusTrap(showRef, panel)
useScrollLock(showRef)
useEscapeKey(computed(() => showRef.value && props.closeOnEsc), close)

// 用弹簧做进场而不是 CSS transition，和全站动效语言保持一致
watch(showRef, async on => {
  if (!on) return
  await nextTick()
  if (panel.value) springIn(panel.value, { y: 18, scale: 0.97 })
})

function close() {
  emit('update:show', false)
}

function onMaskDown() {
  if (props.maskClosable) close()
}

function onPositive() {
  emit('positive-click')
}

function onNegative() {
  emit('negative-click')
  close()
}

function onClosed() {
  emit('closed')
}
</script>

<style scoped>
.ui-modal-mask {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: grid;
  place-items: center;
  padding: var(--s6);
  background: color-mix(in srgb, var(--surface-inverse) 42%, transparent);
  backdrop-filter: blur(6px) saturate(1.1);
  overflow-y: auto;
}

.ui-modal {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  max-height: calc(100vh - var(--s12));
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
  outline: none;
}

.ui-modal--sm { max-width: 400px; }
.ui-modal--md { max-width: 560px; }
.ui-modal--lg { max-width: 760px; }
.ui-modal--xl { max-width: 1040px; }

.ui-modal__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--s4);
  padding: var(--s4) var(--s5);
  border-bottom: 1px solid var(--line-faint);
}

.ui-modal__titles {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.ui-modal__title {
  margin: 0;
  font-size: var(--fn-lg);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-tight);
  color: var(--ink-max);
}

.ui-modal__x {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  margin: -3px -6px 0 0;
  border: 0;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--ink-faint);
  transition: background-color 0.14s ease, color 0.14s ease;
}

.ui-modal__x:hover {
  background: var(--surface-hover);
  color: var(--ink-max);
}

.ui-modal__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--s5);
}

.ui-modal__content {
  color: var(--ink);
  font-size: var(--fn-md);
  line-height: var(--leading-loose);
}

.ui-modal__foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--s2);
  padding: var(--s3) var(--s5);
  border-top: 1px solid var(--line-faint);
  background: var(--surface-inset);
  border-radius: 0 0 var(--r-lg) var(--r-lg);
}

/* 遮罩淡入；面板位移由 springIn 负责 */
.ui-mask-enter-active,
.ui-mask-leave-active { transition: opacity 0.18s ease; }

.ui-mask-enter-from,
.ui-mask-leave-to { opacity: 0; }

@media (max-width: 640px) {
  .ui-modal-mask {
    padding: var(--s3);
    place-items: end stretch;
  }

  .ui-modal { max-height: calc(100vh - var(--s8)); }
}
</style>
