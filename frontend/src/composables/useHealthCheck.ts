import { ref } from 'vue'
import { accountApi } from '../api'
import type { HealthCheckResult, BatchHealthCheckResult } from '../types'

export function useHealthCheck() {
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
        window.$notify('账号状态正常', 'success')
      } else {
        window.$notify(`账号异常: ${res.data?.health_message || '凭证验证失败'}`, 'warning')
      }
      return res.data
    } catch (e: any) {
      window.$notify(e.message || '健康检查失败', 'error')
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
        window.$notify(`健康检查完成: ${healthy_count} 个正常, ${unhealthy_count} 个异常`, 'warning')
      } else {
        window.$notify(`健康检查完成: 所有 ${healthy_count} 个账号正常`, 'success')
      }
      return res.data
    } catch (e: any) {
      window.$notify(e.message || '健康检查失败', 'error')
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
