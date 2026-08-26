<!--
  UiFileDrop —— 替代 n-upload（备份导入 / CSV 批量导入两处）。

  和 Naive 的差别：直接 emit 原生 File，不包 `{ file: { file } }` 那层。
  两个调用点的 handler 相应简化。

  默认插槽当触发器（沿用原来"包一个按钮"的写法），
  同时整个区域支持拖拽落文件 —— 拖拽态用 signal 色虚线描边。
-->
<template>
  <div
    :class="['drop', { 'is-over': over, 'is-disabled': disabled, 'is-plain': !dropzone }]"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent
    @dragleave="onDragLeave"
    @drop.prevent="onDrop"
  >
    <input
      ref="input"
      class="drop__input"
      type="file"
      :accept="accept"
      :disabled="disabled"
      @change="onChange"
    />

    <div class="drop__trigger" @click="pick">
      <slot>
        <div class="drop__hint">
          <UploadCloud :size="18" class="drop__hint-icon" />
          <p class="drop__hint-title">拖拽文件到此处，或点击选择</p>
          <p v-if="accept" class="drop__hint-desc mono">{{ accept }}</p>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { UploadCloud } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  accept?: string
  disabled?: boolean
  /** true 时渲染成一整块虚线拖拽区；false 时只把默认插槽当触发器 */
  dropzone?: boolean
}>(), { dropzone: false })

const emit = defineEmits<{ select: [file: File] }>()

const input = ref<HTMLInputElement | null>(null)
const over = ref(false)
/** dragenter/dragleave 会在子元素间反复触发，用计数器判断真正离开 */
let depth = 0

function pick() {
  if (props.disabled) return
  input.value?.click()
}

function emitFile(file: File | null | undefined) {
  if (!file) return
  emit('select', file)
}

function onChange(event: Event) {
  const target = event.target as HTMLInputElement
  emitFile(target.files?.[0])
  // 清空 value，否则连续选同一个文件不会再触发 change
  target.value = ''
}

function onDragEnter() {
  if (props.disabled) return
  depth++
  over.value = true
}

function onDragLeave() {
  if (--depth <= 0) {
    depth = 0
    over.value = false
  }
}

function onDrop(event: DragEvent) {
  depth = 0
  over.value = false
  if (props.disabled) return
  emitFile(event.dataTransfer?.files?.[0])
}
</script>

<style scoped>
.drop { position: relative; }

.drop.is-plain { display: inline-flex; }

.drop__input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.drop__trigger { display: inline-flex; }

.drop:not(.is-plain) .drop__trigger {
  display: block;
  padding: var(--s8) var(--s5);
  border: 1px dashed var(--line-strong);
  border-radius: var(--r-md);
  background: var(--surface-inset);
  cursor: pointer;
  text-align: center;
  transition: border-color 0.14s ease, background-color 0.14s ease;
}

.drop:not(.is-plain):hover .drop__trigger { border-color: var(--signal-deep); }

.drop.is-over .drop__trigger {
  border-color: var(--signal);
  border-style: solid;
  background: var(--signal-wash);
}

/* 只包按钮时也要有拖拽反馈：给触发器套一层 signal 色光圈 */
.drop.is-plain.is-over .drop__trigger {
  border-radius: var(--r-sm);
  box-shadow: 0 0 0 2px var(--signal), 0 0 20px -4px var(--signal-glow);
}

.drop.is-disabled { opacity: 0.5; }
.drop.is-disabled .drop__trigger { cursor: not-allowed; }

.drop__hint { display: grid; gap: 4px; justify-items: center; }

.drop__hint-icon { color: var(--ink-faint); }

.drop__hint-title {
  color: var(--ink-strong);
  font-size: var(--fn-sm);
  font-weight: var(--weight-medium);
}

.drop__hint-desc {
  color: var(--ink-faint);
  font-size: var(--fn-xs);
}
</style>
