<template>
  <UiModal :show="show" bare :width="680" @update:show="(val: boolean) => emit('update:show', val)">
    <div class="command-palette">
      <div class="cp-search">
        <Search :size="16" />
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
          <kbd class="cp-kbd"><ArrowUp :size="11" /></kbd>
          <kbd class="cp-kbd"><ArrowDown :size="11" /></kbd>
          <kbd class="cp-kbd"><CornerDownLeft :size="11" /></kbd>
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
              <component :is="item.icon" :size="14" />
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
  </UiModal>
</template>

<script setup lang="ts">
import { UiModal } from '../../ui'
import { ref, computed, watch, nextTick, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, ArrowDown, ArrowUp, Clock, CornerDownLeft, LayoutDashboard, Plus, RefreshCw, Search, Server, Settings, Users, Zap } from 'lucide-vue-next'
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
  { id: 'refresh', title: '刷新当前视图', subtitle: '重新请求当前页面数据', icon: RefreshCw, actionId: 'refresh', keywords: ['refresh', 'reload', '刷新', '重新加载'] },
  { id: 'add-account', title: '添加账号', subtitle: '跳转到账号页继续新增', icon: Plus, actionId: 'add-account', keywords: ['add account', 'account', '账号', '添加'] },
  { id: 'batch-sign', title: '一键签到', subtitle: '对全部启用账号执行签到', icon: Zap, actionId: 'batch-sign', keywords: ['sign', 'batch sign', '签到', '一键'] },
  { id: 'health-check-all', title: '批量健康检查', subtitle: '检查全部账号的当前凭证状态', icon: Activity, actionId: 'health-check-all', keywords: ['health', 'check', '健康检查', '健康'] },
  { id: 'open-dashboard', title: '打开仪表盘', subtitle: '跳转到首页概览', icon: LayoutDashboard, actionId: 'open-dashboard', keywords: ['dashboard', 'home', '仪表盘', '首页'] },
  { id: 'open-logs', title: '打开签到日志', subtitle: '查看全局签到记录', icon: Clock, actionId: 'open-logs', keywords: ['logs', 'history', '日志', '签到记录'] },
  { id: 'open-platforms', title: '打开平台页', subtitle: '查看平台 Base URL 和接口配置', icon: Server, actionId: 'open-platforms', keywords: ['platform', '平台', 'base url'] },
  { id: 'open-settings', title: '打开设置页', subtitle: '查看调度与推送配置', icon: Settings, actionId: 'open-settings', keywords: ['settings', 'config', '设置', '配置'] }
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
        icon: Users, score, accountId: account.id
      })
    }
  })

  cpPlatforms.value.forEach(platform => {
    const score = scoreTerms(kw, [platform.name, platform.base_url])
    if (score > 0) {
      items.push({
        id: `platform-${platform.id}`, kind: 'platform',
        title: platform.name, subtitle: platform.base_url,
        icon: Server, score
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
        icon: Clock, score,
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
.command-palette { position: relative; display: flex; width: 100%; min-width: 0; min-height: 0; max-height: inherit; overflow: hidden; flex-direction: column; border: 1px solid var(--line); border-radius: var(--r-xl); background: var(--surface-overlay); box-shadow: var(--lift-4); }
.command-palette::before { position: absolute; z-index: 2; top: 0; right: 0; left: 0; height: 2px; content: ''; pointer-events: none; background: linear-gradient(90deg, var(--signal-deep), transparent 68%); }
.cp-search { display: flex; align-items: center; gap: 12px; padding: 17px 19px; border-bottom: 1px solid var(--line-faint); background: linear-gradient(to right, var(--grid-line) 1px, transparent 1px), var(--surface-inset); background-size: 18px 18px; }
.cp-search > svg { flex: 0 0 auto; color: var(--signal-deep); }
.cp-input { min-width: 0; flex: 1; padding: 0; border: 0; outline: 0; color: var(--ink-max); background: transparent; font-size: var(--fn-lg); }
.cp-input::placeholder { color: var(--ink-ghost); }
.cp-hints { display: flex; gap: 3px; color: var(--ink-faint); }
.cp-kbd { display: inline-grid; min-width: 21px; height: 21px; padding: 0 5px; place-items: center; border: 1px solid var(--line); border-radius: var(--r-sm); color: var(--ink-muted); background: var(--surface-raised); box-shadow: 0 1px 0 var(--line); font-family: var(--font-mono); font-size: 9px; }
.cp-body { flex: 1; min-height: 0; padding: 8px; overflow-y: auto; overscroll-behavior: contain; }
.cp-section-title { padding: 10px 12px 7px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; font-weight: var(--weight-semibold); letter-spacing: .12em; text-transform: uppercase; }
.cp-item { display: flex; width: 100%; align-items: center; gap: 11px; padding: 10px 12px; border: 1px solid transparent; border-radius: var(--r-md); color: var(--ink-strong); background: transparent; text-align: left; transition: background var(--transition-fast), border-color var(--transition-fast), transform var(--transition-bounce); }
.cp-item.active { border-color: color-mix(in srgb, var(--signal-deep) 22%, transparent); background: var(--signal-wash); transform: translateX(3px); }
.cp-item-icon { display: grid; width: 30px; height: 30px; flex: 0 0 auto; place-items: center; border: 1px solid var(--line-faint); border-radius: 50%; color: var(--ink-muted); background: var(--surface-inset); }
.cp-item-icon.action { color: var(--signal-deep); background: var(--signal-wash); }
.cp-item-icon.account { color: var(--info); background: var(--info-wash); }
.cp-item-icon.platform { color: var(--ok); background: var(--ok-wash); }
.cp-item-icon.log { color: var(--warn); background: var(--warn-wash); }
.cp-item-body { min-width: 0; flex: 1; }
.cp-item-top { display: flex; align-items: center; justify-content: space-between; gap: var(--s2); }
.cp-item-title { color: var(--ink-strong); font-size: var(--fn-sm); font-weight: var(--weight-semibold); }
.cp-item-kind { flex: 0 0 auto; color: var(--ink-faint); font-family: var(--font-mono); font-size: 8px; letter-spacing: .08em; text-transform: uppercase; }
.cp-item-desc { margin-top: 2px; overflow: hidden; color: var(--ink-muted); font-size: var(--fn-xs); text-overflow: ellipsis; white-space: nowrap; }
.cp-state, .cp-empty { padding: var(--s10) var(--s4); color: var(--ink-faint); font-size: var(--fn-sm); text-align: center; }
@media (max-width: 560px) { .cp-hints { display: none; } .cp-search { padding-inline: 15px; } }
</style>
