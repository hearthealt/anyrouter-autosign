<template>
  <div class="settings-page">
    <section class="page-toolbar settings-toolbar" aria-label="设置概览">
      <div class="page-toolbar__summary">
        <span class="page-toolbar__label"><Settings2 :size="15" /> 系统设置</span>
        <div class="filter-meta page-toolbar__meta">
          <span :class="{ success: autoSignEnabled }">自动签到 <strong>{{ autoSignEnabled ? '已开启' : '未开启' }}</strong></span>
          <span>通知渠道 <strong>{{ channelCount }}</strong></span>
          <span>账号分组 <strong>{{ groupCount }}</strong></span>
        </div>
      </div>
    </section>

    <section class="settings-navigation">
      <div class="settings-navigation__head"><span class="mono">NAVIGATION / 06—A</span><strong>系统模块</strong><Activity :size="15" /></div>
      <UiSegment v-model:value="activeTab" class="settings-tabs" :options="[{ label: '常规', value: 'general' }, { label: '通知', value: 'notify' }, { label: '数据', value: 'data' }, { label: '日志', value: 'logs' }, { label: '关于', value: 'about' }]" />
    </section>

    <div v-show="activeTab === 'general'" class="tab-panel">
      <GeneralSettingsTab ref="generalRef" @update:auto-sign-enabled="autoSignEnabled = $event" />
    </div>
    <div v-show="activeTab === 'notify'" class="tab-panel">
      <NotifyChannelsTab ref="notifyRef" @update:count="channelCount = $event" />
    </div>
    <div v-show="activeTab === 'data'" class="tab-panel">
      <div class="sub-section">
        <div class="sub-section-nav">
          <UiSegment v-model:value="dataSection" size="small" :options="[{ label: '分组管理', value: 'groups' }, { label: '数据备份', value: 'backup' }]" />
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
    </div>
    <div v-show="activeTab === 'logs'" class="tab-panel">
      <div class="sub-section">
        <div class="sub-section-nav">
          <UiSegment v-model:value="logSection" size="small" :options="[{ label: '审计日志', value: 'audit' }, { label: '系统日志', value: 'system' }]" />
        </div>
        <div class="sub-section-body">
          <AuditLogsTab v-if="logSection === 'audit'" ref="auditRef" />
          <SystemLogsTab v-else-if="logSection === 'system'" />
        </div>
      </div>
    </div>
    <div v-show="activeTab === 'about'" class="tab-panel">
      <AboutTab ref="aboutRef" />
    </div>
  </div>
</template>
<script setup lang="ts">
import { UiSegment } from '../ui'
import { Activity, Settings2 } from 'lucide-vue-next'
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
.settings-page { display: flex; flex-direction: column; gap: clamp(14px, 1.8vw, 24px); padding-bottom: 48px; }
.settings-navigation { padding: 15px 17px 17px; border: 1px solid var(--line); border-radius: 18px; background: linear-gradient(135deg, var(--surface-raised), var(--surface-inset)); box-shadow: var(--lift-2); }
.settings-navigation__head { display: flex; align-items: center; gap: 13px; margin-bottom: 13px; padding-bottom: 12px; border-bottom: 1px solid var(--line-faint); }
.settings-navigation__head .mono { color: var(--signal-deep); font-family: var(--font-mono); font-size: 9px; letter-spacing: .14em; }
.settings-navigation__head strong { color: var(--ink-strong); font-size: 12px; }
.settings-navigation__head svg { margin-left: auto; color: var(--signal-deep); }
.settings-tabs { max-width: 100%; overflow-x: auto; scrollbar-width: none; }
.settings-tabs::-webkit-scrollbar { display: none; }
/* 内容区自带内边距：原来 general/notify/about 三个面板直接贴在卡片描边上 */
.tab-panel { position: relative; overflow: hidden; padding: clamp(16px, 2.4vw, 24px); border: 1px solid var(--line); border-radius: 20px; background: var(--surface-raised); box-shadow: var(--lift-2); }
.tab-panel::before { content: ''; position: absolute; top: 0; left: 24px; z-index: 1; width: 76px; height: 2px; background: var(--signal); box-shadow: 0 0 14px var(--signal-glow); }
/* 子标签页在同一块面板内，内边距由 .tab-panel 给，这里只管纵向节奏 */
.sub-section { display: flex; flex-direction: column; gap: var(--s4); }
.sub-section-nav { display: flex; align-items: center; padding-bottom: var(--s4); border-bottom: 1px solid var(--line-faint); }
.sub-section-body { display: flex; flex-direction: column; min-width: 0; }
@media (max-width: 560px) {
  .settings-navigation { padding: 13px; }
  .settings-navigation__head { align-items: flex-start; flex-wrap: wrap; }
  .tab-panel { border-radius: 16px; }
}
</style>