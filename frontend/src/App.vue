<template>
  <!-- 登录页自己占满视口，不套外壳 -->
  <router-view v-if="isLoginPage" />

  <div v-else class="shell">
    <div class="shell__scrim" :class="{ 'is-open': mobileMenuOpen }" @click="mobileMenuOpen = false" />

    <!-- ───────────────────────────────── 侧栏 -->
    <aside
      ref="sidebarEl"
      class="rail material-noise"
      :class="{ 'is-collapsed': collapsed, 'is-mobile-open': mobileMenuOpen }"
    >
      <div class="rail__brand">
        <button type="button" class="rail__mark" aria-label="返回首页" @click="router.push('/')">
          <Zap :size="15" />
        </button>
        <div class="rail__id">
          <span class="rail__name">AnyRouter</span>
          <button
            type="button"
            class="rail__version"
            :class="{ 'has-update': versionStore.hasNewVersion }"
            :title="versionStore.hasNewVersion ? `有新版本 ${versionStore.latestTag}，点击查看` : '查看版本信息'"
            @click="showVersionModal = true"
          >
            <span class="mono">{{ versionStore.currentTag || (versionStore.loading ? '加载中…' : '版本未知') }}</span>
            <span v-if="versionStore.hasNewVersion" class="rail__dot" aria-hidden="true" />
            <span v-if="versionStore.hasNewVersion" class="sr-only">有新版本</span>
          </button>
        </div>
      </div>

      <nav class="rail__nav" aria-label="主导航">
        <!-- 活动指示条：位置由弹簧驱动，在导航项之间滑动 -->
        <span ref="indicatorEl" class="rail__indicator" aria-hidden="true" />
        <button
          v-for="item in menuItems"
          :key="item.path"
          :ref="el => setNavRef(item.path, el as HTMLElement | null)"
          type="button"
          class="rail__item"
          :class="{ 'is-active': isActive(item.path) }"
          :aria-current="isActive(item.path) ? 'page' : undefined"
          @click="navigateTo(item.path)"
        >
          <component :is="item.icon" :size="16" class="rail__icon" />
          <span class="rail__label">{{ item.label }}</span>
        </button>
      </nav>

      <div class="rail__foot">
        <button
          type="button"
          class="rail__item is-small"
          :aria-label="currentTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
          @click="toggleTheme"
        >
          <component :is="currentTheme === 'dark' ? Sun : Moon" :size="16" class="rail__icon" />
          <span class="rail__label">{{ currentTheme === 'dark' ? '浅色' : '深色' }}</span>
        </button>
        <button
          type="button"
          class="rail__item is-small"
          :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
          :aria-expanded="!collapsed"
          @click="collapsed = !collapsed"
        >
          <component :is="collapsed ? PanelLeftOpen : PanelLeftClose" :size="16" class="rail__icon" />
          <span class="rail__label">收起</span>
        </button>
      </div>
    </aside>

    <!-- ───────────────────────────────── 主区 -->
    <div class="frame" :class="{ 'is-wide': collapsed }">
      <header class="bar">
        <UiButton class="bar__burger" quaternary size="small" aria-label="打开导航菜单" @click="mobileMenuOpen = true">
          <template #icon><Menu :size="17" /></template>
        </UiButton>

        <div class="bar__title">
          <h1 class="bar__heading">{{ pageTitle }}</h1>
          <span v-if="breadcrumbTail" class="bar__crumb">
            <ChevronRight :size="11" />
            {{ breadcrumbTail }}
          </span>
        </div>

        <div class="bar__search">
          <UiPopover
            trigger="manual"
            placement="bottom"
            :show="searchResults.length > 0"
            :width="380"
            bare
            @update:show="(show: boolean) => !show && (searchResults = [])"
          >
            <template #trigger>
              <UiInput
                v-model:value="searchKeyword"
                class="bar__field"
                placeholder="搜索账号、日志…"
                size="small"
                clearable
                @keyup.enter="handleGlobalSearch"
              >
                <template #prefix>
                  <UiSpinner v-if="searchLoading" :size="12" />
                  <Search v-else :size="13" />
                </template>
                <template #suffix>
                  <button
                    type="button"
                    class="bar__kbd"
                    aria-label="打开命令面板 (Ctrl/Cmd+K)"
                    @click="showCommandPalette = true"
                  >
                    <kbd>{{ modKeyLabel }}</kbd><kbd>K</kbd>
                  </button>
                </template>
              </UiInput>
            </template>

            <div class="hits">
              <button
                v-for="(result, index) in searchResults"
                :key="index"
                type="button"
                class="hits__row"
                @click="handleSearchResultClick(result)"
              >
                <span class="hits__kind" :class="result.type">
                  {{ result.type === 'account' ? '账号' : '日志' }}
                </span>
                <span class="hits__body">
                  <span class="hits__title">{{ result.title }}</span>
                  <span class="hits__desc">{{ result.description }}</span>
                </span>
              </button>
            </div>
          </UiPopover>
        </div>

        <div class="bar__tools">
          <UiTooltip :content="versionStore.hasNewVersion ? `发现新版本 ${versionStore.latestTag}` : '查看版本和更新'">
            <UiBadge :dot="versionStore.hasNewVersion" type="primary">
              <UiButton quaternary size="small" circle aria-label="查看版本和更新" @click="showVersionModal = true">
                <template #icon><CloudDownload :size="15" /></template>
              </UiButton>
            </UiBadge>
          </UiTooltip>

          <UiTooltip content="快捷键帮助 (Shift+?)">
            <UiButton quaternary size="small" circle aria-label="键盘快捷键帮助" @click="showShortcutsHelp = true">
              <template #icon><CircleHelp :size="15" /></template>
            </UiButton>
          </UiTooltip>

          <NotificationCenter />

          <UiButton
            quaternary
            size="small"
            circle
            aria-label="刷新数据"
            :loading="refreshBus.refreshing.value"
            @click="refreshData"
          >
            <template #icon><RefreshCw :size="15" /></template>
          </UiButton>

          <UiDropdown :options="userMenuOptions" @select="handleUserMenuSelect">
            <UiButton quaternary size="small" class="bar__user">
              <template #icon>
                <span class="bar__avatar">{{ (currentUser?.username || 'A')[0].toUpperCase() }}</span>
              </template>
              <span class="bar__username">{{ currentUser?.username || 'admin' }}</span>
            </UiButton>
          </UiDropdown>
        </div>
      </header>

      <main ref="contentEl" class="stage">
        <router-view />
      </main>
    </div>

    <nav class="tabs" aria-label="底部导航">
      <button
        v-for="item in menuItems"
        :key="item.path"
        type="button"
        class="tabs__item"
        :class="{ 'is-active': isActive(item.path) }"
        :aria-current="isActive(item.path) ? 'page' : undefined"
        @click="navigateTo(item.path)"
      >
        <component :is="item.icon" :size="17" aria-hidden="true" />
        <span>{{ item.label }}</span>
      </button>
    </nav>
  </div>

  <PasswordModal v-model:show="showPasswordModal" @changed="handlePasswordChanged" />
  <ShortcutsHelpModal v-model:show="showShortcutsHelp" />
  <VersionUpdateModal v-model:show="showVersionModal" />
  <CommandPalette v-model:show="showCommandPalette" @request-refresh="refreshBus.trigger()" />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { BarChart3, ChevronRight, CircleHelp, CloudDownload, History, KeyRound, LayoutDashboard, LogOut, Menu, Moon, PanelLeftClose, PanelLeftOpen, RefreshCw, Search, Server, Settings, Sun, Users, Zap } from 'lucide-vue-next'
import { UiBadge, UiButton, UiDropdown, UiInput, UiPopover, UiSpinner, UiTooltip } from './ui'
import { spring, SPRING, springIn, type SpringHandle } from './design/motion'
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
const showPasswordModal = ref(false)

const sidebarEl = ref<HTMLElement | null>(null)
const indicatorEl = ref<HTMLElement | null>(null)
const contentEl = ref<HTMLElement | null>(null)

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

const handlePasswordChanged = () => {
  removeToken()
  router.push('/login')
}

const isLoginPage = computed(() => route.path === '/login')
const modKeyLabel = computed(() => /mac/i.test(navigator.platform) ? '⌘' : 'Ctrl')

const menuItems = [
  { path: '/', label: '总览面板', icon: LayoutDashboard },
  { path: '/accounts', label: '账号管理', icon: Users },
  { path: '/logs', label: '签到记录', icon: History },
  { path: '/statistics', label: '数据统计', icon: BarChart3 },
  { path: '/platforms', label: '平台管理', icon: Server },
  { path: '/settings', label: '系统设置', icon: Settings },
]

const userMenuOptions = [
  { label: '修改密码', key: 'change-password', icon: KeyRound },
  { type: 'divider' as const },
  { label: '退出登录', key: 'logout', icon: LogOut, tone: 'error' as const },
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

/* ───────────────────────────── 导航活动指示条
 *
 * 一条 signal 色竖条在导航项之间滑动。位置用弹簧求解，
 * 所以连续切换路由时它会带着速度继续走，不会每次从零加速。
 */
const navRefs = new Map<string, HTMLElement>()
let indicatorSpring: SpringHandle | null = null

function setNavRef(path: string, el: HTMLElement | null) {
  if (el) navRefs.set(path, el)
  else navRefs.delete(path)
}

function moveIndicator(animate = true) {
  const active = menuItems.find(item => isActive(item.path))
  const el = active ? navRefs.get(active.path) : null
  const nav = el?.parentElement
  if (!el || !nav || !indicatorEl.value) return

  const top = el.offsetTop
  const height = el.offsetHeight
  indicatorEl.value.style.height = `${height}px`
  indicatorEl.value.style.opacity = '1'

  if (!indicatorSpring) {
    indicatorSpring = spring(top, value => {
      if (indicatorEl.value) indicatorEl.value.style.transform = `translate3d(0, ${value.toFixed(2)}px, 0)`
    }, SPRING.crisp)
  }

  animate ? indicatorSpring.set(top) : indicatorSpring.jump(top)
}

/* ───────────────────────────── 全局搜索 */

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

const handleUserMenuSelect = (key: string | number) => {
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
  async (path) => {
    if (path === '/login' || !isLoggedIn()) return
    if (!currentUser.value) void loadCurrentUser()
    void loadVersion()

    await nextTick()
    moveIndicator(true)
    // 路由切换时内容区弹簧入场，给页面切换一个物理落点
    if (contentEl.value) springIn(contentEl.value, { y: 10, opacity: 0, config: SPRING.crisp })
  },
  { immediate: true }
)

// 侧栏折叠会改变导航项高度，指示条要跟着重新量
watch(collapsed, () => nextTick(() => moveIndicator(false)))

let mediaQuery: MediaQueryList | null = null

function onSystemThemeChange(e: MediaQueryListEvent) {
  const stored = localStorage.getItem('anyrouter-theme')
  if (!stored || stored === 'auto') {
    currentTheme.value = e.matches ? 'dark' : 'light'
  }
}

onMounted(async () => {
  mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  mediaQuery.addEventListener('change', onSystemThemeChange)
  await nextTick()
  moveIndicator(false)
})

onBeforeUnmount(() => {
  mediaQuery?.removeEventListener('change', onSystemThemeChange)
  indicatorSpring?.stop()
})
</script>

<style scoped>
.shell {
  display: flex;
  width: 100%;
  min-height: 100vh;
  min-width: 0;
  background: var(--surface-page);
}

.shell__scrim {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: color-mix(in srgb, var(--surface-inverse) 40%, transparent);
  backdrop-filter: blur(3px);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.shell__scrim.is-open {
  opacity: 1;
  pointer-events: auto;
}

/* ───────────────────────────────────────── 侧栏 */

.rail {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  display: flex;
  flex-direction: column;
  width: var(--shell-sidebar);
  background: var(--surface-sunken);
  border-right: 1px solid var(--line-faint);
  transition: width 0.22s cubic-bezier(0.2, 0.9, 0.3, 1), transform 0.22s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.rail.is-collapsed { width: var(--shell-sidebar-collapsed); }

.rail__brand {
  display: flex;
  align-items: center;
  gap: var(--s3);
  height: var(--shell-header);
  padding: 0 var(--s4);
  border-bottom: 1px solid var(--line-faint);
  overflow: hidden;
}

.rail__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border: 0;
  border-radius: var(--r-sm);
  background: var(--signal);
  color: var(--signal-ink);
  transition: box-shadow 0.18s ease;
}

.rail__mark:hover { box-shadow: 0 0 20px -4px var(--signal-glow); }

.rail__id {
  display: grid;
  gap: 1px;
  min-width: 0;
  opacity: 1;
  transition: opacity 0.16s ease;
}

.rail.is-collapsed .rail__id {
  opacity: 0;
  pointer-events: none;
}

.rail__name {
  color: var(--ink-max);
  font-size: var(--fn-sm);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-tight);
  white-space: nowrap;
}

.rail__version {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--ink-faint);
  font-size: var(--fn-2xs);
  white-space: nowrap;
}

.rail__version:hover { color: var(--ink); }
.rail__version.has-update { color: var(--signal-deep); }

.rail__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--signal-deep);
}

/* ── 导航 */

.rail__nav {
  position: relative;
  display: grid;
  gap: 1px;
  padding: var(--s3) var(--s2);
}

/* 活动指示条：贴左缘的 signal 色细条 */
.rail__indicator {
  position: absolute;
  left: 0;
  top: var(--s3);
  width: 2px;
  border-radius: 0 var(--r-full) var(--r-full) 0;
  background: var(--signal);
  opacity: 0;
  pointer-events: none;
  box-shadow: 0 0 12px 0 var(--signal-glow);
}

.rail__item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--s3);
  width: 100%;
  height: 34px;
  padding: 0 var(--s3);
  border: 0;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--ink-muted);
  font-size: var(--fn-sm);
  font-weight: var(--weight-medium);
  text-align: left;
  white-space: nowrap;
  transition: background-color 0.14s ease, color 0.14s ease;
}

.rail__item:hover {
  background: var(--surface-hover);
  color: var(--ink-strong);
}

.rail__item.is-active {
  background: var(--signal-wash);
  color: var(--ink-max);
  font-weight: var(--weight-semibold);
}

.rail__item.is-small { height: 30px; font-size: var(--fn-xs); }

.rail__icon { flex-shrink: 0; }

.rail__item.is-active .rail__icon { color: var(--signal-deep); }

.rail__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 1;
  transition: opacity 0.16s ease;
}

.rail.is-collapsed .rail__label { opacity: 0; }

.rail__foot {
  display: grid;
  gap: 1px;
  margin-top: auto;
  padding: var(--s2);
  border-top: 1px solid var(--line-faint);
}

/* ───────────────────────────────────────── 主区 */

.frame {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  margin-left: var(--shell-sidebar);
  transition: margin-left 0.22s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.frame.is-wide { margin-left: var(--shell-sidebar-collapsed); }

.bar {
  position: sticky;
  top: 0;
  z-index: var(--z-sticky);
  display: flex;
  align-items: center;
  gap: var(--s4);
  height: var(--shell-header);
  padding: 0 var(--s5);
  background: color-mix(in srgb, var(--surface-page) 82%, transparent);
  backdrop-filter: blur(12px) saturate(1.4);
  border-bottom: 1px solid var(--line-faint);
}

.bar__burger { display: none; }

.bar__title {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
  flex-shrink: 0;
}

.bar__heading {
  margin: 0;
  font-size: var(--fn-lg);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-tight);
  color: var(--ink-max);
  white-space: nowrap;
}

.bar__crumb {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: var(--ink-faint);
  font-size: var(--fn-xs);
  white-space: nowrap;
}

.bar__search {
  flex: 1;
  display: flex;
  justify-content: center;
  min-width: 0;
}

.bar__field { max-width: 420px; }

.bar__kbd {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 0;
  border: 0;
  background: transparent;
}

.bar__kbd kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 17px;
  height: 16px;
  padding: 0 3px;
  border: 1px solid var(--line);
  border-radius: var(--r-xs);
  background: var(--surface-sunken);
  color: var(--ink-faint);
  font-family: var(--font-mono);
  font-size: 9px;
}

.bar__kbd:hover kbd {
  border-color: var(--signal-deep);
  color: var(--signal-deep);
}

.bar__tools {
  display: flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.bar__user { padding-inline: 5px 8px; }

.bar__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 21px;
  height: 21px;
  border-radius: var(--r-sm);
  background: var(--signal);
  color: var(--signal-ink);
  font-size: var(--fn-2xs);
  font-weight: var(--weight-bold);
}

.bar__username {
  max-width: 96px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stage {
  flex: 1;
  min-width: 0;
  width: 100%;
  max-width: var(--shell-max);
  margin: 0 auto;
  padding: var(--s5);
}

/* ───────────────────────────────────────── 搜索结果 */

.hits {
  display: grid;
  max-height: 340px;
  overflow-y: auto;
}

.hits__row {
  display: flex;
  align-items: flex-start;
  gap: var(--s3);
  width: 100%;
  padding: var(--s2) var(--s3);
  border: 0;
  border-radius: var(--r-xs);
  background: transparent;
  text-align: left;
}

.hits__row:hover { background: var(--surface-hover); }

.hits__kind {
  flex-shrink: 0;
  padding: 1px 5px;
  border-radius: var(--r-xs);
  font-size: var(--fn-2xs);
  font-weight: var(--weight-semibold);
}

.hits__kind.account { background: var(--signal-wash); color: var(--signal-deep); }
.hits__kind.log { background: var(--info-wash); color: var(--info); }

.hits__body {
  display: grid;
  gap: 1px;
  min-width: 0;
}

.hits__title {
  color: var(--ink-max);
  font-size: var(--fn-sm);
  font-weight: var(--weight-medium);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hits__desc {
  color: var(--ink-muted);
  font-size: var(--fn-xs);
}

/* ───────────────────────────────────────── 移动端 */

.tabs { display: none; }

@media (max-width: 900px) {
  .rail {
    transform: translateX(-100%);
    box-shadow: var(--lift-4);
  }

  .rail.is-mobile-open { transform: translateX(0); }

  .frame { margin-left: 0; }
  .frame.is-wide { margin-left: 0; }

  .bar__burger { display: inline-flex; }
  .bar__title { display: none; }

  .stage { padding: var(--s4) var(--s3) calc(var(--s16) + var(--s4)); }

  .tabs {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: var(--z-nav);
    display: grid;
    grid-auto-flow: column;
    background: color-mix(in srgb, var(--surface-page) 90%, transparent);
    backdrop-filter: blur(14px);
    border-top: 1px solid var(--line-faint);
    padding-bottom: env(safe-area-inset-bottom);
  }

  .tabs__item {
    display: grid;
    justify-items: center;
    gap: 2px;
    padding: 7px 2px;
    border: 0;
    background: transparent;
    color: var(--ink-faint);
    font-size: 9px;
    font-weight: var(--weight-medium);
  }

  .tabs__item.is-active { color: var(--signal-deep); }
}

@media (max-width: 620px) {
  .bar { gap: var(--s2); padding: 0 var(--s3); }
  .bar__username { display: none; }
}
</style>
