<template>
  <n-spin :show="loading">
    <div class="settings-grid">
      <div class="setting-card">
        <div class="setting-card-header">
          <div class="setting-card-icon auto-sign">
            <n-icon :size="20"><TimeOutline /></n-icon>
          </div>
          <div class="setting-card-title">
            <span>自动签到</span>
            <n-switch v-model:value="settings.auto_sign_enabled" size="small" />
          </div>
        </div>
        <div class="setting-card-body" v-if="settings.auto_sign_enabled">
          <div class="setting-row">
            <span class="setting-row-label">签到时间</span>
            <n-time-picker v-model:value="signTimeValue" format="HH:mm" size="small" style="width: 100px;" />
          </div>
          <div class="setting-row" v-if="schedulerStatus.next_run">
            <span class="setting-row-label">下次执行</span>
            <n-tag size="small" type="info">{{ schedulerStatus.next_run }}</n-tag>
          </div>
        </div>
        <div class="setting-card-footer" v-else>
          <span class="setting-disabled-text">开启后将在指定时间自动签到</span>
        </div>
      </div>

      <div class="setting-card">
        <div class="setting-card-header">
          <div class="setting-card-icon health">
            <n-icon :size="20"><PulseOutline /></n-icon>
          </div>
          <div class="setting-card-title">
            <span>健康检查</span>
            <n-switch v-model:value="settings.health_check_enabled" size="small" />
          </div>
        </div>
        <div class="setting-card-body" v-if="settings.health_check_enabled">
          <div class="setting-row">
            <span class="setting-row-label">检查间隔</span>
            <div class="setting-row-control">
              <n-input-number v-model:value="settings.health_check_interval" :min="1" :max="24" size="small" style="width: 70px;" />
              <span class="setting-row-unit">小时</span>
            </div>
          </div>
        </div>
        <div class="setting-card-footer" v-else>
          <span class="setting-disabled-text">定期检查凭证有效性</span>
        </div>
      </div>

      <div class="setting-card">
        <div class="setting-card-header">
          <div class="setting-card-icon retry">
            <n-icon :size="20"><RefreshOutline /></n-icon>
          </div>
          <div class="setting-card-title">
            <span>失败重试</span>
            <n-switch v-model:value="settings.sign_retry_enabled" size="small" />
          </div>
        </div>
        <div class="setting-card-body" v-if="settings.sign_retry_enabled">
          <div class="setting-row">
            <span class="setting-row-label">最大次数</span>
            <div class="setting-row-control">
              <n-input-number v-model:value="settings.sign_max_retries" :min="1" :max="10" size="small" style="width: 70px;" />
              <span class="setting-row-unit">次</span>
            </div>
          </div>
          <div class="setting-row">
            <span class="setting-row-label">重试间隔</span>
            <div class="setting-row-control">
              <n-input-number v-model:value="settings.sign_retry_interval" :min="5" :max="120" size="small" style="width: 70px;" />
              <span class="setting-row-unit">分钟</span>
            </div>
          </div>
        </div>
        <div class="setting-card-footer" v-else>
          <span class="setting-disabled-text">签到失败后自动重试</span>
        </div>
      </div>

      <div class="setting-card">
        <div class="setting-card-header">
          <div class="setting-card-icon proxy">
            <n-icon :size="20"><GlobeOutline /></n-icon>
          </div>
          <div class="setting-card-title">
            <span>平台代理</span>
            <n-switch v-model:value="settings.anyrouter_proxy_enabled" size="small" />
          </div>
        </div>
        <div class="setting-card-body" v-if="settings.anyrouter_proxy_enabled">
          <div class="setting-stack">
            <span class="setting-row-label">代理地址</span>
            <n-input
              v-model:value="settings.anyrouter_proxy_url"
              size="small"
              clearable
              placeholder="http://127.0.0.1:7890"
            />
          </div>
          <div class="setting-note">
            仅影响服务端访问平台接口的请求，推荐填写 HTTP/HTTPS 代理地址
          </div>
        </div>
        <div class="setting-card-footer" v-else>
          <span class="setting-disabled-text">关闭后将直接连接目标平台</span>
        </div>
      </div>

      <div class="setting-card">
        <div class="setting-card-header">
          <div class="setting-card-icon quota">
            <n-icon :size="20"><WarningOutline /></n-icon>
          </div>
          <div class="setting-card-title">
            <span>额度告警</span>
          </div>
        </div>
        <div class="setting-card-body">
          <div class="setting-row">
            <span class="setting-row-label">阈值</span>
            <div class="setting-row-control">
              <n-input-number
                v-model:value="settings.quota_warning_threshold"
                :min="0"
                :precision="2"
                size="small"
                style="width: 96px;"
              >
                <template #prefix>$</template>
              </n-input-number>
            </div>
          </div>
          <div class="setting-note">
            低于该额度时，账号列表和仪表盘会显示红色高亮与告警提示
          </div>
        </div>
      </div>
    </div>

    <div class="settings-footer">
      <div class="settings-tip">
        <n-icon><InformationCircleOutline /></n-icon>
        签到推送渠道请在「控制台」编辑账号时配置
      </div>
      <n-button type="primary" @click="saveSettings" :loading="saving">
        保存设置
      </n-button>
    </div>
  </n-spin>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  TimeOutline,
  PulseOutline,
  RefreshOutline,
  GlobeOutline,
  WarningOutline,
  InformationCircleOutline
} from '@vicons/ionicons5'
import { settingsApi } from '../../api'
import { apiError } from '../../utils/apiError'

const emit = defineEmits<{
  (e: 'update:auto-sign-enabled', v: boolean): void
}>()

const loading = ref(false)
const saving = ref(false)
const settings = ref({
  auto_sign_enabled: false,
  auto_sign_time: '08:00',
  health_check_enabled: true,
  health_check_interval: 6,
  sign_retry_enabled: true,
  sign_max_retries: 3,
  sign_retry_interval: 30,
  anyrouter_proxy_enabled: false,
  anyrouter_proxy_url: '',
  quota_warning_threshold: 5
})
const schedulerStatus = ref({
  next_run: null as string | null
})

const signTimeValue = computed({
  get: () => {
    if (!settings.value.auto_sign_time) return null
    const [h, m] = settings.value.auto_sign_time.split(':').map(Number)
    return new Date(2000, 0, 1, h, m).getTime()
  },
  set: (val: number | null) => {
    if (val) {
      const d = new Date(val)
      settings.value.auto_sign_time = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
    }
  }
})

watch(() => settings.value.auto_sign_enabled, v => emit('update:auto-sign-enabled', v))

const load = async () => {
  loading.value = true
  try {
    const [settingsRes, schedulerRes] = await Promise.all([
      settingsApi.get(),
      settingsApi.getScheduler()
    ])
    if (settingsRes.data) {
      settings.value = { ...settings.value, ...settingsRes.data }
    }
    if (schedulerRes.data) {
      schedulerStatus.value = schedulerRes.data
    }
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  const proxyUrl = settings.value.anyrouter_proxy_url.trim()
  if (settings.value.anyrouter_proxy_enabled && !proxyUrl) {
    window.$notify('启用代理时请填写代理地址', 'warning')
    return
  }

  settings.value.anyrouter_proxy_url = proxyUrl
  saving.value = true
  try {
    await settingsApi.update(settings.value)
    window.$notify('设置保存成功', 'success')
    const res = await settingsApi.getScheduler()
    if (res.data) {
      schedulerStatus.value = res.data
    }
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    saving.value = false
  }
}

defineExpose({ load })

onMounted(load)
</script>

<style scoped>
.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.setting-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-md);
  padding: var(--spacing-4);
  transition: border-color var(--transition-fast);
}

.setting-card:hover {
  border-color: var(--border-color);
}

.setting-card-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-3);
}

.setting-card-icon {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.setting-card-icon.auto-sign { background: var(--primary-color-light); color: var(--primary-color); }
.setting-card-icon.health { background: var(--info-color-light); color: var(--info-color); }
.setting-card-icon.retry { background: var(--warning-color-light); color: var(--warning-color); }
.setting-card-icon.proxy { background: var(--cyan-light); color: var(--cyan-color); }
.setting-card-icon.quota { background: var(--warning-color-light); color: var(--warning-color); }

.setting-card-title {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-2);
}

.setting-card-title span {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.setting-card-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
}

.setting-card-footer {
  padding-top: var(--spacing-2);
  border-top: 1px solid var(--border-color-light);
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 28px;
}

.setting-row-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.setting-row-control {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.setting-row-unit {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.setting-stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.setting-note {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  line-height: 1.5;
}

.setting-disabled-text {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.settings-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-3);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
}

.settings-tip {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
}

@media (max-width: 900px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .settings-footer {
    flex-direction: column;
    align-items: stretch;
    gap: var(--spacing-2);
  }
}
</style>
