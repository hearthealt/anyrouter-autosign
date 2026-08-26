<!--
  UiSwitch —— 替代 n-switch。v-model:value 对齐原 API。

  滑块用弹簧驱动而非 CSS transition，所以快速连点时不会出现"卡在中间"，
  它会带着速度继续走完 —— 这是 spring 相对 ease 的实际收益。
-->
<template>
  <button
    :class="['ui-switch', `ui-switch--${size}`, { 'is-on': value, 'is-disabled': disabled }]"
    type="button"
    role="switch"
    :aria-checked="value"
    :disabled="disabled || loading"
    v-bind="$attrs"
    @click="toggle"
  >
    <span ref="knob" class="ui-switch__knob">
      <UiSpinner v-if="loading" :size="size === 'small' ? 8 : 10" />
    </span>
  </button>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { spring, SPRING, type SpringHandle } from '../design/motion'
import UiSpinner from './UiSpinner.vue'

const props = withDefaults(defineProps<{
  value?: boolean
  disabled?: boolean
  loading?: boolean
  size?: 'small' | 'medium'
}>(), { size: 'medium' })

const emit = defineEmits<{ 'update:value': [value: boolean] }>()

defineOptions({ inheritAttrs: false })

const knob = ref<HTMLElement | null>(null)
let handle: SpringHandle | null = null

// 滑块行程：轨道宽 - 滑块宽 - 两侧内边距
const TRAVEL = { small: 14, medium: 16 }

onMounted(() => {
  if (!knob.value) return
  const travel = TRAVEL[props.size]
  handle = spring(props.value ? travel : 0, value => {
    if (knob.value) knob.value.style.transform = `translate3d(${value.toFixed(2)}px, 0, 0)`
  }, SPRING.pop)
  // spring() 只在 set()/jump() 时才回调 onUpdate，构造时不会。
  // 这里必须显式 jump 一次，否则初始为「开」的开关滑块会停在左边。
  handle.jump(props.value ? travel : 0)
})

watch(() => props.value, on => handle?.set(on ? TRAVEL[props.size] : 0))

function toggle() {
  if (props.disabled || props.loading) return
  emit('update:value', !props.value)
}
</script>

<style scoped>
.ui-switch {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  padding: 2px;
  border: 1px solid var(--line-strong);
  border-radius: var(--r-full);
  background: var(--surface-sunken);
  transition: background-color 0.18s ease, border-color 0.18s ease;
}

.ui-switch--small { width: 32px; height: 18px; }
.ui-switch--medium { width: 36px; height: 20px; }

.ui-switch.is-on {
  background: var(--signal);
  border-color: var(--signal);
}

.ui-switch.is-disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ui-switch__knob {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--surface-raised);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
  color: var(--ink-muted);
}

.ui-switch--small .ui-switch__knob { width: 12px; height: 12px; }
.ui-switch--medium .ui-switch__knob { width: 14px; height: 14px; }

.ui-switch.is-on .ui-switch__knob { background: var(--signal-ink); color: var(--signal); }
</style>
