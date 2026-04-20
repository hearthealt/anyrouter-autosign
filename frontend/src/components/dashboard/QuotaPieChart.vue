<template>
  <div class="quota-shell" v-if="hasData">
    <div ref="chartRef" class="pie-chart-container"></div>
    <div class="quota-legend">
      <div v-for="item in legendData" :key="item.name" class="legend-item">
        <span class="legend-dot" :style="{ background: item.color }"></span>
        <span class="legend-name">{{ item.name }}</span>
        <span class="legend-value">{{ item.value }}</span>
      </div>
    </div>
  </div>
  <div v-else class="empty-state quota-empty">
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

// 图表颜色（Linear 配色）
const chartColors = [
  '#5e6ad2', '#0284c7', '#7c3aed', '#d97706', '#db2777',
  '#0891b2', '#16a34a', '#dc2626', '#64748b', '#ea580c'
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
    textColor: 'rgba(255, 255, 255, 0.7)',
    tooltipBg: '#16181c',
    tooltipBorder: '#2a2d33',
    labelColor: 'rgba(255, 255, 255, 0.5)'
  } : {
    backgroundColor: 'transparent',
    textColor: 'rgba(11, 12, 14, 0.6)',
    tooltipBg: '#ffffff',
    tooltipBorder: '#e3e5e8',
    labelColor: 'rgba(11, 12, 14, 0.45)'
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
          borderRadius: 3,
          borderColor: props.isDark ? '#16181c' : '#ffffff',
          borderWidth: 2
        },
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: 'bold',
            color: theme.textColor
          }
        },
        labelLine: {
          show: false
        },
        data: pieData.map((item, index) => ({
          ...item,
          itemStyle: {
            color: chartColors[index % chartColors.length]
          }
        }))
      }
    ]
  }

  chart.setOption(option)
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
.quota-shell {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  height: 100%;
  min-height: 220px;
}

.pie-chart-container {
  flex: 1;
  height: 220px;
  min-width: 180px;
}

.quota-legend {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
  min-width: 130px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: 3px 0;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-name {
  flex: 1;
  font-size: var(--text-xs);
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 80px;
}

.legend-value {
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.quota-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 220px;
  gap: var(--spacing-2);
}

.empty-text {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

@media (max-width: 600px) {
  .quota-shell {
    flex-direction: column;
  }

  .pie-chart-container {
    width: 100%;
    height: 160px;
  }

  .quota-legend {
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
    min-width: auto;
  }

  .legend-item {
    padding: 2px 6px;
  }
}
</style>
