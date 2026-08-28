<template>
  <router-view v-if="isLoginPage" />

  <div v-else class="shell">
    <SignalField class="shell__field" :density="34" :intensity="0.62" />
    <div class="shell__aura shell__aura--one" aria-hidden="true" />
    <div class="shell__aura shell__aura--two" aria-hidden="true" />
    <div class="shell__scrim" :class="{ 'is-open': mobileMenuOpen }" @click="mobileMenuOpen = false" />

    <aside
      ref="sidebarEl"
      class="rail material-noise"
      :class="{ 'is-collapsed': collapsed, 'is-mobile-open': mobileMenuOpen }"
    >
      <div class="rail__brand">
        <button type="button" class="rail__mark" aria-label="返回总览" @click="router.push('/')">
          <Zap :size="18" :stroke-width="2.2" />
        </button>
        <div class="rail__id">
          <span class="rail__eyebrow">AUTOMATION / 01</span>
          <span class="rail__name">AnyRouter</span>
          <button
            type="button"
            class="rail__version"
            :class="{ 'has-update': versionStore.hasNewVersion }"
            :title="versionStore.hasNewVersion ? `有新版本 ${versionStore.latestTag}，点击查看` : '查看版本信息'"
            @click="showVersionModal = true"
          >
            <span class="mono">{{ versionStore.currentTag || (versionStore.loading ? 'LOADING' : 'VERSION N/A') }}</span>
            <span v-if="versionStore.hasNewVersion" class="rail__dot" aria-hidden="true" />
          </button>
        </div>
      </div>

      <div class="rail__section-label">
        <span>Navigation</span>
        <span class="mono">06</span>
      </div>

      <nav class="rail__nav" aria-label="主导航">
        <span ref="indicatorEl" class="rail__indicator" aria-hidden="true" />
        <button
          v-for="(item, index) in menuItems"
          :key="item.path"
          :ref="el => setNavRef(item.path, el as HTMLElement | null)"
          type="button"
          class="rail__item"
          :class="{ 'is-active': isActive(item.path) }"
          :aria-current="isActive(item.path) ? 'page' : undefined"
          :title="collapsed ? item.label : undefined"
          @click="navigateTo(item.path)"
        >
          <span class="rail__number mono">{{ String(index + 1).padStart(2, '0') }}</span>
          <component :is="item.icon" :size="17" :stroke-width="1.8" class="rail__icon" />
          <span class="rail__label">{{ item.label }}</span>
          <ChevronRight :size="13" class="rail__arrow" />
        </button>
      </nav>

      <div class="rail__foot">
        <div class="rail__system">
          <span class="rail__system-orbit" aria-hidden="true"><span /></span>
          <span class="rail__system-copy">
            <strong>System online</strong>
            <small class="mono">REALTIME LINK</small>
          </span>
        </div>
        <div class="rail__foot-actions">
          <button
            type="button"
            class="rail__utility"
            :aria-label="currentTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
            :title="currentTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
            @click="toggleTheme"
          >
            <component :is="currentTheme === 'dark' ? Sun : Moon" :size="16" />
            <span>{{ currentTheme === 'dark' ? 'Light' : 'Dark' }}</span>
          </button>
          <button
            type="button"
            class="rail__utility rail__collapse"
            :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
            :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
            :aria-expanded="!collapsed"
            @click="collapsed = !collapsed"
          >
            <component :is="collapsed ? PanelLeftOpen : PanelLeftClose" :size="16" />
            <span>Collapse</span>
          </button>
        </div>
      </div>
    </aside>

    <div class="frame" :class="{ 'is-wide': collapsed }">
      <header class="bar">
        <UiButton class="bar__burger" quaternary size="small" aria-label="打开导航菜单" @click="mobileMenuOpen = true">
          <template #icon><Menu :size="18" /></template>
        </UiButton>

        <div class="bar__title">
          <span class="bar__index mono">AR / CONTROL PLANE</span>
          <div class="bar__title-line">
            <h1 class="bar__heading">{{ pageTitle }}</h1>
            <span v-if="breadcrumbTail" class="bar__crumb">
              <ChevronRight :size="11" />
              {{ breadcrumbTail }}
            </span>
          </div>
        </div>

        <div class="bar__search">
          <UiPopover
            trigger="manual"
            placement="bottom"
            :show="searchResults.length > 0"
            :width="420"
            bare
            @update:show="(show: boolean) => !show && (searchResults = [])"
          >
            <template #trigger>
              <UiInput
                v-model:value="searchKeyword"
                class="bar__field"
                placeholder="搜索账号、日志或动作"
                size="small"
                clearable
                @keyup.enter="handleGlobalSearch"
              >
                <template #prefix>
                  <UiSpinner v-if="searchLoading" :size="12" />
                  <Search v-else :size="14" />
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
          <div class="bar__live"><span />LIVE</div>
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
        <component :is="item.icon" :size="18" aria-hidden="true" />
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
import SignalField from './components/layout/SignalField.vue'

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
  position: relative;
  display: flex;
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  overflow: clip;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--surface-page) 94%, var(--signal) 6%), var(--surface-page) 38%),
    var(--surface-page);
}

.shell::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.55;
  background-image:
    linear-gradient(to right, var(--grid-line) 1px, transparent 1px),
    linear-gradient(to bottom, var(--grid-line) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(to bottom right, #000 0%, transparent 72%);
}

.shell__field {
  position: fixed;
  inset: 0;
  z-index: 0;
  opacity: 0.72;
}

.shell__aura {
  position: fixed;
  z-index: 0;
  width: 34vw;
  aspect-ratio: 1;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(90px);
  opacity: 0.08;
}

.shell__aura--one { top: -18vw; right: -8vw; background: var(--signal); }
.shell__aura--two { bottom: -24vw; left: 18vw; background: var(--info); }

.shell__scrim {
  position: fixed;
  inset: 0;
  z-index: 190;
  background: color-mix(in srgb, var(--surface-inverse) 42%, transparent);
  backdrop-filter: blur(7px);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.24s ease;
}

.shell__scrim.is-open { opacity: 1; pointer-events: auto; }

.rail {
  position: fixed;
  top: 16px;
  bottom: 16px;
  left: 16px;
  z-index: var(--z-nav);
  display: flex;
  flex-direction: column;
  width: var(--shell-sidebar);
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--line) 82%, transparent);
  border-radius: 22px;
  background: color-mix(in srgb, var(--surface-sunken) 90%, transparent);
  box-shadow: var(--lift-3);
  backdrop-filter: blur(24px) saturate(1.25);
  transition: width 0.28s cubic-bezier(0.2, 0.9, 0.3, 1), transform 0.28s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.rail > * { position: relative; z-index: 2; }
.rail.is-collapsed { width: var(--shell-sidebar-collapsed); }

.rail__brand {
  display: flex;
  align-items: center;
  gap: var(--s3);
  min-height: 88px;
  padding: var(--s4);
  overflow: hidden;
  border-bottom: 1px solid var(--line-faint);
}

.rail__mark {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border: 0;
  border-radius: 13px;
  color: var(--signal-ink);
  background: var(--signal);
  box-shadow: 0 12px 30px -16px var(--signal-glow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.rail__mark::after {
  content: "";
  position: absolute;
  inset: -5px;
  border: 1px solid var(--signal-glow);
  border-radius: 17px;
  opacity: 0;
  transform: scale(0.85);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.rail__mark:hover { transform: rotate(-5deg) scale(1.04); box-shadow: 0 0 32px -8px var(--signal-glow); }
.rail__mark:hover::after { opacity: 1; transform: scale(1); }

.rail__id {
  display: grid;
  gap: 1px;
  min-width: 0;
  opacity: 1;
  transition: opacity 0.16s ease, transform 0.24s ease;
}

.rail__eyebrow,
.rail__version {
  color: var(--ink-faint);
  font-family: var(--font-mono);
  font-size: 8px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  white-space: nowrap;
}

.rail__name {
  color: var(--ink-max);
  font-size: var(--fn-lg);
  font-weight: var(--weight-bold);
  letter-spacing: var(--track-tight);
  white-space: nowrap;
}

.rail__version {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  width: max-content;
  padding: 0;
  border: 0;
  background: transparent;
}

.rail__version:hover,
.rail__version.has-update { color: var(--signal-deep); }

.rail__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--signal-deep);
  box-shadow: 0 0 9px var(--signal-glow);
}

.rail__section-label {
  display: flex;
  justify-content: space-between;
  padding: 18px 18px 8px;
  color: var(--ink-faint);
  font-size: 9px;
  font-weight: var(--weight-semibold);
  letter-spacing: 0.13em;
  text-transform: uppercase;
  white-space: nowrap;
  transition: opacity 0.16s ease;
}

.rail__nav {
  position: relative;
  display: grid;
  gap: 5px;
  padding: 0 9px;
}

.rail__indicator {
  position: absolute;
  top: 0;
  left: 4px;
  width: 3px;
  border-radius: var(--r-full);
  background: var(--signal);
  box-shadow: 0 0 18px var(--signal-glow);
  opacity: 0;
  pointer-events: none;
}

.rail__item {
  position: relative;
  display: grid;
  grid-template-columns: 24px 20px minmax(0, 1fr) 14px;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 48px;
  padding: 0 11px;
  overflow: hidden;
  border: 1px solid transparent;
  border-radius: 13px;
  color: var(--ink-muted);
  background: transparent;
  font-size: var(--fn-sm);
  font-weight: var(--weight-medium);
  text-align: left;
  white-space: nowrap;
  transition: color 0.18s ease, background-color 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.rail__item::before {
  content: "";
  position: absolute;
  inset: 0;
  opacity: 0;
  background: linear-gradient(95deg, var(--signal-wash), transparent 78%);
  transition: opacity 0.18s ease;
}

.rail__item:hover { color: var(--ink-max); transform: translateX(2px); }
.rail__item:hover::before { opacity: 0.7; }

.rail__item.is-active {
  color: var(--ink-max);
  border-color: color-mix(in srgb, var(--signal-deep) 22%, var(--line-faint));
  background: color-mix(in srgb, var(--surface-raised) 76%, transparent);
}

.rail__item.is-active::before { opacity: 1; }
.rail__item > * { position: relative; z-index: 1; }

.rail__number {
  color: var(--ink-ghost);
  font-size: 8px;
  letter-spacing: 0.06em;
}

.rail__icon { flex-shrink: 0; }
.rail__item.is-active .rail__icon { color: var(--signal-deep); }

.rail__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  opacity: 1;
  transition: opacity 0.15s ease;
}

.rail__arrow { justify-self: end; color: var(--ink-ghost); opacity: 0; transform: translateX(-4px); transition: all 0.18s ease; }
.rail__item:hover .rail__arrow,
.rail__item.is-active .rail__arrow { opacity: 1; transform: translateX(0); }

.rail__foot {
  display: grid;
  gap: 12px;
  margin-top: auto;
  padding: 14px 10px 10px;
  border-top: 1px solid var(--line-faint);
}

.rail__system {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  min-width: 0;
  border-radius: 13px;
  background: color-mix(in srgb, var(--surface-raised) 70%, transparent);
}

.rail__system-orbit {
  position: relative;
  display: grid;
  place-items: center;
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  border: 1px solid color-mix(in srgb, var(--ok) 35%, var(--line));
  border-radius: 50%;
}

.rail__system-orbit::before {
  content: "";
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--ok);
  animation: system-orbit 4s linear infinite;
  transform-origin: 0 0;
}

.rail__system-orbit span { width: 6px; height: 6px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 12px color-mix(in srgb, var(--ok) 70%, transparent); }

@keyframes system-orbit {
  from { transform: rotate(0deg) translateX(12px); }
  to { transform: rotate(360deg) translateX(12px); }
}

.rail__system-copy { display: grid; min-width: 0; white-space: nowrap; }
.rail__system-copy strong { color: var(--ink-strong); font-size: var(--fn-xs); font-weight: var(--weight-semibold); }
.rail__system-copy small { color: var(--ink-faint); font-size: 7px; letter-spacing: 0.08em; }

.rail__foot-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 5px; }
.rail__utility {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-width: 0;
  height: 34px;
  padding: 0 8px;
  overflow: hidden;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: var(--ink-muted);
  font-size: var(--fn-xs);
  white-space: nowrap;
}
.rail__utility:hover { border-color: var(--line-faint); background: var(--surface-hover); color: var(--ink-max); }

.rail.is-collapsed .rail__section-label,
.rail.is-collapsed .rail__label,
.rail.is-collapsed .rail__arrow,
.rail.is-collapsed .rail__utility span { opacity: 0; pointer-events: none; }
/* 折叠宽只有 60px，这两块必须撤出布局流：仅设 opacity 会继续占 flex 空间，
   把 logo 和状态环挤离中线（logo 42px 甚至会被 overflow 裁掉右缘） */
.rail.is-collapsed .rail__id,
.rail.is-collapsed .rail__system-copy { display: none; }
.rail.is-collapsed .rail__brand { justify-content: center; gap: 0; padding-inline: 0; }
.rail.is-collapsed .rail__nav { padding-inline: 9px; }
.rail.is-collapsed .rail__item { grid-template-columns: 0 20px 0 0; gap: 0; justify-content: center; padding: 0; }
.rail.is-collapsed .rail__number { opacity: 0; }
.rail.is-collapsed .rail__system { justify-content: center; padding-inline: 0; background: transparent; }
.rail.is-collapsed .rail__foot { padding-inline: 6px; }
.rail.is-collapsed .rail__foot-actions { grid-template-columns: 1fr; justify-items: center; }
.rail.is-collapsed .rail__utility { width: 38px; padding: 0; gap: 0; }
.rail.is-collapsed .rail__utility span { display: none; }

.frame {
  position: relative;
  z-index: 2;
  display: flex;
  flex: 1;
  flex-direction: column;
  min-width: 0;
  margin-left: calc(var(--shell-sidebar) + 32px);
  transition: margin-left 0.28s cubic-bezier(0.2, 0.9, 0.3, 1);
}

.frame.is-wide { margin-left: calc(var(--shell-sidebar-collapsed) + 32px); }

.bar {
  position: sticky;
  top: 16px;
  z-index: var(--z-sticky);
  display: grid;
  grid-template-columns: minmax(180px, auto) minmax(260px, 1fr) auto;
  align-items: center;
  gap: var(--s4);
  min-height: 70px;
  margin: 16px 18px 0 0;
  padding: 10px 13px 10px 20px;
  border: 1px solid color-mix(in srgb, var(--line) 78%, transparent);
  border-radius: 19px;
  background: color-mix(in srgb, var(--surface-page) 78%, transparent);
  box-shadow: var(--lift-2);
  backdrop-filter: blur(24px) saturate(1.35);
}

.bar__burger { display: none; }

.bar__title { display: grid; gap: 1px; min-width: 0; }
.bar__index { color: var(--ink-faint); font-size: 7px; letter-spacing: 0.13em; }
.bar__title-line { display: flex; align-items: baseline; gap: 7px; }
.bar__heading { margin: 0; font-size: var(--fn-xl); font-weight: var(--weight-bold); letter-spacing: var(--track-tight); white-space: nowrap; }
.bar__crumb { display: inline-flex; align-items: center; gap: 2px; color: var(--ink-faint); font-size: var(--fn-xs); white-space: nowrap; }

.bar__search { display: flex; justify-content: center; min-width: 0; }
.bar__field { width: min(100%, 520px); }
.bar__field :deep(.ui-input) { border-radius: 12px; background: color-mix(in srgb, var(--surface-inset) 76%, transparent); }

.bar__kbd { display: inline-flex; align-items: center; gap: 2px; padding: 0; border: 0; background: transparent; }
.bar__kbd kbd { display: inline-flex; align-items: center; justify-content: center; min-width: 18px; height: 17px; padding: 0 3px; border: 1px solid var(--line); border-radius: 4px; background: var(--surface-sunken); color: var(--ink-faint); font-family: var(--font-mono); font-size: 8px; }
.bar__kbd:hover kbd { border-color: var(--signal-deep); color: var(--signal-deep); }

.bar__tools { display: flex; align-items: center; gap: 2px; flex-shrink: 0; }
.bar__live { display: inline-flex; align-items: center; gap: 5px; margin-right: 7px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 8px; letter-spacing: 0.1em; }
.bar__live span { width: 5px; height: 5px; border-radius: 50%; background: var(--ok); box-shadow: 0 0 10px var(--ok); animation: live-pulse 2s ease-in-out infinite; }
@keyframes live-pulse { 50% { opacity: 0.35; transform: scale(0.72); } }

.bar__user { padding-inline: 5px 9px; margin-left: 4px; border: 1px solid var(--line-faint); border-radius: 11px; background: color-mix(in srgb, var(--surface-raised) 68%, transparent); }
.bar__avatar { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 8px; background: var(--signal); color: var(--signal-ink); font-size: var(--fn-2xs); font-weight: var(--weight-bold); }
.bar__username { max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.stage {
  flex: 1;
  width: 100%;
  min-width: 0;
  max-width: var(--shell-max);
  margin: 0 auto;
  padding: 26px 28px 72px 10px;
}

.hits { display: grid; max-height: 380px; overflow-y: auto; padding: 6px; }
.hits__row { display: flex; align-items: flex-start; gap: var(--s3); width: 100%; padding: 10px; border: 0; border-radius: 10px; background: transparent; text-align: left; }
.hits__row:hover { background: var(--surface-hover); }
.hits__kind { flex-shrink: 0; padding: 2px 6px; border-radius: 4px; font-size: var(--fn-2xs); font-weight: var(--weight-semibold); }
.hits__kind.account { background: var(--signal-wash); color: var(--signal-deep); }
.hits__kind.log { background: var(--info-wash); color: var(--info); }
.hits__body { display: grid; gap: 1px; min-width: 0; }
.hits__title { overflow: hidden; color: var(--ink-max); font-size: var(--fn-sm); font-weight: var(--weight-medium); text-overflow: ellipsis; white-space: nowrap; }
.hits__desc { color: var(--ink-muted); font-size: var(--fn-xs); }

.tabs { display: none; }

@media (max-width: 1120px) {
  .bar { grid-template-columns: minmax(150px, auto) 1fr auto; }
  .bar__live { display: none; }
  .bar__username { display: none; }
}

@media (max-width: 900px) {
  .rail { top: 10px; bottom: 10px; left: 10px; width: min(270px, calc(100vw - 20px)); transform: translateX(calc(-100% - 20px)); box-shadow: var(--lift-4); }
  .rail.is-mobile-open { transform: translateX(0); }
  .rail.is-collapsed { width: min(270px, calc(100vw - 20px)); }
  .rail.is-collapsed .rail__section-label,
  .rail.is-collapsed .rail__label,
  .rail.is-collapsed .rail__arrow,
  .rail.is-collapsed .rail__utility span { display: inline; opacity: 1; pointer-events: auto; }
  /* 移动端折叠态其实是全宽抽屉，这两块要恢复成各自原本的 grid（不是 inline，否则内部行会塌成一行） */
  .rail.is-collapsed .rail__id,
  .rail.is-collapsed .rail__system-copy { display: grid; opacity: 1; pointer-events: auto; }
  .rail.is-collapsed .rail__brand { justify-content: flex-start; gap: var(--s3); padding-inline: var(--s4); }
  .rail.is-collapsed .rail__item { grid-template-columns: 24px 20px minmax(0, 1fr) 14px; gap: 8px; justify-content: initial; padding: 0 11px; }
  .rail.is-collapsed .rail__number { opacity: 1; }
  .rail.is-collapsed .rail__foot { padding-inline: 10px; }
  .rail.is-collapsed .rail__foot-actions { grid-template-columns: 1fr 1fr; justify-items: stretch; }
  .rail.is-collapsed .rail__utility { width: auto; padding: 0 8px; gap: 7px; }
  .frame,
  .frame.is-wide { margin-left: 0; }
  .bar { top: 10px; grid-template-columns: auto minmax(0, 1fr) auto; min-height: 62px; margin: 10px 10px 0; padding: 8px 10px; border-radius: 16px; }
  .bar__burger { display: inline-flex; }
  .bar__title { display: none; }
  .bar__search { justify-content: stretch; }
  .bar__tools > :not(:last-child) { display: none; }
  .stage { padding: 24px 12px calc(var(--s20) + env(safe-area-inset-bottom)); }
  .tabs { position: fixed; right: 10px; bottom: 10px; left: 10px; z-index: var(--z-nav); display: grid; grid-auto-flow: column; overflow: hidden; border: 1px solid var(--line); border-radius: 17px; background: color-mix(in srgb, var(--surface-page) 88%, transparent); box-shadow: var(--lift-4); backdrop-filter: blur(20px); padding-bottom: env(safe-area-inset-bottom); }
  .tabs__item { position: relative; display: grid; justify-items: center; gap: 3px; padding: 8px 2px 7px; border: 0; background: transparent; color: var(--ink-faint); font-size: 8px; font-weight: var(--weight-medium); }
  .tabs__item::after { content: ""; position: absolute; top: 0; width: 18px; height: 2px; border-radius: 2px; background: var(--signal); opacity: 0; }
  .tabs__item.is-active { color: var(--signal-deep); }
  .tabs__item.is-active::after { opacity: 1; }
}

@media (max-width: 620px) {
  .bar { gap: 5px; }
  .bar__field :deep(input) { font-size: 11px; }
  .bar__user { padding: 0; border: 0; background: transparent; }
  .bar__username { display: none; }
}
</style>
