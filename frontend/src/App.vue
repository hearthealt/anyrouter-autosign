<template>
  <n-config-provider :theme="naiveTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <template v-if="isLoginPage">
          <router-view />
        </template>

        <div v-else class="layout">
          <div class="mobile-overlay" :class="{ show: mobileMenuOpen }" @click="mobileMenuOpen = false"></div>

          <aside class="sidebar" :class="{ collapsed, 'mobile-open': mobileMenuOpen }">
            <div class="sidebar-brand">
              <button type="button" class="brand-home" aria-label="返回首页" @click="$router.push('/')">
                <div class="brand-icon" aria-hidden="true">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
                    <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </div>
              </button>
              <div class="brand-copy">
                <span class="brand-text">AnyRouter</span>
                <button
                  type="button"
                  class="brand-version"
                  :class="{ 'has-update': versionStore.hasNewVersion }"
                  :title="versionStore.hasNewVersion ? `有新版本 ${versionStore.latestTag}，点击查看` : '查看版本信息'"
                  @click="showVersionModal = true"
                >
                  <span class="version-tag mono">{{ versionStore.currentTag || (versionStore.loading ? '加载中…' : '版本未知') }}</span>
                  <span v-if="versionStore.hasNewVersion" class="version-dot" aria-hidden="true"></span>
                  <span v-if="versionStore.hasNewVersion" class="sr-only">有新版本</span>
                </button>
              </div>
            </div>

            <nav class="sidebar-nav" aria-label="主导航">
              <button
                v-for="item in menuItems"
                :key="item.path"
                type="button"
                class="nav-item"
                :class="{ active: isActive(item.path) }"
                :aria-current="isActive(item.path) ? 'page' : undefined"
                @click="navigateTo(item.path)"
              >
                <div class="nav-icon" aria-hidden="true">
                  <n-icon :size="16"><component :is="item.icon" /></n-icon>
                </div>
                <span class="nav-label">{{ item.label }}</span>
              </button>
            </nav>

            <div class="sidebar-footer">
              <button type="button" class="nav-item small" :aria-label="currentTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'" @click="toggleTheme">
                <div class="nav-icon" aria-hidden="true">
                  <n-icon :size="16">
                    <SunnyOutline v-if="currentTheme === 'dark'" />
                    <MoonOutline v-else />
                  </n-icon>
                </div>
                <span class="nav-label">{{ currentTheme === 'dark' ? '浅色' : '深色' }}</span>
              </button>
              <button type="button" class="nav-item small collapse-btn" :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'" :aria-expanded="!collapsed" @click="collapsed = !collapsed">
                <div class="nav-icon" aria-hidden="true">
                  <n-icon :size="16">
                    <ChevronBackOutline v-if="!collapsed" />
                    <ChevronForwardOutline v-else />
                  </n-icon>
                </div>
                <span class="nav-label">收起</span>
              </button>
            </div>
          </aside>

          <div class="main" :class="{ expanded: collapsed }">
            <header class="header">
              <n-button class="mobile-menu-btn" quaternary size="small" aria-label="打开导航菜单" @click="mobileMenuOpen = true">
                <template #icon><n-icon :size="18"><MenuOutline /></n-icon></template>
              </n-button>

              <div class="header-left">
                <span class="header-title">{{ pageTitle }}</span>
                <span v-if="breadcrumbTail" class="header-crumb">
                  <n-icon :size="12"><ChevronForwardOutline /></n-icon>
                  {{ breadcrumbTail }}
                </span>
              </div>

              <div class="header-center">
                <n-popover
                  trigger="manual"
                  :show="searchResults.length > 0"
                  placement="bottom"
                  :width="360"
                  @update:show="(show: boolean) => !show && (searchResults = [])"
                >
                  <template #trigger>
                    <n-input
                      v-model:value="searchKeyword"
                      placeholder="搜索账号、日志…   或按 ⌘K 打开命令面板"
                      clearable
                      size="small"
                      class="global-search"
                      :loading="searchLoading"
                      @keyup.enter="handleGlobalSearch"
                    >
                      <template #prefix>
                        <n-icon :size="14"><SearchOutline /></n-icon>
                      </template>
                      <template #suffix>
                        <button
                          type="button"
                          class="cpk-hint"
                          aria-label="打开命令面板 (Ctrl/Cmd+K)"
                          @click="showCommandPalette = true"
                        >
                          <kbd>{{ modKeyLabel }}</kbd><kbd>K</kbd>
                        </button>
                      </template>
                    </n-input>
                  </template>
                  <div class="search-results">
                    <div
                      v-for="(result, index) in searchResults"
                      :key="index"
                      class="search-result-item"
                      @click="handleSearchResultClick(result)"
                    >
                      <span class="search-result-badge" :class="result.type">
                        {{ result.type === 'account' ? '账号' : '日志' }}
                      </span>
                      <div class="search-result-content">
                        <div class="search-result-title">{{ result.title }}</div>
                        <div class="search-result-desc">{{ result.description }}</div>
                      </div>
                    </div>
                  </div>
                </n-popover>
              </div>

              <div class="header-right">
                <n-tooltip>
                  <template #trigger>
                    <n-button
                      quaternary
                      size="small"
                      class="icon-btn version-entry-btn"
                      :class="{ 'has-update': versionStore.hasNewVersion }"
                      aria-label="查看版本和更新"
                      @click="showVersionModal = true"
                    >
                      <template #icon><n-icon :size="16"><CloudDownloadOutline /></n-icon></template>
                      <span v-if="versionStore.hasNewVersion" class="header-version-dot" aria-hidden="true"></span>
                    </n-button>
                  </template>
                  {{ versionStore.hasNewVersion ? `发现新版本 ${versionStore.latestTag}` : '查看版本和更新' }}
                </n-tooltip>

                <n-tooltip>
                  <template #trigger>
                    <n-button quaternary size="small" class="icon-btn" aria-label="键盘快捷键帮助" @click="showShortcutsHelp = true">
                      <template #icon><n-icon :size="16"><HelpCircleOutline /></n-icon></template>
                    </n-button>
                  </template>
                  快捷键帮助 (Shift+?)
                </n-tooltip>

                <NotificationCenter />

                <n-button quaternary size="small" class="icon-btn" aria-label="刷新数据" :loading="refreshBus.refreshing.value" @click="refreshData">
                  <template #icon><n-icon :size="16"><RefreshOutline /></n-icon></template>
                </n-button>

                <n-dropdown :options="userMenuOptions" @select="handleUserMenuSelect" trigger="click">
                  <n-button quaternary size="small" class="user-btn">
                    <div class="user-avatar">{{ (currentUser?.username || 'A')[0].toUpperCase() }}</div>
                    <span class="user-name">{{ currentUser?.username || 'admin' }}</span>
                    <n-icon :size="12"><ChevronDownOutline /></n-icon>
                  </n-button>
                </n-dropdown>
              </div>
            </header>

            <main class="content">
              <router-view />
            </main>
          </div>

          <nav class="mobile-tabbar" aria-label="底部导航">
            <button
              v-for="item in menuItems"
              :key="item.path"
              type="button"
              class="tabbar-item"
              :class="{ active: isActive(item.path) }"
              :aria-current="isActive(item.path) ? 'page' : undefined"
              @click="navigateTo(item.path)"
            >
              <n-icon :size="18" aria-hidden="true"><component :is="item.icon" /></n-icon>
              <span>{{ item.label }}</span>
            </button>
          </nav>
        </div>

        <PasswordModal
          v-model:show="showPasswordModal"
          @changed="handlePasswordChanged"
        />

        <ShortcutsHelpModal v-model:show="showShortcutsHelp" />

        <VersionUpdateModal v-model:show="showVersionModal" />

        <CommandPalette v-model:show="showCommandPalette" @request-refresh="refreshBus.trigger()" />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NIcon, darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import {
  GridOutline,
  PeopleOutline,
  SettingsOutline,
  TimeOutline,
  StatsChartOutline,
  ChevronBackOutline,
  ChevronForwardOutline,
  ChevronDownOutline,
  RefreshOutline,
  LockClosedOutline,
  LogOutOutline,
  SunnyOutline,
  MoonOutline,
  MenuOutline,
  SearchOutline,
  HelpCircleOutline,
  CloudDownloadOutline,
  ServerOutline
} from '@vicons/ionicons5'
import { authApi, accountApi, signApi } from './api'
import type { Account, SignLog } from './types'
import { removeToken, isLoggedIn } from './utils/auth'
import { getActiveTheme, setThemeMode, type ThemeMode } from './utils'
import { provideViewRefresh, useShortcuts } from './composables'
import { useVersionStore } from './stores'
import PasswordModal from './components/layout/PasswordModal.vue'
import ShortcutsHelpModal from './components/layout/ShortcutsHelpModal.vue'
import CommandPalette from './components/layout/CommandPalette.vue'
import NotificationCenter from './components/layout/NotificationCenter.vue'
import VersionUpdateModal from './components/layout/VersionUpdateModal.vue'

interface GlobalSearchResult {
  type: 'account' | 'log'
  title: string
  description: string
  data: Account | SignLog
}

const route = useRoute()
const router = useRouter()
const versionStore = useVersionStore()
const collapsed = ref(false)
const mobileMenuOpen = ref(false)
const currentUser = ref<any>(null)
const currentTheme = ref<'light' | 'dark'>(getActiveTheme())

const refreshBus = provideViewRefresh()

const showShortcutsHelp = ref(false)
const showCommandPalette = ref(false)
const showVersionModal = ref(false)

const buildLocalDateParam = (value: string) => {
  const date = new Date(value)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const buildLogRouteQuery = (log: SignLog) => {
  const signDate = buildLocalDateParam(log.sign_time)
  return {
    account_id: String(log.account_id),
    success: String(log.success),
    start_date: signDate,
    end_date: signDate
  }
}

useShortcuts([
  {
    key: 'mod+k',
    description: '打开命令面板',
    allowInInput: true,
    handler: () => { showCommandPalette.value = true }
  },
  {
    key: 'shift+?',
    description: '显示快捷键帮助',
    handler: () => { showShortcutsHelp.value = true }
  },
  {
    key: 'r',
    description: '刷新当前视图',
    handler: () => { refreshBus.trigger() }
  },
  { keys: 'g d', description: '跳转 总览面板', handler: () => { void router.push('/') } },
  { keys: 'g a', description: '跳转 账号管理', handler: () => { void router.push('/accounts') } },
  { keys: 'g l', description: '跳转 签到记录', handler: () => { void router.push('/logs') } },
  { keys: 'g s', description: '跳转 数据统计', handler: () => { void router.push('/statistics') } },
  { keys: 'g p', description: '跳转 平台管理', handler: () => { void router.push('/platforms') } },
  { keys: 'g c', description: '跳转 系统设置', handler: () => { void router.push('/settings') } },
])

const searchKeyword = ref('')
const searchLoading = ref(false)
const searchResults = ref<GlobalSearchResult[]>([])

const showPasswordModal = ref(false)

const handlePasswordChanged = () => {
  removeToken()
  router.push('/login')
}

const naiveTheme = computed(() => currentTheme.value === 'dark' ? darkTheme : null)
const isLoginPage = computed(() => route.path === '/login')
const modKeyLabel = computed(() => /mac/i.test(navigator.platform) ? '⌘' : 'Ctrl')

const menuItems = [
  { path: '/', label: '总览面板', icon: GridOutline },
  { path: '/accounts', label: '账号管理', icon: PeopleOutline },
  { path: '/logs', label: '签到记录', icon: TimeOutline },
  { path: '/statistics', label: '数据统计', icon: StatsChartOutline },
  { path: '/platforms', label: '平台管理', icon: ServerOutline },
  { path: '/settings', label: '系统设置', icon: SettingsOutline },
]

const userMenuOptions = [
  {
    label: '修改密码',
    key: 'change-password',
    icon: () => h(NIcon, null, { default: () => h(LockClosedOutline) })
  },
  { type: 'divider', key: 'd1' },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOutOutline) })
  }
]

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/': '总览面板',
    '/accounts': '账号管理',
    '/logs': '签到记录',
    '/statistics': '数据统计',
    '/platforms': '平台管理',
    '/settings': '系统设置'
  }
  if (route.path.startsWith('/account/')) return '账号管理'
  return titles[route.path] || ''
})

const breadcrumbTail = computed(() => {
  if (route.path.startsWith('/account/')) return '详情'
  return ''
})

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  if (path === '/accounts') return route.path === '/accounts' || route.path.startsWith('/account/')
  return route.path.startsWith(path)
}

const navigateTo = (path: string) => {
  router.push(path)
  mobileMenuOpen.value = false
}

const refreshData = () => {
  refreshBus.trigger()
}

const toggleTheme = () => {
  const newTheme: ThemeMode = currentTheme.value === 'light' ? 'dark' : 'light'
  setThemeMode(newTheme)
  currentTheme.value = newTheme
}

const handleGlobalSearch = async () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    searchResults.value = []
    return
  }

  searchLoading.value = true
  searchResults.value = []

  try {
    const keyword_lower = keyword.toLowerCase()

    try {
      const accountRes: any = await accountApi.getList()
      if (accountRes.data) {
        const accounts = Array.isArray(accountRes.data) ? accountRes.data : []
        accounts.forEach((account: any) => {
          if (
            account.username?.toLowerCase().includes(keyword_lower) ||
            account.user_id?.toString().includes(keyword)
          ) {
            searchResults.value.push({
              type: 'account',
              title: account.username || `账号 ${account.user_id}`,
              description: `用户ID: ${account.user_id}`,
              data: account
            })
          }
        })
      }
    } catch (e) {
      console.error('Search accounts failed:', e)
    }

    try {
      const logsRes: any = await signApi.getAllLogs({ size: 50 })
      if (logsRes.data?.items) {
        logsRes.data.items.forEach((log: SignLog) => {
          if (
            log.account?.username?.toLowerCase().includes(keyword_lower) ||
            log.account_id?.toString().includes(keyword) ||
            log.message?.toLowerCase().includes(keyword_lower)
          ) {
            searchResults.value.push({
              type: 'log',
              title: `${log.account?.username || '未知账号'} - ${log.success ? '成功' : '失败'}`,
              description: `时间: ${new Date(log.sign_time).toLocaleString()}`,
              data: log
            })
          }
        })
      }
    } catch (e) {
      console.error('Search logs failed:', e)
    }

    if (searchResults.value.length === 0) {
      window.$notify('未找到相关内容', 'info')
    }
  } catch (e) {
    window.$notify('搜索失败', 'error')
  } finally {
    searchLoading.value = false
  }
}

const handleSearchResultClick = (result: GlobalSearchResult) => {
  searchKeyword.value = ''
  searchResults.value = []

  if (result.type === 'account') {
    router.push(`/account/${(result.data as Account).id}`)
  } else if (result.type === 'log') {
    router.push({
      path: '/logs',
      query: buildLogRouteQuery(result.data as SignLog)
    })
  }
}

const handleUserMenuSelect = (key: string) => {
  if (key === 'logout') {
    removeToken()
    window.$notify('已退出登录', 'success')
    router.push('/login')
  } else if (key === 'change-password') {
    showPasswordModal.value = true
  }
}

const loadCurrentUser = async () => {
  if (!isLoggedIn()) return
  try {
    const res: any = await authApi.getMe()
    if (res.success) {
      currentUser.value = res.data
    }
  } catch (e) {
    // 忽略错误
  }
}

// 侧边栏和顶部工具栏展示版本入口及新版本红点。检查失败不主动打扰用户，
// 用户可从任意页面打开版本弹窗查看原因、重新检查或执行更新。
const loadVersion = async () => {
  if (!isLoggedIn()) return

  if (!versionStore.info) {
    try {
      await versionStore.loadVersion()
    } catch {
      return
    }
  }

  if (!versionStore.checked) {
    await versionStore.checkLatest()
  }
}

watch(
  () => route.path,
  (path) => {
    if (path === '/login' || !isLoggedIn()) return
    if (!currentUser.value) void loadCurrentUser()
    void loadVersion()
  },
  { immediate: true }
)

onMounted(() => {

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const stored = localStorage.getItem('anyrouter-theme')
    if (!stored || stored === 'auto') {
      currentTheme.value = e.matches ? 'dark' : 'light'
    }
  })
})

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#5e6ad2',
    primaryColorHover: '#4f5ac7',
    primaryColorPressed: '#4048b1',
    borderRadius: '6px',
    fontSize: '13px'
  },
  Button: {
    fontWeight: '500'
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-color);
}

/* Sidebar */
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  z-index: 100;
  display: flex;
  flex-direction: column;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color-light);
  transition: width var(--transition-normal), transform var(--transition-normal);
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  width: 100%;
  height: var(--header-height);
  padding: 0 var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
  color: var(--text-primary);
}

.brand-home {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-inverse);
  background: transparent;
  font: inherit;
}

.brand-home:focus-visible,
.brand-version:focus-visible,
.sidebar-brand:focus-visible,
.nav-item:focus-visible,
.tabbar-item:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: -2px;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 1px;
  min-width: 0;
  transition: opacity var(--transition-fast), width var(--transition-fast);
}

.sidebar.collapsed .sidebar-brand {
  justify-content: center;
  padding: 0;
}

.brand-icon {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  min-width: 24px;
  border-radius: var(--radius-sm);
  background: var(--primary-color);
  color: var(--text-inverse);
}

.brand-text {
  font-family: var(--font-display);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  line-height: 1.1;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  white-space: nowrap;
}

.brand-version {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  max-width: 100%;
  padding: 0;
  border: none;
  border-radius: var(--radius-xs);
  cursor: pointer;
  color: var(--text-quaternary);
  background: transparent;
  font: inherit;
  transition: color var(--transition-fast), background var(--transition-fast);
}

.brand-version:hover,
.brand-version.has-update {
  color: var(--warning-color);
}

.brand-version:hover {
  background: var(--bg-card-hover);
}

.sidebar.collapsed .brand-copy {
  width: 0;
  opacity: 0;
  overflow: hidden;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
  overflow-y: auto;
  padding: var(--spacing-2);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  width: 100%;
  height: 30px;
  padding: 0 var(--spacing-2);
  color: var(--text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: background var(--transition-fast), color var(--transition-fast);
  background: transparent;
  border: none;
  font-family: inherit;
  text-align: left;
}

.nav-item.small {
  height: 28px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0;
}

.nav-item:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--primary-color-light);
  color: var(--primary-color);
}

.nav-icon {
  display: grid;
  place-items: center;
  width: 16px;
  min-width: 16px;
  color: inherit;
}

.nav-label {
  white-space: nowrap;
  transition: opacity var(--transition-fast);
}

.sidebar.collapsed .nav-label {
  width: 0;
  opacity: 0;
  overflow: hidden;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
}

.version-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.02em;
  white-space: nowrap;
}

.version-dot {
  flex-shrink: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--warning-color);
}


.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Main */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  transition: margin-left var(--transition-normal);
}

.main.expanded {
  margin-left: var(--sidebar-collapsed-width);
}

.header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: grid;
  grid-template-columns: auto minmax(240px, 360px) auto;
  align-items: center;
  gap: var(--spacing-3);
  height: var(--header-height);
  padding: 0 var(--spacing-5);
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-color-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  min-width: 0;
}

.header-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  letter-spacing: -0.01em;
}

.header-crumb {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.header-center {
  display: flex;
  justify-content: center;
}

.global-search {
  width: 100%;
  max-width: 360px;
}

.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 2px;
}

.icon-btn {
  width: 28px;
  height: 28px;
  padding: 0 !important;
  color: var(--text-secondary);
}

.icon-btn:hover {
  color: var(--text-primary);
}

.version-entry-btn {
  position: relative;
}

.version-entry-btn.has-update {
  color: var(--warning-color);
}

.header-version-dot {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 6px;
  height: 6px;
  border: 1px solid var(--bg-header);
  border-radius: 50%;
  background: var(--warning-color);
}

.search-results {
  max-height: 340px;
  overflow-y: auto;
}

.search-result-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: var(--spacing-3);
  padding: var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.search-result-item:hover {
  background: var(--bg-card-hover);
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-badge {
  display: inline-flex;
  align-items: center;
  height: 18px;
  padding: 0 6px;
  border-radius: var(--radius-xs);
  font-size: 10px;
  font-weight: var(--font-medium);
  color: var(--text-inverse);
}

.search-result-badge.account {
  background: var(--primary-color);
}

.search-result-badge.log {
  background: var(--info-color);
}

.search-result-title {
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.search-result-desc {
  margin-top: 2px;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.user-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  height: 28px;
  padding: 0 var(--spacing-2) !important;
  color: var(--text-secondary);
}

.user-avatar {
  width: 20px;
  height: 20px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  background: var(--primary-color);
  color: var(--text-inverse);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.content {
  flex: 1;
  width: 100%;
  padding: var(--spacing-5) var(--spacing-6);
}

.cpk-hint {
  display: inline-flex;
  gap: 2px;
  align-items: center;
  background: transparent;
  border: none;
  padding: 0;
  cursor: pointer;
}

.cpk-hint kbd {
  display: inline-grid;
  place-items: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-tertiary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xs);
}

.cpk-hint:hover kbd {
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(11, 12, 14, 0.5);
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--transition-normal);
  z-index: 90;
}

.mobile-overlay.show {
  opacity: 1;
  pointer-events: auto;
}

.mobile-menu-btn {
  display: none;
}

.mobile-tabbar {
  display: none;
}

@media (max-width: 900px) {
  .header {
    grid-template-columns: auto 1fr auto;
  }

  .header-center {
    display: none;
  }
}

@media (max-width: 768px) {
  .toast-stack {
    right: 12px;
    left: 12px;
    bottom: calc(var(--tabbar-height) + 16px);
    max-width: none;
  }

  .toast-item {
    min-width: 0;
  }

  .mobile-overlay,
  .mobile-menu-btn,
  .mobile-tabbar {
    display: block;
  }

  .sidebar {
    transform: translateX(-100%);
    width: min(var(--sidebar-width), 80vw);
  }

  .sidebar.mobile-open {
    transform: translateX(0);
  }

  .sidebar.collapsed {
    width: min(var(--sidebar-width), 80vw);
  }

  .sidebar.collapsed .brand-copy,
  .sidebar.collapsed .nav-label {
    width: auto;
    opacity: 1;
    overflow: visible;
  }

  .sidebar-footer .collapse-btn {
    display: none;
  }

  .main,
  .main.expanded {
    margin-left: 0;
  }

  .header {
    padding: 0 var(--spacing-4);
  }

  .user-name {
    display: none;
  }

  .content {
    padding: var(--spacing-4) var(--spacing-4) calc(var(--tabbar-height) + 16px);
  }

  .mobile-tabbar {
    position: fixed;
    right: 0;
    bottom: 0;
    left: 0;
    z-index: 95;
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    align-items: center;
    height: var(--tabbar-height);
    background: var(--bg-elevated);
    border-top: 1px solid var(--border-color-light);
  }

  .tabbar-item {
    display: grid;
    justify-items: center;
    gap: 2px;
    color: var(--text-tertiary);
    font-size: 10px;
    cursor: pointer;
    background: transparent;
    border: none;
    font-family: inherit;
    padding: 0;
  }

  .tabbar-item.active {
    color: var(--primary-color);
  }
}

@media (max-width: 520px) {
  .header-left .header-crumb {
    display: none;
  }

  .mobile-tabbar {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    row-gap: 6px;
    height: auto;
    padding: var(--spacing-2) 0;
  }
}
</style>
