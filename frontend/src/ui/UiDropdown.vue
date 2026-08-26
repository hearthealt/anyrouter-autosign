<!--
  UiDropdown —— 替代 n-dropdown。options 结构对齐原 API：
  { label, key, icon?, disabled?, type: 'divider' }，通过 @select 回传 key。

  内部复用 UiPopover 的定位与关闭逻辑，只负责菜单项渲染和键盘导航。
-->
<template>
  <UiPopover
    v-model:show="open"
    :placement="placement"
    :arrow="false"
    bare
    trigger="click"
    :disabled="disabled"
  >
    <template #trigger><slot /></template>

    <div class="ui-menu" role="menu" @keydown="onKeydown">
      <template v-for="(opt, index) in options" :key="opt.key ?? `d-${index}`">
        <div v-if="opt.type === 'divider'" class="ui-menu__divider" role="separator" />
        <button
          v-else
          :ref="el => setItemRef(index, el as HTMLElement | null)"
          :class="['ui-menu__item', { 'is-danger': opt.tone === 'error', 'is-disabled': opt.disabled }]"
          type="button"
          role="menuitem"
          :disabled="opt.disabled"
          @click="select(opt)"
        >
          <span v-if="opt.icon" class="ui-menu__icon"><component :is="opt.icon" :size="14" /></span>
          <span class="ui-menu__label">{{ opt.label }}</span>
          <span v-if="opt.hint" class="ui-menu__hint mono">{{ opt.hint }}</span>
        </button>
      </template>
    </div>
  </UiPopover>
</template>

<script setup lang="ts">
import { ref, type Component } from 'vue'
import UiPopover from './UiPopover.vue'
import type { Placement } from './useAnchoredLayer'

export interface DropdownOption {
  label?: string
  key?: string | number
  icon?: Component
  disabled?: boolean
  type?: 'divider'
  tone?: 'default' | 'error'
  /** 右侧提示，通常放快捷键 */
  hint?: string
}

withDefaults(defineProps<{
  options?: DropdownOption[]
  placement?: Placement
  disabled?: boolean
}>(), {
  options: () => [],
  placement: 'bottom-end',
})

const emit = defineEmits<{ select: [key: string | number] }>()

const open = ref(false)
const itemRefs = new Map<number, HTMLElement>()

function setItemRef(index: number, el: HTMLElement | null) {
  if (el) itemRefs.set(index, el)
  else itemRefs.delete(index)
}

function select(opt: DropdownOption) {
  if (opt.disabled || opt.key === undefined) return
  emit('select', opt.key)
  open.value = false
}

// 上下键在菜单项之间移动焦点；菜单项本身是 button，Enter/Space 原生就能触发
function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return
  event.preventDefault()
  const items = Array.from(itemRefs.entries())
    .sort((a, b) => a[0] - b[0])
    .map(([, el]) => el)
    .filter(el => !(el as HTMLButtonElement).disabled)
  if (!items.length) return

  const current = items.indexOf(document.activeElement as HTMLElement)
  const step = event.key === 'ArrowDown' ? 1 : -1
  const next = current === -1 ? (step > 0 ? 0 : items.length - 1) : (current + step + items.length) % items.length
  items[next].focus()
}
</script>

<style scoped>
.ui-menu {
  min-width: 176px;
  display: grid;
  gap: 1px;
}

.ui-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  border: 0;
  border-radius: var(--r-xs);
  background: transparent;
  color: var(--ink-strong);
  font-size: var(--fn-sm);
  text-align: left;
  transition: background-color 0.12s ease, color 0.12s ease;
}

.ui-menu__item:hover:not(.is-disabled),
.ui-menu__item:focus-visible {
  background: var(--surface-hover);
  color: var(--ink-max);
}

.ui-menu__item.is-danger { color: var(--bad); }
.ui-menu__item.is-danger:hover:not(.is-disabled) { background: var(--bad-wash); }

.ui-menu__item.is-disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.ui-menu__icon {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  color: var(--ink-faint);
}

.ui-menu__item:hover .ui-menu__icon { color: currentColor; }

.ui-menu__label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.ui-menu__hint {
  flex-shrink: 0;
  color: var(--ink-ghost);
  font-size: var(--fn-2xs);
}

.ui-menu__divider {
  height: 1px;
  margin: 3px 0;
  background: var(--line-faint);
}
</style>
