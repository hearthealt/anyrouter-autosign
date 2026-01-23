# AnyRouter 前端优化方案

> 基于当前代码库分析的系统性前端优化建议

## 一、项目现状分析

### 1.1 技术栈
- **框架**: Vue 3.4 + TypeScript 5.6
- **UI库**: Naive UI 2.37
- **构建工具**: Vite 6.0
- **状态管理**: Pinia 2.1
- **路由**: Vue Router 4.2
- **图表**: ECharts 6.0
- **HTTP**: Axios 1.6

### 1.2 主要问题

| 类别 | 问题 | 位置 | 严重程度 |
|------|------|------|----------|
| **性能** | 路由组件静态导入，首屏加载全部代码 | `router/index.ts` | 🔴 高 |
| **性能** | Dashboard.vue 超过1300行，组件过大 | `views/Dashboard.vue` | 🔴 高 |
| **性能** | Settings.vue 超过2300行，维护困难 | `views/Settings.vue` | 🔴 高 |
| **性能** | 长列表未使用虚拟滚动 | 账号列表、日志列表 | 🟡 中 |
| **质量** | 大量使用 `any` 类型，类型安全性差 | 所有视图组件 | 🟡 中 |
| **质量** | 状态分散，重复请求 | 各组件独立管理 | 🟡 中 |
| **体验** | 缺少骨架屏，加载体验一般 | 各页面 | 🟢 低 |
| **体验** | 移动端底部导航功能有限 | 移动端适配 | 🟢 低 |
| **安全** | `v-html` 使用未做过滤 | 潜在位置 | 🟡 中 |

---

## 二、性能优化

### 2.1 代码分割与懒加载

#### 路由级懒加载
**现状**: 所有路由组件都是静态导入
```typescript
// ❌ 当前写法
import Dashboard from '../views/Dashboard.vue'
import Settings from '../views/Settings.vue'
```

**优化**: 使用动态导入
```typescript
// ✅ 优化后
const Dashboard = () => import('../views/Dashboard.vue')
const Settings = () => import('../views/Settings.vue')
const AccountDetail = () => import('../views/AccountDetail.vue')
const SignLogs = () => import('../views/SignLogs.vue')
const Statistics = () => import('../views/Statistics.vue')
```

**收益**: 首屏加载体积减少约 40-50%

#### 组件级懒加载
**现状**: Dashboard.vue 中的图表组件静态导入
```typescript
// ❌ 当前写法
import { TrendChart, QuotaPieChart, AccountModal } from '../components/dashboard'
```

**优化**: 使用 `defineAsyncComponent`
```typescript
// ✅ 优化后
import { defineAsyncComponent } from 'vue'

const TrendChart = defineAsyncComponent(() =>
  import('../components/dashboard/TrendChart.vue')
)
const QuotaPieChart = defineAsyncComponent(() =>
  import('../components/dashboard/QuotaPieChart.vue')
)
const AccountModal = defineAsyncComponent(() =>
  import('../components/dashboard/AccountModal.vue')
)

// 添加加载状态
const AsyncChart = defineAsyncComponent({
  loader: () => import('../components/dashboard/TrendChart.vue'),
  loadingComponent: LoadingSpinner,
  delay: 200,
  timeout: 3000
})
```

### 2.2 虚拟滚动

**适用场景**: 账号列表、签到日志、审计日志等长列表

**实现方案**:
```bash
npm install vue-virtual-scroller
```

```vue
<!-- AccountList.vue -->
<template>
  <RecycleScroller
    class="scroller"
    :items="accounts"
    :item-size="60"
    key-field="id"
    v-slot="{ item }"
  >
    <div class="account-item">
      {{ item.username }}
    </div>
  </RecycleScroller>
</template>

<script setup>
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'
</script>

<style scoped>
.scroller {
  height: 500px;
}
</style>
```

**收益**: 1000 条数据渲染时间从 500ms 降至 50ms

### 2.3 图表优化

**现状**: ECharts 图表每次渲染都创建新实例

**优化**: 复用图表实例
```typescript
// composables/useChart.ts
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

export function useChart(containerRef: Ref<HTMLElement>) {
  let chartInstance: echarts.ECharts | null = null

  const initChart = () => {
    if (!containerRef.value) return
    chartInstance = echarts.init(containerRef.value)
  }

  const updateChart = (option: echarts.EChartsOption) => {
    if (chartInstance) {
      chartInstance.setOption(option, true) // true 表示不合并
    }
  }

  const resizeChart = () => {
    chartInstance?.resize()
  }

  onMounted(() => {
    initChart()
    window.addEventListener('resize', resizeChart)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', resizeChart)
    chartInstance?.dispose()
  })

  return { updateChart, resizeChart }
}
```

### 2.4 请求优化

#### 请求缓存
```typescript
// utils/requestCache.ts
const cache = new Map<string, { data: any; timestamp: number }>()
const CACHE_TTL = 5 * 60 * 1000 // 5分钟

export async function cachedRequest<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = CACHE_TTL
): Promise<T> {
  const cached = cache.get(key)
  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data
  }

  const data = await fetcher()
  cache.set(key, { data, timestamp: Date.now() })
  return data
}

// 使用示例
const loadAccountInfo = async (accountId: number) => {
  return cachedRequest(
    `account:${accountId}:info`,
    () => accountApi.getCachedInfo(accountId)
  )
}
```

#### 请求去重
```typescript
// utils/requestDedup.ts
const pendingRequests = new Map<string, Promise<any>>()

export async function dedupedRequest<T>(
  key: string,
  fetcher: () => Promise<T>
): Promise<T> {
  if (pendingRequests.has(key)) {
    return pendingRequests.get(key)!
  }

  const promise = fetcher().finally(() => {
    pendingRequests.delete(key)
  })

  pendingRequests.set(key, promise)
  return promise
}
```

---

## 三、代码质量优化

### 3.1 TypeScript 类型完善

**现状**: 大量使用 `any` 类型

**优化**: 定义完整的接口类型
```typescript
// types/account.ts
export interface Account {
  id: number
  username: string
  display_name?: string
  anyrouter_user_id?: string
  is_active: boolean
  health_status: 'healthy' | 'unhealthy' | 'unknown'
  quota: number
  used_quota: number
  quota_display: string
  group_id?: number
  group?: AccountGroup
  last_sign?: SignRecord
  created_at: string
  updated_at: string
}

export interface AccountGroup {
  id: number
  name: string
  description?: string
  color: string
  account_count: number
}

export interface SignRecord {
  time: string
  success: boolean
  reward_quota?: number
  message?: string
}

// types/dashboard.ts
export interface DashboardData {
  account_count: number
  unhealthy_account_count: number
  today_sign_count: number
  today_sign_success: number
  success_rate: number
  month_reward: number
  month_reward_display: string
  total_quota: number
  total_quota_display: string
  daily_trend: DailyTrendItem[]
}

export interface DailyTrendItem {
  date: string
  success_count: number
  fail_count: number
  reward: number
}
```

### 3.2 组件拆分

#### Dashboard.vue 拆分
```
src/views/Dashboard/
├── index.vue                    # 主容器 (~200行)
└── components/
    ├── QuickActions.vue         # 快捷操作栏 (~100行)
    ├── StatCards.vue            # 统计卡片组 (~150行)
    ├── SignTrendChart.vue       # 签到趋势图 (~100行)
    ├── QuotaPieChart.vue        # 额度分布图 (~80行)
    ├── AccountStatus.vue        # 账号状态列表 (~200行)
    ├── AccountQuickList.vue     # 账号快速列表 (~150行)
    ├── ActivityTimeline.vue     # 活动时间线 (~100行)
    └── EndpointsCard.vue        # API节点卡片 (~100行)
```

#### Settings.vue 拆分
```
src/views/Settings/
├── index.vue                    # 主容器 (~150行)
└── components/
    ├── BasicSettings.vue        # 基础设置 (~200行)
    ├── NotifyChannels.vue       # 推送渠道 (~300行)
    ├── DataBackup.vue           # 数据备份 (~200行)
    ├── GroupManagement.vue      # 分组管理 (~150行)
    ├── AuditLogs.vue            # 审计日志 (~200行)
    └── SystemLogs.vue           # 系统日志 (~200行)
```

### 3.3 组合式函数复用

**已存在的 composables**:
- `useSign` - 签到操作
- `useHealthCheck` - 健康检查
- `useTheme` - 主题切换
- `useClipboard` - 剪贴板操作
- `useFormat` - 格式化工具

**建议新增**:
```typescript
// composables/usePagination.ts
export function usePagination(fetchData: (page: number, size: number) => Promise<any>) {
  const page = ref(1)
  const pageSize = ref(20)
  const total = ref(0)
  const loading = ref(false)

  const loadData = async () => {
    loading.value = true
    try {
      const result = await fetchData(page.value, pageSize.value)
      total.value = result.total
      return result.items
    } finally {
      loading.value = false
    }
  }

  const handlePageChange = (newPage: number) => {
    page.value = newPage
    loadData()
  }

  return { page, pageSize, total, loading, loadData, handlePageChange }
}

// composables/useTable.ts
export function useTable<T>(columns: any[], fetchData: Function) {
  const data = ref<T[]>([])
  const { page, pageSize, total, loading, loadData, handlePageChange } = usePagination(fetchData)

  const refresh = () => {
    page.value = 1
    loadData()
  }

  return {
    data,
    columns,
    pagination: { page, pageSize, total },
    loading,
    refresh,
    handlePageChange
  }
}

// composables/useModal.ts
export function useModal() {
  const visible = ref(false)
  const loading = ref(false)

  const open = () => {
    visible.value = true
  }

  const close = () => {
    visible.value = false
  }

  return { visible, loading, open, close }
}
```

---

## 四、状态管理优化

### 4.1 Pinia Store 完善

**现状**: 已创建 stores 但未充分利用

**优化**: 完善各 Store
```typescript
// stores/account.ts
export const useAccountStore = defineStore('account', {
  state: () => ({
    accounts: [] as Account[],
    loading: false,
    selectedIds: [] as number[],
    filters: {
      status: 'all' as 'all' | 'healthy' | 'unhealthy' | 'pending' | 'disabled',
      groupId: null as number | null,
      keyword: ''
    }
  }),

  getters: {
    healthyAccounts: (state) =>
      state.accounts.filter(a => a.is_active && a.health_status === 'healthy'),
    unhealthyAccounts: (state) =>
      state.accounts.filter(a => a.is_active && a.health_status === 'unhealthy'),
    pendingAccounts: (state) =>
      state.accounts.filter(a => a.is_active && (!a.last_sign || !isToday(a.last_sign.time))),
    disabledAccounts: (state) =>
      state.accounts.filter(a => !a.is_active),

    filteredAccounts: (state): Account[] => {
      let result = state.accounts

      // 状态过滤
      if (state.filters.status !== 'all') {
        if (state.filters.status === 'pending') {
          result = result.filter(a =>
            a.is_active && (!a.last_sign || !isToday(a.last_sign.time))
          )
        } else if (state.filters.status === 'disabled') {
          result = result.filter(a => !a.is_active)
        } else {
          result = result.filter(a =>
            a.is_active && a.health_status === state.filters.status
          )
        }
      }

      // 分组过滤
      if (state.filters.groupId !== null) {
        result = result.filter(a => a.group_id === state.filters.groupId)
      }

      // 关键词过滤
      if (state.filters.keyword) {
        const keyword = state.filters.keyword.toLowerCase()
        result = result.filter(a =>
          a.username?.toLowerCase().includes(keyword) ||
          a.display_name?.toLowerCase().includes(keyword)
        )
      }

      return result
    },

    totalQuota: (state) =>
      state.accounts.reduce((sum, a) => sum + (a.quota || 0), 0),

    activeCount: (state) =>
      state.accounts.filter(a => a.is_active).length
  },

  actions: {
    async fetchAccounts() {
      this.loading = true
      try {
        const { data } = await accountApi.getList()
        this.accounts = data || []
      } catch (error) {
        console.error('Failed to fetch accounts:', error)
      } finally {
        this.loading = false
      }
    },

    async addAccount(account: Omit<Account, 'id'>) {
      const { data } = await accountApi.create(account)
      this.accounts.push(data)
      return data
    },

    async updateAccount(id: number, data: Partial<Account>) {
      await accountApi.update(id, data)
      const index = this.accounts.findIndex(a => a.id === id)
      if (index !== -1) {
        this.accounts[index] = { ...this.accounts[index], ...data }
      }
    },

    async deleteAccount(id: number) {
      await accountApi.delete(id)
      this.accounts = this.accounts.filter(a => a.id !== id)
    },

    async batchSign(accountIds?: number[]) {
      const ids = accountIds || this.selectedIds
      const { data } = await signApi.batchSign()
      // 刷新数据
      await this.fetchAccounts()
      return data
    },

    setFilter(filter: Partial<typeof this.filters>) {
      Object.assign(this.filters, filter)
    },

    toggleSelection(id: number) {
      const index = this.selectedIds.indexOf(id)
      if (index === -1) {
        this.selectedIds.push(id)
      } else {
        this.selectedIds.splice(index, 1)
      }
    },

    selectAll() {
      this.selectedIds = this.filteredAccounts.map(a => a.id)
    },

    clearSelection() {
      this.selectedIds = []
    }
  }
})

// stores/dashboard.ts
export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    data: null as DashboardData | null,
    loading: false,
    lastUpdate: null as Date | null
  }),

  actions: {
    async fetchDashboard() {
      this.loading = true
      try {
        const { data } = await dashboardApi.get()
        this.data = data
        this.lastUpdate = new Date()
      } catch (error) {
        console.error('Failed to fetch dashboard:', error)
      } finally {
        this.loading = false
      }
    }
  }
})

// stores/notify.ts
export const useNotifyStore = defineStore('notify', {
  state: () => ({
    channels: [] as NotifyChannel[],
    loading: false
  }),

  getters: {
    enabledChannels: (state) =>
      state.channels.filter(c => c.is_enabled),

    getChannelById: (state) => (id: number) =>
      state.channels.find(c => c.id === id)
  },

  actions: {
    async fetchChannels() {
      this.loading = true
      try {
        const { data } = await notifyApi.getChannels()
        this.channels = data || []
      } catch (error) {
        console.error('Failed to fetch channels:', error)
      } finally {
        this.loading = false
      }
    },

    async createChannel(channel: Omit<NotifyChannel, 'id'>) {
      const { data } = await notifyApi.createChannel(channel)
      this.channels.push(data)
      return data
    },

    async updateChannel(id: number, data: Partial<NotifyChannel>) {
      await notifyApi.updateChannel(id, data)
      const index = this.channels.findIndex(c => c.id === id)
      if (index !== -1) {
        this.channels[index] = { ...this.channels[index], ...data }
      }
    },

    async deleteChannel(id: number) {
      await notifyApi.deleteChannel(id)
      this.channels = this.channels.filter(c => c.id !== id)
    }
  }
})
```

### 4.2 持久化配置

```typescript
// stores/index.ts
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

export default pinia

// 使用示例
export const useThemeStore = defineStore('theme', {
  state: () => ({
    mode: 'light' as 'light' | 'dark' | 'auto',
    primaryColor: '#10b981'
  }),

  persist: {
    key: 'anyrouter-theme',
    storage: localStorage
  }
})
```

---

## 五、构建优化

### 5.1 Vite 配置优化

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    vue(),
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true
    })
  ],

  build: {
    target: 'es2015',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },

    rollupOptions: {
      output: {
        manualChunks: {
          // Vue 核心库
          'vue-vendor': ['vue', 'vue-router', 'pinia'],

          // UI 库
          'naive-ui': ['naive-ui', '@vicons/ionicons5'],

          // 图表库
          'echarts': ['echarts'],

          // 工具库
          'axios-vendor': ['axios']
        }
      }
    },

    chunkSizeWarningLimit: 1000
  },

  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### 5.2 资源压缩

```bash
npm install vite-plugin-compression -D
```

```typescript
// vite.config.ts
import viteCompression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    vue(),
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 10240,
      deleteOriginFile: false
    }),
    viteCompression({
      algorithm: 'brotliCompress',
      ext: '.br',
      threshold: 10240,
      deleteOriginFile: false
    })
  ]
})
```

### 5.3 图片优化

- 使用 SVG Sprite 替代内联 SVG
- 使用 `vite-plugin-svg-icons` 统一管理图标

```bash
npm install vite-plugin-svg-icons -D
```

```typescript
// vite.config.ts
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
import path from 'path'

export default defineConfig({
  plugins: [
    createSvgIconsPlugin({
      iconDirs: [path.resolve(process.cwd(), 'src/assets/icons')],
      symbolId: 'icon-[dir]-[name]'
    })
  ]
})
```

---

## 六、用户体验优化

### 6.1 骨架屏

```vue
<!-- components/common/SkeletonCard.vue -->
<template>
  <div class="skeleton-card">
    <n-skeleton height="24px" width="40%" style="margin-bottom: 12px" />
    <n-skeleton height="40px" width="100%" style="margin-bottom: 16px" />
    <n-space vertical>
      <n-skeleton height="20px" width="80%" />
      <n-skeleton height="20px" width="60%" />
    </n-space>
  </div>
</template>

<style scoped>
.skeleton-card {
  padding: 20px;
  border-radius: 12px;
  background: var(--bg-card);
}
</style>
```

### 6.2 错误边界

```vue
<!-- components/common/ErrorBoundary.vue -->
<template>
  <slot v-if="!error" />
  <div v-else class="error-boundary">
    <n-result status="error" title="出错了" :description="error.message">
      <template #footer>
        <n-button @click="reset">重试</n-button>
      </template>
    </n-result>
  </div>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'

const error = ref(null)

onErrorCaptured((err) => {
  error.value = err
  // 阻止错误继续向上传播
  return false
})

const reset = () => {
  error.value = null
}
</script>
```

### 6.3 加载状态

```typescript
// composables/useLoading.ts
export function useLoading() {
  const loading = ref(false)

  const withLoading = async <T>(fn: () => Promise<T>): Promise<T> => {
    loading.value = true
    try {
      return await fn()
    } finally {
      loading.value = false
    }
  }

  return { loading, withLoading }
}

// 使用示例
const { loading, withLoading } = useLoading()

const loadData = () => withLoading(async () => {
  const data = await api.getData()
  return data
})
```

### 6.4 离线支持 (PWA)

```bash
npm install vite-plugin-pwa -D
```

```typescript
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg'],
      manifest: {
        name: 'AnyRouter 自动签到',
        short_name: 'AnyRouter',
        description: '多账号自动签到管理平台',
        theme_color: '#10b981',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
    })
  ]
})
```

---

## 七、样式优化

### 7.1 CSS 变量完善

```css
/* styles/variables.css */
:root {
  /* 品牌色 */
  --color-primary: #10b981;
  --color-primary-hover: #059669;
  --color-primary-active: #047857;
  --color-primary-light: #d1fae5;

  /* 语义色 */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;

  /* 中性色 - 亮色主题 */
  --color-bg: #f8fafc;
  --color-bg-elevated: #ffffff;
  --color-bg-hover: #f1f5f9;
  --color-bg-active: #e2e8f0;

  --color-text-primary: #0f172a;
  --color-text-secondary: #475569;
  --color-text-tertiary: #94a3b8;
  --color-text-disabled: #cbd5e1;

  --color-border: #e2e8f0;
  --color-border-hover: #cbd5e1;

  /* 阴影 */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);

  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-2xl: 24px;
  --radius-full: 9999px;

  /* 间距 */
  --space-0: 0;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* 字体 */
  --font-size-xs: 11px;
  --font-size-sm: 12px;
  --font-size-base: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-size-3xl: 30px;

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* 过渡 */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

  /* 布局 */
  --sidebar-width: 240px;
  --sidebar-collapsed-width: 72px;
  --header-height: 64px;
}

/* 深色主题 */
[data-theme='dark'] {
  --color-bg: #0f172a;
  --color-bg-elevated: #1e293b;
  --color-bg-hover: #334155;
  --color-bg-active: #475569;

  --color-text-primary: #f1f5f9;
  --color-text-secondary: #cbd5e1;
  --color-text-tertiary: #94a3b8;
  --color-text-disabled: #64748b;

  --color-border: #334155;
  --color-border-hover: #475569;

  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
}
```

### 7.2 组件样式规范

```css
/* styles/components.css */
/* 卡片 */
.card {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition-normal);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

/* 按钮 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn:active {
  transform: scale(0.98);
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
}

/* 输入框 */
.input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-base);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-elevated);
  color: var(--color-text-primary);
  transition: border-color var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* 表格 */
.table {
  width: 100%;
  border-collapse: collapse;
}

.table th {
  position: sticky;
  top: 0;
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-align: left;
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
}

.table td {
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-base);
  border-bottom: 1px solid var(--color-border);
}

.table tr:hover {
  background: var(--color-bg-hover);
}
```

---

## 八、安全性优化

### 8.1 XSS 防护

```bash
npm install dompurify
```

```typescript
// utils/sanitize.ts
import DOMPurify from 'dompurify'

export function sanitizeHTML(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'span'],
    ALLOWED_ATTR: ['href', 'title', 'target']
  })
}

// 使用示例
const safeHTML = computed(() => sanitizeHTML(props.content))
```

### 8.2 CSP 配置

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'vite-plugin-csp',
      transformIndexHtml(html) {
        const csp = [
          "default-src 'self'",
          "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
          "style-src 'self' 'unsafe-inline'",
          "img-src 'self' data: https:",
          "font-src 'self' data:",
          "connect-src 'self' https://anyrouter.top"
        ].join('; ')

        return html.replace(
          '<head>',
          `<head><meta http-equiv="Content-Security-Policy" content="${csp}">`
        )
      }
    }
  ]
})
```

---

## 九、监控与调试

### 9.1 错误监控

```bash
npm install @sentry/vue
```

```typescript
// main.ts
import * as Sentry from '@sentry/vue'

const app = createApp(App)

if (import.meta.env.PROD) {
  Sentry.init({
    app,
    dsn: 'YOUR_SENTRY_DSN',
    environment: import.meta.env.MODE,
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    integrations: [
      new Sentry.BrowserTracing(),
      new Sentry.Replay()
    ]
  })
}
```

### 9.2 性能监控

```typescript
// utils/performance.ts
export function measurePerformance(name: string, fn: () => void) {
  if (import.meta.env.DEV) {
    const start = performance.now()
    fn()
    const end = performance.now()
    console.log(`[Performance] ${name}: ${(end - start).toFixed(2)}ms`)
  } else {
    fn()
  }
}

// 使用示例
measurePerformance('loadDashboard', () => {
  loadDashboard()
})
```

---

## 十、实施计划

### 第一阶段：基础优化（1周）
- [ ] 路由级懒加载
- [ ] 组件拆分（Dashboard.vue、Settings.vue）
- [ ] TypeScript 类型完善
- [ ] 组合式函数扩展

### 第二阶段：性能优化（1周）
- [ ] 虚拟滚动集成
- [ ] 请求缓存与去重
- [ ] 图表实例复用
- [ ] Vite 构建优化

### 第三阶段：状态管理（1周）
- [ ] Pinia Store 完善
- [ ] 状态持久化
- [ ] 统一错误处理

### 第四阶段：体验优化（1周）
- [ ] 骨架屏加载
- [ ] 错误边界
- [ ] 样式系统统一
- [ ] PWA 支持

### 第五阶段：安全与监控（可选）
- [ ] XSS 防护
- [ ] CSP 配置
- [ ] 错误监控
- [ ] 性能监控

---

## 十一、预期收益

| 优化项 | 预期收益 |
|--------|----------|
| 路由懒加载 | 首屏加载时间减少 40-50% |
| 组件拆分 | 代码可维护性提升，开发效率提升 30% |
| 虚拟滚动 | 长列表渲染性能提升 10 倍 |
| 请求缓存 | API 请求减少 50% |
| Pinia Store | 状态管理统一，数据一致性提升 |
| TypeScript 类型 | 减少 80% 的类型错误 |
| 构建优化 | 打包体积减少 20-30% |
| PWA 支持 | 支持离线访问，移动端体验提升 |

---

## 十二、参考资源

- [Vue 3 官方文档](https://vuejs.org/)
- [Vite 官方文档](https://vitejs.dev/)
- [Pinia 官方文档](https://pinia.vuejs.org/)
- [Naive UI 官方文档](https://www.naiveui.com/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [Web Vitals](https://web.dev/vitals/)