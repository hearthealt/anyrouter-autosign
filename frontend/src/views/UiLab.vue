<!--
  组件实验室 —— 把 src/ui/ 下所有原语渲染在一页，用于验证设计系统。

  这是开发期工具，不挂在导航里，只能通过 /ui-lab 直达。
  改动令牌或原语后先看这一页，比在业务页面里逐个找更快。
-->
<template>
  <div class="lab material-noise">
    <header class="lab__head material-grid">
      <span class="kicker">Design System</span>
      <h1 class="display display-md">Telemetry<br />as Instrument</h1>
      <p class="lab__lede">
        单色基底 + 一个信号色。层次靠材质而非配色制造，时间函数只有弹簧。
      </p>
      <div class="lab__head-actions">
        <UiSegment v-model:value="theme" :options="themeOptions" @update:value="applyTheme" />
        <UiSegment v-model:value="motion" :options="motionOptions" @update:value="applyMotion" />
      </div>
    </header>

    <!-- 排版尺度 -->
    <section class="lab__sec">
      <h2 class="lab__sec-title">排版尺度</h2>
      <div class="lab__stack">
        <div v-for="scale in displayScales" :key="scale" class="lab__type-row">
          <span class="kicker lab__type-tag">{{ scale }}</span>
          <span :class="['display', `display-${scale}`]">98.4</span>
        </div>
        <hr class="hairline" />
        <p v-for="fn in fnScales" :key="fn.name" class="lab__fn-row">
          <span class="kicker lab__type-tag">{{ fn.name }}</span>
          <span :style="{ fontSize: `var(--fn-${fn.name})` }">签到成功 1,204 次 · Telemetry 0123456789</span>
        </p>
      </div>
    </section>

    <!-- 按钮 -->
    <section class="lab__sec">
      <h2 class="lab__sec-title">按钮</h2>
      <div class="lab__row">
        <UiButton type="primary">主操作</UiButton>
        <UiButton>默认</UiButton>
        <UiButton ghost>描边</UiButton>
        <UiButton quaternary>平铺</UiButton>
        <UiButton text>文字</UiButton>
        <UiButton type="error">危险</UiButton>
        <UiButton type="primary" loading>加载中</UiButton>
        <UiButton disabled>禁用</UiButton>
      </div>
      <div class="lab__row">
        <UiButton v-for="s in sizes" :key="s" :size="s" type="primary">{{ s }}</UiButton>
        <UiButton size="small" quaternary circle aria-label="刷新">
          <template #icon><RefreshCw :size="14" /></template>
        </UiButton>
      </div>
    </section>

    <!-- 表单 -->
    <section class="lab__sec">
      <h2 class="lab__sec-title">表单控件</h2>
      <div class="lab__grid">
        <label class="lab__field">
          <span class="lab__label">文本</span>
          <UiInput v-model:value="text" placeholder="输入账号名" clearable />
        </label>
        <label class="lab__field">
          <span class="lab__label">密码</span>
          <UiInput v-model:value="secret" type="password" show-password-on="click" placeholder="访问令牌" />
        </label>
        <label class="lab__field">
          <span class="lab__label">数字</span>
          <UiNumberInput v-model:value="count" :min="0" :max="100" :step="5">
            <template #suffix>次</template>
          </UiNumberInput>
        </label>
        <label class="lab__field">
          <span class="lab__label">单选</span>
          <UiSelect v-model:value="picked" :options="selectOptions" clearable placeholder="选择平台" />
        </label>
        <label class="lab__field">
          <span class="lab__label">多选 + 过滤</span>
          <UiSelect v-model:value="multi" :options="selectOptions" multiple filterable placeholder="选择多个" />
        </label>
        <label class="lab__field">
          <span class="lab__label">日期区间</span>
          <UiDateRange v-model:value="range" />
        </label>
        <label class="lab__field">
          <span class="lab__label">时间</span>
          <UiTimeField v-model:value="time" />
        </label>
        <label class="lab__field">
          <span class="lab__label">多行</span>
          <UiInput v-model:value="notes" type="textarea" :rows="2" placeholder="备注" />
        </label>
      </div>
      <div class="lab__row">
        <UiCheckbox v-model:checked="agree">勾选项</UiCheckbox>
        <UiCheckbox :checked="false" indeterminate>半选</UiCheckbox>
        <UiCheckbox :checked="true" disabled>禁用</UiCheckbox>
        <UiSwitch v-model:value="toggled" />
        <UiSwitch :value="true" loading />
        <UiSwitch :value="false" disabled />
      </div>
      <UiFileDrop dropzone accept=".csv,.json" @select="onFile" />
      <p v-if="fileName" class="lab__note mono">已选：{{ fileName }}</p>
    </section>

    <!-- 标签与反馈 -->
    <section class="lab__sec">
      <h2 class="lab__sec-title">标签与状态</h2>
      <div class="lab__row">
        <UiTag v-for="t in tones" :key="t" :type="t">{{ t }}</UiTag>
      </div>
      <div class="lab__row">
        <!-- 徽标锚点用图标按钮：这才是它的真实用法，挂在窄文字按钮上会压住文案 -->
        <UiBadge :value="8">
          <UiButton size="small" quaternary circle aria-label="通知">
            <template #icon><Bell :size="15" /></template>
          </UiButton>
        </UiBadge>
        <UiBadge :value="256">
          <UiButton size="small" quaternary circle aria-label="消息溢出">
            <template #icon><Inbox :size="15" /></template>
          </UiButton>
        </UiBadge>
        <UiBadge dot type="success">
          <UiButton size="small" quaternary circle aria-label="在线状态">
            <template #icon><Activity :size="15" /></template>
          </UiButton>
        </UiBadge>
        <UiSpinner :size="16" />
        <UiSkeleton :width="120" :height="12" />
      </div>
    </section>

    <!-- 浮层 -->
    <section class="lab__sec">
      <h2 class="lab__sec-title">浮层</h2>
      <div class="lab__row">
        <UiTooltip content="这是一条提示，会在停留 260ms 后出现">
          <UiButton size="small">悬停提示</UiButton>
        </UiTooltip>

        <UiPopover placement="bottom">
          <template #trigger><UiButton size="small">点击浮层</UiButton></template>
          <p class="lab__note">浮层定位、翻面、贴边全部走 useAnchoredLayer。</p>
        </UiPopover>

        <UiDropdown :options="menuOptions" @select="onMenu">
          <UiButton size="small" quaternary>
            下拉菜单
            <template #icon><ChevronDown :size="13" /></template>
          </UiButton>
        </UiDropdown>

        <UiConfirm @positive-click="onConfirm">
          <template #trigger>
            <UiButton size="small" type="error" quaternary>删除确认</UiButton>
          </template>
          删除后不可恢复，确认继续？
        </UiConfirm>

        <UiButton size="small" @click="showModal = true">打开弹窗</UiButton>
        <UiButton size="small" @click="showDrawer = true">打开抽屉</UiButton>
      </div>
      <p v-if="lastAction" class="lab__note mono">最近操作：{{ lastAction }}</p>
    </section>

    <!-- 数据表 -->
    <section class="lab__sec">
      <h2 class="lab__sec-title">数据表</h2>
      <DataGrid
        :columns="gridColumns"
        :data="rows"
        :checked-row-keys="checked"
        :row-key="(row: Row) => row.id"
        :scroll-x="720"
        @update:sorter="onSort"
        @update:checked-row-keys="keys => (checked = keys)"
      />
      <UiPagination
        v-model:page="page"
        :page-size="10"
        :item-count="94"
        :page-sizes="[10, 20, 50]"
      />
      <DataGrid :columns="gridColumns" :data="[]" loading />
      <DataGrid :columns="gridColumns" :data="[]" />
    </section>

    <UiModal
      v-model:show="showModal"
      kicker="Dialog"
      title="弹窗标题"
      size="md"
      positive-text="确认"
      negative-text="取消"
      @positive-click="showModal = false"
    >
      <p class="lab__note">
        遮罩用低透明度 + 轻度模糊，底层界面仍可辨识 —— 运维工具里"我刚才在哪一行"很重要。
      </p>
    </UiModal>

    <UiDrawer v-model:show="showDrawer" kicker="Drawer" title="抽屉标题" :width="380">
      <p class="lab__note">从右侧弹簧推入，焦点被限制在抽屉内，Esc 可关。</p>
      <template #footer>
        <UiButton size="small" @click="showDrawer = false">关闭</UiButton>
      </template>
    </UiDrawer>
  </div>
</template>

<script setup lang="ts">
import { h, ref } from 'vue'
import { Activity, Bell, ChevronDown, Copy, Inbox, RefreshCw, Trash2 } from 'lucide-vue-next'
import { DataGrid, UiBadge, UiButton, UiCheckbox, UiConfirm, UiDateRange, UiDrawer, UiDropdown, UiFileDrop, UiInput, UiModal, UiNumberInput, UiPagination, UiPopover, UiSegment, UiSelect, UiSkeleton, UiSpinner, UiSwitch, UiTag, UiTimeField, UiTooltip, type GridColumn, type GridSortState } from '../ui'
import { setMotionSetting, useMotionPreference } from '../design/useMotionPreference'

const displayScales = ['xs', 'sm', 'md', 'lg', 'xl'] as const
const fnScales = [
  { name: '2xs' }, { name: 'xs' }, { name: 'sm' }, { name: 'md' },
  { name: 'lg' }, { name: 'xl' }, { name: '2xl' },
]
const sizes = ['tiny', 'small', 'medium', 'large'] as const
const tones = ['default', 'primary', 'success', 'warning', 'error', 'info'] as const

// ── 主题与动效开关
const theme = ref(document.documentElement.getAttribute('data-theme') ?? 'light')
const themeOptions = [
  { label: '亮色', value: 'light' },
  { label: '暗色', value: 'dark' },
]
function applyTheme(value: string | number) {
  document.documentElement.setAttribute('data-theme', String(value))
}

const { setting } = useMotionPreference()
const motion = ref<string>(setting.value)
const motionOptions = [
  { label: '跟随系统', value: 'system' },
  { label: '全动效', value: 'full' },
  { label: '降级', value: 'reduced' },
]
function applyMotion(value: string | number) {
  setMotionSetting(value as 'system' | 'full' | 'reduced')
}

// ── 表单状态
const text = ref('')
const secret = ref('')
const notes = ref('')
const count = ref<number | null>(20)
const picked = ref<string | number | null>(null)
const multi = ref<Array<string | number | null>>([])
const range = ref<[number, number] | null>(null)
const time = ref<number | null>(new Date(2000, 0, 1, 9, 30).getTime())
const agree = ref(true)
const toggled = ref(true)
const fileName = ref('')

const selectOptions = [
  { label: 'AnyRouter', value: 'anyrouter' },
  { label: 'New API', value: 'newapi' },
  { label: '自建中转', value: 'custom' },
  { label: '已停用平台', value: 'disabled', disabled: true },
]

function onFile(file: File) {
  fileName.value = `${file.name} (${file.size} B)`
}

// ── 浮层状态
const showModal = ref(false)
const showDrawer = ref(false)
const lastAction = ref('')

const menuOptions = [
  { label: '复制令牌', key: 'copy', icon: Copy, hint: '⌘C' },
  { type: 'divider' as const },
  { label: '删除账号', key: 'delete', icon: Trash2, tone: 'error' as const },
]

function onMenu(key: string | number) {
  lastAction.value = `菜单选择 ${key}`
}

function onConfirm() {
  lastAction.value = '确认了删除'
}

// ── 数据表
interface Row {
  id: number
  name: string
  quota: number
  status: 'ok' | 'warn' | 'bad'
  note: string
}

const rows = ref<Row[]>([
  { id: 1, name: 'tester@example.com', quota: 1204350, status: 'ok', note: '正常签到中，最近一次奖励 +500' },
  { id: 2, name: 'admin@example.com', quota: 856000, status: 'ok', note: '正常' },
  { id: 3, name: 'ops@example.com', quota: 12400, status: 'warn', note: '额度偏低，建议充值以免中断' },
  { id: 4, name: 'ci-bot@example.com', quota: 0, status: 'bad', note: '令牌已失效，需要重新登录' },
])

const checked = ref<Array<string | number>>([2])
const page = ref(3)
const sortState = ref<GridSortState | null>(null)

function sortOrderFor(key: string) {
  return sortState.value?.columnKey === key ? sortState.value.order : false
}

const gridColumns = ref<GridColumn<Row>[]>([])

function buildColumns(): GridColumn<Row>[] {
  return [
    { type: 'selection' },
    {
      title: '账号', key: 'name', width: 220,
      sorter: 'default', sortOrder: sortOrderFor('name'),
      render: row => h('span', { class: 'mono' }, row.name),
    },
    {
      title: '额度', key: 'quota', width: 130, align: 'right',
      sorter: 'default', sortOrder: sortOrderFor('quota'),
      render: row => h('strong', { class: 'tabular' }, row.quota.toLocaleString()),
    },
    {
      title: '状态', key: 'status', width: 110,
      render: row => h(
        UiTag,
        { type: row.status === 'ok' ? 'success' : row.status === 'warn' ? 'warning' : 'error', size: 'tiny' },
        () => (row.status === 'ok' ? '正常' : row.status === 'warn' ? '偏低' : '失效'),
      ),
    },
    { title: '备注', key: 'note', ellipsis: { tooltip: true } },
    {
      title: '操作', key: 'actions', width: 90, align: 'right',
      render: () => h(UiButton, { size: 'tiny', quaternary: true }, () => '详情'),
    },
  ]
}

gridColumns.value = buildColumns()

function onSort(sorter: GridSortState | null) {
  sortState.value = sorter
  gridColumns.value = buildColumns()
  // 本地排序只为演示；真实页面是远程排序
  if (!sorter) return
  const dir = sorter.order === 'ascend' ? 1 : -1
  rows.value = [...rows.value].sort((a, b) => {
    const av = a[sorter.columnKey as keyof Row]
    const bv = b[sorter.columnKey as keyof Row]
    return (av > bv ? 1 : av < bv ? -1 : 0) * dir
  })
}
</script>

<style scoped>
.lab {
  min-height: 100vh;
  padding: var(--s10) var(--s8) var(--s24);
  background: var(--surface-page);
}

.lab__head {
  display: grid;
  gap: var(--s3);
  padding: var(--s10) var(--s6) var(--s12);
  margin-bottom: var(--s12);
  border: 1px solid var(--line-faint);
  border-radius: var(--r-xl);
  background-color: var(--surface-raised);
}

.lab__lede {
  max-width: 46ch;
  color: var(--ink-muted);
  font-size: var(--fn-lg);
  line-height: var(--leading-loose);
}

.lab__head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s3);
  margin-top: var(--s3);
}

.lab__sec {
  display: grid;
  gap: var(--s4);
  max-width: 1180px;
  margin-bottom: var(--s16);
}

.lab__sec-title {
  padding-bottom: var(--s2);
  border-bottom: 1px solid var(--line-faint);
  font-size: var(--fn-xs);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-caps);
  text-transform: uppercase;
  /* faint 在暗色下太暗看不清分区，用 muted */
  color: var(--ink-muted);
}

.lab__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s3);
}

.lab__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(224px, 1fr));
  gap: var(--s4);
}

.lab__field { display: grid; gap: 5px; }

.lab__label {
  color: var(--ink-muted);
  font-size: var(--fn-xs);
  font-weight: var(--weight-medium);
}

.lab__stack { display: grid; gap: var(--s4); }

.lab__type-row {
  display: flex;
  /* 巨字用 baseline 对齐会把小标签甩到很低的位置，改成居中 */
  align-items: center;
  gap: var(--s4);
}

.lab__fn-row {
  display: flex;
  align-items: baseline;
  gap: var(--s4);
}

.lab__type-tag {
  flex-shrink: 0;
  width: 44px;
}

.lab__note {
  color: var(--ink-muted);
  font-size: var(--fn-sm);
  line-height: var(--leading-loose);
}
</style>
