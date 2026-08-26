<template>
  <div class="card settings-panel">
    <UiLoading :show="loading">
      <div class="channel-header">
        <div class="channel-header-info">
          <div class="channel-header-title">账号分组</div>
          <div class="channel-header-desc">创建分组来组织和管理账号</div>
        </div>
        <UiButton type="primary" @click="showAddGroupModal">
          <template #icon><Plus /></template>
          新建分组
        </UiButton>
      </div>

      <UiDivider style="margin: 16px 0;" />

      <div v-if="groups.length > 0" class="group-grid">
        <div v-for="group in groups" :key="group.id" class="group-card">
          <div class="group-card-header">
            <div class="group-color-dot" :style="{ background: getGroupColor(group.color) }"></div>
            <div class="group-account-count">
              <UiTag size="small" :bordered="false">{{ group.account_count }} 个账号</UiTag>
            </div>
          </div>
          <div class="group-card-body">
            <div class="group-name">{{ group.name }}</div>
            <div class="group-desc">{{ group.description || '暂无描述' }}</div>
          </div>
          <div class="group-card-footer">
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
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">
          <FolderOpen :size="48" />
        </div>
        <div class="empty-title">暂无分组</div>
        <div class="empty-desc">创建分组来更好地组织和管理您的账号</div>
        <UiButton type="primary" @click="showAddGroupModal" style="margin-top: 16px;">
          <template #icon><Plus /></template>
          创建第一个分组
        </UiButton>
      </div>
    </UiLoading>
  </div>

  <UiModal v-model:show="showGroupModal" :mask-closable="false">
    <div class="modal-container">
      <div class="modal-header">
        <h3>{{ editingGroup ? '编辑分组' : '新建分组' }}</h3>
        <UiButton text @click="showGroupModal = false">
          <X :size="20" />
        </UiButton>
      </div>
      <div class="modal-body">
        <div class="form-item">
          <label>分组名称</label>
          <UiInput v-model:value="groupForm.name" placeholder="输入分组名称" />
        </div>
        <div class="form-item">
          <label>分组描述（可选）</label>
          <UiInput v-model:value="groupForm.description" placeholder="输入分组描述" />
        </div>
        <div class="form-item">
          <label>分组颜色</label>
          <div class="color-picker">
            <div
              v-for="color in colorOptions"
              :key="color.value"
              class="color-option"
              :class="{ active: groupForm.color === color.value }"
              :style="{ background: color.hex }"
              @click="groupForm.color = color.value"
            >
              <Check :size="14" />
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <UiButton @click="showGroupModal = false">取消</UiButton>
        <UiButton type="primary" @click="saveGroup" :loading="savingGroup">保存</UiButton>
      </div>
    </div>
  </UiModal>
</template>

<script setup lang="ts">
import { UiButton, UiConfirm, UiDivider, UiInput, UiLoading, UiModal, UiTag } from '../../ui'
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
.settings-panel :deep(.n-card__content) { padding: 0; }
.settings-panel :deep(.n-card) { background: transparent; border: none; box-shadow: none; }

.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}
.channel-header-info { flex: 1; }
.channel-header-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: 2px;
}
.channel-header-desc { font-size: var(--text-xs); color: var(--text-tertiary); }

.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--spacing-3);
}

.group-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-3);
  transition: border-color var(--transition-fast);
}
.group-card:hover { border-color: var(--border-color); }

.group-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-2);
}

.group-color-dot {
  width: 20px;
  height: 20px;
  border-radius: var(--radius-sm);
}

.group-card-body { margin-bottom: var(--spacing-2); }
.group-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
  margin-bottom: 2px;
}
.group-desc { font-size: var(--text-xs); color: var(--text-tertiary); }

.group-card-footer {
  display: flex;
  gap: 2px;
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
}
.group-card-footer .n-button { flex: 1; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--spacing-12) var(--spacing-5);
  gap: var(--spacing-2);
}
.empty-icon { margin-bottom: var(--spacing-2); }
.empty-title { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--text-primary); }
.empty-desc { font-size: var(--text-xs); color: var(--text-tertiary); }

.delete-btn:hover { color: var(--error-color) !important; }

.modal-container {
  width: min(480px, calc(100vw - 24px));
  background: var(--bg-modal);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}
.modal-header h3 { margin: 0; font-size: var(--text-md); font-weight: var(--font-semibold); }
.modal-body { padding: var(--spacing-4); max-height: 60vh; overflow-y: auto; }

.form-item { margin-bottom: var(--spacing-3); }
.form-item:last-child { margin-bottom: 0; }
.form-item label {
  display: block;
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.color-picker {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.color-option {
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: grid;
  place-items: center;
  transition: transform var(--transition-fast);
  border: 2px solid transparent;
}
.color-option:hover { transform: scale(1.08); }
.color-option.active {
  border-color: var(--bg-card);
  box-shadow: 0 0 0 2px currentColor;
}

@media (max-width: 768px) {
  .channel-header { flex-direction: column; align-items: flex-start; gap: var(--spacing-2); }
  .group-grid { grid-template-columns: 1fr; }
}
</style>
