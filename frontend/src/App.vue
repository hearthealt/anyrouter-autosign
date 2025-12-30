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
                @click="$router.push(item.path)"
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
            <header class="header">
              <!-- 移动端菜单按钮 -->
              <n-button class="mobile-menu-btn" quaternary @click="mobileMenuOpen = true">
                <template #icon><n-icon :size="22"><MenuOutline /></n-icon></template>
              </n-button>
              <h1 class="page-title">{{ pageTitle }}</h1>
              <div class="header-actions">
                <n-button quaternary circle size="small" @click="refreshData">
                  <template #icon><n-icon :size="18"><RefreshOutline /></n-icon></template>
                </n-button>
                <n-dropdown :options="userMenuOptions" @select="handleUserMenuSelect">
                  <n-button quaternary size="small">
                    <template #icon><n-icon :size="18"><PersonCircleOutline /></n-icon></template>
                    {{ currentUser?.username || 'admin' }}
                  </n-button>
                </n-dropdown>
              </div>
            </header>
            <main class="content">
              <router-view />
            </main>
          </div>

          <!-- 移动端底部导航 -->
          <nav class="mobile-tabbar">
            <div
              v-for="item in menuItems"
              :key="item.path"
              class="tabbar-item"
              :class="{ active: isActive(item.path) }"
              @click="$router.push(item.path)"
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
  RefreshOutline,
  PersonCircleOutline,
  LockClosedOutline,
  LogOutOutline,
  SunnyOutline,
  MoonOutline,
  CloseOutline,
  MenuOutline
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
  { path: '/', label: '控制台', icon: GridOutline },
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

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    '/': '控制台',
    '/logs': '签到日志',
    '/statistics': '统计报表',
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

const toggleTheme = () => {
  const newTheme: ThemeMode = currentTheme.value === 'light' ? 'dark' : 'light'
  setThemeMode(newTheme)
  currentTheme.value = newTheme
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
    // 清除登录状态，跳转到登录页
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

// 监听系统主题变化
onMounted(() => {
  loadCurrentUser()

  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const stored = localStorage.getItem('anyrouter-theme')
    if (!stored || stored === 'auto') {
      currentTheme.value = e.matches ? 'dark' : 'light'
    }
  })
})

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
  background: var(--bg-color);
}

/* 侧边栏 */
.sidebar {
  width: 220px;
  background: var(--bg-color);
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
  width: 64px;
}

/* Logo 区域 */
.sidebar-brand {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 18px;
  gap: 12px;
  cursor: pointer;
  transition: padding 0.3s ease;
  flex-shrink: 0;
}

.sidebar.collapsed .sidebar-brand {
  padding: 0 14px;
}

.brand-icon {
  width: 36px;
  height: 36px;
  min-width: 36px;
  background: linear-gradient(135deg, #00b38a 0%, #00d4a4 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 179, 138, 0.3);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.sidebar-brand:hover .brand-icon {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 179, 138, 0.4);
}

.brand-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.3px;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar.collapsed .brand-text {
  opacity: 0;
  pointer-events: none;
}

/* 导航区域 */
.sidebar-nav {
  flex: 1;
  padding: 8px 12px;
  overflow-y: auto;
  overflow-x: hidden;
  transition: padding 0.3s ease;
}

.sidebar.collapsed .sidebar-nav {
  padding: 8px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
  height: 44px;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 4px;
  color: var(--text-secondary);
  transition: background 0.2s ease, color 0.2s ease, padding 0.3s ease;
}

.sidebar.collapsed .nav-item {
  padding: 0 10px;
}

.nav-item:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(0, 179, 138, 0.1);
  color: #00b38a;
}

/* 左侧指示器 */
.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: linear-gradient(180deg, #00b38a 0%, #00d4a4 100%);
  border-radius: 0 2px 2px 0;
  transition: height 0.2s ease;
}

.nav-item.active .nav-indicator {
  height: 20px;
}

.sidebar.collapsed .nav-indicator {
  opacity: 0;
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
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.2s ease;
}

.sidebar.collapsed .nav-label {
  opacity: 0;
  pointer-events: none;
}

/* 底部区域 */
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
  transition: padding 0.3s ease;
}

.sidebar.collapsed .sidebar-footer {
  padding: 8px;
}

.sidebar-footer .nav-item {
  margin-bottom: 4px;
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
  margin-left: 220px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  transition: margin-left 0.3s ease;
}

.main.expanded {
  margin-left: 64px;
}

/* 顶部栏 */
.header {
  height: 60px;
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 内容区 */
.content {
  flex: 1;
  padding: 24px;
}

/* 修改密码弹窗 */
.password-modal {
  width: 400px;
  background: var(--bg-card);
  border-radius: 12px;
  overflow: hidden;
}

.password-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.password-modal .modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.password-modal .modal-body {
  padding: 20px;
}

.password-modal .modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
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
  margin-right: 8px;
}

/* 移动端底部导航 */
.mobile-tabbar {
  display: none;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
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
  font-size: 11px;
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
    left: -220px;
    width: 220px;
    transition: left 0.3s ease;
    z-index: 101;
  }

  .sidebar.mobile-open {
    left: 0;
  }

  .sidebar.collapsed {
    width: 220px;
    left: -220px;
  }

  .sidebar.collapsed.mobile-open {
    left: 0;
  }

  .sidebar.collapsed .brand-text,
  .sidebar.collapsed .nav-label {
    opacity: 1;
    pointer-events: auto;
  }

  .sidebar-footer .collapse-btn {
    display: none;
  }

  .main {
    margin-left: 0;
    padding-bottom: 70px;
  }

  .main.expanded {
    margin-left: 0;
  }

  .header {
    padding: 0 16px;
  }

  .page-title {
    font-size: 16px;
  }

  .content {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .header-actions .n-button:not(.mobile-menu-btn) {
    display: none;
  }

  .header-actions .n-dropdown {
    display: block;
  }
}
</style>
