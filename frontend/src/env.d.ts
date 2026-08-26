/// <reference types="vite/client" />

/**
 * Vite 环境类型。
 *
 * 补上 `import.meta.env`（DEV / PROD 等）的类型，以及 .vue 单文件组件的模块声明 ——
 * 后者原先靠 vue-tsc 隐式处理，显式声明后编辑器里的跳转和补全更稳。
 */
declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

/** NotificationCenter.vue 在 window 上挂的全局通知入口。 */
declare global {
  interface Window {
    $notify: (
      message: string,
      type?: 'success' | 'error' | 'warning' | 'info',
      options?: Record<string, unknown>,
    ) => void
  }
}
