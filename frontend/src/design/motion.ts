/**
 * 动效内核 —— 弹簧是唯一的时间函数。
 *
 * 这里不导出任何 duration/easing。所有过渡都由阻尼弹簧求解，
 * 因为弹簧能被中途打断并从当前速度继续，而 ease 曲线做不到 ——
 * 这正是"物理动效"和"CSS 过渡"的区别。
 *
 * 提供：
 * - `spring()`      逐帧求解器，可中途改目标值
 * - `springTo()`    把弹簧结果写到元素样式上
 * - `stagger()`     列表错峰入场
 * - `flip()`        位置变化的 FLIP 过渡
 * - `magnetic()`    指针磁吸悬停
 * - `parallax()`    指针视差
 * - `countTo()`     数字滚动
 *
 * 每个入口都先查 motionReduced()：关掉动效时直接落终态，不留半截动画。
 */
import { motionReduced } from './useMotionPreference'

/* ────────────────────────────────────────────── 弹簧参数 */

export interface SpringConfig {
  /** 刚度。越大越快越"紧" */
  stiffness: number
  /** 阻尼。越大回弹越少 */
  damping: number
  /** 质量。越大越"沉" */
  mass: number
  /** 静止判定阈值 */
  restDelta: number
}

/** 预设。命名按用途而非数值，调用点读起来才有意义。 */
export const SPRING = {
  /** 界面默认：几乎不回弹，干脆 */
  crisp: { stiffness: 420, damping: 34, mass: 1, restDelta: 0.002 },
  /** 浮层进出：轻微过冲，有"弹出"感 */
  pop: { stiffness: 320, damping: 24, mass: 1, restDelta: 0.002 },
  /** 大块内容：沉稳 */
  heavy: { stiffness: 180, damping: 26, mass: 1.4, restDelta: 0.002 },
  /** 跟手：磁吸、视差这类跟随指针的 */
  follow: { stiffness: 260, damping: 22, mass: 0.7, restDelta: 0.0005 },
  /** 弹性：需要明显回弹的强调动作 */
  bouncy: { stiffness: 380, damping: 15, mass: 1, restDelta: 0.002 },
} satisfies Record<string, SpringConfig>

/* ────────────────────────────────────────────── 求解器 */

export interface SpringHandle {
  /** 改目标值。弹簧会带着当前速度继续，不会重启 */
  set(target: number): void
  /** 立刻落到某个值，速度清零 */
  jump(value: number): void
  get current(): number
  get velocity(): number
  stop(): void
}

/**
 * 单值阻尼弹簧。每帧调用 `onUpdate`，静止后自动停表。
 *
 * 用半隐式欧拉积分并把步长钳在 1/60s 上限 —— 标签页切回来时
 * requestAnimationFrame 会给一个很大的 dt，不钳会直接把弹簧炸飞。
 */
export function spring(
  initial: number,
  onUpdate: (value: number, velocity: number) => void,
  config: SpringConfig = SPRING.crisp,
): SpringHandle {
  let current = initial
  let target = initial
  let velocity = 0
  let frame = 0
  let last = 0

  const immediate = motionReduced()

  function step(now: number) {
    const dt = Math.min((now - last) / 1000, 1 / 60)
    last = now

    const displacement = current - target
    const accel = (-config.stiffness * displacement - config.damping * velocity) / config.mass
    velocity += accel * dt
    current += velocity * dt

    if (Math.abs(current - target) < config.restDelta && Math.abs(velocity) < config.restDelta) {
      current = target
      velocity = 0
      frame = 0
      onUpdate(current, 0)
      return
    }

    onUpdate(current, velocity)
    frame = requestAnimationFrame(step)
  }

  function start() {
    if (frame) return
    last = performance.now()
    frame = requestAnimationFrame(step)
  }

  return {
    set(next: number) {
      target = next
      if (immediate) {
        current = next
        velocity = 0
        onUpdate(current, 0)
        return
      }
      start()
    },
    jump(value: number) {
      if (frame) cancelAnimationFrame(frame)
      frame = 0
      current = value
      target = value
      velocity = 0
      onUpdate(current, 0)
    },
    get current() { return current },
    get velocity() { return velocity },
    stop() {
      if (frame) cancelAnimationFrame(frame)
      frame = 0
    },
  }
}

/* ────────────────────────────────────────────── 入场 / 退场 */

export interface EnterOptions {
  /** 起始位移，px。正数从下方进入 */
  y?: number
  x?: number
  /** 起始缩放 */
  scale?: number
  /** 起始透明度 */
  opacity?: number
  delay?: number
  config?: SpringConfig
}

/**
 * 弹簧入场。返回一个 Promise，动画结束后 resolve。
 *
 * 直接改 transform/opacity 而不用 Web Animations API，
 * 是为了让它能被 magnetic()/parallax() 这类持续动效接手而不打架。
 */
export function springIn(el: HTMLElement, options: EnterOptions = {}): Promise<void> {
  const { y = 16, x = 0, scale = 1, opacity = 0, delay = 0, config = SPRING.crisp } = options

  if (motionReduced()) {
    el.style.transform = ''
    el.style.opacity = ''
    return Promise.resolve()
  }

  return new Promise(resolve => {
    const run = () => {
      let done = 0
      const finish = () => { if (++done === 2) resolve() }

      const progress = spring(0, value => {
        const ty = y * (1 - value)
        const tx = x * (1 - value)
        const s = scale + (1 - scale) * value
        el.style.transform = `translate3d(${tx.toFixed(2)}px, ${ty.toFixed(2)}px, 0) scale(${s.toFixed(4)})`
        if (value === 1) {
          el.style.transform = ''
          finish()
        }
      }, config)

      const fade = spring(opacity, value => {
        el.style.opacity = String(value)
        if (value === 1) {
          el.style.opacity = ''
          finish()
        }
      }, config)

      progress.set(1)
      fade.set(1)
    }

    if (delay > 0) window.setTimeout(run, delay)
    else run()
  })
}

/** 列表错峰入场。`step` 是相邻元素的间隔毫秒。 */
export function stagger(
  elements: ArrayLike<HTMLElement>,
  options: EnterOptions & { step?: number } = {},
): Promise<void[]> {
  const { step = 42, ...rest } = options
  return Promise.all(
    Array.from(elements).map((el, index) =>
      springIn(el, { ...rest, delay: (rest.delay ?? 0) + index * step }),
    ),
  )
}

/* ────────────────────────────────────────────── FLIP */

type Rects = Map<Element, DOMRect>

/** 记录一组元素的当前位置，供 `flipPlay` 反算位移。 */
export function flipRead(elements: ArrayLike<Element>): Rects {
  const rects: Rects = new Map()
  for (const el of Array.from(elements)) rects.set(el, el.getBoundingClientRect())
  return rects
}

/**
 * DOM 变更后调用：把元素先"拉回"旧位置，再用弹簧送到新位置。
 * 只处理位移和缩放，不碰透明度 —— 透明度交给 springIn。
 */
export function flipPlay(before: Rects, config: SpringConfig = SPRING.heavy) {
  if (motionReduced()) return

  before.forEach((from, el) => {
    if (!(el instanceof HTMLElement) || !el.isConnected) return
    const to = el.getBoundingClientRect()
    const dx = from.left - to.left
    const dy = from.top - to.top
    const sx = from.width / (to.width || 1)
    const sy = from.height / (to.height || 1)

    // 位移和缩放都在 1px / 1% 以内就不值得动画
    if (Math.abs(dx) < 1 && Math.abs(dy) < 1 && Math.abs(sx - 1) < 0.01 && Math.abs(sy - 1) < 0.01) return

    const progress = spring(0, value => {
      const t = 1 - value
      const cx = dx * t
      const cy = dy * t
      const csx = 1 + (sx - 1) * t
      const csy = 1 + (sy - 1) * t
      el.style.transform = `translate3d(${cx.toFixed(2)}px, ${cy.toFixed(2)}px, 0) scale(${csx.toFixed(4)}, ${csy.toFixed(4)})`
      if (value === 1) el.style.transform = ''
    }, config)

    el.style.transformOrigin = 'top left'
    progress.set(1)
  })
}

/* ────────────────────────────────────────────── 指针交互 */

type Cleanup = () => void

/**
 * 磁吸悬停：元素朝指针方向轻微位移，离开后弹回。
 *
 * `strength` 是最大位移像素数。位移量按指针到中心的归一化距离缩放，
 * 所以靠近边缘时吸附最强 —— 这比线性跟随更像真的磁场。
 */
export function magnetic(el: HTMLElement, strength = 6, config: SpringConfig = SPRING.follow): Cleanup {
  if (motionReduced()) return () => {}

  let tx = 0
  let ty = 0
  const write = () => { el.style.transform = `translate3d(${tx.toFixed(2)}px, ${ty.toFixed(2)}px, 0)` }
  const sx = spring(0, value => { tx = value; write() }, config)
  const sy = spring(0, value => { ty = value; write() }, config)

  const onMove = (event: PointerEvent) => {
    const rect = el.getBoundingClientRect()
    const nx = (event.clientX - (rect.left + rect.width / 2)) / (rect.width / 2 || 1)
    const ny = (event.clientY - (rect.top + rect.height / 2)) / (rect.height / 2 || 1)
    sx.set(Math.max(-1, Math.min(1, nx)) * strength)
    sy.set(Math.max(-1, Math.min(1, ny)) * strength)
  }
  const onLeave = () => { sx.set(0); sy.set(0) }

  el.addEventListener('pointermove', onMove)
  el.addEventListener('pointerleave', onLeave)
  el.addEventListener('pointercancel', onLeave)

  return () => {
    el.removeEventListener('pointermove', onMove)
    el.removeEventListener('pointerleave', onLeave)
    el.removeEventListener('pointercancel', onLeave)
    sx.stop()
    sy.stop()
    el.style.transform = ''
  }
}

/**
 * 指针视差：在容器上监听，把归一化坐标写成 CSS 变量
 * `--px` / `--py`（范围 -1..1），由 CSS 决定各层位移多少。
 *
 * 用 CSS 变量而不是直接改 transform，是为了让一次监听驱动任意多层。
 */
export function parallax(container: HTMLElement, config: SpringConfig = SPRING.follow): Cleanup {
  if (motionReduced()) {
    container.style.setProperty('--px', '0')
    container.style.setProperty('--py', '0')
    return () => {}
  }

  const sx = spring(0, value => container.style.setProperty('--px', value.toFixed(4)), config)
  const sy = spring(0, value => container.style.setProperty('--py', value.toFixed(4)), config)

  const onMove = (event: PointerEvent) => {
    const rect = container.getBoundingClientRect()
    sx.set(Math.max(-1, Math.min(1, (event.clientX - (rect.left + rect.width / 2)) / (rect.width / 2 || 1))))
    sy.set(Math.max(-1, Math.min(1, (event.clientY - (rect.top + rect.height / 2)) / (rect.height / 2 || 1))))
  }
  const onLeave = () => { sx.set(0); sy.set(0) }

  container.addEventListener('pointermove', onMove)
  container.addEventListener('pointerleave', onLeave)

  return () => {
    container.removeEventListener('pointermove', onMove)
    container.removeEventListener('pointerleave', onLeave)
    sx.stop()
    sy.stop()
  }
}

/* ────────────────────────────────────────────── 数字滚动 */

export interface CountOptions {
  from?: number
  decimals?: number
  config?: SpringConfig
  format?: (value: number) => string
}

/**
 * 指标数字滚动。用弹簧而非线性插值，所以改目标值时能顺滑接管
 * （仪表盘轮询刷新时数字不会跳）。
 *
 * 返回的 handle 可以反复 `set()` 新目标。
 */
export function countTo(
  el: HTMLElement,
  target: number,
  options: CountOptions = {},
): SpringHandle {
  const { from = 0, decimals = 0, config = SPRING.heavy, format } = options
  const render = format ?? ((value: number) => value.toFixed(decimals))

  const handle = spring(from, value => { el.textContent = render(value) }, config)
  handle.set(target)
  return handle
}

/* ────────────────────────────────────────────── 工具 */

/** 把值从一个区间映射到另一个区间并钳位。 */
export function mapRange(value: number, inMin: number, inMax: number, outMin: number, outMax: number): number {
  const t = (value - inMin) / (inMax - inMin || 1)
  const clamped = Math.max(0, Math.min(1, t))
  return outMin + clamped * (outMax - outMin)
}

/**
 * 元素进入视口时触发一次回调。用于滚动入场。
 * 不做退出处理 —— 反复进出时重播动画很烦人。
 */
export function onceInView(
  el: Element,
  callback: () => void,
  options: IntersectionObserverInit = { threshold: 0.15 },
): Cleanup {
  if (motionReduced() || typeof IntersectionObserver === 'undefined') {
    callback()
    return () => {}
  }
  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        callback()
        observer.disconnect()
      }
    }
  }, options)
  observer.observe(el)
  return () => observer.disconnect()
}
