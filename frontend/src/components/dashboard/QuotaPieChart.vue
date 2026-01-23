<template>
  <div class="quota-pie-section" v-if="hasData">
    <div ref="chartRef" class="pie-chart-container"></div>
    <div class="quota-legend">
      <div v-for="item in legendData" :key="item.name" class="legend-item">
        <span class="legend-dot" :style="{ background: item.color }"></span>
        <span class="legend-name">{{ item.name }}</span>
        <span class="legend-value">{{ item.value }}</span>
      </div>
    </div>
  </div>
  <div v-else class="empty-state">
    <n-icon :size="48" color="var(--text-tertiary)"><WalletOutline /></n-icon>
    <span class="empty-text">暂无额度数据</span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { WalletOutline } from '@vicons/ionicons5'
import type { Account } from '../../types'

const props = defineProps<{
  accounts: Account[]
  isDark?: boolean
}>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const hasData = computed(() => props.accounts && props.accounts.length > 0)

// 图表颜色
const chartColors = [
  '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899',
  '#06b6d4', '#22c55e', '#ef4444', '#6366f1', '#14b8a6'
]

// 图例数据
const legendData = computed(() => {
  if (!props.accounts?.length) return []

  const sorted = [...props.accounts]
    .filter(a => a.cached_quota && a.cached_quota > 0)
    .sort((a, b) => (b.cached_quota || 0) - (a.cached_quota || 0))
    .slice(0, 6)

  return sorted.map((account, index) => ({
    name: account.username || `账号${account.id}`,
    value: account.quota_display || '$0.00',
    color: chartColors[index % chartColors.length]
  }))
})

// 获取图表主题配置
const getChartTheme = () => {
  return props.isDark ? {
    backgroundColor: 'transparent',
    textColor: 'rgba(255, 255, 255, 0.85)',
    tooltipBg: 'rgba(30, 30, 46, 0.95)',
    tooltipBorder: 'rgba(255, 255, 255, 0.1)',
    labelColor: 'rgba(255, 255, 255, 0.65)'
  } : {
    backgroundColor: 'transparent',
    textColor: 'rgba(0, 0, 0, 0.65)',
    tooltipBg: 'rgba(255, 255, 255, 0.98)',
    tooltipBorder: 'rgba(0, 0, 0, 0.08)',
    labelColor: 'rgba(0, 0, 0, 0.45)'
  }
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value || !props.accounts?.length) return

  chart = echarts.init(chartRef.value)
  updateChart()
  window.addEventListener('resize', handleResize)
}

// 更新图表
const updateChart = () => {
  if (!chart || !props.accounts?.length) return

  const theme = getChartTheme()

  // 准备数据 - 取前6个账号，其余归为"其他"
  const sorted = [...props.accounts]
    .filter(a => a.cached_quota && a.cached_quota > 0)
    .sort((a, b) => (b.cached_quota || 0) - (a.cached_quota || 0))

  let pieData: Array<{ name: string; value: number }> = []

  if (sorted.length <= 6) {
    pieData = sorted.map(a => ({
      name: a.username || `账号${a.id}`,
      value: a.cached_quota || 0
    }))
  } else {
    pieData = sorted.slice(0, 5).map(a => ({
      name: a.username || `账号${a.id}`,
      value: a.cached_quota || 0
    }))
    const otherTotal = sorted.slice(5).reduce((sum, a) => sum + (a.cached_quota || 0), 0)
    if (otherTotal > 0) {
      pieData.push({ name: '其他', value: otherTotal })
    }
  }

  if (pieData.length === 0) {
    chart.clear()
    return
  }

  const option: echarts.EChartsOption = {
    backgroundColor: theme.backgroundColor,
    tooltip: {
      trigger: 'item',
      backgroundColor: theme.tooltipBg,
      borderColor: theme.tooltipBorder,
      borderWidth: 1,
      padding: [10, 14],
      textStyle: {
        color: props.isDark ? '#fff' : '#333',
        fontSize: 12
      },
      formatter: (params: any) => {
        const value = params.value / 100
        return `<div style="font-weight: 600;">${params.name}</div>
                <div style="margin-top: 4px;">$${value.toFixed(2)} (${params.percent}%)</div>`
      }
    },
    series: [
      {
        name: '额度分布',
        type: 'pie',
        radius: ['45%', '75%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: props.isDark ? '#1a3328' : '#ffffff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            color: theme.textColor
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.2)'
          }
        },
        labelLine: {
          show: false
        },
        data: pieData.map((item, index) => ({
          ...item,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: chartColors[index % chartColors.length] },
              { offset: 1, color: adjustColor(chartColors[index % chartColors.length], -20) }
            ])
          }
        }))
      }
    ]
  }

  chart.setOption(option)
}

// 调整颜色亮度
const adjustColor = (color: string, amount: number): string => {
  const hex = color.replace('#', '')
  const r = Math.max(0, Math.min(255, parseInt(hex.slice(0, 2), 16) + amount))
  const g = Math.max(0, Math.min(255, parseInt(hex.slice(2, 4), 16) + amount))
  const b = Math.max(0, Math.min(255, parseInt(hex.slice(4, 6), 16) + amount))
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`
}

const handleResize = () => {
  chart?.resize()
}

// 监听数据变化
watch(() => props.accounts, (newVal) => {
  if (newVal && newVal.length > 0) {
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
  if (props.accounts?.length) {
    initChart()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})
</script>

<style scoped>
.quota-pie-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  height: 100%;
  min-height: 200px;
}

.pie-chart-container {
  flex: 1;
  height: 220px;
  min-width: 200px;
}

.quota-legend {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  min-width: 140px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-1) 0;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.legend-name {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 80px;
}

.legend-value {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: var(--spacing-3);
}

.empty-text {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

@media (max-width: 600px) {
  .quota-pie-section {
    flex-direction: column;
  }

  .pie-chart-container {
    width: 100%;
    height: 180px;
  }

  .quota-legend {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    min-width: auto;
  }

  .legend-item {
    padding: var(--spacing-1) var(--spacing-2);
  }
}
</style>
