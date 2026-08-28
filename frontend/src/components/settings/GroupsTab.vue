<template>
  <UiLoading :show="loading">
    <div class="settings-pane">
      <div class="pane-head">
        <div class="pane-heading">
          <div class="pane-title"><FolderOpen :size="15" />账号分组</div>
          <div class="pane-desc">创建分组来组织和管理账号，分组颜色会显示在账号列表里</div>
        </div>
        <div class="pane-actions">
          <UiButton type="primary" size="small" @click="showAddGroupModal">
            <template #icon><Plus /></template>
            新建分组
          </UiButton>
        </div>
      </div>

      <div v-if="groups.length > 0" class="group-grid">
        <article
          v-for="group in groups"
          :key="group.id"
          class="group-card"
          :style="{ '--group-color': getGroupColor(group.color) }"
        >
          <header class="group-card-head">
            <span class="group-color-dot"></span>
            <div class="group-card-heading">
              <span class="group-name">{{ group.name }}</span>
              <span class="group-desc">{{ group.description || '暂无描述' }}</span>
            </div>
            <span class="group-count mono">{{ group.account_count }}</span>
          </header>
          <footer class="group-card-foot">
            <UiButton size="small" quaternary @click="editGroup(group)">
              <template #icon><Pencil /></template>
              编辑
            </UiButton>
            <UiConfirm @positive-click="deleteGroup(group.id)">
              <template #trigger>
                <UiButton size="small" quaternary class="delete-btn">
                  <template #icon><Trash2 /></template>
                  删除
                </UiButton>
              </template>
              删除分组后，账号将变为未分组状态
            </UiConfirm>
          </footer>
        </article>
      </div>

      <div v-else class="empty-state">
        <FolderOpen :size="40" class="empty-icon" />
        <div class="empty-title">暂无分组</div>
        <div class="empty-desc">创建分组来更好地组织和管理您的账号</div>
        <UiButton type="primary" size="small" @click="showAddGroupModal">
          <template #icon><Plus /></template>
          创建第一个分组
        </UiButton>
      </div>
    </div>
  </UiLoading>

  <UiModal v-model:show="showGroupModal" bare :width="440" :mask-closable="false">
    <div class="modal-container">
      <div class="modal-header">
        <h3>{{ editingGroup ? '编辑分组' : '新建分组' }}</h3>
        <UiButton text @click="showGroupModal = false">
          <X :size="18" />
        </UiButton>
      </div>
      <div class="modal-body">
        <div class="form-item">
          <label>分组名称</label>
          <UiInput v-model:value="groupForm.name" size="small" placeholder="输入分组名称" />
        </div>
        <div class="form-item">
          <label>分组描述（可选）</label>
          <UiInput v-model:value="groupForm.description" size="small" placeholder="输入分组描述" />
        </div>
        <div class="form-item">
          <label>分组颜色</label>
          <div class="color-picker">
            <button
              v-for="color in colorOptions"
              :key="color.value"
              type="button"
              class="color-option"
              :class="{ 'is-active': groupForm.color === color.value }"
              :style="{ '--swatch': color.hex }"
              :aria-label="color.value"
              :aria-pressed="groupForm.color === color.value"
              @click="groupForm.color = color.value"
            >
              <Check :size="13" />
            </button>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <UiButton size="small" @click="showGroupModal = false">取消</UiButton>
        <UiButton size="small" type="primary" @click="saveGroup" :loading="savingGroup">保存</UiButton>
      </div>
    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { UiButton, UiConfirm, UiInput, UiLoading, UiModal } from '../../ui'
import { ref, onMounted, watch } from 'vue'
import { Check, FolderOpen, Pencil, Plus, Trash2, X } from 'lucide-vue-next'
import { groupsApi } from '../../api'
import { apiError } from '../../utils/apiError'

const emit = defineEmits<{
  (e: 'update:count', v: number): void
}>()

const loading = ref(false)
const groups = ref<any[]>([])
const showGroupModal = ref(false)
const editingGroup = ref<any>(null)
const savingGroup = ref(false)
const groupForm = ref({
  name: '',
  description: '',
  color: 'default'
})

const colorOptions = [
  { value: 'default', hex: '#8b8b8b' },
  { value: 'blue', hex: '#2080f0' },
  { value: 'green', hex: '#18a058' },
  { value: 'red', hex: '#d03050' },
  { value: 'orange', hex: '#f0a020' },
  { value: 'purple', hex: '#8b5cf6' },
  { value: 'pink', hex: '#ec4899' },
  { value: 'cyan', hex: '#06b6d4' }
]

const getGroupColor = (color: string) => {
  const found = colorOptions.find(c => c.value === color)
  return found ? found.hex : '#8b8b8b'
}

watch(() => groups.value.length, v => emit('update:count', v))

const load = async () => {
  loading.value = true
  try {
    const res = await groupsApi.getList()
    groups.value = res.data || []
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    loading.value = false
  }
}

const showAddGroupModal = () => {
  editingGroup.value = null
  groupForm.value = { name: '', description: '', color: 'default' }
  showGroupModal.value = true
}

const editGroup = (group: any) => {
  editingGroup.value = group
  groupForm.value = {
    name: group.name,
    description: group.description || '',
    color: group.color || 'default'
  }
  showGroupModal.value = true
}

const saveGroup = async () => {
  if (!groupForm.value.name.trim()) {
    window.$notify('请输入分组名称', 'warning')
    return
  }
  savingGroup.value = true
  try {
    const payload = {
      name: groupForm.value.name,
      description: groupForm.value.description || undefined,
      color: groupForm.value.color
    }
    if (editingGroup.value) {
      await groupsApi.update(editingGroup.value.id, payload)
      window.$notify('分组更新成功', 'success')
    } else {
      await groupsApi.create(payload)
      window.$notify('分组创建成功', 'success')
    }
    showGroupModal.value = false
    load()
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    savingGroup.value = false
  }
}

const deleteGroup = async (id: number) => {
  try {
    await groupsApi.delete(id)
    window.$notify('分组删除成功', 'success')
    load()
  } catch (e) {
    window.$notify(apiError(e), 'error')
  }
}

defineExpose({ load })

onMounted(load)
</script>

<style scoped>
.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(252px, 1fr));
  gap: var(--s3);
}

/**
 * 分组色通过 --group-color 传进来，卡片左边一条竖线用它上色 ——
 * 比原来一个 20px 色块更能把"这张卡属于哪个分组"讲清楚。
 */
.group-card {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-lg);
  background: var(--surface-raised);
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.group-card::before {
  content: "";
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 3px;
  background: var(--group-color);
}

.group-card:hover {
  border-color: var(--line);
  box-shadow: var(--lift-2);
}

.group-card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 13px 12px 16px;
}

.group-color-dot {
  flex: 0 0 auto;
  width: 10px;
  height: 10px;
  border-radius: var(--r-full);
  background: var(--group-color);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--group-color) 18%, transparent);
}

.group-card-heading {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.group-name {
  overflow: hidden;
  color: var(--ink-max);
  font-size: var(--fn-md);
  font-weight: var(--weight-semibold);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.group-desc {
  overflow: hidden;
  color: var(--ink-faint);
  font-size: var(--fn-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 账号数用等宽数字读数，右侧对齐 */
.group-count {
  flex: 0 0 auto;
  padding: 2px 7px;
  border-radius: var(--r-sm);
  background: var(--surface-sunken);
  color: var(--ink-muted);
  font-size: var(--fn-xs);
  font-weight: var(--weight-semibold);
}

.group-card-foot {
  display: flex;
  gap: 2px;
  padding: 6px;
  border-top: 1px solid var(--line-faint);
  background: var(--surface-inset);
}

.group-card-foot > * { flex: 1; }
.group-card-foot :deep(.ui-btn) { width: 100%; }

.empty-icon { color: var(--ink-ghost); }
.delete-btn:hover { color: var(--bad); }

/* ── 分组编辑弹窗 */

.modal-container {
  display: flex;
  width: 100%;
  min-width: 0;
  min-height: 0;
  max-height: inherit;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--r-xl);
  background: var(--surface-overlay);
  box-shadow: var(--lift-4);
}

.modal-header {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  padding: 14px var(--s5);
  border-bottom: 1px solid var(--line-faint);
  background: var(--surface-inset);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--fn-lg);
  font-weight: var(--weight-semibold);
}

.modal-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: var(--s4);
  min-width: 0;
  min-height: 0;
  max-height: none;
  padding: var(--s5);
  overflow-y: auto;
  overscroll-behavior: contain;
}

.form-item { margin-bottom: 0; }

.modal-footer {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: flex-end;
  gap: var(--s2);
  padding: 12px var(--s5);
  border-top: 1px solid var(--line-faint);
  background: var(--surface-inset);
}

.color-picker {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s2);
}

.color-option {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: 2px solid transparent;
  border-radius: var(--r-md);
  background: var(--swatch);
  color: transparent;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.color-option:hover { transform: scale(1.08); }

/* 选中态：白勾 + 一圈同色光环，暗色主题下也看得出选了哪个 */
.color-option.is-active {
  color: #fff;
  box-shadow: 0 0 0 2px var(--surface-overlay), 0 0 0 4px var(--swatch);
}
</style>
