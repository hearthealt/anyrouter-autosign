<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <div class="layout">
          <!-- 侧边栏 -->
          <aside class="sidebar" :class="{ collapsed }">
            <div class="sidebar-logo" @click="$router.push('/')">
              <div class="logo-icon">A</div>
              <span class="logo-text" v-show="!collapsed">AnyRouter</span>
            </div>

            <nav class="sidebar-menu">
              <div
                v-for="item in menuItems"
                :key="item.path"
                class="menu-item"
                :class="{ active: isActive(item.path) }"
                @click="$router.push(item.path)"
              >
                <n-icon :size="18"><component :is="item.icon" /></n-icon>
                <span v-show="!collapsed">{{ item.label }}</span>
              </div>
            </nav>

            <div class="sidebar-bottom">
              <div class="menu-item" @click="collapsed = !collapsed">
                <n-icon :size="18">
                  <ChevronBackOutline v-if="!collapsed" />
                  <ChevronForwardOutline v-else />
                </n-icon>
                <span v-show="!collapsed">收起菜单</span>
              </div>
            </div>
          </aside>

          <!-- 主区域 -->
          <div class="main" :class="{ expanded: collapsed }">
            <header class="header">
              <h1 class="title">{{ pageTitle }}</h1>
              <div class="header-actions">
                <n-button quaternary circle @click="refreshData">
                  <template #icon><n-icon><RefreshOutline /></n-icon></template>
                </n-button>
              </div>
            </header>
            <main class="content">
              <router-view />
            </main>
          </div>
        </div>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import type { GlobalThemeOverrides } from 'naive-ui'
import {
  GridOutline,
  SettingsOutline,
  TimeOutline,
  ChevronBackOutline,
  ChevronForwardOutline,
  RefreshOutline
} from '@vicons/ionicons5'

const route = useRoute()
const collapsed = ref(false)

const menuItems = [
  { path: '/', label: '控制台', icon: GridOutline },
  { path: '/logs', label: '签到日志', icon: TimeOutline },
  { path: '/settings', label: '系统设置', icon: SettingsOutline },
]

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/': '控制台',
    '/logs': '签到日志',
    '/settings': '系统设置'
  }
  if (route.path.startsWith('/account/')) return '账号详情'
  return titles[route.path] || '控制台'
})

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const refreshData = () => {
  window.location.reload()
}

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#00b38a',
    primaryColorHover: '#00c99b',
    primaryColorPressed: '#009e7a',
    borderRadius: '8px'
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: #f4f6f8;
}

.sidebar {
  width: 200px;
  background: #1a1a2e;
  display: flex;
  flex-direction: column;
  transition: width 0.2s ease;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}

.logo-icon {
  width: 28px;
  height: 28px;
  background: #00b38a;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.logo-text {
  color: white;
  font-weight: 600;
  font-size: 15px;
}

.sidebar-menu {
  flex: 1;
  padding: 12px 8px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: rgba(255,255,255,0.6);
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 2px;
  font-size: 13px;
  transition: all 0.15s;
}

.menu-item:hover {
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.9);
}

.menu-item.active {
  background: rgba(0,179,138,0.2);
  color: #00b38a;
}

.sidebar-bottom {
  padding: 12px 8px;
  border-top: 1px solid rgba(255,255,255,0.08);
}

.main {
  flex: 1;
  margin-left: 200px;
  transition: margin-left 0.2s ease;
}

.main.expanded {
  margin-left: 60px;
}

.header {
  height: 56px;
  background: white;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
}

.content {
  padding: 20px 24px;
}
</style>
