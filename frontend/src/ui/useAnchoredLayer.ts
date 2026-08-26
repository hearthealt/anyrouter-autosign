/**
 * 锚定浮层定位 —— popover / tooltip / dropdown / select / date-picker 共用。
 *
 * 不引第三方定位库。核心就三件事：算位置、越界翻面、贴边收拢。
 * 全项目的浮层定位逻辑只在这里，出 bug 也只可能出在这一处。
 *
 * 浮层渲染在 body 下（Teleport），用 fixed 定位，所以坐标直接用视口坐标，
 * 不需要处理祖先的 transform / overflow。
 */
import { onScopeDispose, ref, type Ref } from 'vue'

export type Placement =
  | 'top' | 'top-start' | 'top-end'
  | 'bottom' | 'bottom-start' | 'bottom-end'
  | 'left' | 'left-start' | 'left-end'
  | 'right' | 'right-start' | 'right-end'

export interface AnchoredOptions {
  placement?: Placement
  /** 锚点与浮层的间距 */
  offset?: number
  /** 贴边时与视口保留的边距 */
  padding?: number
  /** 是否把浮层最小宽度对齐锚点宽度（select 需要） */
  matchWidth?: boolean
}

export interface LayerPosition {
  top: number
  left: number
  /** 实际采用的位置（可能因翻面与请求的不同），用于箭头方向和入场动画方向 */
  placement: Placement
  minWidth?: number
}

function basePlacement(placement: Placement): 'top' | 'bottom' | 'left' | 'right' {
  return placement.split('-')[0] as 'top' | 'bottom' | 'left' | 'right'
}

function flip(placement: Placement): Placement {
  const [base, align] = placement.split('-')
  const opposite = { top: 'bottom', bottom: 'top', left: 'right', right: 'left' }[base] ?? 'bottom'
  return (align ? `${opposite}-${align}` : opposite) as Placement
}

function computeFor(
  placement: Placement,
  anchor: DOMRect,
  layer: { width: number; height: number },
  offset: number,
): { top: number; left: number } {
  const base = basePlacement(placement)
  const align = placement.split('-')[1]
  let top = 0
  let left = 0

  if (base === 'top' || base === 'bottom') {
    top = base === 'top' ? anchor.top - layer.height - offset : anchor.bottom + offset
    if (align === 'start') left = anchor.left
    else if (align === 'end') left = anchor.right - layer.width
    else left = anchor.left + (anchor.width - layer.width) / 2
  } else {
    left = base === 'left' ? anchor.left - layer.width - offset : anchor.right + offset
    if (align === 'start') top = anchor.top
    else if (align === 'end') top = anchor.bottom - layer.height
    else top = anchor.top + (anchor.height - layer.height) / 2
  }

  return { top, left }
}

function fitsInViewport(
  pos: { top: number; left: number },
  layer: { width: number; height: number },
  padding: number,
): boolean {
  return (
    pos.top >= padding &&
    pos.left >= padding &&
    pos.top + layer.height <= window.innerHeight - padding &&
    pos.left + layer.width <= window.innerWidth - padding
  )
}

/**
 * 返回一个响应式位置和一个 `update()`。
 *
 * 打开浮层后要先让它渲染出来（拿到真实尺寸）再调 `update()`，
 * 否则测不到高度就没法正确翻面 —— 调用方通常在 `nextTick` 里调。
 */
export function useAnchoredLayer(
  anchorRef: Ref<HTMLElement | null | undefined>,
  layerRef: Ref<HTMLElement | null | undefined>,
  options: AnchoredOptions = {},
) {
  const { placement: preferred = 'bottom-start', offset = 6, padding = 8, matchWidth = false } = options

  const position = ref<LayerPosition>({ top: 0, left: 0, placement: preferred })
  let raf = 0

  function measure() {
    const anchor = anchorRef.value
    const layer = layerRef.value
    if (!anchor || !layer) return

    const anchorRect = anchor.getBoundingClientRect()
    const size = { width: layer.offsetWidth, height: layer.offsetHeight }

    // 先试首选位置，放不下就翻到对面；对面也放不下就用首选并靠贴边收拢兜底
    let used = preferred
    let pos = computeFor(used, anchorRect, size, offset)
    if (!fitsInViewport(pos, size, padding)) {
      const flipped = flip(preferred)
      const flippedPos = computeFor(flipped, anchorRect, size, offset)
      if (fitsInViewport(flippedPos, size, padding)) {
        used = flipped
        pos = flippedPos
      }
    }

    // 贴边收拢：保证浮层始终完整可见
    pos.left = Math.min(Math.max(pos.left, padding), Math.max(padding, window.innerWidth - size.width - padding))
    pos.top = Math.min(Math.max(pos.top, padding), Math.max(padding, window.innerHeight - size.height - padding))

    position.value = {
      top: Math.round(pos.top),
      left: Math.round(pos.left),
      placement: used,
      minWidth: matchWidth ? Math.round(anchorRect.width) : undefined,
    }
  }

  function update() {
    if (raf) cancelAnimationFrame(raf)
    raf = requestAnimationFrame(() => {
      raf = 0
      measure()
    })
  }

  let bound = false

  /** 开始跟随滚动与尺寸变化。浮层打开时调。 */
  function track() {
    if (bound) return
    bound = true
    // capture 模式：任意祖先滚动都要跟，不只是 window
    window.addEventListener('scroll', update, true)
    window.addEventListener('resize', update)
    update()
  }

  /** 停止跟随。浮层关闭时调。 */
  function untrack() {
    if (!bound) return
    bound = false
    window.removeEventListener('scroll', update, true)
    window.removeEventListener('resize', update)
    if (raf) cancelAnimationFrame(raf)
    raf = 0
  }

  onScopeDispose(untrack)

  return { position, update, track, untrack }
}
