<template>
  <n-modal :show="show" @update:show="(val: boolean) => emit('update:show', val)">
    <div class="command-palette">
      <div class="cp-search">
        <n-icon :size="16"><SearchOutline /></n-icon>
        <input
          ref="inputRef"
          v-model="keyword"
          class="cp-input"
          placeholder="搜索账号、平台、日志... 或输入动作"
          @keydown.down.prevent="moveSelection(1)"
          @keydown.up.prevent="moveSelection(-1)"
          @keydown.enter.prevent="handleEnter"
          @keydown.esc.prevent="close"
        />
        <div class="cp-hints">
          <kbd class="cp-kbd">↑</kbd>
          <kbd class="cp-kbd">↓</kbd>
          <kbd class="cp-kbd">↵</kbd>
          <kbd class="cp-kbd">ESC</kbd>
        </div>
      </div>
      <div class="cp-body">
        <div class="cp-section" v-if="commandItems.length > 0">
          <div class="cp-section-title">{{ keyword.trim() ? '匹配结果' : '快捷动作' }}</div>
          <button
            v-for="(item, index) in commandItems"
            :key="item.id"
            type="button"
            class="cp-item"
            :class="{ active: index === selectionIndex }"
            @mouseenter="selectionIndex = index"
            @click="executeCommandItem(item)"
          >
            <span class="cp-item-icon" :class="item.kind">
              <n-icon :size="14"><component :is="item.icon" /></n-icon>
            </span>
            <div class="cp-item-body">
              <div class="cp-item-top">
                <span class="cp-item-title">{{ item.title }}</span>
                <span class="cp-item-kind">{{ getKindLabel(item.kind) }}</span>
              </div>
              <div class="cp-item-desc">{{ item.subtitle }}</div>
            </div>
          </button>
        </div>
        <div v-else-if="loading && keyword.trim()" class="cp-state">
          正在加载账号、平台和日志索引...
        </div>
        <div v-else class="cp-empty">
          {{ keyword.trim() ? '没有匹配结果，试试用户名、平台名或日志关键字' : '输入关键词搜索账号、平台或签到日志' }}
        </div>
      </div>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, type Component } from 'vue'
import { useRouter } from 'vue-router'
import {
  AddOutline, FlashOutline, GridOutline, PeopleOutline, PulseOutline,
  SettingsOutline, TimeOutline, RefreshOutline, SearchOutline, ServerOutline
} from '@vicons/ionicons5'
import { accountApi, platformApi, signApi } from '../../api'
import type { Account, Platform, SignLog } from '../../types'
import { apiError } from '../../utils/apiError'

type CommandActionId =
  | 'refresh' | 'add-account' | 'batch-sign' | 'health-check-all'
  | 'open-dashboard' | 'open-logs' | 'open-platforms' | 'open-settings'

type CommandItemKind = 'action' | 'account' | 'platform' | 'log'

interface CommandActionItem {
  id: string
  title: string
  subtitle: string
  icon: Component
  actionId: CommandActionId
  keywords: string[]
}

interface CommandItem {
  id: string
  kind: CommandItemKind
  title: string
  subtitle: string
  icon: Component
  score: number
  actionId?: CommandActionId
  accountId?: number
  success?: boolean
  logDate?: string
}

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'request-refresh'): void
}>()

const router = useRouter()

const keyword = ref('')
const inputRef = ref<HTMLInputElement | null>(null)
const loading = ref(false)
const selectionIndex = ref(0)
const cpAccounts = ref<Account[]>([])
const cpPlatforms = ref<Platform[]>([])
const cpLogs = ref<SignLog[]>([])

const normalizeText = (value: string) => value.trim().toLowerCase()

const scoreText = (kw: string, rawValue: string) => {
  const value = normalizeText(rawValue)
  if (!kw || !value) return 0
  if (value === kw) return 120
  if (value.startsWith(kw)) return 90

  const index = value.indexOf(kw)
  if (index >= 0) return Math.max(50, 76 - index)

  let matchedIndex = 0
  for (const char of value) {
    if (char === kw[matchedIndex]) {
      matchedIndex += 1
      if (matchedIndex === kw.length) {
        return Math.max(24, 48 - Math.max(0, value.length - kw.length))
      }
    }
  }
  return 0
}

const scoreTerms = (kw: string, terms: Array<string | number | undefined | null>) =>
  terms.reduce<number>((best, term) => Math.max(best, scoreText(kw, String(term ?? ''))), 0)

const buildLocalDateParam = (value: string) => {
  const date = new Date(value)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const actionCatalog: CommandActionItem[] = [
  { id: 'refresh', title: '刷新当前视图', subtitle: '重新请求当前页面数据', icon: RefreshOutline, actionId: 'refresh', keywords: ['refresh', 'reload', '刷新', '重新加载'] },
  { id: 'add-account', title: '添加账号', subtitle: '跳转到账号页继续新增', icon: AddOutline, actionId: 'add-account', keywords: ['add account', 'account', '账号', '添加'] },
  { id: 'batch-sign', title: '一键签到', subtitle: '对全部启用账号执行签到', icon: FlashOutline, actionId: 'batch-sign', keywords: ['sign', 'batch sign', '签到', '一键'] },
  { id: 'health-check-all', title: '批量健康检查', subtitle: '检查全部账号的当前凭证状态', icon: PulseOutline, actionId: 'health-check-all', keywords: ['health', 'check', '健康检查', '健康'] },
  { id: 'open-dashboard', title: '打开仪表盘', subtitle: '跳转到首页概览', icon: GridOutline, actionId: 'open-dashboard', keywords: ['dashboard', 'home', '仪表盘', '首页'] },
  { id: 'open-logs', title: '打开签到日志', subtitle: '查看全局签到记录', icon: TimeOutline, actionId: 'open-logs', keywords: ['logs', 'history', '日志', '签到记录'] },
  { id: 'open-platforms', title: '打开平台页', subtitle: '查看平台 Base URL 和接口配置', icon: ServerOutline, actionId: 'open-platforms', keywords: ['platform', '平台', 'base url'] },
  { id: 'open-settings', title: '打开设置页', subtitle: '查看调度与推送配置', icon: SettingsOutline, actionId: 'open-settings', keywords: ['settings', 'config', '设置', '配置'] }
]

const commandItems = computed<CommandItem[]>(() => {
  const kw = normalizeText(keyword.value)
  const items: CommandItem[] = []

  actionCatalog.forEach((action, index) => {
    const score = kw
      ? scoreTerms(kw, [action.title, action.subtitle, ...action.keywords])
      : 200 - index
    if (!kw || score > 0) {
      items.push({
        id: action.id, kind: 'action', title: action.title, subtitle: action.subtitle,
        icon: action.icon, score, actionId: action.actionId
      })
    }
  })

  if (!kw) return items

  cpAccounts.value.forEach(account => {
    const score = scoreTerms(kw, [
      account.username, account.display_name, account.note,
      account.platform?.name, account.anyrouter_user_id
    ])
    if (score > 0) {
      items.push({
        id: `account-${account.id}`, kind: 'account',
        title: account.username || `账号 ${account.id}`,
        subtitle: `${account.platform?.name || '未配置平台'} · UID ${account.anyrouter_user_id ?? '-'}`,
        icon: PeopleOutline, score, accountId: account.id
      })
    }
  })

  cpPlatforms.value.forEach(platform => {
    const score = scoreTerms(kw, [platform.name, platform.base_url])
    if (score > 0) {
      items.push({
        id: `platform-${platform.id}`, kind: 'platform',
        title: platform.name, subtitle: platform.base_url,
        icon: ServerOutline, score
      })
    }
  })

  cpLogs.value.forEach(log => {
    const username = log.account?.username || `账号 ${log.account_id}`
    const statusLabel = log.success ? '签到成功' : '签到失败'
    const score = scoreTerms(kw, [username, log.account_id, log.message, log.status, statusLabel])
    if (score > 0) {
      items.push({
        id: `log-${log.id}`, kind: 'log',
        title: `${username} · ${statusLabel}`,
        subtitle: `${new Date(log.sign_time).toLocaleString()}${log.message ? ` · ${log.message}` : ''}`,
        icon: TimeOutline, score,
        accountId: log.account_id, success: log.success,
        logDate: buildLocalDateParam(log.sign_time)
      })
    }
  })

  const kindPriority: Record<CommandItemKind, number> = { action: 0, account: 1, platform: 2, log: 3 }
  return items
    .sort((a, b) => b.score - a.score || kindPriority[a.kind] - kindPriority[b.kind] || a.title.localeCompare(b.title))
    .slice(0, 10)
})

const close = () => {
  emit('update:show', false)
  keyword.value = ''
  selectionIndex.value = 0
}

const loadData = async () => {
  loading.value = true
  try {
    const [accountsRes, platformsRes, logsRes] = await Promise.allSettled([
      accountApi.getList(),
      platformApi.getList(),
      signApi.getAllLogs({ page: 1, size: 80 })
    ])
    cpAccounts.value = accountsRes.status === 'fulfilled' ? (accountsRes.value.data || []) : []
    cpPlatforms.value = platformsRes.status === 'fulfilled' ? (platformsRes.value.data || []) : []
    cpLogs.value = logsRes.status === 'fulfilled' ? (logsRes.value.data?.items || []) : []
  } finally {
    loading.value = false
  }
}

const executeCommand = async (command: CommandActionId) => {
  try {
    const routeMap: Partial<Record<CommandActionId, string>> = {
      'open-dashboard': '/',
      'open-logs': '/logs',
      'open-platforms': '/platforms',
      'open-settings': '/settings'
    }
    const target = routeMap[command]
    if (target) {
      close()
      await router.push(target)
      return
    }

    if (command === 'add-account') {
      close()
      await router.push('/accounts')
      window.$notify('已跳转到账号页，可继续添加账号', 'info', { route: '/accounts' })
      return
    }

    if (command === 'batch-sign') {
      close()
      const res: any = await signApi.batchSign()
      window.$notify(res.message || '批量签到完成', 'success')
      emit('request-refresh')
      return
    }

    if (command === 'health-check-all') {
      close()
      const res: any = await accountApi.healthCheckAll()
      const healthy = res.data?.healthy_count ?? 0
      const unhealthy = res.data?.unhealthy_count ?? 0
      window.$notify(`批量检查完成，正常 ${healthy}，异常 ${unhealthy}`, 'success')
      emit('request-refresh')
      return
    }

    close()
    emit('request-refresh')
  } catch (e) {
    window.$notify(apiError(e, '命令执行失败'), 'error')
  }
}

const moveSelection = (step: number) => {
  const total = commandItems.value.length
  if (total === 0) return
  selectionIndex.value = (selectionIndex.value + step + total) % total
}

const getKindLabel = (kind: CommandItemKind) => {
  const labels: Record<CommandItemKind, string> = {
    action: '动作', account: '账号', platform: '平台', log: '日志'
  }
  return labels[kind]
}

const executeCommandItem = async (item: CommandItem) => {
  if (item.kind === 'action' && item.actionId) {
    await executeCommand(item.actionId)
    return
  }

  close()

  if (item.kind === 'account' && item.accountId) {
    await router.push(`/account/${item.accountId}`)
    return
  }

  if (item.kind === 'platform') {
    await router.push('/platforms')
    window.$notify(`已跳转到平台页，可继续查看 ${item.title}`, 'info', { route: '/platforms' })
    return
  }

  if (item.kind === 'log' && item.accountId && item.logDate) {
    await router.push({
      path: '/logs',
      query: {
        account_id: String(item.accountId),
        success: String(item.success),
        start_date: item.logDate,
        end_date: item.logDate
      }
    })
  }
}

const handleEnter = () => {
  const activeItem = commandItems.value[selectionIndex.value]
  if (!activeItem) {
    window.$notify('没有匹配结果', 'info')
    return
  }
  void executeCommandItem(activeItem)
}

watch(() => props.show, (show) => {
  if (!show) {
    keyword.value = ''
    selectionIndex.value = 0
    return
  }
  void loadData()
  nextTick(() => {
    inputRef.value?.focus()
    inputRef.value?.select()
  })
})

watch(keyword, () => {
  selectionIndex.value = 0
})

watch(commandItems, (items) => {
  if (items.length === 0) {
    selectionIndex.value = 0
    return
  }
  if (selectionIndex.value > items.length - 1) {
    selectionIndex.value = items.length - 1
  }
})
</script>

<style scoped>
.command-palette {
  width: min(640px, calc(100vw - 32px));
  max-height: 70vh;
  background: var(--bg-modal);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cp-search {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
}

.cp-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: var(--text-md);
  color: var(--text-primary);
}

.cp-input::placeholder { color: var(--text-placeholder); }

.cp-hints {
  display: flex;
  gap: 2px;
  color: var(--text-tertiary);
}

.cp-kbd {
  display: inline-grid;
  place-items: center;
  min-width: 18px;
  padding: 0 4px;
  height: 18px;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-tertiary);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xs);
  background: var(--bg-secondary);
}

.cp-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-2);
}

.cp-section-title {
  padding: var(--spacing-2) var(--spacing-3) 4px;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: var(--font-medium);
}

.cp-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-2) var(--spacing-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-align: left;
  color: var(--text-primary);
}

.cp-item.active {
  background: var(--primary-color-light);
}

.cp-item-icon {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: var(--bg-secondary);
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.cp-item-icon.action { background: var(--primary-color-light); color: var(--primary-color); }
.cp-item-icon.account { background: var(--info-color-light); color: var(--info-color); }
.cp-item-icon.platform { background: var(--success-color-light); color: var(--success-color); }
.cp-item-icon.log { background: var(--warning-color-light); color: var(--warning-color); }

.cp-item-body {
  flex: 1;
  min-width: 0;
}

.cp-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-2);
}

.cp-item-title {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.cp-item-kind {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.cp-item-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cp-state,
.cp-empty {
  padding: var(--spacing-8) var(--spacing-4);
  text-align: center;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}
</style>
