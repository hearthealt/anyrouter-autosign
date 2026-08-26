<!--
  UiTooltip —— 替代 n-tooltip。纯文字提示，hover / focus 触发。

  比 UiPopover 更轻：不做外部点击、不做焦点管理，用 role="tooltip"
  并挂 aria-describedby 让屏幕阅读器能读到。
-->
<template>
  <span
    ref="anchor"
    class="ui-tip__anchor"
    :aria-describedby="open ? id : undefined"
    @pointerenter="onEnter"
    @pointerleave="onLeave"
    @focusin="onEnter"
    @focusout="onLeave"
  >
    <slot />
  </span>

  <Teleport to="body">
    <Transition name="ui-tip">
      <div
        v-if="open && hasContent"
        :id="id"
        ref="layer"
        class="ui-tip"
        role="tooltip"
        :style="{ top: `${position.top}px`, left: `${position.left}px` }"
      >
        <slot name="content">{{ content }}</slot>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useId, watch } from 'vue'
import { useAnchoredLayer, type Placement } from './useAnchoredLayer'

const props = withDefaults(defineProps<{
  content?: string
  placement?: Placement
  /** 悬停多久才弹出，避免快速划过时闪烁 */
  delay?: number
  disabled?: boolean
}>(), {
  placement: 'top',
  delay: 260,
})

const slots = defineSlots<{ default?: unknown; content?: unknown }>()

const id = useId()
const anchor = ref<HTMLElement | null>(null)
const layer = ref<HTMLElement | null>(null)
const open = ref(false)

const hasContent = computed(() => !!props.content || !!slots.content)

const { position, track, untrack, update } = useAnchoredLayer(anchor, layer, {
  placement: props.placement,
  offset: 7,
})

let timer = 0

function onEnter() {
  if (props.disabled || !hasContent.value) return
  clearTimeout(timer)
  timer = window.setTimeout(() => { open.value = true }, props.delay)
}

function onLeave() {
  clearTimeout(timer)
  open.value = false
}

watch(open, async on => {
  if (on) {
    await nextTick()
    track()
    update()
  } else {
    untrack()
  }
})
</script>

<style scoped>
.ui-tip__anchor {
  display: inline-flex;
  min-width: 0;
}

.ui-tip {
  position: fixed;
  z-index: var(--z-layer);
  max-width: min(88vw, 300px);
  padding: 5px 8px;
  border-radius: var(--r-sm);
  /* 反色底：提示是"临时覆盖层"，和常规面板区分开 */
  background: var(--surface-inverse);
  color: var(--ink-inverse);
  font-size: var(--fn-xs);
  line-height: var(--leading-normal);
  pointer-events: none;
  overflow-wrap: anywhere;
}

.ui-tip-enter-active,
.ui-tip-leave-active { transition: opacity 0.12s ease, transform 0.14s ease; }

.ui-tip-enter-from,
.ui-tip-leave-to {
  opacity: 0;
  transform: translateY(2px);
}
</style>
