<template>
  <div class="settings-page">
    <div class="page-head">
      <div>
        <h1 class="page-title">设置</h1>
        <p class="page-subtitle">
          自动签到 <span :class="['status', { on: autoSignEnabled }]">{{ autoSignEnabled ? '已开启' : '未开启' }}</span>
          <span class="sep">·</span>
          {{ channelCount }} 个推送渠道
          <span class="sep">·</span>
          {{ groupCount }} 个分组
        </p>
      </div>
    </div>

    <n-tabs v-model:value="activeTab" type="segment" animated class="settings-tabs">
      <n-tab-pane name="general" tab="常规" display-directive="show:lazy">
        <GeneralSettingsTab ref="generalRef" @update:auto-sign-enabled="autoSignEnabled = $event" />
      </n-tab-pane>

      <n-tab-pane name="notify" tab="通知" display-directive="show:lazy">
        <NotifyChannelsTab ref="notifyRef" @update:count="channelCount = $event" />
      </n-tab-pane>

      <n-tab-pane name="data" tab="数据" display-directive="show:lazy">
        <div class="sub-section">
          <div class="sub-section-nav">
            <n-radio-group v-model:value="dataSection" size="small">
              <n-radio-button value="groups">分组管理</n-radio-button>
              <n-radio-button value="backup">数据备份</n-radio-button>
            </n-radio-group>
          </div>
          <div class="sub-section-body">
            <GroupsTab
              v-if="dataSection === 'groups'"
              ref="groupsRef"
              @update:count="groupCount = $event"
            />
            <BackupTab
              v-else-if="dataSection === 'backup'"
              ref="backupRef"
              @update:account-count="backupAccountCount = $event"
            />
          </div>
        </div>
      </n-tab-pane>

      <n-tab-pane name="logs" tab="日志" display-directive="show:lazy">
        <div class="sub-section">
          <div class="sub-section-nav">
            <n-radio-group v-model:value="logSection" size="small">
              <n-radio-button value="audit">审计日志</n-radio-button>
              <n-radio-button value="system">系统日志</n-radio-button>
            </n-radio-group>
          </div>
          <div class="sub-section-body">
            <AuditLogsTab v-if="logSection === 'audit'" ref="auditRef" />
            <SystemLogsTab v-else-if="logSection === 'system'" />
          </div>
        </div>
      </n-tab-pane>

      <n-tab-pane name="about" tab="关于" display-directive="show:lazy">
        <AboutTab ref="aboutRef" />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useViewRefresh } from '../composables'
import GeneralSettingsTab from '../components/settings/GeneralSettingsTab.vue'
import NotifyChannelsTab from '../components/settings/NotifyChannelsTab.vue'
import BackupTab from '../components/settings/BackupTab.vue'
import GroupsTab from '../components/settings/GroupsTab.vue'
import AuditLogsTab from '../components/settings/AuditLogsTab.vue'
import SystemLogsTab from '../components/settings/SystemLogsTab.vue'
import AboutTab from '../components/settings/AboutTab.vue'

const route = useRoute()

const TAB_NAMES = ['general', 'notify', 'data', 'logs', 'about'] as const

// 支持 /settings?tab=about 直接打开指定标签（侧边栏版本号点击会带上）
const initialTab = () => {
  const tab = String(route.query.tab || '')
  return (TAB_NAMES as readonly string[]).includes(tab) ? tab : 'general'
}

const activeTab = ref(initialTab())
const dataSection = ref<'groups' | 'backup'>('groups')
const logSection = ref<'audit' | 'system'>('audit')

const autoSignEnabled = ref(false)
const channelCount = ref(0)
const groupCount = ref(0)
const backupAccountCount = ref(0)

const generalRef = ref<InstanceType<typeof GeneralSettingsTab> | null>(null)
const notifyRef = ref<InstanceType<typeof NotifyChannelsTab> | null>(null)
const backupRef = ref<InstanceType<typeof BackupTab> | null>(null)
const groupsRef = ref<InstanceType<typeof GroupsTab> | null>(null)
const auditRef = ref<InstanceType<typeof AuditLogsTab> | null>(null)
const aboutRef = ref<InstanceType<typeof AboutTab> | null>(null)

useViewRefresh(async () => {
  await Promise.all([
    generalRef.value?.load(),
    notifyRef.value?.load(),
    backupRef.value?.load(),
    groupsRef.value?.load(),
    auditRef.value?.load(),
    aboutRef.value?.load()
  ])
})
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  padding-bottom: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin: 0;
}

.page-subtitle {
  margin-top: 4px;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.page-subtitle .status {
  color: var(--text-tertiary);
}

.page-subtitle .status.on {
  color: var(--success-color);
  font-weight: var(--font-medium);
}

.page-subtitle .sep {
  color: var(--text-quaternary);
}

.settings-tabs :deep(.n-tabs-nav) {
  margin-bottom: var(--spacing-5);
}

.settings-tabs :deep(.n-tabs-rail) {
  background: var(--bg-secondary);
  padding: 3px;
  border-radius: var(--radius-md);
  box-shadow: none;
}

.settings-tabs :deep(.n-tabs-tab) {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  padding: 6px 18px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.settings-tabs :deep(.n-tabs-tab:hover) {
  color: var(--text-primary);
}

.settings-tabs :deep(.n-tabs-tab.n-tabs-tab--active) {
  color: var(--text-primary);
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
}

.sub-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.sub-section-nav {
  display: flex;
  align-items: center;
}

.sub-section-body {
  display: flex;
  flex-direction: column;
}

@media (max-width: 560px) {
  .settings-tabs :deep(.n-tabs-tab) {
    padding: 6px 12px;
  }
}
</style>
