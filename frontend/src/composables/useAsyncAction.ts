import { ref, type Ref } from 'vue'
import { apiError } from '../utils/apiError'

export interface AsyncActionOptions<T> {
  errorMessage?: string
  successMessage?: string | ((result: T) => string | null | undefined)
  notifyOnError?: boolean
  onSuccess?: (result: T) => void | Promise<void>
  onError?: (e: unknown) => void
}

export interface AsyncActionReturn<TArgs extends unknown[], TResult> {
  run: (...args: TArgs) => Promise<TResult | undefined>
  loading: Ref<boolean>
  error: Ref<unknown>
}

export function useAsyncAction<TArgs extends unknown[], TResult>(
  action: (...args: TArgs) => Promise<TResult>,
  options: AsyncActionOptions<TResult> = {}
): AsyncActionReturn<TArgs, TResult> {
  const loading = ref(false)
  const error = ref<unknown>(null)
  const {
    errorMessage = '操作失败',
    successMessage,
    notifyOnError = true,
    onSuccess,
    onError
  } = options

  const run = async (...args: TArgs): Promise<TResult | undefined> => {
    loading.value = true
    error.value = null
    try {
      const result = await action(...args)
      if (successMessage) {
        const msg = typeof successMessage === 'function' ? successMessage(result) : successMessage
        if (msg) window.$notify?.(msg, 'success')
      }
      await onSuccess?.(result)
      return result
    } catch (e) {
      error.value = e
      if (notifyOnError) {
        window.$notify?.(apiError(e, errorMessage), 'error')
      }
      onError?.(e)
      return undefined
    } finally {
      loading.value = false
    }
  }

  return { run, loading, error }
}
