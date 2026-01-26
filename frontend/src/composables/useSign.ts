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
      window.$notify(res.data?.message || '签到成功', 'success')
      return res.data
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
      const { success_count, fail_count } = res.data
      window.$notify(`批量签到完成：成功 ${success_count}，失败 ${fail_count}`, 'success')
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
