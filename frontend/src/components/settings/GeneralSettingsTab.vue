<template>
  <UiLoading :show="loading">
    <div class="settings-pane">
      <div class="pane-head">
        <div class="pane-heading">
          <div class="pane-title"><SlidersHorizontal :size="15" />常规设置</div>
          <div class="pane-desc">定时签到、健康检查、失败重试、告警阈值与日志保留策略</div>
        </div>
      </div>

      <div class="settings-grid">
        <section class="setting-card">
          <header class="setting-card-head">
            <span class="setting-card-icon is-signal"><Clock :size="16" /></span>
            <div class="setting-card-heading">
              <span class="setting-card-name">自动签到</span>
              <span class="setting-card-hint">每天在指定时间批量签到</span>
            </div>
            <UiSwitch v-model:value="settings.auto_sign_enabled" size="small" />
          </header>
          <div class="setting-card-body">
            <template v-if="settings.auto_sign_enabled">
              <div class="setting-row">
                <span class="setting-row-label">签到时间</span>
                <UiTimeField v-model:value="signTimeValue" format="HH:mm" size="small" style="width: 104px;" />
              </div>
              <div class="setting-row" v-if="schedulerStatus.next_run">
                <span class="setting-row-label">下次执行</span>
                <UiTag size="small" type="info">{{ schedulerStatus.next_run }}</UiTag>
              </div>
            </template>
            <p v-else class="setting-off">功能已关闭</p>
          </div>
        </section>

        <section class="setting-card">
          <header class="setting-card-head">
            <span class="setting-card-icon is-ok"><Activity :size="16" /></span>
            <div class="setting-card-heading">
              <span class="setting-card-name">健康检查</span>
              <span class="setting-card-hint">定期检查账号凭证是否仍然有效</span>
            </div>
            <UiSwitch v-model:value="settings.health_check_enabled" size="small" />
          </header>
          <div class="setting-card-body">
            <div v-if="settings.health_check_enabled" class="setting-row">
              <span class="setting-row-label">检查间隔</span>
              <div class="setting-row-control">
                <UiNumberInput v-model:value="settings.health_check_interval" :min="1" :max="24" size="small" style="width: 76px;" />
                <span class="setting-row-unit">小时</span>
              </div>
            </div>
            <p v-else class="setting-off">功能已关闭</p>
          </div>
        </section>

        <section class="setting-card">
          <header class="setting-card-head">
            <span class="setting-card-icon is-warn"><RefreshCw :size="16" /></span>
            <div class="setting-card-heading">
              <span class="setting-card-name">失败重试</span>
              <span class="setting-card-hint">定时签到失败后按间隔自动重试</span>
            </div>
            <UiSwitch v-model:value="settings.sign_retry_enabled" size="small" />
          </header>
          <div class="setting-card-body">
            <template v-if="settings.sign_retry_enabled">
              <div class="setting-row">
                <span class="setting-row-label">最大次数</span>
                <div class="setting-row-control">
                  <UiNumberInput v-model:value="settings.sign_max_retries" :min="1" :max="10" size="small" style="width: 76px;" />
                  <span class="setting-row-unit">次</span>
                </div>
              </div>
              <div class="setting-row">
                <span class="setting-row-label">重试间隔</span>
                <div class="setting-row-control">
                  <UiNumberInput v-model:value="settings.sign_retry_interval" :min="5" :max="120" size="small" style="width: 76px;" />
                  <span class="setting-row-unit">分</span>
                </div>
              </div>
            </template>
            <p v-else class="setting-off">功能已关闭</p>
          </div>
        </section>

        <section class="setting-card">
          <header class="setting-card-head">
            <span class="setting-card-icon is-info"><Bell :size="16" /></span>
            <div class="setting-card-heading">
              <span class="setting-card-name">签到推送</span>
              <span class="setting-card-hint">定时签到与定时重试的结果汇总</span>
            </div>
            <UiSwitch v-model:value="settings.sign_notify_enabled" size="small" />
          </header>
          <div class="setting-card-body">
            <template v-if="settings.sign_notify_enabled">
              <div class="setting-stack">
                <span class="setting-row-label">推送渠道</span>
                <UiSelect
                  v-model:value="settings.sign_notify_channel_ids"
                  multiple
                  size="small"
                  :options="notifyChannelOptions"
                  :loading="loadingChannels"
                  placeholder="选择接收定时签到汇总的渠道"
                  clearable
                />
              </div>
              <p class="setting-note">仅定时签到和定时重试会发送汇总，手动签到不推送</p>
            </template>
            <p v-else class="setting-off">功能已关闭</p>
          </div>
        </section>

        <section class="setting-card">
          <header class="setting-card-head">
            <span class="setting-card-icon is-bad"><TriangleAlert :size="16" /></span>
            <div class="setting-card-heading">
              <span class="setting-card-name">额度告警</span>
              <span class="setting-card-hint">余额低于阈值时高亮提示</span>
            </div>
          </header>
          <div class="setting-card-body">
            <div class="setting-row">
              <span class="setting-row-label">告警阈值</span>
              <UiNumberInput
                v-model:value="settings.quota_warning_threshold"
                :min="0"
                :precision="2"
                size="small"
                style="width: 104px;"
              >
                <template #prefix>$</template>
              </UiNumberInput>
            </div>
            <p class="setting-note">低于该额度时，账号列表和仪表盘会显示红色高亮与告警提示</p>
          </div>
        </section>

        <section class="setting-card">
          <header class="setting-card-head">
            <span class="setting-card-icon is-muted"><Archive :size="16" /></span>
            <div class="setting-card-heading">
              <span class="setting-card-name">日志保留</span>
              <span class="setting-card-hint">超期记录与归档文件的自动清理</span>
            </div>
          </header>
          <div class="setting-card-body">
            <div class="setting-row">
              <span class="setting-row-label">审计日志</span>
              <div class="setting-row-control">
                <UiNumberInput
                  v-model:value="settings.audit_log_retention_days"
                  :min="0"
                  :max="365"
                  size="small"
                  style="width: 76px;"
                />
                <span class="setting-row-unit">天</span>
              </div>
            </div>
            <div class="setting-row">
              <span class="setting-row-label">系统日志</span>
              <div class="setting-row-control">
                <UiNumberInput
                  v-model:value="settings.system_log_retention_days"
                  :min="0"
                  :max="365"
                  size="small"
                  style="width: 76px;"
                />
                <span class="setting-row-unit">天</span>
              </div>
            </div>
            <p class="setting-note">每天 03:17 自动清理，0 表示不清理；也可在「日志」标签页手动清理</p>
          </div>
        </section>
      </div>

      <div class="settings-footer">
        <div class="pane-note">
          <Info />
          <span>这里选择的渠道接收定时签到汇总；账号编辑里的渠道仅用于定时健康告警</span>
        </div>
        <UiButton type="primary" @click="saveSettings" :loading="saving">
          <template #icon><Save /></template>
          保存设置
        </UiButton>
      </div>
    </div>
  </UiLoading>
</template>

<script setup lang="ts">
import { UiButton, UiLoading, UiNumberInput, UiSelect, UiSwitch, UiTag, UiTimeField } from '../../ui'
import { ref, computed, onMounted, watch } from 'vue'
import { Activity, Archive, Bell, Clock, Info, RefreshCw, Save, SlidersHorizontal, TriangleAlert } from 'lucide-vue-next'
import { notifyApi, settingsApi } from '../../api'
import { apiError } from '../../utils/apiError'
import type { NotifyChannel, SelectOption } from '../../types'

const emit = defineEmits<{
  (e: 'update:auto-sign-enabled', v: boolean): void
}>()

const loading = ref(false)
const saving = ref(false)
const loadingChannels = ref(false)
const notifyChannelOptions = ref<SelectOption<number>[]>([])
const settings = ref({
  auto_sign_enabled: false,
  auto_sign_time: '08:00',
  health_check_enabled: true,
  health_check_interval: 6,
  sign_retry_enabled: true,
  sign_max_retries: 3,
  sign_retry_interval: 30,
  sign_notify_enabled: false,
  sign_notify_channel_ids: [] as number[],
  quota_warning_threshold: 5,
  audit_log_retention_days: 0,
  system_log_retention_days: 0
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
  loadingChannels.value = true
  try {
    const [settingsRes, schedulerRes, channelsRes] = await Promise.all([
      settingsApi.get(),
      settingsApi.getScheduler(),
      notifyApi.getChannels()
    ])
    if (settingsRes.data) {
      settings.value = { ...settings.value, ...settingsRes.data }
    }
    if (schedulerRes.data) {
      schedulerStatus.value = schedulerRes.data
    }
    notifyChannelOptions.value = (channelsRes.data || [])
      .filter((channel: NotifyChannel) => channel.is_enabled)
      .map((channel: NotifyChannel) => ({ label: channel.name, value: channel.id }))
  } catch (e) {
    window.$notify(apiError(e), 'error')
  } finally {
    loading.value = false
    loadingChannels.value = false
  }
}

const saveSettings = async () => {
  if (settings.value.sign_notify_enabled && settings.value.sign_notify_channel_ids.length === 0) {
    window.$notify('启用签到推送时请选择推送渠道', 'warning')
    return
  }

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
/**
 * 卡片网格：auto-fit + minmax 而不是写死两列 —— 侧栏折叠或超宽屏时
 * 会自动变三列，窄屏自动掉到一列，不用堆断点。
 */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(288px, 1fr));
  gap: var(--s3);
}

.setting-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding: 14px;
  border: 1px solid var(--line-faint);
  border-radius: var(--r-lg);
  background: var(--surface-raised);
  transition: border-color var(--transition-normal), box-shadow var(--transition-normal);
}

.setting-card:hover {
  border-color: var(--line);
  box-shadow: var(--lift-2);
}

.setting-card-head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

/* 图标用语义色的 wash 底 —— 六张卡各自一个色相，扫一眼就能定位 */
.setting-card-icon {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: var(--r-md);
}

.setting-card-icon.is-signal { background: var(--signal-wash); color: var(--signal-deep); }
.setting-card-icon.is-ok { background: var(--ok-wash); color: var(--ok); }
.setting-card-icon.is-warn { background: var(--warn-wash); color: var(--warn); }
.setting-card-icon.is-info { background: var(--info-wash); color: var(--info); }
.setting-card-icon.is-bad { background: var(--bad-wash); color: var(--bad); }
.setting-card-icon.is-muted { background: var(--surface-sunken); color: var(--ink-muted); }

.setting-card-heading {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  padding-top: 1px;
}

.setting-card-name {
  color: var(--ink-max);
  font-size: var(--fn-md);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--track-tight);
}

.setting-card-hint {
  color: var(--ink-faint);
  font-size: var(--fn-xs);
  line-height: 1.45;
}

.setting-card-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line-faint);
}

.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s3);
  min-height: 28px;
}

.setting-row-label {
  color: var(--ink);
  font-size: var(--fn-sm);
  font-weight: var(--weight-medium);
}

.setting-row-control {
  display: flex;
  align-items: center;
  gap: 7px;
}

.setting-row-unit {
  color: var(--ink-faint);
  font-size: var(--fn-xs);
}

.setting-stack {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.setting-note {
  color: var(--ink-faint);
  font-size: var(--fn-xs);
  line-height: var(--leading-loose);
}

/* 关闭态：只留一行灰字，卡片高度不塌，网格行高保持一致 */
.setting-off {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  color: var(--ink-ghost);
  font-size: var(--fn-sm);
}

.setting-off::before {
  content: "";
  width: 5px;
  height: 5px;
  border-radius: var(--r-full);
  background: var(--ink-ghost);
}

.settings-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s3);
  padding-top: var(--s4);
  border-top: 1px solid var(--line-faint);
}

.settings-footer .pane-note { flex: 1; }

@media (max-width: 560px) {
  .settings-footer {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
