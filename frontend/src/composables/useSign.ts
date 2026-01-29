import { ref } from 'vue'
import { signApi } from '../api'
import type { SignResult, BatchSignResult } from '../types'

export function useSign() {
  const signing = ref(false)
  const signingId = ref<number | null>(null)
  const batchSigning = ref(false)

  async function sign(accountId: number): Promise<SignResult | null> {
    signingId.value = accountId
    signing.value = true
    try {
      const res = await signApi.sign(accountId)
      const data = res.data
      let notifyType: 'success' | 'info' | 'error' = 'success'
      let message = data?.message || '签到成功'

      // 根据状态显示不同的提示
      if (data?.status === 'success') {
        message = `签到成功，获得 ${data?.reward_display || '0'}`
        notifyType = 'success'
      } else if (data?.status === 'already_signed') {
        message = '今日已签到，无新奖励'
        notifyType = 'info'
      } else if (data?.status === 'failed') {
        message = data?.message || '签到失败'
        notifyType = 'error'
      }

      window.$notify(message, notifyType)
      return data
    } catch (e: any) {
      window.$notify(e.message || '签到失败', 'error')
      return null
    } finally {
      signing.value = false
      signingId.value = null
    }
  }

  async function batchSign(): Promise<BatchSignResult | null> {
    batchSigning.value = true
    try {
      const res = await signApi.batchSign()
      const { success_count, fail_count, already_signed_count = 0 } = res.data
      const message = `签到完成 - 成功 ${success_count}，已签过 ${already_signed_count}，失败 ${fail_count}`
      window.$notify(message, 'success')
      return res.data
    } catch (e: any) {
      window.$notify(e.message || '批量签到失败', 'error')
      return null
    } finally {
      batchSigning.value = false
    }
  }

  function isSigningAccount(accountId: number): boolean {
    return signingId.value === accountId
  }

  return {
    signing,
    signingId,
    batchSigning,
    sign,
    batchSign,
    isSigningAccount
  }
}
