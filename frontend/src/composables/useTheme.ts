import { ref, onMounted, onUnmounted } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'auto'

export function useTheme() {
  const currentTheme = ref<'light' | 'dark'>(getActiveTheme())
  const themeMode = ref<ThemeMode>(getStoredThemeMode())

  function getStoredThemeMode(): ThemeMode {
    const stored = localStorage.getItem('anyrouter-theme')
    if (stored === 'light' || stored === 'dark' || stored === 'auto') {
      return stored
    }
    return 'auto'
  }

  function getActiveTheme(): 'light' | 'dark' {
    const stored = localStorage.getItem('anyrouter-theme')
    if (stored === 'light') return 'light'
    if (stored === 'dark') return 'dark'
    // auto 模式：跟随系统
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  function setThemeMode(mode: ThemeMode) {
    themeMode.value = mode
    localStorage.setItem('anyrouter-theme', mode)
    applyTheme()
  }

  function applyTheme() {
    const active = getActiveTheme()
    currentTheme.value = active
    document.documentElement.setAttribute('data-theme', active)
  }

  function toggleTheme() {
    const newMode: ThemeMode = currentTheme.value === 'light' ? 'dark' : 'light'
    setThemeMode(newMode)
  }

  function handleSystemThemeChange(e: MediaQueryListEvent) {
    if (themeMode.value === 'auto') {
      currentTheme.value = e.matches ? 'dark' : 'light'
      applyTheme()
    }
  }

  const isDark = () => currentTheme.value === 'dark'
  const isLight = () => currentTheme.value === 'light'

  // 初始化
  onMounted(() => {
    applyTheme()
    window.matchMedia('(prefers-color-scheme: dark)')
      .addEventListener('change', handleSystemThemeChange)
  })

  onUnmounted(() => {
    window.matchMedia('(prefers-color-scheme: dark)')
      .removeEventListener('change', handleSystemThemeChange)
  })

  return {
    currentTheme,
    themeMode,
    setThemeMode,
    toggleTheme,
    isDark,
    isLight
  }
}
