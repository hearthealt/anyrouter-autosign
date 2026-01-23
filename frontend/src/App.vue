<template>
  <n-config-provider :theme="naiveTheme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <!-- 登录页面 -->
        <template v-if="isLoginPage">
          <router-view />
        </template>

        <!-- 主布局 -->
        <div v-else class="layout">
          <!-- 移动端遮罩 -->
          <div class="mobile-overlay" :class="{ show: mobileMenuOpen }" @click="mobileMenuOpen = false"></div>

          <!-- 侧边栏 -->
          <aside class="sidebar" :class="{ collapsed, 'mobile-open': mobileMenuOpen }">
            <!-- Logo -->
            <div class="sidebar-brand" @click="$router.push('/')">
              <div class="brand-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor" opacity="0.9"/>
                  <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
              <span class="brand-text">AnyRouter</span>
            </div>

            <!-- 导航菜单 -->
            <nav class="sidebar-nav">
              <div
                v-for="item in menuItems"
                :key="item.path"
                class="nav-item"
                :class="{ active: isActive(item.path) }"
                @click="navigateTo(item.path)"
              >
                <div class="nav-indicator"></div>
                <div class="nav-icon">
                  <n-icon :size="20"><component :is="item.icon" /></n-icon>
                </div>
                <span class="nav-label">{{ item.label }}</span>
              </div>
            </nav>

            <!-- 底部操作 -->
            <div class="sidebar-footer">
              <div class="nav-item" @click="toggleTheme">
                <div class="nav-icon">
                  <n-icon :size="20">
                    <SunnyOutline v-if="currentTheme === 'dark'" />
                    <MoonOutline v-else />
                  </n-icon>
                </div>
                <span class="nav-label">{{ currentTheme === 'dark' ? '浅色' : '深色' }}</span>
              </div>
              <div class="nav-item collapse-btn" @click="collapsed = !collapsed">
                <div class="nav-icon">
                  <n-icon :size="20">
                    <ChevronBackOutline v-if="!collapsed" />
                    <ChevronForwardOutline v-else />
                  </n-icon>
                </div>
                <span class="nav-label">收起</span>
              </div>
            </div>
          </aside>

          <!-- 主区域 -->
          <div class="main" :class="{ expanded: collapsed }">
            <!-- 顶部导航栏 -->
            <header class="header">
              <!-- 移动端菜单按钮 -->
              <n-button class="mobile-menu-btn" quaternary @click="mobileMenuOpen = true">
                <template #icon><n-icon :size="22"><MenuOutline /></n-icon></template>
              </n-button>

              <!-- 面包屑导航 -->
              <div class="header-left">
                <n-breadcrumb>
                  <n-breadcrumb-item @click="$router.push('/')">
                    <n-icon><HomeOutline /></n-icon>
                  </n-breadcrumb-item>
                  <n-breadcrumb-item v-for="crumb in breadcrumbs" :key="crumb.path">
                    {{ crumb.label }}
                  </n-breadcrumb-item>
                </n-breadcrumb>
              </div>

              <!-- 全局搜索 -->
              <div class="header-center">
                <n-input
                  v-model:value="searchKeyword"
                  placeholder="搜索账号、日志..."
                  clearable
                  round
                  size="small"
                  class="global-search"
                  @keyup.enter="handleGlobalSearch"
                >
                  <template #prefix>
                    <n-icon><SearchOutline /></n-icon>
                  </template>
                </n-input>
              </div>

              <!-- 右侧操作 -->
              <div class="header-right">
                <!-- 通知中心 -->
                <n-popover trigger="click" placement="bottom-end" :width="320">
                  <template #trigger>
                    <n-badge :value="notifications.length" :max="99" :show="notifications.length > 0">
                      <n-button quaternary circle size="small">
                        <template #icon><n-icon :size="18"><NotificationsOutline /></n-icon></template>
                      </n-button>
                    </n-badge>
                  </template>
                  <div class="notification-panel">
                    <div class="notification-header">
                      <span>通知中心</span>
                      <n-button text size="tiny" @click="clearNotifications">清空</n-button>
                    </div>
                    <div class="notification-list" v-if="notifications.length > 0">
                      <div v-for="(notif, index) in notifications" :key="index" class="notification-item">
                        <div class="notif-icon" :class="notif.type">
                          <n-icon :size="14">
                            <CheckmarkCircleOutline v-if="notif.type === 'success'" />
                            <AlertCircleOutline v-else-if="notif.type === 'warning'" />
                            <CloseCircleOutline v-else-if="notif.type === 'error'" />
                            <InformationCircleOutline v-else />
                          </n-icon>
                        </div>
                        <div class="notif-content">
                          <div class="notif-title">{{ notif.title }}</div>
                          <div class="notif-time">{{ notif.time }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="notification-empty" v-else>
                      <n-icon :size="32" color="var(--text-tertiary)"><NotificationsOffOutline /></n-icon>
                      <span>暂无通知</span>
                    </div>
                  </div>
                </n-popover>

                <!-- 刷新按钮 -->
                <n-button quaternary circle size="small" @click="refreshData">
                  <template #icon><n-icon :size="18"><RefreshOutline /></n-icon></template>
                </n-button>

                <!-- 用户菜单 -->
                <n-dropdown :options="userMenuOptions" @select="handleUserMenuSelect">
                  <n-button quaternary size="small" class="user-btn">
                    <div class="user-avatar">{{ (currentUser?.username || 'A')[0].toUpperCase() }}</div>
                    <span class="user-name">{{ currentUser?.username || 'admin' }}</span>
                    <n-icon :size="14"><ChevronDownOutline /></n-icon>
                  </n-button>
                </n-dropdown>
              </div>
            </header>

            <!-- 页面操作栏 -->
            <div class="page-toolbar" v-if="showToolbar">
              <h1 class="page-title">{{ pageTitle }}</h1>
              <div class="toolbar-actions">
                <slot name="toolbar-actions"></slot>
              </div>
            </div>

            <!-- 内容区 -->
            <main class="content">
              <router-view />
            </main>

            <!-- 底部状态栏 -->
            <footer class="footer">
              <div class="footer-left">
                <span class="footer-item">
                  <n-icon :size="14"><CodeOutline /></n-icon>
                  v1.0.0
                </span>
                <span class="footer-divider">|</span>
                <span class="footer-item" :class="connectionStatus">
                  <span class="status-dot"></span>
                  {{ connectionStatus === 'connected' ? '已连接' : '未连接' }}
                </span>
              </div>
              <div class="footer-right">
                <span class="footer-item">
                  <n-icon :size="14"><TimeOutline /></n-icon>
                  最后同步: {{ lastSyncTime || '暂无' }}
                </span>
              </div>
            </footer>
          </div>

          <!-- 移动端底部导航 -->
          <nav class="mobile-tabbar">
            <div
              v-for="item in menuItems"
              :key="item.path"
              class="tabbar-item"
              :class="{ active: isActive(item.path) }"
              @click="navigateTo(item.path)"
            >
              <n-icon :size="22"><component :is="item.icon" /></n-icon>
              <span>{{ item.label }}</span>
            </div>
          </nav>
        </div>

        <!-- 修改密码弹窗 -->
        <n-modal v-model:show="showPasswordModal" :mask-closable="false">
          <div class="password-modal">
            <div class="modal-header">
              <h3>修改密码</h3>
              <n-button text @click="showPasswordModal = false">
                <n-icon :size="20"><CloseOutline /></n-icon>
              </n-button>
            </div>
            <div class="modal-body">
              <n-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules">
                <n-form-item label="原密码" path="old_password">
                  <n-input
                    v-model:value="passwordForm.old_password"
                    type="password"
                    show-password-on="click"
                    placeholder="请输入原密码"
                  />
                </n-form-item>
                <n-form-item label="新密码" path="new_password">
                  <n-input
                    v-model:value="passwordForm.new_password"
                    type="password"
                    show-password-on="click"
                    placeholder="请输入新密码（至少6位）"
                  />
                </n-form-item>
                <n-form-item label="确认密码" path="confirm_password">
                  <n-input
                    v-model:value="passwordForm.confirm_password"
                    type="password"
                    show-password-on="click"
                    placeholder="请再次输入新密码"
                  />
                </n-form-item>
              </n-form>
            </div>
            <div class="modal-footer">
              <n-button @click="showPasswordModal = false">取消</n-button>
              <n-button type="primary" @click="handleChangePassword" :loading="changingPassword">
                确认修改
              </n-button>
            </div>
          </div>
        </n-modal>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NIcon, createDiscreteApi, darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides, FormInst, FormRules } from 'naive-ui'
import {
  GridOutline,
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
  CloseOutline,
  MenuOutline,
  HomeOutline,
  SearchOutline,
  NotificationsOutline,
  NotificationsOffOutline,
  CheckmarkCircleOutline,
  AlertCircleOutline,
  CloseCircleOutline,
  InformationCircleOutline,
  CodeOutline
} from '@vicons/ionicons5'
import { authApi } from './api'
import { removeToken, isLoggedIn } from './utils/auth'
import { getActiveTheme, setThemeMode, type ThemeMode } from './utils'

const { message } = createDiscreteApi(['message'])

const route = useRoute()
const router = useRouter()
const collapsed = ref(false)
const mobileMenuOpen = ref(false)
const currentUser = ref<any>(null)
const currentTheme = ref<'light' | 'dark'>(getActiveTheme())

// 全局搜索
const searchKeyword = ref('')

// 通知中心
const notifications = ref<Array<{ type: string; title: string; time: string }>>([])

// 连接状态
const connectionStatus = ref<'connected' | 'disconnected'>('connected')
const lastSyncTime = ref<string>('')

// 修改密码
const showPasswordModal = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref<FormInst | null>(null)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule: any, value: string) => {
        return value === passwordForm.value.new_password
      },
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

// Naive UI theme
const naiveTheme = computed(() => currentTheme.value === 'dark' ? darkTheme : null)

const isLoginPage = computed(() => route.path === '/login')

const menuItems = [
  { path: '/', label: '仪表盘', icon: GridOutline },
  { path: '/logs', label: '签到日志', icon: TimeOutline },
  { path: '/statistics', label: '统计报表', icon: StatsChartOutline },
  { path: '/settings', label: '系统设置', icon: SettingsOutline },
]

const userMenuOptions = [
  {
    label: '修改密码',
    key: 'change-password',
    icon: () => h(NIcon, null, { default: () => h(LockClosedOutline) })
  },
  {
    type: 'divider',
    key: 'd1'
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOutOutline) })
  }
]

// 面包屑
const breadcrumbs = computed(() => {
  const crumbs: Array<{ path: string; label: string }> = []
  const titles: Record<string, string> = {
    '/': '仪表盘',
    '/logs': '签到日志',
    '/statistics': '统计报表',
    '/settings': '系统设置'
  }

  if (route.path === '/') {
    crumbs.push({ path: '/', label: '仪表盘' })
  } else if (route.path.startsWith('/account/')) {
    crumbs.push({ path: '/', label: '仪表盘' })
    crumbs.push({ path: route.path, label: '账号详情' })
  } else if (titles[route.path]) {
    crumbs.push({ path: route.path, label: titles[route.path] })
  }

  return crumbs
})

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/': '仪表盘',
    '/logs': '签到日志',
    '/statistics': '统计报表',
    '/settings': '系统设置'
  }
  if (route.path.startsWith('/account/')) return '账号详情'
  return titles[route.path] || '仪表盘'
})

const showToolbar = computed(() => false) // 可根据需要显示

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const navigateTo = (path: string) => {
  router.push(path)
  mobileMenuOpen.value = false
}

const refreshData = () => {
  lastSyncTime.value = new Date().toLocaleTimeString()
  window.location.reload()
}

const toggleTheme = () => {
  const newTheme: ThemeMode = currentTheme.value === 'light' ? 'dark' : 'light'
  setThemeMode(newTheme)
  currentTheme.value = newTheme
}

const handleGlobalSearch = () => {
  if (searchKeyword.value.trim()) {
    message.info(`搜索: ${searchKeyword.value}`)
    // TODO: 实现全局搜索功能
  }
}

const clearNotifications = () => {
  notifications.value = []
}

const handleUserMenuSelect = (key: string) => {
  if (key === 'logout') {
    removeToken()
    message.success('已退出登录')
    router.push('/login')
  } else if (key === 'change-password') {
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' }
    showPasswordModal.value = true
  }
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value?.validate()
  } catch {
    return
  }

  changingPassword.value = true
  try {
    await authApi.changePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password
    })
    message.success('密码修改成功，请重新登录')
    showPasswordModal.value = false
    removeToken()
    router.push('/login')
  } catch (e: any) {
    message.error(e.message || '修改失败')
  } finally {
    changingPassword.value = false
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

// 更新最后同步时间
const updateSyncTime = () => {
  lastSyncTime.value = new Date().toLocaleTimeString()
}

onMounted(() => {
  loadCurrentUser()
  updateSyncTime()

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const stored = localStorage.getItem('anyrouter-theme')
    if (!stored || stored === 'auto') {
      currentTheme.value = e.matches ? 'dark' : 'light'
    }
  })
})

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#10b981',
    primaryColorHover: '#059669',
    primaryColorPressed: '#047857',
    borderRadius: '8px'
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-color);
}

/* 侧边栏 */
.sidebar {
  width: var(--sidebar-width);
  background: var(--bg-card);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

/* Logo 区域 */
.sidebar-brand {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 var(--spacing-5);
  gap: var(--spacing-3);
  cursor: pointer;
  transition: padding 0.3s ease;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-color-light);
}

.sidebar.collapsed .sidebar-brand {
  padding: 0 var(--spacing-4);
  justify-content: center;
}

.brand-icon {
  width: 40px;
  height: 40px;
  min-width: 40px;
  background: var(--primary-gradient);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: var(--shadow-md);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.sidebar-brand:hover .brand-icon {
  transform: scale(1.05);
  box-shadow: var(--shadow-lg);
}

.brand-text {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  letter-spacing: -0.3px;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar.collapsed .brand-text {
  opacity: 0;
  pointer-events: none;
  width: 0;
}

/* 导航区域 */
.sidebar-nav {
  flex: 1;
  padding: var(--spacing-4) var(--spacing-3);
  overflow-y: auto;
  overflow-x: hidden;
  transition: padding 0.3s ease;
}

.sidebar.collapsed .sidebar-nav {
  padding: var(--spacing-4) var(--spacing-2);
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: 0 var(--spacing-4);
  height: 44px;
  border-radius: var(--radius-lg);
  cursor: pointer;
  margin-bottom: var(--spacing-1);
  color: var(--text-secondary);
  transition: background 0.2s ease, color 0.2s ease, padding 0.3s ease;
}

.sidebar.collapsed .nav-item {
  padding: 0;
  justify-content: center;
}

.nav-item:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: var(--primary-color-light);
  color: var(--primary-color);
}

/* 左侧指示器 */
.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: var(--primary-gradient);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  transition: height 0.2s ease;
}

.nav-item.active .nav-indicator {
  height: 20px;
}

.sidebar.collapsed .nav-indicator {
  display: none;
}

.nav-icon {
  width: 24px;
  height: 24px;
  min-width: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-label {
  font-size: var(--text-md);
  font-weight: var(--font-medium);
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar.collapsed .nav-label {
  opacity: 0;
  pointer-events: none;
  width: 0;
}

/* 底部区域 */
.sidebar-footer {
  padding: var(--spacing-3);
  border-top: 1px solid var(--border-color-light);
  flex-shrink: 0;
  transition: padding 0.3s ease;
}

.sidebar.collapsed .sidebar-footer {
  padding: var(--spacing-2);
}

.sidebar-footer .nav-item {
  margin-bottom: var(--spacing-1);
}

.sidebar-footer .nav-item:last-child {
  margin-bottom: 0;
}

.collapse-btn .nav-icon {
  transition: transform 0.3s ease;
}

.sidebar.collapsed .collapse-btn .nav-icon {
  transform: rotate(180deg);
}

/* 主区域 */
.main {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left 0.3s ease;
}

.main.expanded {
  margin-left: var(--sidebar-collapsed-width);
}

/* 顶部栏 */
.header {
  height: var(--header-height);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-6);
  position: sticky;
  top: 0;
  z-index: 50;
  gap: var(--spacing-4);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.header-center {
  flex: 1;
  max-width: 400px;
  margin: 0 var(--spacing-4);
}

.global-search {
  width: 100%;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

/* 用户按钮 */
.user-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-1) var(--spacing-3) !important;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  background: var(--primary-gradient);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

/* 通知面板 */
.notification-panel {
  padding: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-3);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
  cursor: pointer;
  transition: background 0.2s;
}

.notification-item:hover {
  background: var(--bg-card-hover);
}

.notification-item:last-child {
  border-bottom: none;
}

.notif-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.notif-icon.success {
  background: var(--success-color-light);
  color: var(--success-color);
}

.notif-icon.warning {
  background: var(--warning-color-light);
  color: var(--warning-color);
}

.notif-icon.error {
  background: var(--error-color-light);
  color: var(--error-color);
}

.notif-icon.info {
  background: var(--info-color-light);
  color: var(--info-color);
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: var(--text-sm);
  color: var(--text-primary);
  margin-bottom: 2px;
}

.notif-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.notification-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  gap: var(--spacing-2);
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

/* 页面工具栏 */
.page-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-6);
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color-light);
}

.page-title {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0;
}

.toolbar-actions {
  display: flex;
  gap: var(--spacing-2);
}

/* 内容区 */
.content {
  flex: 1;
  padding: var(--spacing-6);
  background: var(--bg-color);
}

/* 底部状态栏 */
.footer {
  height: 36px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-color-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--spacing-6);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.footer-left,
.footer-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.footer-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.footer-item.connected .status-dot {
  background: var(--success-color);
}

.footer-item.disconnected .status-dot {
  background: var(--error-color);
}

.footer-divider {
  color: var(--border-color);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--success-color);
}

/* 修改密码弹窗 */
.password-modal {
  width: 400px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.password-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color);
}

.password-modal .modal-header h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.password-modal .modal-body {
  padding: var(--spacing-5);
}

.password-modal .modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-5);
  border-top: 1px solid var(--border-color);
  background: var(--bg-card-hover);
}

/* 移动端遮罩 */
.mobile-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.mobile-overlay.show {
  opacity: 1;
  pointer-events: auto;
}

/* 移动端菜单按钮 */
.mobile-menu-btn {
  display: none;
  margin-right: var(--spacing-2);
}

/* 移动端底部导航 */
.mobile-tabbar {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--tabbar-height);
  background: var(--bg-card);
  border-top: 1px solid var(--border-color);
  z-index: 100;
  padding-bottom: env(safe-area-inset-bottom);
}

.tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: color 0.2s;
}

.tabbar-item.active {
  color: var(--primary-color);
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .mobile-overlay {
    display: block;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .mobile-tabbar {
    display: flex;
  }

  .sidebar {
    position: fixed;
    left: calc(-1 * var(--sidebar-width));
    width: var(--sidebar-width);
    transition: left 0.3s ease;
    z-index: 101;
  }

  .sidebar.mobile-open {
    left: 0;
  }

  .sidebar.collapsed {
    width: var(--sidebar-width);
    left: calc(-1 * var(--sidebar-width));
  }

  .sidebar.collapsed.mobile-open {
    left: 0;
  }

  .sidebar.collapsed .brand-text,
  .sidebar.collapsed .nav-label {
    opacity: 1;
    pointer-events: auto;
    width: auto;
  }

  .sidebar-footer .collapse-btn {
    display: none;
  }

  .main {
    margin-left: 0;
    padding-bottom: calc(var(--tabbar-height) + 10px);
  }

  .main.expanded {
    margin-left: 0;
  }

  .header {
    padding: 0 var(--spacing-4);
  }

  .header-center {
    display: none;
  }

  .user-name {
    display: none;
  }

  .content {
    padding: var(--spacing-4);
  }

  .footer {
    display: none;
  }
}

@media (max-width: 480px) {
  .header-left {
    display: none;
  }
}
</style>
