<template>
  <div class="trend-section" v-if="hasTrend">
    <div class="section-header">
      <h3 class="section-title">近7天签到趋势</h3>
      <div class="trend-legend">
        <span class="legend-item"><span class="dot success"></span>成功</span>
        <span class="legend-item"><span class="dot fail"></span>失败</span>
      </div>
    </div>
    <div ref="chartRef" class="trend-chart-container"></div>
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
    textColor: 'rgba(255, 255, 255, 0.85)',
    axisLineColor: 'rgba(255, 255, 255, 0.15)',
    splitLineColor: 'rgba(255, 255, 255, 0.08)',
    tooltipBg: 'rgba(30, 30, 46, 0.95)',
    tooltipBorder: 'rgba(255, 255, 255, 0.1)',
    successColor: '#00d4a0',
    failColor: '#ff6b6b'
  } : {
    backgroundColor: 'transparent',
    textColor: 'rgba(0, 0, 0, 0.65)',
    axisLineColor: 'rgba(0, 0, 0, 0.15)',
    splitLineColor: 'rgba(0, 0, 0, 0.06)',
    tooltipBg: 'rgba(255, 255, 255, 0.98)',
    tooltipBorder: 'rgba(0, 0, 0, 0.08)',
    successColor: '#10b981',
    failColor: '#ef4444'
  }
}

// 格式化短日期
const formatShortDate = (dateStr: string): string => {
  const parts = dateStr.split('-')
  return parts.length >= 3 ? `${parts[1]}/${parts[2]}` : dateStr
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value || !props.data?.length) return

  chart = echarts.init(chartRef.value)
  updateChart()
  window.addEventListener('resize', handleResize)
}

// 更新图表
const updateChart = () => {
  if (!chart || !props.data?.length) return

  const theme = getChartTheme()
  const data = props.data

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
        let html = `<div style="font-weight: 600; margin-bottom: 6px;">${date}</div>`
        params.forEach((item: any) => {
          const color = item.seriesName === '成功' ? theme.successColor : theme.failColor
          html += `<div style="display: flex; align-items: center; gap: 8px; margin: 3px 0;">
            <span style="width: 8px; height: 8px; border-radius: 2px; background: ${color};"></span>
            <span>${item.seriesName}: <b>${item.value}</b></span>
          </div>`
        })
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
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: theme.textColor, fontSize: 10 },
      splitLine: {
        lineStyle: { color: theme.splitLineColor, type: 'dashed' }
      }
    },
    series: [
      {
        name: '成功',
        type: 'bar',
        stack: 'total',
        barWidth: '50%',
        barMaxWidth: 24,
        data: data.map(d => d.success),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#34d399' },
            { offset: 1, color: theme.successColor }
          ]),
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
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#f87171' },
            { offset: 1, color: theme.failColor }
          ]),
          borderRadius: [3, 3, 0, 0]
        }
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
.trend-section {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--spacing-6);
  padding: var(--spacing-4) var(--spacing-5);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin: 0;
}

.trend-legend {
  display: flex;
  gap: var(--spacing-3);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-item .dot.success {
  background: var(--success-color);
}

.legend-item .dot.fail {
  background: var(--error-color);
}

.trend-chart-container {
  width: 100%;
  height: 120px;
  margin-top: var(--spacing-3);
}

@media (max-width: 600px) {
  .trend-section {
    display: none;
  }
}
</style>
