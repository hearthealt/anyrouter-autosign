export function useClipboard() {
  async function copy(text: string, successMsg = '已复制到剪贴板'): Promise<boolean> {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
      } else {
        // 降级方案
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.left = '-999999px'
        textArea.style.top = '-999999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        textArea.remove()
      }
      window.$notify(successMsg, 'success')
      return true
    } catch (e) {
      window.$notify('复制失败', 'error')
      return false
    }
  }

  function copyToken(key: string): Promise<boolean> {
    const fullKey = key.startsWith('sk-') ? key : `sk-${key}`
    return copy(fullKey)
  }

  function copyUrl(url: string): Promise<boolean> {
    return copy(url, '已复制')
  }

  return {
    copy,
    copyToken,
    copyUrl
  }
}
