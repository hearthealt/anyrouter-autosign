import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import App from './App.vue'
import router from './router'
import './styles/global.css'
import { initTheme } from './utils'

// Polyfill: 为 wheel/mousewheel 事件添加 passive 标志
// 这可以改善页面滚动性能，并消除 Chrome 的性能警告
const originalAddEventListener = EventTarget.prototype.addEventListener
EventTarget.prototype.addEventListener = function (
  type: string,
  listener: EventListenerOrEventListenerObject,
  options?: boolean | AddEventListenerOptions
) {
  // 对于 wheel/mousewheel 事件，自动设置 passive: true
  if (type === 'wheel' || type === 'mousewheel') {
    const opts = typeof options === 'object' ? options : {}
    opts.passive = true
    return originalAddEventListener.call(this, type, listener, opts)
  }
  return originalAddEventListener.call(this, type, listener, options)
}

// 初始化主题
initTheme()

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

app.mount('#app')
