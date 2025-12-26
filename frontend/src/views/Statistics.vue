<template>
  <div>
    <!-- 统计概览 -->
    <div class="stats-overview">
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
          <div class="trend-chart" v-if="displayDailyData.length > 0">
            <!-- Y轴刻度 -->
            <div class="y-axis">
              <span>{{ maxDailyValue }}</span>
              <span>{{ Math.round(maxDailyValue / 2) }}</span>
              <span>0</span>
            </div>
            <!-- 图表区域 -->
            <div class="chart-scroll-area">
              <div class="chart-bars-container">
                <div
                  v-for="(item, index) in displayDailyData"
                  :key="item.date"
                  class="bar-column"
                  @mouseenter="activeBar = index"
                  @mouseleave="activeBar = -1"
                >
                  <!-- 堆叠柱子 -->
                  <div class="stacked-bar">
                    <div
                      class="bar-segment fail"
                      :style="{ height: getBarHeight(item.fail, maxDailyValue) + 'px' }"
                    ></div>
                    <div
                      class="bar-segment success"
                      :style="{ height: getBarHeight(item.success, maxDailyValue) + 'px' }"
                    ></div>
                  </div>
                  <!-- 日期标签 -->
                  <div class="bar-date">{{ formatBarDate(item.date) }}</div>
                  <!-- 悬浮提示 -->
                  <Transition name="tooltip-fade">
                    <div v-if="activeBar === index" class="bar-tooltip">
                      <div class="tooltip-date">{{ item.date }}</div>
                      <div class="tooltip-row">
                        <span class="tooltip-dot success"></span>
                        <span>成功</span>
                        <span class="tooltip-value">{{ item.success }}</span>
                      </div>
                      <div class="tooltip-row">
                        <span class="tooltip-dot fail"></span>
                        <span>失败</span>
                        <span class="tooltip-value">{{ item.fail }}</span>
                      </div>
                      <div class="tooltip-divider"></div>
                      <div class="tooltip-row reward">
                        <span>奖励</span>
                        <span class="tooltip-value">{{ item.reward_display }}</span>
                      </div>
                    </div>
                  </Transition>
                </div>
              </div>
            </div>
          </div>
          <!-- 空状态 -->
          <div class="chart-empty" v-else>
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
          <div class="monthly-list">
            <div v-for="item in monthlyData" :key="item.month" class="monthly-item">
              <div class="month-info">
                <div class="month-name">{{ formatMonth(item.month) }}</div>
                <div class="month-stats">
                  <span class="success">{{ item.success }}</span>
                  <span class="separator">/</span>
                  <span class="total">{{ item.total }}</span>
                </div>
              </div>
              <div class="month-progress">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{ width: item.success_rate + '%' }"
                  ></div>
                </div>
                <div class="progress-rate">{{ item.success_rate }}%</div>
              </div>
              <div class="month-reward">{{ item.reward_display }}</div>
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
        <div class="ranking-table" v-if="accountStats.length > 0">
          <div class="ranking-header-row">
            <div class="col-rank">排名</div>
            <div class="col-account">账号</div>
            <div class="col-streak">连签</div>
            <div class="col-success">成功</div>
            <div class="col-rate">成功率</div>
            <div class="col-reward">累计奖励</div>
          </div>
          <div class="ranking-body">
            <div v-for="(item, index) in accountStats" :key="item.account_id" class="ranking-row">
              <div class="col-rank">
                <span class="rank-badge" :class="getRankClass(index)">{{ index + 1 }}</span>
              </div>
              <div class="col-account">
                <div class="account-info">
                  <span class="account-name">{{ item.username }}</span>
                  <n-tag v-if="item.health_status === 'unhealthy'" type="error" size="tiny" :bordered="false">异常</n-tag>
                </div>
              </div>
              <div class="col-streak">
                <span class="streak-badge" v-if="item.streak_days > 0">
                  <n-icon><FlameOutline /></n-icon>
                  {{ item.streak_days }}天
                </span>
                <span v-else class="no-streak">-</span>
              </div>
              <div class="col-success">{{ item.success_count }}</div>
              <div class="col-rate">
                <n-progress
                  type="line"
                  :percentage="item.success_rate"
                  :show-indicator="false"
                  :height="6"
                  :border-radius="3"
                  :color="getProgressColor(item.success_rate)"
                  style="width: 60px;"
                />
                <span class="rate-text">{{ item.success_rate }}%</span>
              </div>
              <div class="col-reward">{{ item.total_reward_display }}</div>
            </div>
          </div>
        </div>
        <n-empty v-else description="暂无数据" />
      </n-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import {
  CalendarOutline,
  TrophyOutline,
  GiftOutline,
  TrendingUpOutline,
  RefreshOutline,
  FlameOutline
} from '@vicons/ionicons5'
import { statisticsApi } from '../api'

const message = useMessage()

const overview = ref<any>({})
const dailyData = ref<any[]>([])
const monthlyData = ref<any[]>([])
const accountStats = ref<any[]>([])
const loadingAccounts = ref(false)

const dailyDays = ref(7)
const activeBar = ref(-1)

const displayDailyData = computed(() => {
  // 只显示最近 N 天的数据
  const days = dailyDays.value
  return dailyData.value.slice(-days)
})

const maxDailyValue = computed(() => {
  let max = 1
  for (const item of displayDailyData.value) {
    const total = item.success + item.fail
    if (total > max) max = total
  }
  return max
})

const getBarHeight = (value: number, max: number) => {
  if (max === 0) return 0
  return Math.max(2, (value / max) * 100)
}

const formatBarDate = (date: string) => {
  const [, month, day] = date.split('-')
  return `${month}/${day}`
}

const formatMonth = (month: string) => {
  const [, m] = month.split('-')
  return `${m}月`
}

const getRankClass = (index: number) => {
  if (index === 0) return 'gold'
  if (index === 1) return 'silver'
  if (index === 2) return 'bronze'
  return ''
}

const getProgressColor = (rate: number) => {
  if (rate >= 90) return '#18a058'
  if (rate >= 70) return '#f0a020'
  return '#d03050'
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
    const res = await statisticsApi.getDaily(60)  // 获取60天数据
    dailyData.value = res.data || []
  } catch (e: any) {
    console.error('Failed to load daily stats:', e)
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

onMounted(() => {
  loadOverview()
  loadDailyStats()
  loadMonthlyStats()
  loadAccountStats()
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
  background: white;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  position: relative;
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
  color: #1a1a2e;
}

.stat-sub {
  font-size: 14px;
  font-weight: 400;
  color: #999;
}

.stat-label {
  font-size: 13px;
  color: #999;
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
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  min-width: 0;
  overflow: hidden;
}

/* 签到趋势卡片特殊样式 */
.trend-card {
  background: linear-gradient(135deg, #fafbfc 0%, #f5f7fa 100%);
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
  color: #1a1a2e;
  letter-spacing: -0.02em;
}

/* 时间段切换按钮 */
.period-tabs {
  display: flex;
  background: rgba(0,0,0,0.04);
  border-radius: 8px;
  padding: 3px;
}

.period-tab {
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  color: #666;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.period-tab:hover {
  color: #333;
}

.period-tab.active {
  background: white;
  color: #00b38a;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.chart-body {
  padding: 0 20px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.monthly-body {
  padding: 12px 20px;
}

/* 空状态 */
.chart-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #999;
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
  gap: 20px;
  padding-top: 10px;
  border-top: 1px solid rgba(0,0,0,0.05);
}

/* 趋势图表 */
.trend-chart {
  display: flex;
  gap: 10px;
  flex: 1;
}

.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
  padding: 4px 0 24px;
  font-size: 10px;
  color: #999;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.chart-scroll-area {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

/* 自定义滚动条 */
.chart-scroll-area::-webkit-scrollbar {
  height: 4px;
}

.chart-scroll-area::-webkit-scrollbar-track {
  background: transparent;
}

.chart-scroll-area::-webkit-scrollbar-thumb {
  background: rgba(0,0,0,0.15);
  border-radius: 4px;
}

.chart-scroll-area::-webkit-scrollbar-thumb:hover {
  background: rgba(0,0,0,0.25);
}

.chart-bars-container {
  display: flex;
  gap: 6px;
  flex: 1;
  min-height: 100px;
}

.bar-column {
  /* 每个柱子占容器 1/7 宽度 */
  flex: 0 0 calc((100% - 36px) / 7);
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  cursor: pointer;
  padding-bottom: 20px;
}

.stacked-bar {
  flex: 1;
  width: 100%;
  max-width: 28px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  position: relative;
}

.bar-segment {
  width: 70%;
  border-radius: 4px 4px 0 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.bar-segment.success {
  background: linear-gradient(180deg, #00d4a0 0%, #00b38a 100%);
  border-radius: 4px 4px 0 0;
}

.bar-segment.fail {
  background: linear-gradient(180deg, #ff6b6b 0%, #ee5a5a 100%);
  border-radius: 4px 4px 0 0;
  margin-bottom: -1px;
}

.bar-segment.fail + .bar-segment.success {
  border-radius: 0;
}

.bar-column:hover .bar-segment {
  width: 85%;
  filter: brightness(1.1);
}

.bar-column:hover .bar-segment.success {
  box-shadow: 0 0 12px rgba(0, 179, 138, 0.4);
}

.bar-date {
  position: absolute;
  bottom: 0;
  font-size: 10px;
  color: #999;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.bar-column:hover .bar-date {
  color: #00b38a;
}

/* 悬浮提示 */
.bar-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: rgba(26, 26, 46, 0.95);
  backdrop-filter: blur(8px);
  border-radius: 10px;
  padding: 12px 14px;
  min-width: 130px;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.bar-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(26, 26, 46, 0.95);
}

.tooltip-date {
  font-size: 12px;
  font-weight: 600;
  color: white;
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.tooltip-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(255,255,255,0.8);
  margin-bottom: 6px;
}

.tooltip-row:last-child {
  margin-bottom: 0;
}

.tooltip-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.tooltip-dot.success {
  background: #00d4a0;
}

.tooltip-dot.fail {
  background: #ff6b6b;
}

.tooltip-value {
  margin-left: auto;
  font-weight: 600;
  color: white;
  font-variant-numeric: tabular-nums;
}

.tooltip-divider {
  height: 1px;
  background: rgba(255,255,255,0.1);
  margin: 8px 0;
}

.tooltip-row.reward {
  color: #f0a020;
}

.tooltip-row.reward .tooltip-value {
  color: #ffc107;
}

/* 提示框动画 */
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: all 0.2s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(4px);
}

/* 图例 */
.chart-legend {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(0,0,0,0.05);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
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

/* 月度列表 */
.monthly-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.monthly-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.month-info {
  width: 80px;
}

.month-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.month-stats {
  font-size: 11px;
  color: #999;
}

.month-stats .success { color: #18a058; }
.month-stats .separator { margin: 0 2px; }

.month-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #00b38a, #18a058);
  border-radius: 3px;
  transition: width 0.3s;
}

.progress-rate {
  width: 40px;
  font-size: 12px;
  color: #666;
  text-align: right;
}

.month-reward {
  width: 70px;
  font-size: 13px;
  font-weight: 500;
  color: #f0a020;
  text-align: right;
}

/* 账号排行 */
.ranking-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.ranking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.ranking-header h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
}

.ranking-table {
  padding: 0 20px 20px;
}

.ranking-header-row {
  display: grid;
  grid-template-columns: 60px 2fr 80px 80px 120px 100px;
  padding: 12px 0;
  font-size: 12px;
  font-weight: 500;
  color: #999;
  text-transform: uppercase;
  border-bottom: 1px solid #f0f0f0;
}

.ranking-body {
  max-height: 400px;
  overflow-y: auto;
}

.ranking-row {
  display: grid;
  grid-template-columns: 60px 2fr 80px 80px 120px 100px;
  padding: 12px 0;
  align-items: center;
  border-bottom: 1px solid #f5f5f5;
}

.ranking-row:last-child {
  border-bottom: none;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 600;
  background: #f0f0f0;
  color: #666;
}

.rank-badge.gold { background: linear-gradient(135deg, #ffd700, #ffb700); color: white; }
.rank-badge.silver { background: linear-gradient(135deg, #c0c0c0, #a0a0a0); color: white; }
.rank-badge.bronze { background: linear-gradient(135deg, #cd7f32, #b87333); color: white; }

.account-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.account-name {
  font-size: 13px;
  font-weight: 500;
  color: #1a1a2e;
}

.streak-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #f0a020;
  background: rgba(240,160,32,0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.no-streak {
  color: #ccc;
}

.col-success {
  font-size: 14px;
  font-weight: 600;
  color: #18a058;
}

.col-rate {
  display: flex;
  align-items: center;
  gap: 8px;
}

.rate-text {
  font-size: 12px;
  color: #666;
}

.col-reward {
  font-size: 13px;
  font-weight: 500;
  color: #f0a020;
}

@media (max-width: 900px) {
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }

  .ranking-header-row,
  .ranking-row {
    grid-template-columns: 40px 1fr 60px 60px 80px 70px;
  }
}
</style>
