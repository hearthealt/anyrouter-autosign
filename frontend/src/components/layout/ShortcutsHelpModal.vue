<template>
  <n-modal :show="show" @update:show="(v: boolean) => emit('update:show', v)">
    <div class="shortcuts-modal">
      <div class="modal-head">
        <h3>快捷键</h3>
        <n-button text @click="emit('update:show', false)" aria-label="关闭">
          <n-icon :size="16"><CloseOutline /></n-icon>
        </n-button>
      </div>
      <div class="modal-body">
        <div class="shortcut-section">
          <div class="section-title">全局</div>
          <div class="shortcut-row">
            <span class="shortcut-desc">打开命令面板</span>
            <div class="keys"><kbd>⌘</kbd><kbd>K</kbd></div>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-desc">刷新当前视图</span>
            <div class="keys"><kbd>R</kbd></div>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-desc">显示快捷键帮助</span>
            <div class="keys"><kbd>?</kbd></div>
          </div>
        </div>
        <div class="shortcut-section">
          <div class="section-title">跳转（按 <kbd>G</kbd> 后再按下一键）</div>
          <div class="shortcut-row">
            <span class="shortcut-desc">总览面板</span>
            <div class="keys"><kbd>G</kbd><kbd>D</kbd></div>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-desc">账号管理</span>
            <div class="keys"><kbd>G</kbd><kbd>A</kbd></div>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-desc">签到记录</span>
            <div class="keys"><kbd>G</kbd><kbd>L</kbd></div>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-desc">数据统计</span>
            <div class="keys"><kbd>G</kbd><kbd>S</kbd></div>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-desc">平台管理</span>
            <div class="keys"><kbd>G</kbd><kbd>P</kbd></div>
          </div>
          <div class="shortcut-row">
            <span class="shortcut-desc">系统设置</span>
            <div class="keys"><kbd>G</kbd><kbd>C</kbd></div>
          </div>
        </div>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { NModal, NButton, NIcon } from 'naive-ui'
import { CloseOutline } from '@vicons/ionicons5'

defineProps<{ show: boolean }>()
const emit = defineEmits<{ (e: 'update:show', v: boolean): void }>()
</script>

<style scoped>
.shortcuts-modal {
  width: min(92vw, 480px);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.modal-head h3 {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-4);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.shortcut-section .section-title {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--spacing-2);
}

.shortcut-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px dashed var(--border-color-light);
}

.shortcut-row:last-child {
  border-bottom: none;
}

.shortcut-desc {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.keys {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xs);
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}
</style>
