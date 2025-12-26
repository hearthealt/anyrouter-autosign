<template>
  <div>
    <!-- 顶部操作栏 -->
    <n-space justify="space-between" align="center" style="margin-bottom: 20px;">
      <n-space align="center">
        <n-button text @click="router.push('/')">
          <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
        </n-button>
        <span style="font-weight: 600; font-size: 16px;">{{ account?.username || '账号详情' }}</span>
        <n-tag v-if="account" :type="account.is_active ? 'success' : 'default'" size="small">
          {{ account.is_active ? '启用' : '禁用' }}
        </n-tag>
      </n-space>
      <n-space>
        <n-button @click="handleRefreshInfo" :loading="refreshing">
          <template #icon><n-icon><RefreshOutline /></n-icon></template>
          刷新信息
        </n-button>
        <n-button type="primary" @click="handleSign" :loading="signing">
          <template #icon><n-icon><FlashOutline /></n-icon></template>
          立即签到
        </n-button>
      </n-space>
    </n-space>

    <n-spin :show="loading">
      <!-- 账号信息卡片 -->
      <n-grid :cols="2" :x-gap="16" :y-gap="16">
        <n-gi>
          <n-card title="账号信息">
            <template #header-extra>
              <n-button text size="small" @click="showEditModal = true">
                <template #icon><n-icon><CreateOutline /></n-icon></template>
                编辑
              </n-button>
            </template>
            <n-descriptions :column="1" label-placement="left">
              <n-descriptions-item label="用户名">
                {{ accountInfo?.username || account?.username || '-' }}
              </n-descriptions-item>
              <n-descriptions-item label="显示名">
                {{ accountInfo?.display_name || account?.display_name || '-' }}
              </n-descriptions-item>
              <n-descriptions-item label="用户ID">
                {{ accountInfo?.id || account?.anyrouter_user_id || '-' }}
              </n-descriptions-item>
              <n-descriptions-item label="用户组">
                {{ accountInfo?.group || '-' }}
              </n-descriptions-item>
              <n-descriptions-item label="所属分组">
                <n-tag v-if="accountInfo?.local_group || account?.group" size="small" :bordered="false" :style="{ background: getGroupColor((accountInfo?.local_group || account?.group)?.color), color: '#fff' }">
                  {{ (accountInfo?.local_group || account?.group)?.name }}
                </n-tag>
                <span v-else>未分组</span>
              </n-descriptions-item>
              <n-descriptions-item label="创建时间">
                {{ account ? formatDateTime(account.created_at) : '-' }}
              </n-descriptions-item>
              <n-descriptions-item label="最后更新">
                {{ account ? formatDateTime(account.updated_at) : '-' }}
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card title="额度信息">
            <template #header-extra>
              <n-button text size="small" @click="handleRefreshInfo" :loading="refreshing">
                <template #icon><n-icon><RefreshOutline /></n-icon></template>
              </n-button>
            </template>
            <n-descriptions :column="1" label-placement="left">
              <n-descriptions-item label="剩余额度">
                <n-text type="success" strong>{{ accountInfo?.quota_display || formatQuota(accountInfo?.quota || 0) }}</n-text>
              </n-descriptions-item>
              <n-descriptions-item label="已用额度">
                {{ accountInfo?.used_quota_display || formatQuota(accountInfo?.used_quota || 0) }}
              </n-descriptions-item>
              <n-descriptions-item label="剩余比例">
                <n-text type="info">{{ accountInfo?.quota_percent || '0.00%' }}</n-text>
              </n-descriptions-item>
              <n-descriptions-item label="总请求数">
                {{ (accountInfo?.request_count || 0).toLocaleString() }}
              </n-descriptions-item>
              <n-descriptions-item label="推广链接">
                <n-space v-if="accountInfo?.aff_code" align="center">
                  <n-text code style="font-size: 12px;">https://anyrouter.top/register?aff={{ accountInfo.aff_code }}</n-text>
                  <n-button text size="tiny" @click="copyAffLink">
                    <template #icon><n-icon><CopyOutline /></n-icon></template>
                  </n-button>
                </n-space>
                <span v-else>-</span>
              </n-descriptions-item>
              <n-descriptions-item label="推广人数">
                {{ accountInfo?.aff_count || 0 }}
              </n-descriptions-item>
              <n-descriptions-item label="推广所得">
                <n-text type="warning">{{ accountInfo?.aff_history_quota_display || formatQuota(accountInfo?.aff_history_quota || 0) }}</n-text>
              </n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 签到记录 -->
      <n-card title="签到记录" style="margin-top: 16px;">
        <n-data-table
          :columns="columns"
          :data="signLogs"
          :pagination="pagination"
          :loading="loadingLogs"
          remote
          @update:page="handlePageChange"
          @update:page-size="handlePageSizeChange"
        />
      </n-card>
    </n-spin>

    <!-- 编辑账号弹窗 -->
    <n-modal v-model:show="showEditModal" preset="dialog" title="更新账号信息" style="width: 500px;">
      <n-form :model="editForm">
        <n-form-item label="User ID (new-api-user)">
          <n-input v-model:value="editForm.user_id" placeholder="留空则不修改" />
        </n-form-item>
        <n-form-item label="Session Cookie">
          <n-input v-model:value="editForm.session_cookie" type="textarea" :rows="4" placeholder="留空则不修改" />
        </n-form-item>
        <n-form-item label="状态">
          <n-switch v-model:value="editForm.is_active">
            <template #checked>启用</template>
            <template #unchecked>禁用</template>
          </n-switch>
        </n-form-item>
        <n-form-item label="所属分组">
          <n-select
            v-model:value="editForm.group_id"
            :options="groups.map(g => ({ label: g.name, value: g.id }))"
            placeholder="选择分组"
            clearable
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" @click="handleUpdate" :loading="updating">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NTag } from 'naive-ui'
import { RefreshOutline, FlashOutline, CopyOutline, CreateOutline, ArrowBackOutline } from '@vicons/ionicons5'
import { accountApi, signApi, groupsApi } from '../api'
import { formatDateTime, formatQuota, copyToClipboard } from '../utils'

const route = useRoute()
const router = useRouter()
const message = useMessage()

const accountId = Number(route.params.id)
const loading = ref(false)
const refreshing = ref(false)
const signing = ref(false)
const loadingLogs = ref(false)
const updating = ref(false)

const account = ref<any>(null)
const accountInfo = ref<any>(null)
const signLogs = ref<any[]>([])

// 编辑弹窗
const showEditModal = ref(false)
const editForm = ref({
  user_id: '',
  session_cookie: '',
  is_active: true,
  group_id: null as number | null
})

// 分组
const groups = ref<any[]>([])

const getGroupColor = (color: string) => {
  const colors: Record<string, string> = {
    default: '#8b8b8b',
    blue: '#2080f0',
    green: '#18a058',
    red: '#d03050',
    orange: '#f0a020',
    purple: '#8b5cf6',
    pink: '#ec4899',
    cyan: '#06b6d4'
  }
  return colors[color] || colors.default
}

const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const columns = [
  {
    title: '签到时间',
    key: 'sign_time',
    render: (row: any) => formatDateTime(row.sign_time)
  },
  {
    title: '状态',
    key: 'success',
    width: 100,
    render: (row: any) => h(NTag, {
      type: row.success ? 'success' : 'error',
      size: 'small'
    }, { default: () => row.success ? '成功' : '失败' })
  },
  {
    title: '签到奖励',
    key: 'reward_quota',
    render: (row: any) => row.reward_quota ? formatQuota(row.reward_quota) : '-'
  },
  {
    title: '签到消息',
    key: 'message',
    ellipsis: { tooltip: true }
  }
]

const loadAccount = async () => {
  loading.value = true
  try {
    const res = await accountApi.get(accountId)
    account.value = res.data
    // 初始化编辑表单
    editForm.value.is_active = res.data.is_active
    editForm.value.group_id = res.data.group_id || null
  } catch (e: any) {
    message.error(e.message)
  } finally {
    loading.value = false
  }
}

const loadAccountInfo = async () => {
  try {
    // 使用缓存接口快速加载，不请求远程API
    const res = await accountApi.getCachedInfo(accountId)
    accountInfo.value = res.data
  } catch (e: any) {
    // 静默失败，不影响页面加载
    console.error('获取账号信息失败:', e.message)
  }
}

const loadSignLogs = async (page = 1) => {
  loadingLogs.value = true
  try {
    const res = await accountApi.getSignLogs(accountId, page, pagination.value.pageSize)
    signLogs.value = res.data?.items || []
    pagination.value.itemCount = res.data?.total || 0
    pagination.value.page = page
  } catch (e: any) {
    message.error(e.message)
  } finally {
    loadingLogs.value = false
  }
}

const handlePageChange = (page: number) => {
  loadSignLogs(page)
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  loadSignLogs(1)
}

const handleRefreshInfo = async () => {
  refreshing.value = true
  try {
    const res = await accountApi.getInfo(accountId)
    accountInfo.value = res.data
    message.success('账号信息已刷新')
  } catch (e: any) {
    message.error(e.message)
  } finally {
    refreshing.value = false
  }
}

const handleSign = async () => {
  signing.value = true
  try {
    const res = await signApi.sign(accountId)
    if (res.data?.message) {
      message.success(res.data.message)
    } else {
      message.success('签到成功')
    }
    // 签到后静默刷新信息（更新缓存）
    accountApi.getInfo(accountId).then(r => {
      accountInfo.value = r.data
    }).catch(() => {})
    loadSignLogs(1)
  } catch (e: any) {
    message.error(e.message)
  } finally {
    signing.value = false
  }
}

const handleUpdate = async () => {
  updating.value = true
  try {
    const data: any = {
      is_active: editForm.value.is_active
    }
    // 只有填写了才传递
    if (editForm.value.user_id.trim()) {
      data.user_id = editForm.value.user_id.trim()
    }
    if (editForm.value.session_cookie.trim()) {
      data.session_cookie = editForm.value.session_cookie.trim()
    }
    // 分组 ID (0 表示移除分组)
    if (editForm.value.group_id !== account.value?.group_id) {
      data.group_id = editForm.value.group_id || 0
    }

    await accountApi.update(accountId, data)
    message.success('账号信息已更新')
    showEditModal.value = false
    // 清空表单
    editForm.value.user_id = ''
    editForm.value.session_cookie = ''
    // 重新加载数据
    loadAccount()
    loadAccountInfo()
  } catch (e: any) {
    message.error(e.message)
  } finally {
    updating.value = false
  }
}

const copyAffLink = () => {
  if (accountInfo.value?.aff_code) {
    const link = `https://anyrouter.top/register?aff=${accountInfo.value.aff_code}`
    copyToClipboard(link).then(() => {
      message.success('推广链接已复制')
    }).catch(() => {
      message.error('复制失败')
    })
  }
}

const loadGroups = async () => {
  try {
    const res = await groupsApi.getList()
    groups.value = res.data || []
  } catch (e: any) {
    console.error('Failed to load groups:', e)
  }
}

onMounted(() => {
  loadAccount()
  loadAccountInfo()
  loadSignLogs()
  loadGroups()
})
</script>
