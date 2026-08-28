<template>
  <div class="statistics-page">
    <section class="page-toolbar statistics-toolbar" aria-label="统计操作">
      <div class="page-toolbar__summary">
        <span class="page-toolbar__label"><Activity :size="15" /> 数据统计</span>
        <div class="filter-meta page-toolbar__meta">
          <span>本月成功率 <strong>{{ overview.month_success_rate || 0 }}%</strong></span>
          <span class="success">成功 <strong>{{ overview.month_success || 0 }}</strong></span>
          <span>执行 <strong>{{ overview.month_total || 0 }}</strong></span>
        </div>
      </div>
      <div class="page-toolbar__actions">
        <UiButton size="small" type="primary" :loading="loadingAccounts" @click="loadAccountStats">
          <template #icon><RefreshCw :size="14" /></template>
          同步数据
        </UiButton>
      </div>
    </section>

    <section class="metric-deck" aria-label="统计概要">
      <article class="metric-card metric-card--signal">
        <div class="metric-top"><span>01 / MONTH</span><TrendingUp :size="16" /></div>
        <div class="metric-label">本月签到</div>
        <div class="metric-value">{{ overview.month_success || 0 }}<small>/{{ overview.month_total || 0 }}</small></div>
        <div class="metric-foot"><span class="metric-dot"></span>{{ overview.month_success_rate || 0 }}% 执行成功</div>
      </article>
      <article class="metric-card">
        <div class="metric-top"><span>02 / REWARD</span><ArrowUpRight :size="16" /></div>
        <div class="metric-label">本月奖励</div>
        <div class="metric-value metric-value--reward">{{ monthRewardDisplay }}</div>
        <div class="metric-foot">当前自然月累计回报</div>
      </article>
      <article class="metric-card">
        <div class="metric-top"><span>03 / LIFETIME</span><BarChart3 :size="16" /></div>
        <div class="metric-label">累计奖励</div>
        <div class="metric-value metric-value--reward">{{ totalRewardDisplay }}</div>
        <div class="metric-foot">全部历史签到所得</div>
      </article>
      <article class="metric-card metric-card--dark">
        <div class="metric-top"><span>04 / RELIABILITY</span><CircleGauge :size="16" /></div>
        <div class="metric-label">总成功率</div>
        <div class="metric-value">{{ overview.success_rate || 0 }}<small>%</small></div>
        <div class="metric-foot">全量记录稳定性基线</div>
      </article>
    </section>

    <section class="charts-row">
      <article class="instrument-panel instrument-panel--wide">
        <header class="instrument-head">
          <div class="instrument-identity">
            <span class="instrument-code">FLOW / 01</span>
            <div>
              <h3>签到趋势</h3>
              <p>成功、失败与奖励的时间序列</p>
            </div>
          </div>
          <div class="trend-controls">
            <UiSegment v-model:value="dailyDays" size="small" :options="[{ label: '7 天', value: 7 }, { label: '30 天', value: 30 }, { label: '60 天', value: 60 }]" />
          </div>
        </header>
        <div class="chart-body chart-body--primary">
          <span class="chart-axis-label">EVENT DENSITY</span>
          <div ref="trendChartRef" class="echarts-container" v-show="displayDailyData.length > 0"></div>
          <div v-if="displayDailyData.length === 0" class="chart-empty">暂无签到数据</div>
        </div>
      </article>

      <article class="instrument-panel instrument-panel--compact">
        <header class="instrument-head">
          <div class="instrument-identity">
            <span class="instrument-code">CYCLE / 02</span>
            <div>
              <h3>月度统计</h3>
              <p>六个月执行周期对比</p>
            </div>
          </div>
        </header>
        <div class="chart-body">
          <div ref="monthlyChartRef" class="echarts-container" v-show="monthlyData.length > 0"></div>
          <div v-if="monthlyData.length === 0" class="chart-empty">暂无月度数据</div>
        </div>
      </article>
    </section>

    <section class="insight-grid">
      <article class="instrument-panel calendar-panel">
        <header class="instrument-head instrument-head--calendar">
          <div class="instrument-identity">
            <span class="instrument-code">MATRIX / 03</span>
            <div>
              <h3>签到热力矩阵</h3>
              <p>按自然日观察执行完整度</p>
            </div>
          </div>
          <div class="calendar-controls">
            <UiButton size="tiny" quaternary aria-label="上一个月" @click="changeMonth(-1)">
              <template #icon><ChevronLeft :size="14" /></template>
            </UiButton>
            <span class="current-month">{{ currentMonthDisplay }}</span>
            <UiButton size="tiny" quaternary aria-label="下一个月" :disabled="isCurrentMonth" @click="changeMonth(1)">
              <template #icon><ChevronRight :size="14" /></template>
            </UiButton>
          </div>
        </header>
        <div class="calendar-legend">
          <span class="legend-item"><span class="legend-dot success"></span>全部成功</span>
          <span class="legend-item"><span class="legend-dot warning"></span>部分成功</span>
          <span class="legend-item"><span class="legend-dot error"></span>全部失败</span>
          <span class="legend-item"><span class="legend-dot default"></span>无签到</span>
        </div>
        <div class="calendar-body">
          <div class="calendar-decoration"><CalendarDays :size="18" /><span>ACTIVITY MAP</span></div>
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
              <div v-if="day.date" class="day-number">{{ String(day.day).padStart(2, '0') }}</div>
              <div v-if="day.date && (day.success > 0 || day.fail > 0)" class="day-status">
                <span v-if="day.success > 0" class="day-pill success">S {{ day.success }}</span>
                <span v-if="day.fail > 0" class="day-pill error">F {{ day.fail }}</span>
              </div>
            </div>
          </div>
        </div>
      </article>

      <aside class="matrix-note">
        <span class="matrix-note__index">SIGNAL QUALITY / LIVE</span>
        <CalendarDays :size="30" :stroke-width="1.4" />
        <p>颜色不是装饰，而是任务完成度。聚焦异常日期，可以快速定位执行链路中的波动。</p>
        <div class="matrix-note__line"><span></span></div>
      </aside>
    </section>

    <section class="instrument-panel ranking-panel">
      <header class="instrument-head">
        <div class="instrument-identity">
          <span class="instrument-code">RANKING / 04</span>
          <div>
            <h3>账号表现排行</h3>
            <p>用连续性、成功率与奖励衡量长期质量</p>
          </div>
        </div>
        <div class="ranking-controls">
          <Trophy :size="16" />
          <UiSelect
            v-model:value="accountRankSort"
            :options="accountRankSortOptions"
            size="small"
            class="rank-sort-select"
          />
        </div>
      </header>
      <div v-if="loadingAccounts" class="table-wrap skeleton-table" aria-busy="true" aria-label="加载中">
        <UiSkeleton v-for="i in 6" :key="i" :height="36" :sharp="false" style="margin-bottom: 8px" />
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
          <span class="pagination-caption">{{ accountPagination.itemCount }} ACCOUNTS INDEXED</span>
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
    </section>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, h, nextTick } from 'vue'
import { DataGrid, UiButton, UiPagination, UiSegment, UiSelect, UiSkeleton, UiTag, type GridColumns } from '../ui'
import { Activity, ArrowUpRight, BarChart3, CalendarDays, ChevronLeft, ChevronRight, CircleGauge, Flame, RefreshCw, TrendingUp, Trophy } from 'lucide-vue-next'
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

const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

const trendChartRef = ref<HTMLElement | null>(null)
const monthlyChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
let monthlyChart: echarts.ECharts | null = null

const readDarkMode = () => document.documentElement.dataset.theme === 'dark'
const isDarkMode = ref(readDarkMode())
let themeObserver: MutationObserver | null = null

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
    width: 220,
    ellipsis: { tooltip: true },
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
          isHot ? h(Flame, { class: 'flame-icon', size: 12, strokeWidth: 2.1 }) : null,
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
    const res = await statisticsApi.getDaily(dailyDays.value)
    dailyData.value = res.data || []
  } catch (e: any) {
    console.error('Failed to load daily stats:', e)
  }
}

watch(dailyDays, async () => {
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
  themeObserver = new MutationObserver(() => {
    const nextDarkMode = readDarkMode()
    if (nextDarkMode === isDarkMode.value) return
    isDarkMode.value = nextDarkMode
    updateChartsTheme()
  })
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  })

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
  themeObserver?.disconnect()
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  monthlyChart?.dispose()
})
</script>

<style scoped>
.statistics-page {
  display: flex;
  flex-direction: column;
  gap: clamp(14px, 1.8vw, 24px);
  padding-bottom: 48px;
}

.telemetry-hero {
  position: relative;
  isolation: isolate;
  min-height: 370px;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(280px, 0.55fr);
  gap: clamp(32px, 6vw, 96px);
  align-items: end;
  overflow: hidden;
  padding: clamp(28px, 5vw, 72px);
  border: 1px solid var(--line);
  border-radius: 28px;
  background:
    radial-gradient(circle at 78% 18%, var(--signal-wash), transparent 28%),
    linear-gradient(135deg, color-mix(in srgb, var(--surface-raised) 96%, var(--signal) 4%), var(--surface-inset));
  box-shadow: var(--lift-3);
}

.hero-grid {
  position: absolute;
  inset: 0;
  z-index: -2;
  opacity: 0.48;
  background-image:
    linear-gradient(var(--grid-line) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(to right, black 28%, transparent 90%);
}

.hero-signal {
  position: absolute;
  top: -22%;
  right: -6%;
  z-index: -1;
  width: 390px;
  aspect-ratio: 1;
  border: 1px solid color-mix(in srgb, var(--signal-deep) 26%, transparent);
  border-radius: 50%;
  box-shadow:
    0 0 0 54px color-mix(in srgb, var(--signal) 5%, transparent),
    0 0 0 108px color-mix(in srgb, var(--signal) 3%, transparent);
}

.hero-main { align-self: center; max-width: 790px; }

.hero-kicker,
.metric-top,
.instrument-code,
.hero-sync,
.matrix-note__index,
.pagination-caption {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 650;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.hero-kicker {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--ink-muted);
}

.hero-index { margin-left: auto; color: var(--ink-faint); }
.live-pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--signal); box-shadow: 0 0 0 5px var(--signal-wash), 0 0 16px var(--signal-glow); }

.hero-title {
  display: flex;
  flex-direction: column;
  margin: clamp(34px, 5vw, 62px) 0 20px;
  color: var(--ink-max);
  font-family: var(--font-display);
  font-size: clamp(38px, 5.6vw, 84px);
  font-weight: 470;
  line-height: 0.98;
  letter-spacing: -0.065em;
}

.hero-title strong { color: var(--signal-deep); font-weight: 720; }
.hero-copy { max-width: 620px; margin: 0; color: var(--ink-muted); font-size: clamp(13px, 1.1vw, 15px); line-height: 1.9; }
.hero-actions { display: flex; align-items: center; gap: 18px; margin-top: 28px; }
.hero-sync { display: inline-flex; align-items: center; gap: 7px; color: var(--ink-faint); }

.hero-readout {
  position: relative;
  min-width: 0;
  padding: 28px;
  border: 1px solid color-mix(in srgb, var(--line) 82%, transparent);
  border-radius: 24px;
  background: color-mix(in srgb, var(--surface-overlay) 72%, transparent);
  box-shadow: inset 0 1px color-mix(in srgb, white 24%, transparent);
  backdrop-filter: blur(22px);
}

.readout-orbit { position: relative; display: grid; place-items: center; width: min(100%, 240px); margin: 0 auto 30px; aspect-ratio: 1; }
.readout-orbit::before,
.readout-orbit::after,
.readout-orbit__track { content: ""; position: absolute; border-radius: 50%; }
.readout-orbit::before { inset: 0; border: 1px solid var(--line); }
.readout-orbit::after { inset: 16%; border: 1px dashed var(--line-strong); opacity: 0.55; animation: orbit-spin 24s linear infinite; }
.readout-orbit__track { inset: 7%; border: 2px solid var(--signal); border-left-color: transparent; border-bottom-color: color-mix(in srgb, var(--signal) 30%, transparent); transform: rotate(28deg); box-shadow: 0 0 28px -14px var(--signal-glow); }
.readout-value { display: flex; align-items: flex-start; color: var(--ink-max); line-height: 1; }
.readout-value strong { font-family: var(--font-display); font-size: clamp(54px, 6vw, 82px); font-weight: 620; letter-spacing: -0.08em; }
.readout-value span { margin: 9px 0 0 5px; color: var(--signal-deep); font-family: var(--font-mono); font-size: 13px; }
.readout-node { position: absolute; width: 7px; height: 7px; border: 2px solid var(--surface-raised); border-radius: 50%; background: var(--signal); box-shadow: 0 0 12px var(--signal-glow); }
.node-a { top: 11%; right: 25%; }
.node-b { bottom: 19%; left: 12%; }
.readout-caption { display: flex; justify-content: space-between; gap: 16px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.12em; }
.readout-caption strong { color: var(--ink-strong); font-size: 11px; }
.readout-progress { height: 3px; margin-top: 12px; overflow: hidden; border-radius: 999px; background: var(--line-faint); }
.readout-progress span { display: block; height: 100%; border-radius: inherit; background: var(--signal); box-shadow: 0 0 12px var(--signal-glow); transition: width 0.6s cubic-bezier(.2,.8,.2,1); }

.metric-deck { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; overflow: hidden; border: 1px solid var(--line); border-radius: 20px; background: var(--line-faint); box-shadow: var(--lift-2); }
.metric-card { position: relative; min-height: 190px; display: flex; flex-direction: column; padding: 22px; overflow: hidden; background: var(--surface-raised); transition: transform .35s cubic-bezier(.2,.8,.2,1), background .35s; }
.metric-card:hover { z-index: 1; transform: translateY(-3px); background: var(--surface-inset); }
.metric-card--signal { background: linear-gradient(145deg, var(--signal), color-mix(in srgb, var(--signal) 72%, var(--surface-raised))); color: var(--signal-ink); }
.metric-card--signal::after { content: ""; position: absolute; right: -50px; bottom: -90px; width: 190px; aspect-ratio: 1; border: 1px solid color-mix(in srgb, var(--signal-ink) 22%, transparent); border-radius: 50%; box-shadow: 0 0 0 32px color-mix(in srgb, var(--signal-ink) 5%, transparent); }
.metric-card--dark { background: linear-gradient(145deg, var(--surface-raised), var(--surface-inset)); color: var(--ink-strong); }
.metric-top { display: flex; justify-content: space-between; align-items: center; color: var(--ink-faint); }
.metric-card--signal .metric-top,
.metric-card--signal .metric-label,
.metric-card--signal .metric-foot { color: color-mix(in srgb, var(--signal-ink) 70%, transparent); }
.metric-card--dark .metric-top,
.metric-card--dark .metric-label,
.metric-card--dark .metric-foot { color: var(--ink-faint); }
.metric-label { margin-top: auto; color: var(--ink-muted); font-size: 12px; }
.metric-value { margin-top: 8px; color: var(--ink-max); font-family: var(--font-display); font-size: clamp(35px, 3.6vw, 54px); font-weight: 590; line-height: 1; letter-spacing: -0.065em; white-space: nowrap; }
.metric-card--signal .metric-value { color: var(--signal-ink); }
.metric-card--dark .metric-value { color: var(--ink-max); }
.metric-value small { margin-left: 5px; font-family: var(--font-mono); font-size: 13px; font-weight: 500; letter-spacing: 0; opacity: .54; }
.metric-value--reward { overflow: hidden; font-size: clamp(25px, 2.6vw, 42px); text-overflow: ellipsis; }
.metric-foot { display: flex; align-items: center; gap: 7px; margin-top: 12px; color: var(--ink-faint); font-size: 10px; }
.metric-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--signal-ink); }

.charts-row { display: grid; grid-template-columns: minmax(0, 1.65fr) minmax(330px, .85fr); gap: clamp(14px, 1.8vw, 24px); }
.instrument-panel { position: relative; overflow: hidden; border: 1px solid var(--line); border-radius: 22px; background: color-mix(in srgb, var(--surface-raised) 95%, transparent); box-shadow: var(--lift-2); }
.instrument-panel::before { content: ""; position: absolute; top: 0; left: 24px; width: 84px; height: 2px; z-index: 2; background: var(--signal); box-shadow: 0 0 14px var(--signal-glow); }
.instrument-head { min-height: 88px; display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 18px 22px; border-bottom: 1px solid var(--line-faint); background: linear-gradient(90deg, var(--surface-inset), transparent); }
.instrument-identity { display: flex; align-items: center; gap: 18px; min-width: 0; }
.instrument-code { align-self: flex-start; flex: 0 0 auto; padding-top: 5px; color: var(--signal-deep); writing-mode: vertical-rl; }
.instrument-identity h3 { margin: 0; color: var(--ink-max); font-size: 16px; font-weight: 620; letter-spacing: -.02em; }
.instrument-identity p { margin: 5px 0 0; color: var(--ink-faint); font-size: 11px; }
.trend-controls { display: flex; align-items: center; justify-content: flex-end; gap: 8px; flex-wrap: wrap; }
.chart-body { position: relative; min-height: 300px; padding: 14px 18px 16px; background-image: linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px); background-size: 32px 32px; }
.chart-body--primary { min-height: 350px; }
.chart-axis-label { position: absolute; top: 18px; left: 22px; z-index: 1; color: var(--ink-ghost); font-family: var(--font-mono); font-size: 8px; letter-spacing: .16em; writing-mode: vertical-rl; }
.echarts-container { width: 100%; height: 320px; }
.instrument-panel--wide .echarts-container { height: 350px; }
.chart-empty { display: grid; place-items: center; min-height: 280px; color: var(--ink-faint); font-size: 12px; }

.insight-grid { display: grid; grid-template-columns: minmax(0, 1fr) 250px; gap: clamp(14px, 1.8vw, 24px); }
.calendar-panel { min-width: 0; }
.calendar-controls { display: flex; align-items: center; gap: 5px; }
.current-month { min-width: 92px; color: var(--ink-strong); font-family: var(--font-mono); font-size: 12px; font-weight: 650; text-align: center; }
.calendar-legend { display: flex; flex-wrap: wrap; gap: 18px; padding: 11px 22px; border-bottom: 1px solid var(--line-faint); color: var(--ink-faint); font-size: 10px; }
.legend-item { display: inline-flex; align-items: center; gap: 6px; }
.legend-dot { width: 7px; height: 7px; border-radius: 2px; }
.legend-dot.success { background: var(--ok); }
.legend-dot.warning { background: var(--warn); }
.legend-dot.error { background: var(--bad); }
.legend-dot.default { border: 1px solid var(--line); background: var(--surface-inset); }
.calendar-body { position: relative; padding: 22px; }
.calendar-decoration { position: absolute; right: 22px; top: -36px; display: flex; align-items: center; gap: 7px; color: var(--ink-ghost); font-family: var(--font-mono); font-size: 9px; letter-spacing: .12em; }
.weekdays,
.days-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; }
.weekdays { margin-bottom: 6px; }
.weekday { padding: 5px 2px; color: var(--ink-faint); font-family: var(--font-mono); font-size: 9px; letter-spacing: .04em; text-align: center; }
.day-cell { position: relative; min-height: 62px; display: flex; flex-direction: column; justify-content: space-between; padding: 8px; overflow: hidden; border: 1px solid var(--line-faint); border-radius: 10px; background: var(--surface-inset); transition: transform .25s, border-color .25s; }
.day-cell:not(.empty):hover { z-index: 1; transform: translateY(-2px); border-color: var(--line-strong); }
.day-cell.empty { border-color: transparent; background: transparent; }
.day-cell.no-sign { background: color-mix(in srgb, var(--surface-inset) 72%, transparent); }
.day-cell.all-success { border-color: color-mix(in srgb, var(--ok) 24%, var(--line-faint)); background: linear-gradient(145deg, var(--ok-wash), var(--surface-inset)); }
.day-cell.partial { border-color: color-mix(in srgb, var(--warn) 28%, var(--line-faint)); background: linear-gradient(145deg, var(--warn-wash), var(--surface-inset)); }
.day-cell.all-fail { border-color: color-mix(in srgb, var(--bad) 28%, var(--line-faint)); background: linear-gradient(145deg, var(--bad-wash), var(--surface-inset)); }
.day-cell.today { box-shadow: inset 0 0 0 1px var(--signal-deep), 0 0 18px -12px var(--signal-glow); }
.day-number { color: var(--ink-strong); font-family: var(--font-mono); font-size: 11px; font-weight: 600; }
.day-status { display: flex; gap: 4px; flex-wrap: wrap; }
.day-pill { display: inline-flex; align-items: center; min-height: 15px; padding: 0 4px; border-radius: 4px; font-family: var(--font-mono); font-size: 8px; font-weight: 650; }
.day-pill.success { background: var(--ok-wash); color: var(--ok); }
.day-pill.error { background: var(--bad-wash); color: var(--bad); }

.matrix-note { min-height: 100%; display: flex; flex-direction: column; justify-content: space-between; gap: 28px; padding: 26px; border: 1px solid var(--line); border-radius: 22px; background: radial-gradient(circle at 88% 12%, var(--signal-wash), transparent 38%), var(--surface-raised); color: var(--ink-strong); box-shadow: var(--lift-2); }
.matrix-note__index { color: var(--ink-faint); }
.matrix-note svg { color: var(--signal-deep); }
.matrix-note p { margin: auto 0 0; color: var(--ink-muted); font-size: 12px; line-height: 1.9; }
.matrix-note__line { height: 1px; background: var(--line-faint); }
.matrix-note__line span { display: block; width: 42%; height: 100%; background: var(--signal); box-shadow: 0 0 12px var(--signal-glow); }

.ranking-controls { display: flex; align-items: center; gap: 10px; color: var(--signal-deep); }
.rank-sort-select { width: 132px; }
.table-wrap { position: relative; }
.skeleton-table { padding: 20px; }
.table-wrap :deep(.n-data-table) { border: none; border-radius: 0; background: transparent; }
.ranking-pagination { display: flex; justify-content: space-between; align-items: center; gap: 18px; padding: 14px 20px; border-top: 1px solid var(--line-faint); background: var(--surface-inset); }
.pagination-caption { color: var(--ink-faint); }
.statistics-page :deep(.rank-num) { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-inset); color: var(--ink-muted); font-family: var(--font-mono); font-size: 9px; font-weight: 650; }
.statistics-page :deep(.cell-account) { display: flex; align-items: center; gap: 9px; min-width: 0; }
.statistics-page :deep(.account-name) { min-width: 0; overflow: hidden; color: var(--ink-max); font-size: 12px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.statistics-page :deep(.streak) { display: inline-flex; align-items: center; gap: 3px; padding: 3px 7px; border-radius: 6px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; }
.statistics-page :deep(.streak.warm) { background: var(--warn-wash); color: var(--warn); }
.statistics-page :deep(.streak.hot) { background: var(--bad-wash); color: var(--bad); }
.statistics-page :deep(.success-num) { color: var(--ok); font-family: var(--font-mono); font-weight: 650; }
.statistics-page :deep(.reward-num) { color: var(--warn); font-family: var(--font-mono); font-weight: 600; }
.statistics-page :deep(.success-rate-cell) { display: flex; align-items: center; gap: 9px; }
.statistics-page :deep(.rate-bar) { flex: 1; height: 3px; overflow: hidden; border-radius: 99px; background: var(--line-faint); }
.statistics-page :deep(.rate-fill) { height: 100%; transition: width .5s; }
.statistics-page :deep(.rate-fill.high) { background: var(--ok); }
.statistics-page :deep(.rate-fill.mid) { background: var(--warn); }
.statistics-page :deep(.rate-fill.low) { background: var(--bad); }
.statistics-page :deep(.rate-text) { color: var(--ink-muted); font-family: var(--font-mono); font-size: 10px; }
.statistics-page :deep(.muted) { color: var(--ink-faint); }

@keyframes orbit-spin { to { transform: rotate(360deg); } }

@media (max-width: 1180px) {
  .telemetry-hero { grid-template-columns: minmax(0, 1.2fr) minmax(250px, .6fr); }
  .metric-deck { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .charts-row { grid-template-columns: 1fr; }
  .insight-grid { grid-template-columns: 1fr; }
  .matrix-note { min-height: 210px; }
}

@media (max-width: 800px) {
  .telemetry-hero { grid-template-columns: 1fr; align-items: stretch; padding: 28px; border-radius: 22px; }
  .hero-readout { display: grid; grid-template-columns: 150px 1fr; align-items: center; gap: 22px; }
  .readout-orbit { margin: 0; }
  .readout-caption { align-self: end; }
  .readout-progress { grid-column: 2; margin-top: -70px; }
  .instrument-head { align-items: flex-start; flex-direction: column; }
  .trend-controls { width: 100%; justify-content: flex-start; }
  .calendar-decoration { display: none; }
}

@media (max-width: 620px) {
  .statistics-page { gap: 12px; }
  .telemetry-hero { min-height: 0; padding: 22px; }
  .hero-index { display: none; }
  .hero-title { margin-top: 38px; font-size: clamp(38px, 12vw, 58px); }
  .hero-actions { align-items: flex-start; flex-direction: column; }
  .hero-readout { display: block; padding: 20px; }
  .readout-orbit { width: 170px; margin: 0 auto 22px; }
  .readout-progress { margin-top: 12px; }
  .metric-deck { grid-template-columns: 1fr; border-radius: 16px; }
  .metric-card { min-height: 160px; }
  .trend-controls { align-items: stretch; flex-direction: column; }
  .instrument-head { min-height: 0; padding: 17px; }
  .instrument-identity { gap: 12px; }
  .instrument-code { writing-mode: initial; }
  .calendar-body { padding: 14px; overflow-x: auto; }
  .weekdays, .days-grid { min-width: 560px; }
  .ranking-pagination { align-items: flex-end; flex-direction: column; }
  .pagination-caption { align-self: flex-start; }
}

@media (prefers-reduced-motion: reduce) {
  .readout-orbit::after { animation: none; }
  .metric-card,
  .day-cell { transition: none; }
}
</style>