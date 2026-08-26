<!--
  UiPopover —— 替代 n-popover。trigger 支持 click / hover / manual。

  定位、Esc、外部点击全部委托给共用 composable。
  hover 模式带 120ms 关闭延迟，让指针能从锚点移到浮层上而不断开。
-->
<template>
  <span ref="anchor" class="ui-pop__anchor" v-bind="anchorHandlers">
    <slot name="trigger" />
  </span>

  <Teleport to="body">
    <Transition name="ui-layer">
      <div
        v-if="open"
        ref="layer"
        :class="['ui-pop', `ui-pop--${position.placement.split('-')[0]}`, { 'is-bare': bare }]"
        role="dialog"
        :style="{ top: `${position.top}px`, left: `${position.left}px`, width: widthStyle }"
        v-bind="layerHandlers"
      >
        <span v-if="arrow" class="ui-pop__arrow" aria-hidden="true" />
        <div class="ui-pop__inner"><slot /></div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useAnchoredLayer, type Placement } from './useAnchoredLayer'
import { useEscapeKey, useOutsidePointer } from './useOverlay'

const props = withDefaults(defineProps<{
  trigger?: 'click' | 'hover' | 'manual'
  placement?: Placement
  show?: boolean
  arrow?: boolean
  /** 去掉内边距和背景，内容自己排版（下拉菜单用） */
  bare?: boolean
  width?: number | string
  disabled?: boolean
}>(), {
  trigger: 'click',
  placement: 'bottom',
  arrow: true,
})

const emit = defineEmits<{ 'update:show': [value: boolean] }>()

const anchor = ref<HTMLElement | null>(null)
const layer = ref<HTMLElement | null>(null)
const internal = ref(false)

const open = computed(() => (props.trigger === 'manual' ? !!props.show : internal.value))

const widthStyle = computed(() =>
  props.width === undefined ? undefined : typeof props.width === 'number' ? `${props.width}px` : props.width,
)

const { position, track, untrack, update } = useAnchoredLayer(anchor, layer, {
  placement: props.placement,
  offset: props.arrow ? 9 : 6,
})

useEscapeKey(open, () => setOpen(false))
useOutsidePointer(
  computed(() => open.value && props.trigger === 'click'),
  [anchor, layer],
  () => setOpen(false),
)

async function setOpen(next: boolean) {
  if (props.disabled && next) return
  if (props.trigger === 'manual') {
    emit('update:show', next)
    return
  }
  internal.value = next
  emit('update:show', next)
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

// hover 模式：离开后延迟关闭，留出指针跨越间隙的时间
let closeTimer = 0

function cancelClose() {
  if (closeTimer) {
    clearTimeout(closeTimer)
    closeTimer = 0
  }
}

function scheduleClose() {
  cancelClose()
  closeTimer = window.setTimeout(() => setOpen(false), 120)
}

const anchorHandlers = computed(() => {
  if (props.trigger === 'click') return { onClick: () => setOpen(!open.value) }
  if (props.trigger === 'hover') {
    return {
      onPointerenter: () => { cancelClose(); setOpen(true) },
      onPointerleave: scheduleClose,
      onFocusin: () => setOpen(true),
      onFocusout: scheduleClose,
    }
  }
  return {}
})

const layerHandlers = computed(() =>
  props.trigger === 'hover' ? { onPointerenter: cancelClose, onPointerleave: scheduleClose } : {},
)
</script>

<style scoped>
.ui-pop__anchor { display: inline-flex; }

.ui-pop {
  position: fixed;
  z-index: var(--z-layer);
  max-width: min(92vw, 380px);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
  color: var(--ink);
  font-size: var(--fn-sm);
  line-height: var(--leading-normal);
}

.ui-pop.is-bare {
  max-width: none;
  padding: 0;
}

.ui-pop__inner { padding: var(--s3) var(--s4); }
.ui-pop.is-bare .ui-pop__inner { padding: 4px; }

/* 箭头：旋转 45° 的方块，只留朝外的两条边框 */
.ui-pop__arrow {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--surface-overlay);
  border: 1px solid var(--line);
  transform: rotate(45deg);
}

.ui-pop--bottom .ui-pop__arrow {
  top: -5px;
  left: 50%;
  margin-left: -4px;
  border-right: 0;
  border-bottom: 0;
}

.ui-pop--top .ui-pop__arrow {
  bottom: -5px;
  left: 50%;
  margin-left: -4px;
  border-left: 0;
  border-top: 0;
}

.ui-pop--right .ui-pop__arrow {
  left: -5px;
  top: 50%;
  margin-top: -4px;
  border-right: 0;
  border-top: 0;
}

.ui-pop--left .ui-pop__arrow {
  right: -5px;
  top: 50%;
  margin-top: -4px;
  border-left: 0;
  border-bottom: 0;
}

.ui-layer-enter-active,
.ui-layer-leave-active {
  transition: opacity 0.14s ease, transform 0.18s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.ui-layer-enter-from,
.ui-layer-leave-to {
  opacity: 0;
  transform: scale(0.97);
}
</style>
