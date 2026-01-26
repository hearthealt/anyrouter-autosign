<template>
  <div class="settings-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-title">
        <div class="title-icon">⚙️</div>
        <div class="title-text">
          <h1>系统设置</h1>
          <p>配置自动签到、推送渠道和数据备份</p>
        </div>
      </div>
    </div>

    <!-- 快捷操作栏 -->
    <div class="quick-actions">
      <div class="quick-action-card" @click="activeTab = 'basic'">
        <div class="quick-action-icon auto-sign">
          <n-icon :size="24"><TimeOutline /></n-icon>
        </div>
        <div class="quick-action-info">
          <span class="quick-action-title">自动签到</span>
          <span class="quick-action-status" :class="{ active: settings.auto_sign_enabled }">
            {{ settings.auto_sign_enabled ? '已开启' : '未开启' }}
          </span>
        </div>
      </div>
      <div class="quick-action-card" @click="activeTab = 'notify'">
        <div class="quick-action-icon notify">
          <n-icon :size="24"><NotificationsOutline /></n-icon>
        </div>
        <div class="quick-action-info">
          <span class="quick-action-title">推送渠道</span>
          <span class="quick-action-status">{{ channels.length }} 个渠道</span>
        </div>
      </div>
      <div class="quick-action-card" @click="activeTab = 'groups'">
        <div class="quick-action-icon groups">
          <n-icon :size="24"><FolderOpenOutline /></n-icon>
        </div>
        <div class="quick-action-info">
          <span class="quick-action-title">分组管理</span>
          <span class="quick-action-status">{{ groups.length }} 个分组</span>
        </div>
      </div>
      <div class="quick-action-card" @click="activeTab = 'backup'">
        <div class="quick-action-icon backup">
          <n-icon :size="24"><CloudUploadOutline /></n-icon>
        </div>
        <div class="quick-action-info">
          <span class="quick-action-title">数据备份</span>
          <span class="quick-action-status">{{ backupInfo.account_count || 0 }} 个账号</span>
        </div>
      </div>
    </div>

    <n-tabs v-model:value="activeTab" type="line" animated>
      <!-- 基础设置 -->
      <n-tab-pane name="basic" tab="自动签到">
        <n-spin :show="loadingSettings">
          <div class="settings-grid">
            <!-- 自动签到卡片 -->
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

            <!-- 健康检查卡片 -->
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

            <!-- 失败重试卡片 -->
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
          </div>

          <div class="settings-footer">
            <div class="settings-tip">
              <n-icon><InformationCircleOutline /></n-icon>
              签到推送渠道请在「控制台」编辑账号时配置
            </div>
            <n-button type="primary" @click="saveSettings" :loading="savingSettings">
              保存设置
            </n-button>
          </div>
        </n-spin>
      </n-tab-pane>

      <!-- 推送渠道 -->
      <n-tab-pane name="notify" tab="推送渠道">
        <n-card>
          <n-spin :show="loadingChannels">
            <!-- 头部区域 -->
            <div class="channel-header">
              <div class="channel-header-info">
                <div class="channel-header-title">推送渠道</div>
                <div class="channel-header-desc">配置签到结果通知方式，支持多种推送渠道</div>
              </div>
              <n-button type="primary" @click="showAddChannelModal">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                添加渠道
              </n-button>
            </div>

            <n-divider style="margin: 16px 0;" />

            <!-- 渠道列表 -->
            <div v-if="channels.length > 0" class="channel-grid">
              <div v-for="channel in channels" :key="channel.id" class="channel-card">
                <div class="channel-card-header">
                  <div class="channel-icon" :class="channel.channel_type">
                    <n-icon :size="20">
                      <component :is="getChannelIcon(channel.channel_type)" />
                    </n-icon>
                  </div>
                  <div class="channel-status">
                    <n-tag :type="channel.is_enabled ? 'success' : 'default'" size="small" :bordered="false">
                      {{ channel.is_enabled ? '已启用' : '已禁用' }}
                    </n-tag>
                  </div>
                </div>
                <div class="channel-card-body">
                  <div class="channel-name">{{ channel.name }}</div>
                  <div class="channel-type-label">{{ getChannelTypeName(channel.channel_type) }}</div>
                </div>
                <div class="channel-card-footer">
                  <n-button size="small" quaternary @click="testChannel(channel)" :loading="testingId === channel.id">
                    <template #icon><n-icon><SendOutline /></n-icon></template>
                    测试
                  </n-button>
                  <n-button size="small" quaternary @click="editChannel(channel)">
                    <template #icon><n-icon><CreateOutline /></n-icon></template>
                    编辑
                  </n-button>
                  <n-popconfirm @positive-click="deleteChannel(channel.id)">
                    <template #trigger>
                      <n-button size="small" quaternary class="delete-btn">
                        <template #icon><n-icon><TrashOutline /></n-icon></template>
                        删除
                      </n-button>
                    </template>
                    确定删除此渠道？
                  </n-popconfirm>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-state">
              <div class="empty-icon">
                <n-icon :size="48" color="#ddd"><NotificationsOutline /></n-icon>
              </div>
              <div class="empty-title">暂无推送渠道</div>
              <div class="empty-desc">添加推送渠道后，签到结果将自动通知到您</div>
              <n-button type="primary" @click="showAddChannelModal" style="margin-top: 16px;">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                添加第一个渠道
              </n-button>
            </div>
          </n-spin>
        </n-card>
      </n-tab-pane>

      <!-- 数据备份 -->
      <n-tab-pane name="backup" tab="数据备份">
        <n-card>
          <n-spin :show="loadingBackupInfo">
            <div class="backup-section">
              <div class="backup-header">
                <div class="backup-header-info">
                  <div class="backup-header-title">数据备份</div>
                  <div class="backup-header-desc">导出或导入系统数据，用于迁移或恢复</div>
                </div>
              </div>

              <n-divider style="margin: 16px 0;" />

              <!-- 数据统计 -->
              <div class="backup-stats">
                <div class="stat-item">
                  <div class="stat-value">{{ backupInfo.account_count || 0 }}</div>
                  <div class="stat-label">账号数量</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ backupInfo.sign_log_count || 0 }}</div>
                  <div class="stat-label">签到日志</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ backupInfo.notify_channel_count || 0 }}</div>
                  <div class="stat-label">推送渠道</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ backupInfo.setting_count || 0 }}</div>
                  <div class="stat-label">配置项</div>
                </div>
              </div>

              <n-divider style="margin: 16px 0;" />

              <!-- 导出备份 -->
              <div class="backup-action-section">
                <div class="action-info">
                  <div class="action-title">导出备份</div>
                  <div class="action-desc">将账号、设置、推送渠道等数据导出为 JSON 文件</div>
                </div>
                <div class="action-controls">
                  <n-checkbox v-model:checked="exportIncludeLogs">包含签到日志（最近1000条）</n-checkbox>
                  <n-button type="primary" @click="handleExport" :loading="exporting">
                    <template #icon><n-icon><DownloadOutline /></n-icon></template>
                    导出备份
                  </n-button>
                </div>
              </div>

              <n-divider style="margin: 16px 0;" />

              <!-- 导入备份 -->
              <div class="backup-action-section">
                <div class="action-info">
                  <div class="action-title">导入备份</div>
                  <div class="action-desc">从备份文件恢复数据（支持 JSON 格式）</div>
                </div>
                <div class="action-controls">
                  <n-checkbox v-model:checked="importOverwrite">覆盖现有数据</n-checkbox>
                  <n-upload
                    :show-file-list="false"
                    accept=".json"
                    @change="handleImportFile"
                  >
                    <n-button :loading="importing">
                      <template #icon><n-icon><CloudUploadOutline /></n-icon></template>
                      选择文件导入
                    </n-button>
                  </n-upload>
                </div>
              </div>

              <div class="backup-tip">
                <n-icon><InformationCircleOutline /></n-icon>
                备份文件包含敏感信息（如 Session Cookie），请妥善保管
              </div>
            </div>
          </n-spin>
        </n-card>
      </n-tab-pane>

      <!-- 分组管理 -->
      <n-tab-pane name="groups" tab="分组管理">
        <n-card>
          <n-spin :show="loadingGroups">
            <!-- 头部区域 -->
            <div class="channel-header">
              <div class="channel-header-info">
                <div class="channel-header-title">账号分组</div>
                <div class="channel-header-desc">创建分组来组织和管理账号</div>
              </div>
              <n-button type="primary" @click="showAddGroupModal">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                新建分组
              </n-button>
            </div>

            <n-divider style="margin: 16px 0;" />

            <!-- 分组列表 -->
            <div v-if="groups.length > 0" class="group-grid">
              <div v-for="group in groups" :key="group.id" class="group-card">
                <div class="group-card-header">
                  <div class="group-color-dot" :style="{ background: getGroupColor(group.color) }"></div>
                  <div class="group-account-count">
                    <n-tag size="small" :bordered="false">{{ group.account_count }} 个账号</n-tag>
                  </div>
                </div>
                <div class="group-card-body">
                  <div class="group-name">{{ group.name }}</div>
                  <div class="group-desc">{{ group.description || '暂无描述' }}</div>
                </div>
                <div class="group-card-footer">
                  <n-button size="small" quaternary @click="editGroup(group)">
                    <template #icon><n-icon><CreateOutline /></n-icon></template>
                    编辑
                  </n-button>
                  <n-popconfirm @positive-click="deleteGroup(group.id)">
                    <template #trigger>
                      <n-button size="small" quaternary class="delete-btn">
                        <template #icon><n-icon><TrashOutline /></n-icon></template>
                        删除
                      </n-button>
                    </template>
                    删除分组后，账号将变为未分组状态
                  </n-popconfirm>
                </div>
              </div>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-state">
              <div class="empty-icon">
                <n-icon :size="48" color="#ddd"><FolderOpenOutline /></n-icon>
              </div>
              <div class="empty-title">暂无分组</div>
              <div class="empty-desc">创建分组来更好地组织和管理您的账号</div>
              <n-button type="primary" @click="showAddGroupModal" style="margin-top: 16px;">
                <template #icon><n-icon><AddOutline /></n-icon></template>
                创建第一个分组
              </n-button>
            </div>
          </n-spin>
        </n-card>
      </n-tab-pane>

      <!-- 审计日志 -->
      <n-tab-pane name="audit" tab="审计日志">
        <n-card>
          <n-spin :show="loadingAuditLogs">
            <!-- 头部区域 -->
            <div class="channel-header">
              <div class="channel-header-info">
                <div class="channel-header-title">审计日志</div>
                <div class="channel-header-desc">记录系统中的所有敏感操作，包括登录、账号变更等</div>
              </div>
              <n-button @click="exportAuditLogs">
                <template #icon><n-icon><DownloadOutline /></n-icon></template>
                导出日志
              </n-button>
            </div>

            <n-divider style="margin: 16px 0;" />

            <!-- 筛选器 -->
            <div class="audit-filters">
              <n-select
                v-model:value="auditFilters.action"
                :options="auditActionOptions"
                placeholder="操作类型"
                clearable
                style="width: 160px;"
                size="small"
              />
              <n-date-picker
                v-model:value="auditFilters.dateRange"
                type="daterange"
                clearable
                size="small"
                style="width: 240px;"
              />
              <n-input
                v-model:value="auditFilters.keyword"
                placeholder="搜索关键词"
                clearable
                size="small"
                style="width: 160px;"
              />
              <n-button size="small" type="primary" @click="loadAuditLogs">
                <template #icon><n-icon><SearchOutline /></n-icon></template>
                查询
              </n-button>
            </div>

            <n-divider style="margin: 16px 0;" />

            <!-- 日志列表 -->
            <n-data-table
              :columns="auditColumns"
              :data="auditLogs"
              :pagination="auditPagination"
              :bordered="false"
              size="small"
              remote
              @update:page="handleAuditPageChange"
              @update:page-size="handleAuditPageSizeChange"
            />
          </n-spin>
        </n-card>
      </n-tab-pane>

      <!-- 系统日志 -->
      <n-tab-pane name="syslogs" tab="系统日志">
        <n-card>
          <n-spin :show="loadingSysLogs">
            <!-- 头部区域 -->
            <div class="channel-header">
              <div class="channel-header-info">
                <div class="channel-header-title">系统日志</div>
                <div class="channel-header-desc">查看应用运行日志，支持按级别筛选和关键词搜索</div>
              </div>
              <div class="log-header-actions">
                <n-checkbox v-model:checked="autoRefreshLogs" size="small">
                  自动刷新
                </n-checkbox>
                <n-button size="small" @click="loadSysLogs">
                  <template #icon><n-icon><RefreshOutline /></n-icon></template>
                  刷新
                </n-button>
              </div>
            </div>

            <n-divider style="margin: 16px 0;" />

            <!-- 筛选器 -->
            <div class="audit-filters">
              <n-select
                v-model:value="sysLogFilters.file"
                :options="logFileOptions"
                placeholder="选择日志文件"
                style="width: 180px;"
                size="small"
              />
              <n-select
                v-model:value="sysLogFilters.level"
                :options="logLevelOptions"
                placeholder="日志级别"
                clearable
                style="width: 120px;"
                size="small"
              />
              <n-input
                v-model:value="sysLogFilters.keyword"
                placeholder="搜索关键词"
                clearable
                size="small"
                style="width: 160px;"
                @keyup.enter="loadSysLogs"
              />
              <n-button size="small" type="primary" @click="loadSysLogs">
                <template #icon><n-icon><SearchOutline /></n-icon></template>
                查询
              </n-button>
              <n-button size="small" @click="downloadLogFile">
                <template #icon><n-icon><DownloadOutline /></n-icon></template>
                下载
              </n-button>
              <n-popconfirm @positive-click="clearLogFile">
                <template #trigger>
                  <n-button size="small" type="error" ghost>
                    <template #icon><n-icon><TrashOutline /></n-icon></template>
                    清空
                  </n-button>
                </template>
                确定清空此日志文件？
              </n-popconfirm>
            </div>

            <n-divider style="margin: 16px 0;" />

            <!-- 日志内容 -->
            <div class="log-container">
              <div v-if="sysLogs.length === 0" class="log-empty">
                暂无日志
              </div>
              <div v-else class="log-list">
                <div
                  v-for="(log, index) in sysLogs"
                  :key="index"
                  class="log-item"
                  :class="'log-level-' + (log.level || 'info').toLowerCase()"
                >
                  <span class="log-time">{{ log.timestamp }}</span>
                  <span class="log-level-tag">{{ log.level }}</span>
                  <span class="log-logger">{{ log.logger }}</span>
                  <span class="log-message">{{ log.message }}</span>
                  <span v-if="log.extra && Object.keys(log.extra).length > 0" class="log-extra">
                    {{ JSON.stringify(log.extra) }}
                  </span>
                </div>
              </div>
            </div>

            <!-- 加载更多 -->
            <div v-if="sysLogsHasMore" class="log-load-more">
              <n-button size="small" @click="loadMoreSysLogs" :loading="loadingMoreLogs">
                加载更多
              </n-button>
            </div>

            <!-- 日志文件统计 -->
            <div class="log-files-info" v-if="logFiles.length > 0">
              <n-divider style="margin: 16px 0;" />
              <div class="log-files-title">日志文件</div>
              <div class="log-files-grid">
                <div v-for="file in logFiles" :key="file.name" class="log-file-item">
                  <span class="log-file-name">{{ file.name }}</span>
                  <span class="log-file-size">{{ file.size_display }}</span>
                  <span class="log-file-time">{{ file.modified }}</span>
                </div>
              </div>
            </div>
          </n-spin>
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <!-- 添加/编辑渠道弹窗 -->
    <n-modal v-model:show="showChannelModal" :mask-closable="false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>{{ editingChannel ? '编辑渠道' : '添加渠道' }}</h3>
          <n-button text @click="showChannelModal = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>渠道名称</label>
            <n-input v-model:value="channelForm.name" placeholder="给渠道起个名字" />
          </div>
          <div class="form-item">
            <label>渠道类型</label>
            <n-select v-model:value="channelForm.channel_type" :options="channelTypeOptions" :disabled="!!editingChannel" />
          </div>
          <div class="form-item">
            <label>启用状态</label>
            <n-switch v-model:value="channelForm.is_enabled" />
          </div>

          <!-- PushPlus -->
          <template v-if="channelForm.channel_type === 'pushplus'">
            <div class="form-item">
              <label>Token</label>
              <n-input v-model:value="channelForm.config.token" placeholder="PushPlus Token" />
            </div>
          </template>

          <!-- 微信公众号 -->
          <template v-if="channelForm.channel_type === 'wechat_mp'">
            <div class="form-item">
              <label>AppID</label>
              <n-input v-model:value="channelForm.config.app_id" placeholder="公众号 AppID" />
            </div>
            <div class="form-item">
              <label>AppSecret</label>
              <n-input v-model:value="channelForm.config.app_secret" type="password" placeholder="公众号 AppSecret" />
            </div>
            <div class="form-item">
              <label>模板消息 ID</label>
              <n-input v-model:value="channelForm.config.template_id" placeholder="模板消息 ID" />
            </div>
            <div class="form-item">
              <label>接收者 OpenID</label>
              <n-input v-model:value="channelForm.config.openid" placeholder="接收消息的用户 OpenID" />
            </div>
          </template>

          <!-- 企业微信 -->
          <template v-if="channelForm.channel_type === 'wechat_work'">
            <div class="form-item">
              <label>Webhook URL</label>
              <n-input v-model:value="channelForm.config.webhook_url" placeholder="企业微信机器人 Webhook" />
            </div>
          </template>

          <!-- 钉钉 -->
          <template v-if="channelForm.channel_type === 'dingtalk'">
            <div class="form-item">
              <label>Webhook URL</label>
              <n-input v-model:value="channelForm.config.webhook_url" placeholder="钉钉机器人 Webhook" />
            </div>
            <div class="form-item">
              <label>签名密钥</label>
              <n-input v-model:value="channelForm.config.secret" placeholder="可选" />
            </div>
          </template>

          <!-- 飞书 -->
          <template v-if="channelForm.channel_type === 'feishu'">
            <div class="form-item">
              <label>Webhook URL</label>
              <n-input v-model:value="channelForm.config.webhook_url" placeholder="飞书机器人 Webhook" />
            </div>
            <div class="form-item">
              <label>签名密钥</label>
              <n-input v-model:value="channelForm.config.secret" placeholder="可选" />
            </div>
          </template>

          <!-- 邮箱 -->
          <template v-if="channelForm.channel_type === 'email'">
            <div class="form-item">
              <label>SMTP 服务器</label>
              <n-input v-model:value="channelForm.config.smtp_host" placeholder="如 smtp.qq.com" />
            </div>
            <div class="form-item">
              <label>SMTP 端口</label>
              <n-input-number v-model:value="channelForm.config.smtp_port" :min="1" :max="65535" style="width: 100%;" />
            </div>
            <div class="form-item">
              <label>发件邮箱</label>
              <n-input v-model:value="channelForm.config.username" placeholder="发件人邮箱" />
            </div>
            <div class="form-item">
              <label>邮箱密码</label>
              <n-input v-model:value="channelForm.config.password" type="password" placeholder="密码或授权码" />
            </div>
            <div class="form-item">
              <label>使用 SSL</label>
              <n-switch v-model:value="channelForm.config.use_ssl" />
            </div>
          </template>
        </div>
        <div class="modal-footer">
          <n-button @click="showChannelModal = false">取消</n-button>
          <n-button type="primary" @click="saveChannel" :loading="savingChannel">保存</n-button>
        </div>
      </div>
    </n-modal>

    <!-- 添加/编辑分组弹窗 -->
    <n-modal v-model:show="showGroupModal" :mask-closable="false">
      <div class="modal-container">
        <div class="modal-header">
          <h3>{{ editingGroup ? '编辑分组' : '新建分组' }}</h3>
          <n-button text @click="showGroupModal = false">
            <n-icon :size="20"><CloseOutline /></n-icon>
          </n-button>
        </div>
        <div class="modal-body">
          <div class="form-item">
            <label>分组名称</label>
            <n-input v-model:value="groupForm.name" placeholder="输入分组名称" />
          </div>
          <div class="form-item">
            <label>分组描述（可选）</label>
            <n-input v-model:value="groupForm.description" placeholder="输入分组描述" />
          </div>
          <div class="form-item">
            <label>分组颜色</label>
            <div class="color-picker">
              <div
                v-for="color in colorOptions"
                :key="color.value"
                class="color-option"
                :class="{ active: groupForm.color === color.value }"
                :style="{ background: color.hex }"
                @click="groupForm.color = color.value"
              >
                <n-icon v-if="groupForm.color === color.value" :size="14" color="#fff"><CheckmarkOutline /></n-icon>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <n-button @click="showGroupModal = false">取消</n-button>
          <n-button type="primary" @click="saveGroup" :loading="savingGroup">保存</n-button>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import type { Component } from 'vue'
import {
  AddOutline,
  CloseOutline,
  SendOutline,
  CreateOutline,
  TrashOutline,
  NotificationsOutline,
  LogoWechat,
  MailOutline,
  ChatbubbleOutline,
  PaperPlaneOutline,
  InformationCircleOutline,
  DownloadOutline,
  CloudUploadOutline,
  FolderOpenOutline,
  CheckmarkOutline,
  TimeOutline,
  PulseOutline,
  RefreshOutline,
  SearchOutline
} from '@vicons/ionicons5'
import { settingsApi, notifyApi, backupApi, groupsApi, auditApi, logsApi } from '../api'
import { getToken } from '../utils/auth'
import { channelTypes, getChannelTypeName } from '../utils'

// 渠道图标映射
const getChannelIcon = (type: string): Component => {
  const icons: Record<string, Component> = {
    pushplus: PaperPlaneOutline,
    wechat_mp: LogoWechat,
    wechat_work: LogoWechat,
    dingtalk: ChatbubbleOutline,
    feishu: ChatbubbleOutline,
    email: MailOutline
  }
  return icons[type] || NotificationsOutline
}


// Tab 控制
const activeTab = ref('basic')

// 基础设置
const loadingSettings = ref(false)
const savingSettings = ref(false)
const settings = ref({
  auto_sign_enabled: false,
  auto_sign_time: '08:00',
  health_check_enabled: true,
  health_check_interval: 6,
  sign_retry_enabled: true,
  sign_max_retries: 3,
  sign_retry_interval: 30
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

// 推送渠道
const loadingChannels = ref(false)
const channels = ref<any[]>([])
const testingId = ref<number | null>(null)

// 渠道表单
const showChannelModal = ref(false)
const editingChannel = ref<any>(null)
const savingChannel = ref(false)
const channelForm = ref({
  name: '',
  channel_type: 'pushplus',
  is_enabled: true,
  config: {} as Record<string, any>
})

const channelTypeOptions = Object.entries(channelTypes).map(([value, label]) => ({ value, label }))

// 数据备份
const loadingBackupInfo = ref(false)
const backupInfo = ref<any>({})
const exportIncludeLogs = ref(false)
const exporting = ref(false)
const importOverwrite = ref(false)
const importing = ref(false)

// 分组管理
const loadingGroups = ref(false)
const groups = ref<any[]>([])
const showGroupModal = ref(false)
const editingGroup = ref<any>(null)
const savingGroup = ref(false)
const groupForm = ref({
  name: '',
  description: '',
  color: 'default'
})

const colorOptions = [
  { value: 'default', hex: '#8b8b8b' },
  { value: 'blue', hex: '#2080f0' },
  { value: 'green', hex: '#18a058' },
  { value: 'red', hex: '#d03050' },
  { value: 'orange', hex: '#f0a020' },
  { value: 'purple', hex: '#8b5cf6' },
  { value: 'pink', hex: '#ec4899' },
  { value: 'cyan', hex: '#06b6d4' }
]

const getGroupColor = (color: string) => {
  const found = colorOptions.find(c => c.value === color)
  return found ? found.hex : '#8b8b8b'
}

const loadSettings = async () => {
  loadingSettings.value = true
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
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loadingSettings.value = false
  }
}

const saveSettings = async () => {
  savingSettings.value = true
  try {
    await settingsApi.update(settings.value)
    window.$notify('设置保存成功', 'success')
    // 重新加载调度器状态
    const res = await settingsApi.getScheduler()
    if (res.data) {
      schedulerStatus.value = res.data
    }
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    savingSettings.value = false
  }
}

const loadChannels = async () => {
  loadingChannels.value = true
  try {
    const res = await notifyApi.getChannels()
    channels.value = res.data || []
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loadingChannels.value = false
  }
}

const showAddChannelModal = () => {
  editingChannel.value = null
  channelForm.value = {
    name: '',
    channel_type: 'pushplus',
    is_enabled: true,
    config: {}
  }
  showChannelModal.value = true
}

const editChannel = (channel: any) => {
  editingChannel.value = channel
  channelForm.value = {
    name: channel.name,
    channel_type: channel.channel_type,
    is_enabled: channel.is_enabled,
    config: { ...channel.config }
  }
  showChannelModal.value = true
}

const saveChannel = async () => {
  if (!channelForm.value.name.trim()) {
    window.$notify('请输入渠道名称', 'warning')
    return
  }
  savingChannel.value = true
  try {
    // 转换字段名
    const payload = {
      type: channelForm.value.channel_type,
      name: channelForm.value.name,
      config: channelForm.value.config,
      is_enabled: channelForm.value.is_enabled
    }

    if (editingChannel.value) {
      await notifyApi.updateChannel(editingChannel.value.id, payload)
      window.$notify('渠道更新成功', 'success')
    } else {
      await notifyApi.createChannel(payload)
      window.$notify('渠道添加成功', 'success')
    }
    showChannelModal.value = false
    loadChannels()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    savingChannel.value = false
  }
}

const deleteChannel = async (id: number) => {
  try {
    await notifyApi.deleteChannel(id)
    window.$notify('渠道删除成功', 'success')
    loadChannels()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  }
}

const testChannel = async (channel: any) => {
  testingId.value = channel.id
  try {
    await notifyApi.testChannel(channel.id)
    window.$notify('测试消息已发送', 'success')
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    testingId.value = null
  }
}

// 备份功能
const loadBackupInfo = async () => {
  loadingBackupInfo.value = true
  try {
    const res = await backupApi.getInfo()
    backupInfo.value = res.data || {}
  } catch (e: any) {
    console.error('Failed to load backup info:', e)
  } finally {
    loadingBackupInfo.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const token = getToken()
    const url = `/api/v1/backup/export?include_logs=${exportIncludeLogs.value}`

    // 使用 fetch 下载文件
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error('导出失败')
    }

    const blob = await response.blob()
    const filename = `anyrouter_backup_${new Date().toISOString().slice(0, 10)}.json`

    // 创建下载链接
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)

    window.$notify('备份导出成功', 'success')
  } catch (e: any) {
    window.$notify(e.message || '导出失败', 'error')
  } finally {
    exporting.value = false
  }
}

const handleImportFile = async ({ file }: { file: { file: File } }) => {
  if (!file.file) return

  importing.value = true
  try {
    const res = await backupApi.import(file.file, importOverwrite.value)
    const data = res.data
    window.$notify(`导入成功: ${data.accounts} 个账号, ${data.notify_channels} 个渠道, ${data.settings} 个配置`, 'success')
    loadBackupInfo()
  } catch (e: any) {
    window.$notify(e.message || '导入失败', 'error')
  } finally {
    importing.value = false
  }
}

// 分组管理函数
const loadGroups = async () => {
  loadingGroups.value = true
  try {
    const res = await groupsApi.getList()
    groups.value = res.data || []
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loadingGroups.value = false
  }
}

const showAddGroupModal = () => {
  editingGroup.value = null
  groupForm.value = {
    name: '',
    description: '',
    color: 'default'
  }
  showGroupModal.value = true
}

const editGroup = (group: any) => {
  editingGroup.value = group
  groupForm.value = {
    name: group.name,
    description: group.description || '',
    color: group.color || 'default'
  }
  showGroupModal.value = true
}

const saveGroup = async () => {
  if (!groupForm.value.name.trim()) {
    window.$notify('请输入分组名称', 'warning')
    return
  }
  savingGroup.value = true
  try {
    const payload = {
      name: groupForm.value.name,
      description: groupForm.value.description || undefined,
      color: groupForm.value.color
    }

    if (editingGroup.value) {
      await groupsApi.update(editingGroup.value.id, payload)
      window.$notify('分组更新成功', 'success')
    } else {
      await groupsApi.create(payload)
      window.$notify('分组创建成功', 'success')
    }
    showGroupModal.value = false
    loadGroups()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    savingGroup.value = false
  }
}

const deleteGroup = async (id: number) => {
  try {
    await groupsApi.delete(id)
    window.$notify('分组删除成功', 'success')
    loadGroups()
  } catch (e: any) {
    window.$notify(e.message, 'error')
  }
}

// 审计日志
const loadingAuditLogs = ref(false)
const auditLogs = ref<any[]>([])
const auditFilters = ref({
  action: null as string | null,
  dateRange: null as [number, number] | null,
  keyword: ''
})
const auditPagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100]
})
const auditActionOptions = ref<{ label: string; value: string }[]>([])

// 审计日志表格列
const auditColumns = [
  {
    title: '时间',
    key: 'created_at',
    width: 160,
    render: (row: any) => row.created_at?.replace('T', ' ').substring(0, 19) || '-'
  },
  {
    title: '操作类型',
    key: 'action_name',
    width: 120
  },
  {
    title: '操作用户',
    key: 'username',
    width: 100,
    render: (row: any) => row.username || '-'
  },
  {
    title: '目标',
    key: 'target',
    width: 150,
    render: (row: any) => {
      if (row.target_name) {
        return `${row.target_type || ''}: ${row.target_name}`
      }
      return row.target_type || '-'
    }
  },
  {
    title: '详情',
    key: 'detail',
    ellipsis: { tooltip: true },
    render: (row: any) => {
      if (!row.detail) return '-'
      try {
        const detail = typeof row.detail === 'string' ? JSON.parse(row.detail) : row.detail
        return JSON.stringify(detail)
      } catch {
        return row.detail
      }
    }
  },
  {
    title: 'IP 地址',
    key: 'ip_address',
    width: 130,
    render: (row: any) => row.ip_address || '-'
  }
]

const loadAuditLogs = async () => {
  loadingAuditLogs.value = true
  try {
    const params: any = {
      page: auditPagination.value.page,
      size: auditPagination.value.pageSize
    }

    if (auditFilters.value.action) {
      params.action = auditFilters.value.action
    }
    if (auditFilters.value.dateRange) {
      params.start_date = new Date(auditFilters.value.dateRange[0]).toISOString().split('T')[0]
      params.end_date = new Date(auditFilters.value.dateRange[1]).toISOString().split('T')[0]
    }
    if (auditFilters.value.keyword) {
      params.keyword = auditFilters.value.keyword
    }

    const res = await auditApi.getLogs(params)
    auditLogs.value = res.data?.items || []
    auditPagination.value.itemCount = res.data?.total || 0
  } catch (e: any) {
    window.$notify(e.message, 'error')
  } finally {
    loadingAuditLogs.value = false
  }
}

const loadAuditActions = async () => {
  try {
    const res = await auditApi.getActions()
    const actions = res.data || {}
    auditActionOptions.value = Object.entries(actions).map(([value, label]) => ({
      value,
      label: label as string
    }))
  } catch (e: any) {
    console.error('Failed to load audit actions:', e)
  }
}

const handleAuditPageChange = (page: number) => {
  auditPagination.value.page = page
  loadAuditLogs()
}

const handleAuditPageSizeChange = (pageSize: number) => {
  auditPagination.value.pageSize = pageSize
  auditPagination.value.page = 1
  loadAuditLogs()
}

const exportAuditLogs = () => {
  const params: any = { format: 'csv' }
  if (auditFilters.value.action) {
    params.action = auditFilters.value.action
  }
  if (auditFilters.value.dateRange) {
    params.start_date = new Date(auditFilters.value.dateRange[0]).toISOString().split('T')[0]
    params.end_date = new Date(auditFilters.value.dateRange[1]).toISOString().split('T')[0]
  }

  const url = auditApi.export(params)
  const token = getToken()

  // 使用 fetch 下载
  fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
    .then(res => res.blob())
    .then(blob => {
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `audit_logs_${new Date().toISOString().slice(0, 10)}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
      window.$notify('导出成功', 'success')
    })
    .catch(() => {
      window.$notify('导出失败', 'error')
    })
}

// 系统日志
const loadingSysLogs = ref(false)
const loadingMoreLogs = ref(false)
const sysLogs = ref<any[]>([])
const sysLogsHasMore = ref(false)
const logFiles = ref<any[]>([])
const autoRefreshLogs = ref(false)
let autoRefreshTimer: any = null

const sysLogFilters = ref({
  file: 'app.log',
  level: null as string | null,
  keyword: ''
})
const sysLogOffset = ref(0)

const logFileOptions = ref<{ label: string; value: string }[]>([
  { label: 'app.log', value: 'app.log' }
])

const logLevelOptions = [
  { label: 'DEBUG', value: 'DEBUG' },
  { label: 'INFO', value: 'INFO' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'CRITICAL', value: 'CRITICAL' }
]

const loadLogFiles = async () => {
  try {
    const res = await logsApi.getFiles()
    logFiles.value = res.data || []
    // 更新文件选项
    if (logFiles.value.length > 0) {
      logFileOptions.value = logFiles.value.map((f: any) => ({
        label: `${f.name} (${f.size_display})`,
        value: f.name
      }))
    }
  } catch (e: any) {
    console.error('Failed to load log files:', e)
  }
}

const loadSysLogs = async () => {
  loadingSysLogs.value = true
  sysLogOffset.value = 0
  try {
    const params: any = {
      file: sysLogFilters.value.file,
      lines: 100,
      offset: 0
    }
    if (sysLogFilters.value.level) {
      params.level = sysLogFilters.value.level
    }
    if (sysLogFilters.value.keyword) {
      params.keyword = sysLogFilters.value.keyword
    }

    const res = await logsApi.getLogs(params)
    sysLogs.value = res.data?.logs || []
    sysLogsHasMore.value = res.data?.has_more || false
    sysLogOffset.value = sysLogs.value.length
  } catch (e: any) {
    window.$notify(e.message || '加载日志失败', 'error')
  } finally {
    loadingSysLogs.value = false
  }
}

const loadMoreSysLogs = async () => {
  loadingMoreLogs.value = true
  try {
    const params: any = {
      file: sysLogFilters.value.file,
      lines: 100,
      offset: sysLogOffset.value
    }
    if (sysLogFilters.value.level) {
      params.level = sysLogFilters.value.level
    }
    if (sysLogFilters.value.keyword) {
      params.keyword = sysLogFilters.value.keyword
    }

    const res = await logsApi.getLogs(params)
    const newLogs = res.data?.logs || []
    sysLogs.value = [...sysLogs.value, ...newLogs]
    sysLogsHasMore.value = res.data?.has_more || false
    sysLogOffset.value += newLogs.length
  } catch (e: any) {
    window.$notify(e.message || '加载更多失败', 'error')
  } finally {
    loadingMoreLogs.value = false
  }
}

const downloadLogFile = () => {
  const url = logsApi.download(sysLogFilters.value.file)
  const token = getToken()

  fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  })
    .then(res => res.blob())
    .then(blob => {
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = sysLogFilters.value.file
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
      window.$notify('下载成功', 'success')
    })
    .catch(() => {
      window.$notify('下载失败', 'error')
    })
}

const clearLogFile = async () => {
  try {
    await logsApi.clear(sysLogFilters.value.file)
    window.$notify('日志已清空', 'success')
    loadSysLogs()
    loadLogFiles()
  } catch (e: any) {
    window.$notify(e.message || '清空失败', 'error')
  }
}

// 自动刷新
watch(autoRefreshLogs, (val) => {
  if (val) {
    autoRefreshTimer = setInterval(() => {
      loadSysLogs()
    }, 5000)
  } else {
    if (autoRefreshTimer) {
      clearInterval(autoRefreshTimer)
      autoRefreshTimer = null
    }
  }
})

onUnmounted(() => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
  }
})

onMounted(() => {
  loadSettings()
  loadChannels()
  loadBackupInfo()
  loadGroups()
  loadAuditLogs()
  loadAuditActions()
  loadLogFiles()
  loadSysLogs()  // 默认加载日志
})
</script>

<style scoped>
.settings-page {

  margin: 0 auto;
  padding: var(--spacing-6);
}

/* 页面标题 */
.page-header {
  margin-bottom: var(--spacing-6);
}

.page-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.title-icon {
  font-size: 36px;
}

.title-text h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-1) 0;
}

.title-text p {
  font-size: var(--text-md);
  color: var(--text-tertiary);
  margin: 0;
}

/* 快捷操作栏 */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
}

.quick-action-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  padding: var(--spacing-4);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  cursor: pointer;
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-sm);
}

.quick-action-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.quick-action-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.quick-action-icon.auto-sign {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

.quick-action-icon.notify {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
}

.quick-action-icon.groups {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.quick-action-icon.backup {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.quick-action-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.quick-action-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.quick-action-status {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.quick-action-status.active {
  color: var(--success-color);
}

/* 自动签到设置 - 卡片网格布局 */
.settings-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-5);
  margin-bottom: var(--spacing-6);
}

.setting-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  padding: var(--spacing-5);
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-card);
}

.setting-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.setting-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.setting-card-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.setting-card-icon.auto-sign {
  background: var(--primary-gradient);
}

.setting-card-icon.health {
  background: var(--info-gradient);
}

.setting-card-icon.retry {
  background: var(--warning-gradient);
}

.setting-card-title {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.setting-card-title span {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.setting-card-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.setting-card-footer {
  padding-top: var(--spacing-2);
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.setting-disabled-text {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.settings-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--spacing-5);
  border-top: 1px solid var(--border-color-light);
}

.settings-tip {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--primary-color-light);
  border-radius: var(--radius-lg);
}

/* 旧样式保留兼容 */
.setting-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
}

.setting-info {
  flex: 1;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.setting-desc {
  font-size: 12px;
  color: #999;
}

.setting-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #999;
  padding: 12px 0;
}

.setting-actions {
  display: flex;
  justify-content: flex-end;
}

/* 推送渠道 - 头部 */
.channel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.channel-header-info {
  flex: 1;
}

.channel-header-title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.channel-header-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

/* 推送渠道 - 卡片网格 */
.channel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-4);
}

.channel-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  padding: var(--spacing-5);
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-card);
}

.channel-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.channel-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.channel-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  background: var(--primary-gradient);
}

.channel-icon.pushplus {
  background: var(--primary-gradient);
}

.channel-icon.wechat_mp {
  background: var(--success-gradient);
}

.channel-icon.wechat_work {
  background: var(--success-gradient);
}

.channel-icon.dingtalk {
  background: var(--info-gradient);
}

.channel-icon.feishu {
  background: var(--purple-gradient);
}

.channel-icon.email {
  background: var(--error-gradient);
}

.channel-card-body {
  margin-bottom: var(--spacing-4);
}

.channel-name {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.channel-type-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.channel-card-footer {
  display: flex;
  gap: var(--spacing-1);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--border-color-light);
}

.channel-card-footer .n-button {
  flex: 1;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 20px;
}

.empty-icon {
  margin-bottom: var(--spacing-4);
}

.empty-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-2);
}

.empty-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.delete-btn:hover {
  color: var(--error-color) !important;
}

/* Modal */
.modal-container {
  width: 500px;
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-5) var(--spacing-6);
  border-bottom: 1px solid var(--border-color-light);
}

.modal-header h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
}

.modal-body {
  padding: var(--spacing-6);
  max-height: 60vh;
  overflow-y: auto;
}

.form-item {
  margin-bottom: var(--spacing-5);
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-2);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3);
  padding: var(--spacing-4) var(--spacing-6);
  border-top: 1px solid var(--border-color-light);
  background: var(--bg-card-hover);
}

/* 数据备份 */
.backup-section {
  padding: 0;
}

.backup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.backup-header-info {
  flex: 1;
}

.backup-header-title {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.backup-header-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.backup-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-4);
}

.backup-stats .stat-item {
  background: var(--bg-card-hover);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
  text-align: center;
  transition: all var(--transition-fast);
}

.backup-stats .stat-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.backup-stats .stat-value {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--primary-color);
}

.backup-stats .stat-label {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-top: var(--spacing-1);
}

.backup-action-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-3) 0;
}

.action-info {
  flex: 1;
}

.action-title {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.action-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.action-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.backup-tip {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--text-sm);
  color: var(--warning-color);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--warning-color-light);
  border-radius: var(--radius-lg);
  border-left: 3px solid var(--warning-color);
  margin-top: 16px;
}

/* 分组管理 */
.group-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-4);
}

.group-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-xl);
  padding: var(--spacing-5);
  transition: all var(--transition-normal);
  box-shadow: var(--shadow-card);
}

.group-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.group-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-3);
}

.group-color-dot {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
}

.group-card-body {
  margin-bottom: var(--spacing-4);
}

.group-name {
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.group-desc {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.group-card-footer {
  display: flex;
  gap: var(--spacing-1);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--border-color-light);
}

.group-card-footer .n-button {
  flex: 1;
}

/* 颜色选择器 */
.color-picker {
  display: flex;
  gap: var(--spacing-2);
  flex-wrap: wrap;
}

.color-option {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.active {
  border-color: #fff;
  box-shadow: 0 0 0 2px currentColor;
}

/* 审计日志筛选器 */
.audit-filters {
  display: flex;
  gap: var(--spacing-3);
  flex-wrap: wrap;
  align-items: center;
}

/* 系统日志 */
.log-header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.log-container {
  background: #0f172a;
  border-radius: var(--radius-lg);
  padding: var(--spacing-4);
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  border: 1px solid var(--border-color);
}

.log-empty {
  color: var(--text-tertiary);
  text-align: center;
  padding: var(--spacing-10);
}

.log-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.log-item {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  line-height: 1.5;
  color: #e2e8f0;
}

.log-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.log-time {
  color: #64748b;
  flex-shrink: 0;
}

.log-level-tag {
  padding: 0 6px;
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: var(--font-semibold);
  flex-shrink: 0;
}

.log-level-debug .log-level-tag {
  background: var(--cyan-color);
  color: #000;
}

.log-level-info .log-level-tag {
  background: var(--success-color);
  color: #000;
}

.log-level-warning .log-level-tag {
  background: var(--warning-color);
  color: #000;
}

.log-level-error .log-level-tag {
  background: var(--error-color);
  color: #fff;
}

.log-level-critical .log-level-tag {
  background: #ff00ff;
  color: #fff;
}

.log-logger {
  color: #69c0ff;
  flex-shrink: 0;
}

.log-message {
  color: #fff;
  flex: 1;
  word-break: break-all;
}

.log-extra {
  color: #888;
  font-size: 11px;
  width: 100%;
  padding-left: 20px;
}

.log-load-more {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.log-files-info {
  margin-top: 16px;
}

.log-files-title {
  font-size: 14px;
  font-weight: 500;
  color: #666;
  margin-bottom: 12px;
}

.log-files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
}

.log-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 13px;
}

.log-file-name {
  color: #1a1a2e;
  font-weight: 500;
}

.log-file-size {
  color: #666;
}

.log-file-time {
  color: #999;
  font-size: 12px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .quick-actions {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .settings-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .settings-page {
    padding: var(--spacing-4);
  }

  .quick-actions {
    grid-template-columns: 1fr 1fr;
    gap: var(--spacing-3);
  }

  .quick-action-card {
    padding: var(--spacing-3);
  }

  .quick-action-icon {
    width: 40px;
    height: 40px;
  }

  .channel-header,
  .backup-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .channel-header .n-button,
  .backup-header .n-button {
    width: 100%;
  }

  .channel-grid,
  .group-grid {
    grid-template-columns: 1fr;
  }

  .backup-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .backup-action-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .action-controls {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
  }

  .action-controls .n-button {
    width: 100%;
  }

  .modal-container {
    width: 95vw;
    max-width: 480px;
  }

  .setting-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .setting-item .n-switch,
  .setting-item .n-time-picker,
  .setting-item .n-input-number,
  .setting-item .n-tag {
    align-self: flex-end;
  }

  .audit-filters {
    flex-direction: column;
    align-items: stretch;
  }

  .audit-filters .n-select,
  .audit-filters .n-date-picker,
  .audit-filters .n-input {
    width: 100% !important;
  }
}

@media (max-width: 600px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }

  .settings-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .settings-footer .n-button {
    width: 100%;
  }

  .quick-actions {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .backup-stats {
    grid-template-columns: 1fr;
  }
}
</style>
