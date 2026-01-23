import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { accountApi } from '../api'
import type { HealthCheckResult, BatchHealthCheckResult } from '../types'

export function useHealthCheck() {
  const message = useMessage()
  const checking = ref(false)
  const checkingId = ref<number | null>(null)
  const batchChecking = ref(false)

  async function check(accountId: number): Promise<HealthCheckResult | null> {
    checkingId.value = accountId
    checking.value = true
    try {
      const res = await accountApi.healthCheck(accountId)
      const status = res.data?.health_status
      if (status === 'healthy') {
        message.success('账号状态正常')
      } else {
        message.warning(`账号异常: ${res.data?.health_message || '凭证验证失败'}`)
      }
      return res.data
    } catch (e: any) {
      message.error(e.message || '健康检查失败')
      return null
    } finally {
      checking.value = false
      checkingId.value = null
    }
  }

  async function checkAll(): Promise<BatchHealthCheckResult | null> {
    batchChecking.value = true
    try {
      const res = await accountApi.healthCheckAll()
      const { healthy_count, unhealthy_count } = res.data
      if (unhealthy_count > 0) {
        message.warning(`健康检查完成: ${healthy_count} 个正常, ${unhealthy_count} 个异常`)
      } else {
        message.success(`健康检查完成: 所有 ${healthy_count} 个账号正常`)
      }
      return res.data
    } catch (e: any) {
      message.error(e.message || '健康检查失败')
      return null
    } finally {
      batchChecking.value = false
    }
  }

  function isCheckingAccount(accountId: number): boolean {
    return checkingId.value === accountId
  }

  return {
    checking,
    checkingId,
    batchChecking,
    check,
    checkAll,
    isCheckingAccount
  }
}
