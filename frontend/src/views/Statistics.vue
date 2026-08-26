<template>
  <div class="statistics-page">
    <div class="workspace-toolbar">
      <div class="toolbar-summary">
        <div class="toolbar-label">数据统计</div>
        <div class="toolbar-stats">
          <span class="toolbar-stat">本月签到 <strong>{{ overview.month_success || 0 }}/{{ overview.month_total || 0 }}</strong></span>
          <span class="toolbar-stat success">成功率 <strong>{{ overview.month_success_rate || 0 }}%</strong></span>
        </div>
      </div>
      <div class="toolbar-actions">
        <UiButton size="small" :loading="loadingAccounts" @click="loadAccountStats">
          <template #icon><RefreshCw :size="14" /></template>
          刷新
        </UiButton>
      </div>
    </div>

    <!-- 指标卡 -->
    <div class="stat-row">
      <div class="stat-card">
        <div class="stat-label">本月签到</div>
        <div class="stat-value">
          {{ overview.month_success || 0 }}<span class="stat-sub">/{{ overview.month_total || 0 }}</span>
        </div>
        <div class="stat-foot">
          <span class="tag success">{{ overview.month_success_rate || 0 }}% 成功率</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">本月奖励</div>
        <div class="stat-value">{{ monthRewardDisplay }}</div>
        <div class="stat-foot">
          <span class="muted">本月累计获得</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">累计奖励</div>
        <div class="stat-value">{{ totalRewardDisplay }}</div>
        <div class="stat-foot">
          <span class="muted">全部签到所得</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-label">总成功率</div>
        <div class="stat-value">{{ overview.success_rate || 0 }}<span class="stat-sub">%</span></div>
        <div class="stat-foot">
          <span class="muted">历史所有记录</span>
        </div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="charts-row">
      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">签到趋势</div>
          <div class="trend-controls">
            <UiSegment v-model:value="dailyDays" size="small" :disabled="!!customRange" :options="[{ label: '7 天', value: 7 }, { label: '30 天', value: 30 }, { label: '60 天', value: 60 }]" />
            <UiDateRange
              v-model:value="customRange"
              type="daterange"
              size="small"
              clearable
              class="trend-range"
              :shortcuts="rangeShortcuts"
            />
          </div>
        </div>
        <div class="chart-body">
          <div ref="trendChartRef" class="echarts-container" v-show="displayDailyData.length > 0"></div>
          <div v-if="displayDailyData.length === 0" class="chart-empty">暂无签到数据</div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-head">
          <div class="panel-title">月度统计</div>
        </div>
        <div class="chart-body">
          <div ref="monthlyChartRef" class="echarts-container" v-show="monthlyData.length > 0"></div>
          <div v-if="monthlyData.length === 0" class="chart-empty">暂无月度数据</div>
        </div>
      </div>
    </div>

    <!-- 日历 -->
    <div class="panel">
      <div class="panel-head">
        <div class="panel-title">签到日历</div>
        <div class="calendar-controls">
          <UiButton size="tiny" quaternary @click="changeMonth(-1)">
            <template #icon><ChevronLeft :size="14" /></template>
          </UiButton>
          <span class="current-month">{{ currentMonthDisplay }}</span>
          <UiButton size="tiny" quaternary :disabled="isCurrentMonth" @click="changeMonth(1)">
            <template #icon><ChevronRight :size="14" /></template>
          </UiButton>
        </div>
      </div>
      <div class="calendar-legend">
        <span class="legend-item"><span class="legend-dot success"></span>全部成功</span>
        <span class="legend-item"><span class="legend-dot warning"></span>部分成功</span>
        <span class="legend-item"><span class="legend-dot error"></span>全部失败</span>
        <span class="legend-item"><span class="legend-dot default"></span>无签到</span>
      </div>
      <div class="calendar-body">
        <div class="weekdays">
          <div v-for="day in weekdays" :key="day" class="weekday">{{ day }}</div>
        </div>
        <div class="days-grid">
          <div
            v-for="(day, index) in monthDays"
            :key="index"
            class="day-cell"
            :class="getDayClass(day)"
          >
            <div v-if="day.date" class="day-number">{{ day.day }}</div>
            <div v-if="day.date && (day.success > 0 || day.fail > 0)" class="day-status">
              <span v-if="day.success > 0" class="day-pill success">{{ day.success }}</span>
              <span v-if="day.fail > 0" class="day-pill error">{{ day.fail }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 排行 -->
    <div class="panel">
      <div class="panel-head">
        <div class="panel-title">账号排行</div>
        <UiSelect
          v-model:value="accountRankSort"
          :options="accountRankSortOptions"
          size="small"
          class="rank-sort-select"
        />
      </div>
      <div v-if="loadingAccounts" class="table-wrap skeleton-table" aria-busy="true" aria-label="加载中">
        <UiSkeleton v-for="i in 6" :key="i" :height="32" :sharp="false" style="margin-bottom: 8px" />
      </div>
      <div v-else-if="accountStats.length > 0" class="table-wrap">
        <DataGrid
          :columns="accountColumns"
          :data="accountStats"
          :row-key="(row: any) => row.account_id"
          :max-height="420"
          :pagination="false"
          size="small"
        />
        <div class="ranking-pagination">
          <UiPagination
            v-model:page="accountPagination.page"
            v-model:page-size="accountPagination.pageSize"
            :item-count="accountPagination.itemCount"
            :page-sizes="accountPagination.pageSizes"
            show-size-picker
            size="small"
            @update:page="loadAccountStats"
            @update:page-size="handleAccountPageSizeChange"
          />
        </div>
      </div>
      <div v-else class="chart-empty">暂无数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, h, nextTick } from 'vue'
import { DataGrid, UiButton, UiDateRange, UiPagination, UiSegment, UiSelect, UiSkeleton, UiTag, type GridColumns } from '../ui'
import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-vue-next'
import { statisticsApi } from '../api'
import { useViewRefresh } from '../composables'
import * as echarts from 'echarts'
import { escapeHtml, formatRewardTotals, getAccountStatus } from '../utils'

const overview = ref<any>({})
const dailyData = ref<any[]>([])
const monthlyData = ref<any[]>([])
const accountStats = ref<any[]>([])
const loadingAccounts = ref(false)

const dailyDays = ref(7)
const customRange = ref<[number, number] | null>(null)
const calendarData = ref<any[]>([])
const currentMonth = ref(new Date())
type AccountRankSort = 'streak_days' | 'success_count' | 'success_rate' | 'total_reward'
const accountRankSort = ref<AccountRankSort>('success_count')
const accountRankSortOptions = [
  { label: '成功次数', value: 'success_count' },
  { label: '连签天数', value: 'streak_days' },
  { label: '成功率', value: 'success_rate' },
  { label: '累计奖励', value: 'total_reward' }
]
const monthRewardDisplay = computed(() => formatRewardTotals(
  overview.value.month_reward_totals,
  overview.value.month_reward_display || '$0.00'
))
const totalRewardDisplay = computed(() => formatRewardTotals(
  overview.value.total_reward_totals,
  overview.value.total_reward_display || '$0.00'
))
const accountPagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  pageSizes: [10, 20, 50, 100]
})

const formatYmd = (ts: number) => {
  const d = new Date(ts)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const rangeShortcuts = {
  '最近 7 天': (): [number, number] => {
    const end = Date.now()
    return [end - 6 * 86400000, end]
  },
  '最近 30 天': (): [number, number] => {
    const end = Date.now()
    return [end - 29 * 86400000, end]
  },
  '本月': (): [number, number] => {
    const now = new Date()
    const start = new Date(now.getFullYear(), now.getMonth(), 1).getTime()
    return [start, Date.now()]
  }
}

const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const trendChartRef = ref<HTMLElement | null>(null)
const monthlyChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
let monthlyChart: echarts.ECharts | null = null

const isDarkMode = ref(document.documentElement.dataset.theme === 'dark'
  || window.matchMedia('(prefers-color-scheme: dark)').matches)
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
const handleThemeChange = (e: MediaQueryListEvent) => {
  isDarkMode.value = e.matches
  updateChartsTheme()
}

const getChartTheme = () => {
  return isDarkMode.value ? {
    backgroundColor: 'transparent',
    textColor: 'rgba(255, 255, 255, 0.7)',
    axisLineColor: 'rgba(255, 255, 255, 0.1)',
    splitLineColor: 'rgba(255, 255, 255, 0.06)',
    tooltipBg: '#16181c',
    tooltipBorder: '#2a2d33',
    successColor: '#22c55e',
    failColor: '#ef4444',
    rewardColor: '#f59e0b',
    primaryColor: '#7b84dd'
  } : {
    backgroundColor: 'transparent',
    textColor: 'rgba(11, 12, 14, 0.6)',
    axisLineColor: 'rgba(11, 12, 14, 0.1)',
    splitLineColor: 'rgba(11, 12, 14, 0.05)',
    tooltipBg: '#ffffff',
    tooltipBorder: '#e3e5e8',
    successColor: '#16a34a',
    failColor: '#dc2626',
    rewardColor: '#d97706',
    primaryColor: '#5e6ad2'
  }
}

const formatReward = (quota: number | undefined | null): string => {
  const value = Number(quota || 0)
  const usd = value / 500000
  if (usd > 0 && usd < 0.01) return `$${usd.toFixed(4)}`
  return `$${usd.toFixed(2)}`
}

const currentMonthDisplay = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth() + 1
  return `${year} · ${String(month).padStart(2, '0')}`
})

const isCurrentMonth = computed(() => {
  const now = new Date()
  return currentMonth.value.getFullYear() === now.getFullYear() &&
    currentMonth.value.getMonth() === now.getMonth()
})

const monthDays = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()

  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const firstDayOfWeek = firstDay.getDay()

  const dataMap = new Map()
  for (const item of calendarData.value) {
    dataMap.set(item.date, item)
  }

  const formatLocalDate = (date: Date) => {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  }

  const days: any[] = []
  for (let i = 0; i < firstDayOfWeek; i++) {
    days.push({ date: null, day: null, success: 0, fail: 0, total: 0 })
  }
  for (let day = 1; day <= lastDay.getDate(); day++) {
    const date = new Date(year, month, day)
    const dateStr = formatLocalDate(date)
    const data = dataMap.get(dateStr)
    days.push({
      date: dateStr,
      day,
      success: data?.success || 0,
      fail: data?.fail || 0,
      total: data?.total || 0
    })
  }
  const remainingDays = 7 - (days.length % 7)
  if (remainingDays < 7) {
    for (let i = 0; i < remainingDays; i++) {
      days.push({ date: null, day: null, success: 0, fail: 0, total: 0 })
    }
  }
  return days
})

const changeMonth = (offset: number) => {
  const newDate = new Date(currentMonth.value)
  newDate.setMonth(newDate.getMonth() + offset)
  currentMonth.value = newDate
  loadCalendarData()
}

const getDayClass = (day: any) => {
  if (!day.date) return 'empty'
  const today = new Date().toISOString().split('T')[0]
  const isToday = day.date === today
  let statusClass = ''
  if (day.total === 0) statusClass = 'no-sign'
  else if (day.fail > 0 && day.success === 0) statusClass = 'all-fail'
  else if (day.success > 0 && day.fail === 0) statusClass = 'all-success'
  else statusClass = 'partial'
  return `${statusClass} ${isToday ? 'today' : ''}`
}

const displayDailyData = computed(() => dailyData.value)

const accountColumns: GridColumns = [
  {
    title: '#',
    key: 'rank',
    width: 50,
    render: (_: any, index: number) =>
      h('span', { class: 'rank-num' }, (accountPagination.value.page - 1) * accountPagination.value.pageSize + index + 1)
  },
  {
    title: '账号',
    key: 'username',
    render: (row: any) => {
      const status = getAccountStatus(row)
      return h('div', { class: 'cell-account' }, [
        h('span', { class: 'account-name' }, row.username),
        h(
          UiTag,
          {
            type: status === 'normal' ? 'success' : status === 'unhealthy' ? 'error' : 'default',
            size: 'tiny',
            bordered: false
          },
          { default: () => status === 'normal' ? '正常' : status === 'unhealthy' ? '异常' : '禁用' }
        )
      ])
    }
  },
  {
    title: '连签',
    key: 'streak_days',
    width: 100,
    render: (row: any) => {
      if (row.streak_days > 0) {
        const isHot = row.streak_days >= 3
        return h('span', { class: ['streak', isHot ? 'hot' : 'warm'] }, [
          h('span', { class: 'flame-icon' }, isHot ? '🔥' : ''),
          ` ${row.streak_days}天`
        ])
      }
      return h('span', { class: 'muted' }, '—')
    }
  },
  {
    title: '成功',
    key: 'success_count',
    width: 80,
    align: 'right',
    render: (row: any) => h('span', { class: 'success-num' }, row.success_count)
  },
  {
    title: '成功率',
    key: 'success_rate',
    width: 140,
    render: (row: any) => {
      const level = row.success_rate >= 90 ? 'high' : row.success_rate >= 70 ? 'mid' : 'low'
      return h('div', { class: 'success-rate-cell' }, [
        h('div', { class: 'rate-bar' }, [
          h('div', { class: `rate-fill ${level}`, style: { width: `${row.success_rate}%` } })
        ]),
        h('span', { class: 'rate-text' }, `${row.success_rate}%`)
      ])
    }
  },
  {
    title: '累计奖励',
    key: 'total_reward_display',
    width: 120,
    align: 'right',
    render: (row: any) => h(
      'span',
      { class: 'reward-num' },
      formatRewardTotals(row.reward_totals, row.total_reward_display || '$0.00')
    )
  }
]

const initTrendChart = () => {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  updateTrendChart()
  window.addEventListener('resize', handleResize)
}

const updateTrendChart = () => {
  if (!trendChart) return
  const theme = getChartTheme()
  const data = displayDailyData.value
  const hasReward = data.some((d: any) => Number(d.reward || 0) > 0)

  const option: echarts.EChartsOption = {
    backgroundColor: theme.backgroundColor,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: isDarkMode.value ? '#fff' : '#0b0c0e', fontSize: 12 },
      formatter: (params: any) => {
        const date = String(params[0]?.axisValue || '')
        let html = `<div style="font-weight:600;margin-bottom:6px;">${escapeHtml(date)}</div>`
        params.forEach((item: any) => {
          if (item.seriesName === '奖励') return
          const color = item.seriesName === '成功' ? theme.successColor : theme.failColor
          html += `<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:12px;">
            <span style="display:inline-flex;align-items:center;gap:6px;">
              <span style="width:8px;height:8px;border-radius:2px;background:${color};"></span>${item.seriesName}
            </span><span>${item.value}</span></div>`
        })
        const dayData = data.find((d: any) => d.date === date)
        const rewardDisplay = formatRewardTotals(
          dayData?.reward_totals,
          Number(dayData?.reward || 0) > 0 ? (dayData?.reward_display || formatReward(dayData?.reward)) : ''
        )
        if (rewardDisplay) {
          html += `<div style="margin-top:6px;padding-top:6px;border-top:1px solid ${theme.tooltipBorder};font-size:12px;color:${theme.rewardColor};">
            奖励 ${escapeHtml(rewardDisplay)}</div>`
        }
        return html
      }
    },
    legend: { show: false },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map((d: any) => d.date),
      axisLine: { lineStyle: { color: theme.axisLineColor } },
      axisTick: { show: false },
      axisLabel: {
        color: theme.textColor,
        fontSize: 11,
        formatter: (value: string) => {
          const [, month, day] = value.split('-')
          return `${month}/${day}`
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        minInterval: 1,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: theme.textColor, fontSize: 11 },
        splitLine: { lineStyle: { color: theme.splitLineColor, type: 'dashed' } }
      },
      {
        type: 'value',
        show: hasReward,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: theme.textColor,
          fontSize: 11,
          formatter: (value: number) => formatReward(value)
        },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '成功',
        type: 'bar',
        stack: 'total',
        barWidth: '60%',
        barMaxWidth: 24,
        data: data.map((d: any) => d.success),
        itemStyle: { color: theme.successColor, borderRadius: [0, 0, 0, 0] }
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        barWidth: '60%',
        barMaxWidth: 24,
        data: data.map((d: any) => d.fail),
        itemStyle: { color: theme.failColor, borderRadius: [3, 3, 0, 0] }
      },
      {
        name: '奖励',
        type: 'line',
        yAxisIndex: 1,
        data: data.map((d: any) => d.reward || 0),
        smooth: true,
        symbol: 'circle',
        symbolSize: hasReward ? 6 : 0,
        lineStyle: { color: theme.rewardColor, width: hasReward ? 2 : 0 },
        itemStyle: {
          color: theme.rewardColor,
          borderColor: isDarkMode.value ? '#16181c' : '#fff',
          borderWidth: 2
        },
        emphasis: { disabled: !hasReward }
      }
    ]
  }
  trendChart.setOption(option)
}

const initMonthlyChart = () => {
  if (!monthlyChartRef.value) return
  monthlyChart = echarts.init(monthlyChartRef.value)
  updateMonthlyChart()
}

const updateMonthlyChart = () => {
  if (!monthlyChart) return
  const theme = getChartTheme()
  const data = monthlyData.value

  const option: echarts.EChartsOption = {
    backgroundColor: theme.backgroundColor,
    tooltip: {
      trigger: 'axis',
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: isDarkMode.value ? '#fff' : '#0b0c0e', fontSize: 12 },
      formatter: (params: any) => {
        const monthData = data.find((d: any) => d.month === params[0]?.axisValue)
        if (!monthData) return ''
        const rewardDisplay = formatRewardTotals(
          monthData.reward_totals,
          monthData.reward_display || '$0.00'
        )
        return `<div style="font-weight:600;margin-bottom:6px;">${escapeHtml(monthData.month)}</div>
          <div style="display:flex;justify-content:space-between;gap:12px;font-size:12px;">
            <span>成功率</span><span style="color:${theme.successColor};">${monthData.success_rate}%</span></div>
          <div style="display:flex;justify-content:space-between;gap:12px;font-size:12px;">
            <span>签到</span><span>${monthData.success}/${monthData.total}</span></div>
          <div style="display:flex;justify-content:space-between;gap:12px;font-size:12px;color:${theme.rewardColor};">
             <span>奖励</span><span>${escapeHtml(rewardDisplay)}</span></div>`
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map((d: any) => d.month),
      axisLine: { lineStyle: { color: theme.axisLineColor } },
      axisTick: { show: false },
      axisLabel: {
        color: theme.textColor,
        fontSize: 11,
        formatter: (value: string) => {
          const [, m] = value.split('-')
          return `${parseInt(m)}月`
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: theme.textColor, fontSize: 11 },
        splitLine: { lineStyle: { color: theme.splitLineColor, type: 'dashed' } }
      },
      {
        type: 'value',
        min: 0,
        max: 100,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: theme.textColor, fontSize: 11, formatter: '{value}%' },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '签到数',
        type: 'bar',
        barWidth: '50%',
        barMaxWidth: 20,
        data: data.map((d: any) => d.total),
        itemStyle: { color: theme.primaryColor, borderRadius: [3, 3, 0, 0] }
      },
      {
        name: '成功率',
        type: 'line',
        yAxisIndex: 1,
        data: data.map((d: any) => d.success_rate),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: theme.rewardColor, width: 2 },
        itemStyle: { color: theme.rewardColor, borderColor: isDarkMode.value ? '#16181c' : '#fff', borderWidth: 2 }
      }
    ]
  }
  monthlyChart.setOption(option)
}

const updateChartsTheme = () => {
  updateTrendChart()
  updateMonthlyChart()
}

const handleResize = () => {
  trendChart?.resize()
  monthlyChart?.resize()
}

const loadOverview = async () => {
  try {
    const res = await statisticsApi.getOverview()
    overview.value = res.data || {}
  } catch (e: any) {
    console.error('Failed to load overview:', e)
  }
}

const loadDailyStats = async () => {
  try {
    if (customRange.value) {
      const [s, e] = customRange.value
      const days = Math.ceil((e - s) / 86400000) + 1
      const res = await statisticsApi.getDaily(days, formatYmd(s), formatYmd(e))
      dailyData.value = res.data || []
    } else {
      const res = await statisticsApi.getDaily(dailyDays.value)
      dailyData.value = res.data || []
    }
  } catch (e: any) {
    console.error('Failed to load daily stats:', e)
  }
}

watch(dailyDays, async () => {
  if (customRange.value) return
  await loadDailyStats()
  nextTick(() => updateTrendChart())
})

watch(customRange, async () => {
  await loadDailyStats()
  nextTick(() => updateTrendChart())
})

watch(dailyData, () => {
  nextTick(() => updateTrendChart())
}, { deep: true })

watch(monthlyData, () => {
  nextTick(() => updateMonthlyChart())
}, { deep: true })

const loadCalendarData = async () => {
  try {
    const year = currentMonth.value.getFullYear()
    const month = currentMonth.value.getMonth()
    const lastDay = new Date(year, month + 1, 0)
    const startDate = `${year}-${String(month + 1).padStart(2, '0')}-01`
    const endDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(lastDay.getDate()).padStart(2, '0')}`
    const res = await statisticsApi.getDaily(31, startDate, endDate)
    calendarData.value = res.data || []
  } catch (e: any) {
    console.error('Failed to load calendar data:', e)
  }
}

const loadMonthlyStats = async () => {
  try {
    const res = await statisticsApi.getMonthly(6)
    monthlyData.value = res.data || []
  } catch (e: any) {
    console.error('Failed to load monthly stats:', e)
  }
}

const loadAccountStats = async () => {
  loadingAccounts.value = true
  try {
    const res = await statisticsApi.getAccounts({
      page: accountPagination.value.page,
      size: accountPagination.value.pageSize,
      sort_by: accountRankSort.value
    })
    const data = res.data || {}
    accountStats.value = data.items || []
    accountPagination.value.itemCount = data.total || 0
    accountPagination.value.page = data.page || accountPagination.value.page
    accountPagination.value.pageSize = data.size || accountPagination.value.pageSize
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loadingAccounts.value = false
  }
}

const handleAccountPageSizeChange = (pageSize: number) => {
  accountPagination.value.pageSize = pageSize
  accountPagination.value.page = 1
  loadAccountStats()
}

watch(accountRankSort, () => {
  accountPagination.value.page = 1
  loadAccountStats()
})

onMounted(async () => {
  mediaQuery.addEventListener('change', handleThemeChange)

  loadOverview()
  await Promise.all([loadDailyStats(), loadMonthlyStats()])
  loadCalendarData()
  loadAccountStats()

  nextTick(() => {
    initTrendChart()
    initMonthlyChart()
  })
})

useViewRefresh(async () => {
  await Promise.all([
    loadOverview(),
    loadDailyStats(),
    loadMonthlyStats(),
    loadCalendarData(),
    loadAccountStats()
  ])
})

onUnmounted(() => {
  mediaQuery.removeEventListener('change', handleThemeChange)
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  monthlyChart?.dispose()
})
</script>

<style scoped>
.statistics-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.trend-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.trend-range {
  width: 240px;
}

/* 指标 */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--spacing-3);
}

.stat-card {
  padding: var(--spacing-3);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.stat-label {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.stat-value {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  letter-spacing: -0.02em;
  line-height: 1;
  color: var(--text-primary);
}

.stat-sub {
  font-size: var(--text-md);
  color: var(--text-tertiary);
  margin-left: 2px;
}

.stat-foot {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.tag {
  display: inline-flex;
  align-items: center;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.tag.success {
  background: var(--success-color-light);
  color: var(--success-color);
}

.muted {
  color: var(--text-tertiary);
}

/* 图表 Panel */
.charts-row {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  gap: var(--spacing-3);
}

.panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  min-height: 40px;
  padding: 0 var(--spacing-3);
  border-bottom: 1px solid var(--border-color-light);
}

.panel-title {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.rank-sort-select {
  width: 120px;
}

.chart-body {
  padding: var(--spacing-4);
  min-height: 260px;
  position: relative;
}

.echarts-container {
  width: 100%;
  height: 280px;
}

.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 260px;
  color: var(--text-quaternary);
  font-size: var(--text-sm);
}

/* Calendar */
.calendar-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.current-month {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  min-width: 80px;
  text-align: center;
}

.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  border-bottom: 1px solid var(--border-color-light);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-dot.success {
  background: var(--success-color);
}

.legend-dot.warning {
  background: var(--warning-color);
}

.legend-dot.error {
  background: var(--error-color);
}

.legend-dot.default {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color-light);
}

.calendar-body {
  padding: var(--spacing-3) var(--spacing-4);
  max-width: 720px;
}

.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 4px;
}

.weekday {
  padding: 6px 0;
  text-align: center;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: var(--font-medium);
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day-cell {
  aspect-ratio: 2.2 / 1;
  padding: 2px 4px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color-light);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all var(--transition-fast);
  min-height: 32px;
}

.day-cell.empty {
  border-color: transparent;
}

.day-cell.no-sign {
  background: transparent;
}

.day-cell.all-success {
  background: var(--success-color-light);
  border-color: rgba(22, 163, 74, 0.24);
}

.day-cell.partial {
  background: var(--warning-color-light);
  border-color: rgba(217, 119, 6, 0.24);
}

.day-cell.all-fail {
  background: var(--error-color-light);
  border-color: rgba(220, 38, 38, 0.24);
}

.day-cell.today {
  box-shadow: inset 0 0 0 2px var(--primary-color);
}

.day-number {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.day-status {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
}

.day-pill {
  display: inline-flex;
  align-items: center;
  padding: 0 3px;
  height: 12px;
  border-radius: var(--radius-xs);
  font-size: 9px;
  font-weight: var(--font-semibold);
}

.day-pill.success {
  background: rgba(22, 163, 74, 0.2);
  color: var(--success-color);
}

.day-pill.error {
  background: rgba(220, 38, 38, 0.2);
  color: var(--error-color);
}

/* Ranking */
.table-wrap :deep(.n-data-table) {
  border: none;
  border-radius: 0;
}

.ranking-pagination {
  display: flex;
  justify-content: flex-end;
  padding: var(--spacing-3) var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

.statistics-page :deep(.rank-num) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: var(--radius-xs);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.statistics-page :deep(.cell-account) {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.statistics-page :deep(.account-name) {
  color: var(--text-primary);
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
}

.statistics-page :deep(.streak) {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.statistics-page :deep(.streak.warm) {
  background: var(--warning-color-light);
  color: var(--warning-color);
}

.statistics-page :deep(.streak.hot) {
  background: var(--error-color-light);
  color: var(--error-color);
}

.statistics-page :deep(.success-num) {
  color: var(--success-color);
  font-weight: var(--font-semibold);
  font-family: var(--font-mono);
}

.statistics-page :deep(.reward-num) {
  color: var(--warning-color);
  font-weight: var(--font-medium);
  font-family: var(--font-mono);
}

.statistics-page :deep(.success-rate-cell) {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.statistics-page :deep(.rate-bar) {
  flex: 1;
  height: 3px;
  background: var(--border-color-light);
  border-radius: 999px;
  overflow: hidden;
}

.statistics-page :deep(.rate-fill) {
  height: 100%;
  transition: width var(--transition-slow);
}

.statistics-page :deep(.rate-fill.high) {
  background: var(--success-color);
}

.statistics-page :deep(.rate-fill.mid) {
  background: var(--warning-color);
}

.statistics-page :deep(.rate-fill.low) {
  background: var(--error-color);
}

.statistics-page :deep(.rate-text) {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-secondary);
}

.statistics-page :deep(.muted) {
  color: var(--text-quaternary);
}

@media (max-width: 1100px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .day-cell {
    min-height: 36px;
  }
}

@media (max-width: 480px) {
  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>
