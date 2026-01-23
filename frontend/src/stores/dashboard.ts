import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dashboardApi, apiEndpointsApi } from '../api'
import type { DashboardData, ApiEndpoint, DailyTrend } from '../types'

export const useDashboardStore = defineStore('dashboard', () => {
  // 状态
  const data = ref<DashboardData | null>(null)
  const apiEndpoints = ref<ApiEndpoint[]>([])
  const loading = ref(false)
  const endpointsLoading = ref(false)

  // 计算属性
  const accountCount = computed(() => data.value?.account_count || 0)
  const unhealthyCount = computed(() => data.value?.unhealthy_account_count || 0)
  const todaySignCount = computed(() => data.value?.today_sign_count || 0)
  const todaySignSuccess = computed(() => data.value?.today_sign_success || 0)
  const successRate = computed(() => data.value?.success_rate || 0)
  const monthReward = computed(() => data.value?.month_reward_display || '$0.00')
  const totalQuota = computed(() => data.value?.total_quota_display || '$0.00')
  const dailyTrend = computed(() => data.value?.daily_trend || [])

  const hasUnhealthyAccounts = computed(() => unhealthyCount.value > 0)
  const hasDailyTrend = computed(() => dailyTrend.value.length > 0)

  // 操作
  async function fetchDashboard() {
    loading.value = true
    try {
      const res = await dashboardApi.get()
      data.value = res.data
      return data.value
    } finally {
      loading.value = false
    }
  }

  async function fetchEndpoints() {
    endpointsLoading.value = true
    try {
      const res = await apiEndpointsApi.getList()
      apiEndpoints.value = res.data || []
      return apiEndpoints.value
    } finally {
      endpointsLoading.value = false
    }
  }

  async function syncEndpoints(): Promise<string> {
    endpointsLoading.value = true
    try {
      const res: any = await apiEndpointsApi.sync()
      await fetchEndpoints()
      return res.message || '同步成功'
    } finally {
      endpointsLoading.value = false
    }
  }

  // 获取图表数据
  function getChartData() {
    const trend = dailyTrend.value
    return {
      dates: trend.map((d: DailyTrend) => d.date),
      success: trend.map((d: DailyTrend) => d.success),
      fail: trend.map((d: DailyTrend) => d.fail)
    }
  }

  // 重置状态
  function $reset() {
    data.value = null
    apiEndpoints.value = []
    loading.value = false
    endpointsLoading.value = false
  }

  return {
    // 状态
    data,
    apiEndpoints,
    loading,
    endpointsLoading,

    // 计算属性
    accountCount,
    unhealthyCount,
    todaySignCount,
    todaySignSuccess,
    successRate,
    monthReward,
    totalQuota,
    dailyTrend,
    hasUnhealthyAccounts,
    hasDailyTrend,

    // 方法
    fetchDashboard,
    fetchEndpoints,
    syncEndpoints,
    getChartData,
    $reset
  }
})
