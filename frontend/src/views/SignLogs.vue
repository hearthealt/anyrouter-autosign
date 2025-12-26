<template>
  <div>
    <!-- 筛选条件 -->
    <n-card style="margin-bottom: 16px;">
      <n-space>
        <n-select
          v-model:value="filters.account_id"
          :options="accountOptions"
          placeholder="全部账号"
          clearable
          style="width: 180px;"
          @update:value="loadLogs(1)"
        />
        <n-select
          v-model:value="filters.success"
          :options="statusOptions"
          placeholder="全部状态"
          clearable
          style="width: 120px;"
          @update:value="loadLogs(1)"
        />
        <n-button @click="loadLogs(1)">
          <template #icon><n-icon><RefreshOutline /></n-icon></template>
          刷新
        </n-button>
      </n-space>
    </n-card>

    <!-- 签到日志表格 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="logs"
        :pagination="pagination"
        :loading="loading"
        :row-key="(row: any) => row.id"
        remote
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useMessage, NTag } from 'naive-ui'
import { RefreshOutline } from '@vicons/ionicons5'
import { signApi, accountApi } from '../api'
import { formatDateTime } from '../utils'

const message = useMessage()

const loading = ref(false)
const logs = ref<any[]>([])
const accounts = ref<any[]>([])

const filters = ref({
  account_id: null as number | null,
  success: null as boolean | null
})

const pagination = ref({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50]
})

const accountOptions = ref<{ label: string; value: number }[]>([])

const statusOptions = [
  { label: '成功', value: true },
  { label: '失败', value: false }
]

const columns = [
  {
    title: '账号',
    key: 'username',
    width: 150,
    ellipsis: { tooltip: true }
  },
  {
    title: '签到时间',
    key: 'sign_time',
    width: 180,
    render: (row: any) => formatDateTime(row.sign_time)
  },
  {
    title: '状态',
    key: 'success',
    width: 80,
    render: (row: any) => h(NTag, {
      type: row.success ? 'success' : 'error',
      size: 'small'
    }, { default: () => row.success ? '成功' : '失败' })
  },
  {
    title: '奖励',
    key: 'reward_display',
    width: 100,
    render: (row: any) => row.reward_quota ? row.reward_display : '-'
  },
  {
    title: '消息',
    key: 'message',
    ellipsis: { tooltip: true }
  }
]

const loadAccounts = async () => {
  try {
    const res = await accountApi.getList()
    accounts.value = res.data || []
    accountOptions.value = accounts.value.map((a: any) => ({
      label: a.username || `账号${a.id}`,
      value: a.id
    }))
  } catch (e: any) {
    message.error(e.message)
  }
}

const loadLogs = async (page = 1) => {
  loading.value = true
  try {
    const params: any = {
      page,
      size: pagination.value.pageSize
    }
    if (filters.value.account_id) {
      params.account_id = filters.value.account_id
    }
    if (filters.value.success !== null) {
      params.success = filters.value.success
    }

    const res = await signApi.getAllLogs(params)
    logs.value = res.data?.items || []
    pagination.value.itemCount = res.data?.total || 0
    pagination.value.page = page
  } catch (e: any) {
    message.error(e.message)
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  loadLogs(page)
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  loadLogs(1)
}

onMounted(() => {
  loadAccounts()
  loadLogs()
})
</script>
