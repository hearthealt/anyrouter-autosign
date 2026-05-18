<template>
  <div class="trend-shell" v-if="hasTrend">
    <div ref="chartRef" class="trend-chart-container"></div>
    <div class="trend-legend">
      <span class="legend-item"><span class="dot success"></span>成功</span>
      <span class="legend-item"><span class="dot fail"></span>失败</span>
      <span class="legend-item"><span class="dot reward"></span>奖励</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { DailyTrend } from '../../types'

const props = defineProps<{
  data: DailyTrend[]
  isDark?: boolean
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const hasTrend = ref(false)

// 获取图表主题配置
const getChartTheme = () => {
  return props.isDark ? {
    backgroundColor: 'transparent',
    textColor: 'rgba(255, 255, 255, 0.7)',
    axisLineColor: 'rgba(255, 255, 255, 0.1)',
    splitLineColor: 'rgba(255, 255, 255, 0.06)',
    tooltipBg: '#16181c',
    tooltipBorder: '#2a2d33',
    successColor: '#22c55e',
    failColor: '#ef4444',
    rewardColor: '#f59e0b'
  } : {
    backgroundColor: 'transparent',
    textColor: 'rgba(11, 12, 14, 0.6)',
    axisLineColor: 'rgba(11, 12, 14, 0.1)',
    splitLineColor: 'rgba(11, 12, 14, 0.05)',
    tooltipBg: '#ffffff',
    tooltipBorder: '#e3e5e8',
    successColor: '#16a34a',
    failColor: '#dc2626',
    rewardColor: '#d97706'
  }
}

const formatReward = (quota: number | undefined | null): string => {
  const value = Number(quota || 0)
  const usd = value / 500000
  if (usd > 0 && usd < 0.01) return `$${usd.toFixed(4)}`
  return `$${usd.toFixed(2)}`
}

// 格式化短日期
const formatShortDate = (dateStr: string): string => {
  const parts = dateStr.split('-')
  return parts.length >= 3 ? `${parts[1]}/${parts[2]}` : dateStr
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value || !props.data?.length) return

  chart = echarts.init(chartRef.value, null, {
    useDirtyRect: true,
    useCoarsePointer: true,
    renderer: 'canvas'
  })
  updateChart()
  window.addEventListener('resize', handleResize, { passive: true })
}

// 更新图表
const updateChart = () => {
  if (!chart || !props.data?.length) return

  const theme = getChartTheme()
  const data = props.data
  const hasReward = data.some(d => Number(d.reward || 0) > 0)

  const option: echarts.EChartsOption = {
    backgroundColor: theme.backgroundColor,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      borderWidth: 1,
      padding: [10, 14],
      textStyle: {
        color: props.isDark ? '#fff' : '#333',
        fontSize: 12
      },
      formatter: (params: any) => {
        const date = params[0]?.axisValue || ''
        const dayData = data.find(d => d.date === date)
        let html = `<div style="font-weight: 600; margin-bottom: 6px;">${date}</div>`
        params.forEach((item: any) => {
          if (item.seriesName === '奖励') return
          const color = item.seriesName === '成功' ? theme.successColor : theme.failColor
          html += `<div style="display: flex; align-items: center; gap: 8px; margin: 3px 0;">
            <span style="width: 8px; height: 8px; border-radius: 2px; background: ${color};"></span>
            <span>${item.seriesName}: <b>${item.value}</b></span>
          </div>`
        })
        const rewardDisplay = dayData?.reward_display || (Number(dayData?.reward || 0) > 0 ? formatReward(dayData?.reward) : '')
        if (rewardDisplay) {
          html += `<div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid ${theme.tooltipBorder}; color: ${theme.rewardColor};">
            奖励: <b>${rewardDisplay}</b>
          </div>`
        }
        return html
      }
    },
    grid: {
      left: '3%',
      right: '3%',
      bottom: '12%',
      top: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date),
      axisLine: { lineStyle: { color: theme.axisLineColor } },
      axisTick: { show: false },
      axisLabel: {
        color: theme.textColor,
        fontSize: 10,
        formatter: formatShortDate
      }
    },
    yAxis: [
      {
        type: 'value',
        minInterval: 1,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: theme.textColor, fontSize: 10 },
        splitLine: {
          lineStyle: { color: theme.splitLineColor, type: 'dashed' }
        }
      },
      {
        type: 'value',
        show: hasReward,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: theme.textColor,
          fontSize: 10,
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
        barWidth: '50%',
        barMaxWidth: 24,
        data: data.map(d => d.success),
        itemStyle: {
          color: theme.successColor,
          borderRadius: [0, 0, 0, 0]
        }
      },
      {
        name: '失败',
        type: 'bar',
        stack: 'total',
        barWidth: '50%',
        barMaxWidth: 24,
        data: data.map(d => d.fail),
        itemStyle: {
          color: theme.failColor,
          borderRadius: [3, 3, 0, 0]
        }
      },
      {
        name: '奖励',
        type: 'line',
        yAxisIndex: 1,
        data: data.map(d => d.reward || 0),
        smooth: true,
        symbol: 'circle',
        symbolSize: hasReward ? 5 : 0,
        lineStyle: {
          color: theme.rewardColor,
          width: hasReward ? 2 : 0
        },
        itemStyle: {
          color: theme.rewardColor,
          borderColor: props.isDark ? '#16181c' : '#fff',
          borderWidth: 2
        },
        emphasis: { disabled: !hasReward }
      }
    ]
  }

  chart.setOption(option)
}

const handleResize = () => {
  chart?.resize()
}

// 监听数据变化
watch(() => props.data, (newVal) => {
  hasTrend.value = newVal && newVal.length > 0
  if (hasTrend.value) {
    nextTick(() => {
      if (!chart) {
        initChart()
      } else {
        updateChart()
      }
    })
  }
}, { immediate: true, deep: true })

// 监听主题变化
watch(() => props.isDark, () => {
  updateChart()
})

onMounted(() => {
  if (props.data?.length) {
    initChart()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.trend-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.trend-legend {
  display: flex;
  justify-content: center;
  gap: var(--spacing-3);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.legend-item .dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
}

.legend-item .dot.success {
  background: var(--success-color);
}

.legend-item .dot.fail {
  background: var(--error-color);
}

.legend-item .dot.reward {
  background: var(--warning-color);
}

.trend-chart-container {
  flex: 1;
  width: 100%;
  min-height: 220px;
}
</style>
