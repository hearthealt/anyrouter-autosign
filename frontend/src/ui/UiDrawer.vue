<!--
  UiDrawer —— 替代 n-drawer + n-drawer-content（TokensModal 用）。
  从右侧滑入，宽度可配。进场用弹簧，所以拖动感比 CSS transition 自然。
-->
<template>
  <Teleport to="body">
    <Transition name="ui-mask">
      <div v-if="show" class="ui-drawer-mask" @pointerdown.self="onMaskDown">
        <aside
          ref="panel"
          class="ui-drawer"
          :style="{ width: typeof width === 'number' ? `${width}px` : width }"
          role="dialog"
          aria-modal="true"
          :aria-label="title || undefined"
          tabindex="-1"
        >
          <header v-if="title || $slots.header" class="ui-drawer__head">
            <div class="ui-drawer__titles">
              <slot name="header">
                <span v-if="kicker" class="kicker">{{ kicker }}</span>
                <h2 class="ui-drawer__title">{{ title }}</h2>
              </slot>
            </div>
            <button v-if="closable" class="ui-drawer__x" type="button" aria-label="关闭" @click="close">
              <X :size="15" />
            </button>
          </header>

          <div class="ui-drawer__body"><slot /></div>

          <footer v-if="$slots.footer" class="ui-drawer__foot"><slot name="footer" /></footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import { springIn } from '../design/motion'
import { useEscapeKey, useFocusTrap, useScrollLock } from './useOverlay'

const props = withDefaults(defineProps<{
  show?: boolean
  title?: string
  kicker?: string
  width?: number | string
  closable?: boolean
  maskClosable?: boolean
  closeOnEsc?: boolean
}>(), {
  width: 420,
  closable: true,
  maskClosable: true,
  closeOnEsc: true,
})

const emit = defineEmits<{ 'update:show': [value: boolean] }>()

const panel = ref<HTMLElement | null>(null)
const showRef = computed(() => !!props.show)

useFocusTrap(showRef, panel)
useScrollLock(showRef)
useEscapeKey(computed(() => showRef.value && props.closeOnEsc), close)

watch(showRef, async on => {
  if (!on) return
  await nextTick()
  // 从右侧推入：x 正值配合 springIn 的反向插值
  if (panel.value) springIn(panel.value, { x: 40, y: 0, opacity: 0.4 })
})

function close() { emit('update:show', false) }
function onMaskDown() { if (props.maskClosable) close() }
</script>

<style scoped>
.ui-drawer-mask {
  position: fixed;
  inset: 0;
  z-index: var(--z-modal);
  display: flex;
  justify-content: flex-end;
  background: color-mix(in srgb, var(--surface-inverse) 38%, transparent);
  backdrop-filter: blur(5px);
}

.ui-drawer {
  display: flex;
  flex-direction: column;
  max-width: 100vw;
  height: 100%;
  border-left: 1px solid var(--line);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
  outline: none;
}

.ui-drawer__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--s4);
  padding: var(--s4) var(--s5);
  border-bottom: 1px solid var(--line-faint);
}

.ui-drawer__titles { display: grid; gap: 3px; min-width: 0; }

.ui-drawer__title {
  margin: 0;
  font-size: var(--fn-lg);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-tight);
}

.ui-drawer__x {
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
}

.ui-drawer__x:hover { background: var(--surface-hover); color: var(--ink-max); }

.ui-drawer__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--s5);
}

.ui-drawer__foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--s2);
  padding: var(--s3) var(--s5);
  border-top: 1px solid var(--line-faint);
  background: var(--surface-inset);
}

.ui-mask-enter-active,
.ui-mask-leave-active { transition: opacity 0.18s ease; }

.ui-mask-enter-from,
.ui-mask-leave-to { opacity: 0; }
</style>
