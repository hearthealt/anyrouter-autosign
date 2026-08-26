<template>
  <UiModal
    :show="show"
    kicker="Keyboard"
    title="快捷键"
    size="sm"
    @update:show="(v: boolean) => emit('update:show', v)"
  >
    <div class="sc">
      <section v-for="group in groups" :key="group.title" class="sc__group">
        <h3 class="sc__group-title kicker">
          <span>{{ group.title }}</span>
          <span v-if="group.note" class="sc__group-note">{{ group.note }}</span>
        </h3>
        <div class="sc__rows">
          <div v-for="item in group.items" :key="item.desc" class="sc__row">
            <span class="sc__desc">{{ item.desc }}</span>
            <span class="sc__keys">
              <kbd v-for="key in item.keys" :key="key">{{ key }}</kbd>
            </span>
          </div>
        </div>
      </section>
    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { UiModal } from '../../ui'

defineProps<{ show: boolean }>()
const emit = defineEmits<{ (e: 'update:show', v: boolean): void }>()

// 从模板里提出来成数据：新增快捷键时只动这一处
const groups = [
  {
    title: '全局',
    items: [
      { desc: '打开命令面板', keys: ['⌘', 'K'] },
      { desc: '刷新当前视图', keys: ['R'] },
      { desc: '显示快捷键帮助', keys: ['?'] },
    ],
  },
  {
    title: '跳转',
    note: '按 G 后再按下一键',
    items: [
      { desc: '总览面板', keys: ['G', 'D'] },
      { desc: '账号管理', keys: ['G', 'A'] },
      { desc: '签到记录', keys: ['G', 'L'] },
      { desc: '数据统计', keys: ['G', 'S'] },
      { desc: '平台管理', keys: ['G', 'P'] },
      { desc: '系统设置', keys: ['G', 'C'] },
    ],
  },
]
</script>

<style scoped>
.sc {
  display: grid;
  gap: var(--s6);
}

.sc__group-title {
  display: flex;
  align-items: baseline;
  gap: var(--s2);
  padding-bottom: var(--s2);
  border-bottom: 1px solid var(--line-faint);
}

.sc__group-note {
  color: var(--ink-ghost);
  letter-spacing: var(--track-normal);
  text-transform: none;
  font-weight: var(--weight-normal);
}

.sc__rows {
  display: grid;
  margin-top: var(--s2);
}

.sc__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s4);
  height: 30px;
}

.sc__desc {
  color: var(--ink);
  font-size: var(--fn-sm);
}

.sc__keys {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 21px;
  height: 21px;
  padding: 0 5px;
  border: 1px solid var(--line);
  /* 底缘加深一层描边，做出物理键帽的厚度 */
  border-bottom-width: 2px;
  border-radius: var(--r-xs);
  background: var(--surface-inset);
  color: var(--ink-strong);
  font-family: var(--font-mono);
  font-size: var(--fn-xs);
  font-weight: var(--weight-medium);
}
</style>
