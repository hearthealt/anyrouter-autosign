<template>
  <div>
    <!-- 统计概览骨架屏 -->
    <div class="stats-overview" v-if="loadingOverview">
      <div class="stat-card skeleton-card" v-for="i in 4" :key="i">
        <n-skeleton circle :width="48" :height="48" />
        <div class="stat-content">
          <n-skeleton text :width="80" :height="28" style="margin-bottom: 8px;" />
          <n-skeleton text :width="60" :height="16" />
        </div>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview" v-else>
      <div class="stat-card primary">
        <div class="stat-icon">
          <n-icon :size="24"><CalendarOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ overview.month_success || 0 }}<span class="stat-sub">/{{ overview.month_total || 0 }}</span></div>
          <div class="stat-label">本月签到</div>
        </div>
        <div class="stat-rate" v-if="overview.month_success_rate">
          {{ overview.month_success_rate }}%
        </div>
      </div>
      <div class="stat-card success">
        <div class="stat-icon">
          <n-icon :size="24"><TrophyOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ overview.month_reward_display || '$0.00' }}</div>
          <div class="stat-label">本月奖励</div>
        </div>
      </div>
      <div class="stat-card info">
        <div class="stat-icon">
          <n-icon :size="24"><GiftOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ overview.total_reward_display || '$0.00' }}</div>
          <div class="stat-label">累计奖励</div>
        </div>
      </div>
      <div class="stat-card warning">
        <div class="stat-icon">
          <n-icon :size="24"><TrendingUpOutline /></n-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ overview.success_rate || 0 }}%</div>
          <div class="stat-label">总成功率</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <!-- 每日签到趋势 -->
      <div class="chart-card trend-card">
        <div class="chart-header">
          <div class="chart-title">
            <span class="title-icon"></span>
            <h3>签到趋势</h3>
          </div>
          <div class="period-tabs">
            <button
              v-for="period in [7, 30, 60]"
              :key="period"
              :class="['period-tab', { active: dailyDays === period }]"
              @click="dailyDays = period"
            >
              {{ period }}天
            </button>
          </div>
        </div>
        <div class="chart-body">
          <!-- ECharts 图表容器 -->
          <div ref="trendChartRef" class="echarts-container" v-show="displayDailyData.length > 0"></div>
          <!-- 空状态 -->
          <div class="chart-empty" v-if="displayDailyData.length === 0">
            <span>暂无签到数据</span>
          </div>
        </div>
        <!-- 图例固定在底部 -->
        <div class="chart-footer">
          <div class="chart-legend">
            <div class="legend-item">
              <span class="legend-dot success"></span>
              <span>成功</span>
            </div>
            <div class="legend-item">
              <span class="legend-dot fail"></span>
              <span>失败</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 月度统计 -->
      <div class="chart-card monthly-card">
        <div class="chart-header">
          <div class="chart-title">
            <span class="title-icon orange"></span>
            <h3>月度统计</h3>
          </div>
        </div>
        <div class="chart-body monthly-body">
          <!-- ECharts 图表容器 -->
          <div ref="monthlyChartRef" class="echarts-container" v-show="monthlyData.length > 0"></div>
          <!-- 空状态 -->
          <div class="chart-empty" v-if="monthlyData.length === 0">
            <span>暂无月度数据</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 签到日历 -->
    <div class="calendar-card">
      <div class="calendar-header">
        <div class="calendar-title">
          <span class="title-icon green"></span>
          <h3>签到日历</h3>
        </div>
        <div class="calendar-controls">
          <n-button size="small" @click="changeMonth(-1)">
            <template #icon><n-icon><ChevronBackOutline /></n-icon></template>
          </n-button>
          <span class="current-month">{{ currentMonthDisplay }}</span>
          <n-button size="small" @click="changeMonth(1)" :disabled="isCurrentMonth">
            <template #icon><n-icon><ChevronForwardOutline /></n-icon></template>
          </n-button>
        </div>
        <div class="calendar-legend">
          <span class="legend-item">
            <span class="legend-dot" style="background: var(--bg-card-hover);"></span>
            无签到
          </span>
          <span class="legend-item">
            <span class="legend-dot" style="background: #00b38a;"></span>
            全部成功
          </span>
          <span class="legend-item">
            <span class="legend-dot" style="background: #f0a020;"></span>
            部分成功
          </span>
          <span class="legend-item">
            <span class="legend-dot" style="background: #d03050;"></span>
            全部失败
          </span>
        </div>
      </div>
      <div class="calendar-body">
        <div class="month-calendar">
          <!-- 星期标题 -->
          <div class="calendar-weekdays-row">
            <div v-for="day in ['周日', '周一', '周二', '周三', '周四', '周五', '周六']" :key="day" class="weekday-header">
              {{ day }}
            </div>
          </div>
          <!-- 日期网格 -->
          <div class="calendar-days-grid">
            <div
              v-for="(day, index) in monthDays"
              :key="index"
              class="day-cell"
              :class="getDayClass(day)"
              @click="day.date && handleDayClick(day)"
            >
              <div class="day-number" v-if="day.date">{{ day.day }}</div>
              <div class="day-status" v-if="day.date && (day.success > 0 || day.fail > 0)">
                <div class="status-bar">
                  <span class="success-count" v-if="day.success > 0">✓{{ day.success }}</span>
                  <span class="fail-count" v-if="day.fail > 0">✗{{ day.fail }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 账号排行 -->
    <div class="ranking-card">
      <div class="ranking-header">
        <h3>账号排行</h3>
        <n-button size="small" @click="loadAccountStats" :loading="loadingAccounts">
          <template #icon><n-icon><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
      </div>
      <n-spin :show="loadingAccounts">
        <n-data-table
          v-if="accountStats.length > 0"
          :columns="accountColumns"
          :data="accountStats"
          :row-key="(row: any) => row.account_id"
          :max-height="400"
          size="small"
        />
        <n-empty v-else description="暂无数据" />
      </n-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, h, nextTick } from 'vue'
import { useMessage, NTag, NIcon, NProgress } from 'naive-ui'
import {
  CalendarOutline,
  TrophyOutline,
  GiftOutline,
  TrendingUpOutline,
  RefreshOutline,
  FlameOutline,
  ChevronBackOutline,
  ChevronForwardOutline
} from '@vicons/ionicons5'
import { statisticsApi } from '../api'
import * as echarts from 'echarts'

const message = useMessage()

const overview = ref<any>({})
const dailyData = ref<any[]>([])
const monthlyData = ref<any[]>([])
const accountStats = ref<any[]>([])
const loadingAccounts = ref(false)
const loadingOverview = ref(true)

const dailyDays = ref(7)
const calendarData = ref<any[]>([])
const currentMonth = ref(new Date())

// ECharts 实例
const trendChartRef = ref<HTMLElement | null>(null)
const monthlyChartRef = ref<HTMLElement | null>(null)
let trendChart: echarts.ECharts | null = null
let monthlyChart: echarts.ECharts | null = null

// 检测深色模式
const isDarkMode = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

// 监听系统主题变化
const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
const handleThemeChange = (e: MediaQueryListEvent) => {
  isDarkMode.value = e.matches
  updateChartsTheme()
}

// 获取图表主题配置
const getChartTheme = () => {
  return isDarkMode.value ? {
    backgroundColor: 'transparent',
    textColor: 'rgba(255, 255, 255, 0.85)',
    axisLineColor: 'rgba(255, 255, 255, 0.15)',
    splitLineColor: 'rgba(255, 255, 255, 0.08)',
    tooltipBg: 'rgba(30, 30, 46, 0.95)',
    tooltipBorder: 'rgba(255, 255, 255, 0.1)',
    successColor: '#00d4a0',
    failColor: '#ff6b6b',
    rewardColor: '#f0a020'
  } : {
    backgroundColor: 'transparent',
    textColor: 'rgba(0, 0, 0, 0.65)',
    axisLineColor: 'rgba(0, 0, 0, 0.15)',
    splitLineColor: 'rgba(0, 0, 0, 0.06)',
    tooltipBg: 'rgba(255, 255, 255, 0.98)',
    tooltipBorder: 'rgba(0, 0, 0, 0.08)',
    successColor: '#00b38a',
    failColor: '#ee5a5a',
    rewardColor: '#f0a020'
  }
}

// 当前月份显示文本
const currentMonthDisplay = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth() + 1
  return `${year}年${month}月`
})

// 是否是当前月
const isCurrentMonth = computed(() => {
  const now = new Date()
  return currentMonth.value.getFullYear() === now.getFullYear() &&
         currentMonth.value.getMonth() === now.getMonth()
})

// 生成月历数据
const monthDays = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()

  // 获取当月第一天和最后一天
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  // 获取第一天是星期几（0-6，0是周日）
  const firstDayOfWeek = firstDay.getDay()

  // 创建日期到数据的映射
  const dataMap = new Map()
  for (const item of calendarData.value) {
    dataMap.set(item.date, item)
  }

  // 辅助函数：格式化日期为 YYYY-MM-DD（本地时间）
  const formatLocalDate = (date: Date) => {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  }

  const days: any[] = []

  // 填充上月的空白日期
  for (let i = 0; i < firstDayOfWeek; i++) {
    days.push({ date: null, day: null, success: 0, fail: 0, total: 0 })
  }

  // 填充当月日期
  for (let day = 1; day <= lastDay.getDate(); day++) {
    const date = new Date(year, month, day)
    const dateStr = formatLocalDate(date)
    const data = dataMap.get(dateStr)

    days.push({
      date: dateStr,
      day: day,
      success: data?.success || 0,
      fail: data?.fail || 0,
      total: data?.total || 0
    })
  }

  // 填充下月的空白日期，使总数是7的倍数
  const remainingDays = 7 - (days.length % 7)
  if (remainingDays < 7) {
    for (let i = 0; i < remainingDays; i++) {
      days.push({ date: null, day: null, success: 0, fail: 0, total: 0 })
    }
  }

  return days
})

// 切换月份
const changeMonth = (offset: number) => {
  const newDate = new Date(currentMonth.value)
  newDate.setMonth(newDate.getMonth() + offset)
  currentMonth.value = newDate
  loadCalendarData()
}

// 点击日期
const handleDayClick = (day: any) => {
  if (!day.date) return
}

const getDayClass = (day: any) => {
  if (!day.date) return 'empty'

  const today = new Date().toISOString().split('T')[0]
  const isToday = day.date === today

  let statusClass = ''
  if (day.total === 0) {
    statusClass = 'no-sign'
  } else if (day.fail > 0 && day.success === 0) {
    statusClass = 'all-fail'
  } else if (day.success > 0 && day.fail === 0) {
    statusClass = 'all-success'
  } else {
    statusClass = 'partial-success'
  }

  return `${statusClass} ${isToday ? 'today' : ''}`
}

const displayDailyData = computed(() => {
  // 直接返回已加载的数据（已经是对应天数的）
  return dailyData.value
})

// 账号排行表格列定义
const accountColumns = [
  {
    title: '排名',
    key: 'rank',
    render: (_: any, index: number) => {
      const colors: Record<string, string> = {
        gold: 'background: linear-gradient(135deg, #ffd700, #ffb700); color: white;',
        silver: 'background: linear-gradient(135deg, #c0c0c0, #a0a0a0); color: white;',
        bronze: 'background: linear-gradient(135deg, #cd7f32, #b87333); color: white;'
      }
      const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : ''
      const style = `display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 12px; font-weight: 600; ${colors[rankClass] || 'background: var(--bg-card-hover); color: var(--text-secondary);'}`
      return h('span', { style }, index + 1)
    }
  },
  {
    title: '账号',
    key: 'username',
    render: (row: any) => {
      return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h('span', { style: 'font-size: 13px; font-weight: 500; color: var(--text-primary);' }, row.username),
        row.health_status === 'unhealthy' ? h(NTag, { type: 'error', size: 'tiny', bordered: false }, { default: () => '异常' }) : null
      ])
    }
  },
  {
    title: '连签',
    key: 'streak_days',
    render: (row: any) => {
      if (row.streak_days > 0) {
        const isHot = row.streak_days >= 3
        const color = isHot ? '#d03050' : '#f0a020'
        const bgColor = isHot ? 'rgba(208,48,80,0.1)' : 'rgba(240,160,32,0.1)'
        return h('span', {
          style: `display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: ${color}; background: ${bgColor}; padding: 2px 8px; border-radius: 10px;`
        }, [
          h(NIcon, null, { default: () => h(FlameOutline) }),
          ` ${row.streak_days}天`
        ])
      }
      return h('span', { style: 'color: var(--text-tertiary);' }, '-')
    }
  },
  {
    title: '成功',
    key: 'success_count',
    render: (row: any) => h('span', { style: 'color: #18a058; font-weight: 600;' }, row.success_count)
  },
  {
    title: '成功率',
    key: 'success_rate',
    render: (row: any) => {
      const color = row.success_rate >= 90 ? '#18a058' : row.success_rate >= 70 ? '#f0a020' : '#d03050'
      return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
        h(NProgress, {
          type: 'line',
          percentage: row.success_rate,
          showIndicator: false,
          height: 6,
          borderRadius: 3,
          color: color,
          style: 'width: 60px;'
        }),
        h('span', { style: 'font-size: 12px; color: var(--text-secondary);' }, `${row.success_rate}%`)
      ])
    }
  },
  {
    title: '累计奖励',
    key: 'total_reward_display',
    render: (row: any) => h('span', { style: 'color: #f0a020; font-weight: 500;' }, row.total_reward_display)
  }
]

// 初始化签到趋势图表
const initTrendChart = () => {
  if (!trendChartRef.value) return

  trendChart = echarts.init(trendChartRef.value)
  updateTrendChart()

  // 监听窗口大小变化
  window.addEventListener('resize', handleResize)
}

// 更新签到趋势图表
const updateTrendChart = () => {
  if (!trendChart) return

  const theme = getChartTheme()
  const data = displayDailyData.value

  const option: echarts.EChartsOption = {
    backgroundColor: theme.backgroundColor,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      borderWidth: 1,
      padding: [12, 16],
      textStyle: {
        color: isDarkMode.value ? '#fff' : '#333',
        fontSize: 13
      },
      formatter: (params: any) => {
        const date = params[0]?.axisValue || ''
        let html = `<div style="font-weight: 600; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid ${theme.tooltipBorder}">${date}</div>`

        params.forEach((item: any) => {
          const color = item.seriesName === '成功' ? theme.successColor : theme.failColor
          html += `<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 4px 0;">
            <span style="display: flex; align-items: center; gap: 6px;">
              <span style="width: 10px; height: 10px; border-radius: 2px; background: ${color};"></span>
              ${item.seriesName}
            </span>
            <span style="font-weight: 600;">${item.value}</span>
          </div>`
        })

        // 添加奖励信息
        const dayData = data.find((d: any) => d.date === date)
        if (dayData?.reward_display) {
          html += `<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid ${theme.tooltipBorder}; color: ${theme.rewardColor};">
            奖励: <span style="font-weight: 600;">${dayData.reward_display}</span>
          </div>`
        }

        return html
      }
    },
    legend: {
      show: false
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map((d: any) => d.date),
      axisLine: {
        lineStyle: {
          color: theme.axisLineColor
        }
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: theme.textColor,
        fontSize: 11,
        formatter: (value: string) => {
          const [, month, day] = value.split('-')
          return `${month}/${day}`
        }
      }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: {
        show: false
      },
      axisTick: {
        show: false
      },
      axisLabel: {
        color: theme.textColor,
        fontSize: 11
      },
      splitLine: {
        lineStyle: {
          color: theme.splitLineColor,
          type: 'dashed'
        }
      }
    },
    dataZoom: data.length > 15 ? [
      {
        type: 'inside',
        start: Math.max(0, 100 - (15 / data.length) * 100),
        end: 100
      },
      {
        type: 'slider',
        show: true,
        height: 20,
        bottom: 0,
        start: Math.max(0, 100 - (15 / data.length) * 100),
        end: 100,
        borderColor: 'transparent',
        backgroundColor: theme.splitLineColor,
        fillerColor: isDarkMode.value ? 'rgba(0, 179, 138, 0.2)' : 'rgba(0, 179, 138, 0.15)',
        handleStyle: {
          color: theme.successColor,
          borderColor: theme.successColor
        },
        textStyle: {
          color: theme.textColor
        }
      }
    ] : undefined,
    series: [
      {
        name: '成功',
        type: 'bar',
        stack: 'total',
        barWidth: '60%',
        barMaxWidth: 30,
        data: data.map((d: any) => d.success),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#00d4a0' },
            { offset: 1, color: theme.successColor }
          ]),
          borderRadius: [0, 0, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#00e8b0' },
              { offset: 1, color: '#00c090' }
            ])
          }
        }
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        barWidth: '60%',
        barMaxWidth: 30,
        data: data.map((d: any) => d.fail),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#ff8080' },
            { offset: 1, color: theme.failColor }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#ff9090' },
              { offset: 1, color: '#ff6060' }
            ])
          }
        }
      }
    ]
  }

  trendChart.setOption(option)
}

// 初始化月度统计图表
const initMonthlyChart = () => {
  if (!monthlyChartRef.value) return

  monthlyChart = echarts.init(monthlyChartRef.value)
  updateMonthlyChart()
}

// 更新月度统计图表
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
      padding: [12, 16],
      textStyle: {
        color: isDarkMode.value ? '#fff' : '#333',
        fontSize: 13
      },
      formatter: (params: any) => {
        const monthData = data.find((d: any) => d.month === params[0]?.axisValue)
        if (!monthData) return ''

        return `<div style="font-weight: 600; margin-bottom: 8px;">${monthData.month}</div>
          <div style="display: flex; justify-content: space-between; gap: 16px; margin: 4px 0;">
            <span>成功率</span>
            <span style="font-weight: 600; color: ${theme.successColor}">${monthData.success_rate}%</span>
          </div>
          <div style="display: flex; justify-content: space-between; gap: 16px; margin: 4px 0;">
            <span>签到</span>
            <span style="font-weight: 600;">${monthData.success}/${monthData.total}</span>
          </div>
          <div style="display: flex; justify-content: space-between; gap: 16px; margin: 4px 0; color: ${theme.rewardColor}">
            <span>奖励</span>
            <span style="font-weight: 600;">${monthData.reward_display}</span>
          </div>`
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map((d: any) => d.month),
      axisLine: {
        lineStyle: {
          color: theme.axisLineColor
        }
      },
      axisTick: {
        show: false
      },
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
        name: '签到数',
        position: 'left',
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: theme.textColor,
          fontSize: 11
        },
        splitLine: {
          lineStyle: {
            color: theme.splitLineColor,
            type: 'dashed'
          }
        }
      },
      {
        type: 'value',
        name: '成功率',
        position: 'right',
        min: 0,
        max: 100,
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          color: theme.textColor,
          fontSize: 11,
          formatter: '{value}%'
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: '签到数',
        type: 'bar',
        barWidth: '50%',
        barMaxWidth: 24,
        data: data.map((d: any) => d.total),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 179, 138, 0.8)' },
            { offset: 1, color: 'rgba(0, 179, 138, 0.3)' }
          ]),
          borderRadius: [4, 4, 0, 0]
        }
      },
      {
        name: '成功率',
        type: 'line',
        yAxisIndex: 1,
        data: data.map((d: any) => d.success_rate),
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          color: theme.rewardColor,
          width: 3
        },
        itemStyle: {
          color: theme.rewardColor,
          borderColor: isDarkMode.value ? '#1e1e2e' : '#fff',
          borderWidth: 2
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(240, 160, 32, 0.3)' },
            { offset: 1, color: 'rgba(240, 160, 32, 0.05)' }
          ])
        }
      }
    ]
  }

  monthlyChart.setOption(option)
}

// 更新图表主题
const updateChartsTheme = () => {
  updateTrendChart()
  updateMonthlyChart()
}

// 处理窗口大小变化
const handleResize = () => {
  trendChart?.resize()
  monthlyChart?.resize()
}

const loadOverview = async () => {
  loadingOverview.value = true
  try {
    const res = await statisticsApi.getOverview()
    overview.value = res.data || {}
  } catch (e: any) {
    console.error('Failed to load overview:', e)
  } finally {
    loadingOverview.value = false
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

// 监听天数切换，重新加载数据
watch(dailyDays, async () => {
  await loadDailyStats()
  nextTick(() => {
    updateTrendChart()
  })
})

// 监听数据变化更新图表
watch(dailyData, () => {
  nextTick(() => {
    updateTrendChart()
  })
}, { deep: true })

watch(monthlyData, () => {
  nextTick(() => {
    updateMonthlyChart()
  })
}, { deep: true })

const loadCalendarData = async () => {
  try {
    // 获取当前显示月份的第一天和最后一天
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
    const res = await statisticsApi.getAccounts()
    accountStats.value = res.data || []
  } catch (e: any) {
    message.error(e.message)
  } finally {
    loadingAccounts.value = false
  }
}

onMounted(async () => {
  // 监听主题变化
  mediaQuery.addEventListener('change', handleThemeChange)

  // 加载数据
  loadOverview()
  await Promise.all([loadDailyStats(), loadMonthlyStats()])
  loadCalendarData()
  loadAccountStats()

  // 初始化图表
  nextTick(() => {
    initTrendChart()
    initMonthlyChart()
  })
})

onUnmounted(() => {
  // 清理事件监听
  mediaQuery.removeEventListener('change', handleThemeChange)
  window.removeEventListener('resize', handleResize)

  // 销毁图表实例
  trendChart?.dispose()
  monthlyChart?.dispose()
})
</script>

<style scoped>
.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  position: relative;
}

.stat-card.skeleton-card {
  min-height: 88px;
}

.stat-card.primary .stat-icon { background: rgba(0,179,138,0.1); color: #00b38a; }
.stat-card.success .stat-icon { background: rgba(24,160,88,0.1); color: #18a058; }
.stat-card.info .stat-icon { background: rgba(32,128,240,0.1); color: #2080f0; }
.stat-card.warning .stat-icon { background: rgba(240,160,32,0.1); color: #f0a020; }

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content { flex: 1; }

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-sub {
  font-size: 14px;
  font-weight: 400;
  color: var(--text-tertiary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.stat-rate {
  position: absolute;
  top: 12px;
  right: 16px;
  font-size: 12px;
  color: #18a058;
  background: rgba(24,160,88,0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.chart-card {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow-sm);
  min-width: 0;
  overflow: hidden;
}

/* 签到趋势卡片特殊样式 */
.trend-card {
  background: var(--bg-card);
  display: flex;
  flex-direction: column;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 12px;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 4px;
  height: 18px;
  background: linear-gradient(180deg, #00b38a 0%, #18a058 100%);
  border-radius: 2px;
}

.title-icon.orange {
  background: linear-gradient(180deg, #f0a020 0%, #e09000 100%);
}

.chart-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

/* 时间段切换按钮 */
.period-tabs {
  display: flex;
  background: var(--bg-card-hover);
  border-radius: 8px;
  padding: 3px;
}

.period-tab {
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.period-tab:hover {
  color: var(--text-primary);
}

.period-tab.active {
  background: var(--bg-card);
  color: #00b38a;
  box-shadow: var(--shadow-sm);
}

.chart-body {
  padding: 0 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* ECharts 图表容器 */
.echarts-container {
  width: 100%;
  height: 220px;
  min-height: 180px;
}

.monthly-body {
  padding: 12px 20px;
}

.monthly-body .echarts-container {
  height: 200px;
}

/* 空状态 */
.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-tertiary);
  font-size: 13px;
}

/* 图表底部 */
.chart-footer {
  padding: 12px 20px 16px;
}

/* 图例 */
.chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color-light);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.legend-dot.success {
  background: linear-gradient(135deg, #00d4a0 0%, #00b38a 100%);
}

.legend-dot.fail {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
}

/* 账号排行 */
.ranking-card {
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.ranking-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 签到日历 */
.calendar-card {
  background: var(--bg-card);
  border-radius: 16px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 24px;
  overflow: hidden;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  gap: 16px;
  flex-wrap: wrap;
}

.calendar-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.calendar-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.title-icon.green {
  background: linear-gradient(180deg, #00b38a 0%, #18a058 100%);
}

.calendar-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.current-month {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 100px;
  text-align: center;
}

.calendar-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.calendar-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.calendar-legend .legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.calendar-body {
  padding: 0 20px 20px;
}

.month-calendar {
  width: 100%;
}

.calendar-weekdays-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
  margin-bottom: 8px;
}

.weekday-header {
  text-align: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 8px;
}

.calendar-days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day-cell {
  height: 50px;
  background: var(--bg-card-hover);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  padding: 4px 6px;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.day-cell:hover:not(.empty) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-color);
}

.day-cell.empty {
  background: transparent;
  border-color: transparent;
  cursor: default;
}

.day-cell.empty:hover {
  transform: none;
  box-shadow: none;
}

.day-cell.no-sign {
  background: var(--bg-card-hover);
}

.day-cell.all-success {
  background: rgba(0, 179, 138, 0.1);
  border-color: #00b38a;
}

.day-cell.all-fail {
  background: rgba(208, 48, 80, 0.1);
  border-color: #d03050;
}

.day-cell.partial-success {
  background: rgba(240, 160, 32, 0.1);
  border-color: #f0a020;
}

.day-cell.today {
  box-shadow: 0 0 0 2px var(--primary-color);
}

.day-number {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.day-status {
  flex: 1;
  display: flex;
  align-items: flex-end;
}

.status-bar {
  display: flex;
  gap: 3px;
  flex-wrap: wrap;
  width: 100%;
}

.success-count {
  font-size: 9px;
  font-weight: 500;
  color: #00b38a;
  background: rgba(0, 179, 138, 0.15);
  padding: 1px 3px;
  border-radius: 3px;
}

.fail-count {
  font-size: 9px;
  font-weight: 500;
  color: #d03050;
  background: rgba(208, 48, 80, 0.15);
  padding: 1px 3px;
  border-radius: 3px;
}

.no-streak {
  color: var(--text-tertiary);
}

@media (max-width: 900px) {
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .stats-overview {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
  }

  .stat-value {
    font-size: 20px;
  }

  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .period-tabs {
    width: 100%;
    justify-content: center;
  }

  .ranking-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .ranking-header .n-button {
    width: 100%;
  }

  /* 日历响应式 */
  .calendar-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .calendar-legend {
    width: 100%;
  }

  .calendar-controls {
    width: 100%;
    justify-content: center;
  }

  .day-cell {
    height: 45px;
    padding: 3px 4px;
  }

  .day-number {
    font-size: 10px;
  }

  .success-count,
  .fail-count {
    font-size: 8px;
    padding: 1px 2px;
  }
}
</style>
