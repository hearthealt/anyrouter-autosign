<!--
  UiTimeField —— 替代 n-time-picker format="HH:mm"（设置页的自动签到时间）。

  值格式与原用法一致：毫秒时间戳 | null，只取其中的时分。
  双列滚动选择而非文本输入：签到时间是从固定集合里挑一个，
  滚轮比键入更快，也不用处理非法输入。
-->
<template>
  <div class="tf" :class="{ 'is-disabled': disabled }">
    <div
      ref="anchor"
      class="tf__field"
      :class="`tf__field--${size}`"
      role="button"
      :tabindex="disabled ? -1 : 0"
      :aria-expanded="open"
      @click="toggle"
      @keydown.enter.prevent="toggle"
      @keydown.space.prevent="toggle"
    >
      <Clock :size="13" class="tf__icon" />
      <span v-if="value !== null && value !== undefined" class="tf__text tabular">{{ label }}</span>
      <span v-else class="tf__placeholder">{{ placeholder }}</span>
    </div>

    <Teleport to="body">
      <Transition name="ui-layer">
        <div
          v-if="open"
          ref="layer"
          class="tf__layer"
          :style="{ top: `${position.top}px`, left: `${position.left}px` }"
        >
          <div class="tf__cols">
            <div class="tf__col">
              <span class="tf__col-head kicker">时</span>
              <div ref="hourList" class="tf__scroll">
                <button
                  v-for="h in 24"
                  :key="`h${h}`"
                  :class="['tf__opt', { 'is-active': hours === h - 1 }]"
                  type="button"
                  @click="setPart(h - 1, minutes)"
                >{{ String(h - 1).padStart(2, '0') }}</button>
              </div>
            </div>

            <div class="tf__col">
              <span class="tf__col-head kicker">分</span>
              <div ref="minuteList" class="tf__scroll">
                <button
                  v-for="m in 60"
                  :key="`m${m}`"
                  :class="['tf__opt', { 'is-active': minutes === m - 1 }]"
                  type="button"
                  @click="setPart(hours, m - 1)"
                >{{ String(m - 1).padStart(2, '0') }}</button>
              </div>
            </div>
          </div>

          <footer class="tf__foot">
            <UiButton size="tiny" quaternary @click="setNow">此刻</UiButton>
            <UiButton size="tiny" type="primary" @click="close">完成</UiButton>
          </footer>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { Clock } from 'lucide-vue-next'
import UiButton from './UiButton.vue'
import { useAnchoredLayer } from './useAnchoredLayer'
import { useEscapeKey, useOutsidePointer } from './useOverlay'

const props = withDefaults(defineProps<{
  value?: number | null
  size?: 'tiny' | 'small' | 'medium'
  placeholder?: string
  disabled?: boolean
}>(), {
  size: 'small',
  placeholder: '选择时间',
})

const emit = defineEmits<{ 'update:value': [value: number | null] }>()

const anchor = ref<HTMLElement | null>(null)
const layer = ref<HTMLElement | null>(null)
const hourList = ref<HTMLElement | null>(null)
const minuteList = ref<HTMLElement | null>(null)
const open = ref(false)

const { position, track, untrack, update } = useAnchoredLayer(anchor, layer, {
  placement: 'bottom-start',
  offset: 5,
})

useEscapeKey(open, close)
useOutsidePointer(open, [anchor, layer], close)

const parsed = computed(() => (props.value ? new Date(props.value) : null))
const hours = computed(() => parsed.value?.getHours() ?? 0)
const minutes = computed(() => parsed.value?.getMinutes() ?? 0)

const label = computed(() =>
  parsed.value
    ? `${String(parsed.value.getHours()).padStart(2, '0')}:${String(parsed.value.getMinutes()).padStart(2, '0')}`
    : '',
)

/**
 * 只写时分。基准日期沿用原值的日期部分（没有则用 2000-01-01），
 * 和调用方 computed 的 get 逻辑保持一致。
 */
function setPart(h: number, m: number) {
  const base = parsed.value ? new Date(parsed.value) : new Date(2000, 0, 1)
  base.setHours(h, m, 0, 0)
  emit('update:value', base.getTime())
}

function setNow() {
  const now = new Date()
  setPart(now.getHours(), now.getMinutes())
}

/** 把选中项滚到可视区中间，打开时不用手动找。 */
function scrollToActive() {
  for (const list of [hourList.value, minuteList.value]) {
    if (!list) continue
    const active = list.querySelector<HTMLElement>('.is-active')
    if (active) list.scrollTop = active.offsetTop - list.clientHeight / 2 + active.offsetHeight / 2
  }
}

async function openLayer() {
  if (props.disabled) return
  open.value = true
  await nextTick()
  track()
  update()
  scrollToActive()
}

function close() {
  if (!open.value) return
  open.value = false
  untrack()
}

function toggle() {
  open.value ? close() : openLayer()
}
</script>

<style scoped>
.tf { position: relative; display: inline-flex; }

.tf__field {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--line);
  border-radius: var(--r-sm);
  background: var(--surface-inset);
  color: var(--ink-max);
  cursor: pointer;
  white-space: nowrap;
  transition: border-color 0.14s ease;
}

.tf__field:hover { border-color: var(--line-strong); }
.tf.is-disabled .tf__field { opacity: 0.5; cursor: not-allowed; }

.tf__field--tiny { height: 24px; padding: 0 6px; font-size: var(--fn-xs); }
.tf__field--small { height: 30px; padding: 0 8px; font-size: var(--fn-sm); }
.tf__field--medium { height: 34px; padding: 0 10px; font-size: var(--fn-md); }

.tf__icon { flex-shrink: 0; color: var(--ink-faint); }
.tf__placeholder { color: var(--ink-ghost); }

.tf__layer {
  position: fixed;
  z-index: var(--z-layer);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
  overflow: hidden;
}

.tf__cols { display: flex; }

.tf__col {
  display: grid;
  gap: 2px;
  padding: var(--s2);
}

.tf__col + .tf__col { border-left: 1px solid var(--line-faint); }

.tf__col-head { text-align: center; }

.tf__scroll {
  display: grid;
  gap: 1px;
  height: 178px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: thin;
}

.tf__opt {
  width: 46px;
  padding: 4px 0;
  border: 0;
  border-radius: var(--r-xs);
  background: transparent;
  color: var(--ink-strong);
  font-size: var(--fn-xs);
  font-variant-numeric: tabular-nums;
}

.tf__opt:hover { background: var(--surface-hover); }

.tf__opt.is-active {
  background: var(--signal);
  color: var(--signal-ink);
  font-weight: var(--weight-semibold);
}

.tf__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s2);
  padding: var(--s2);
  border-top: 1px solid var(--line-faint);
  background: var(--surface-inset);
}

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
