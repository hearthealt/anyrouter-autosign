<template>
  <canvas ref="canvasRef" class="signal-field" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

interface FieldNode {
  x: number
  y: number
  vx: number
  vy: number
  phase: number
  radius: number
}

const props = withDefaults(defineProps<{
  density?: number
  intensity?: number
  interactive?: boolean
}>(), {
  density: 28,
  intensity: 0.72,
  interactive: true
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
const nodes: FieldNode[] = []
const pointer = { x: 0, y: 0, active: false }
let context: CanvasRenderingContext2D | null = null
let frame = 0
let width = 0
let height = 0
let dpr = 1
let signal = '#d4ff3f'
let line = '#262a31'
let ink = '#82878f'
let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null
let reduceMotion: MediaQueryList | null = null

function readPalette() {
  const styles = getComputedStyle(document.documentElement)
  signal = styles.getPropertyValue('--signal').trim() || signal
  line = styles.getPropertyValue('--line').trim() || line
  ink = styles.getPropertyValue('--ink-muted').trim() || ink
}

function seedNodes() {
  nodes.length = 0
  const count = Math.max(12, Math.round(props.density * Math.max(0.7, width / 1440)))
  for (let index = 0; index < count; index += 1) {
    nodes.push({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.16,
      vy: (Math.random() - 0.5) * 0.16,
      phase: Math.random() * Math.PI * 2,
      radius: Math.random() * 1.2 + 0.45
    })
  }
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  width = Math.max(1, rect.width)
  height = Math.max(1, rect.height)
  dpr = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = Math.round(width * dpr)
  canvas.height = Math.round(height * dpr)
  context = canvas.getContext('2d')
  context?.setTransform(dpr, 0, 0, dpr, 0, 0)
  seedNodes()
  draw(0)
}

function draw(time: number) {
  if (!context) return
  context.clearRect(0, 0, width, height)

  const t = time * 0.00018
  const connectionDistance = Math.min(190, width * 0.16)

  for (let index = 0; index < nodes.length; index += 1) {
    const node = nodes[index]
    const driftX = Math.cos(t + node.phase) * 0.018
    const driftY = Math.sin(t * 1.3 + node.phase) * 0.018

    node.vx = (node.vx + driftX) * 0.992
    node.vy = (node.vy + driftY) * 0.992

    if (props.interactive && pointer.active) {
      const dx = pointer.x - node.x
      const dy = pointer.y - node.y
      const distance = Math.hypot(dx, dy)
      if (distance < 260 && distance > 0) {
        const force = (1 - distance / 260) * 0.012
        node.vx += dx * force * 0.018
        node.vy += dy * force * 0.018
      }
    }

    node.x += node.vx
    node.y += node.vy

    if (node.x < -30) node.x = width + 30
    if (node.x > width + 30) node.x = -30
    if (node.y < -30) node.y = height + 30
    if (node.y > height + 30) node.y = -30

    for (let otherIndex = index + 1; otherIndex < nodes.length; otherIndex += 1) {
      const other = nodes[otherIndex]
      const dx = other.x - node.x
      const dy = other.y - node.y
      const distance = Math.hypot(dx, dy)
      if (distance >= connectionDistance) continue

      context.beginPath()
      context.moveTo(node.x, node.y)
      context.lineTo(other.x, other.y)
      context.globalAlpha = (1 - distance / connectionDistance) * 0.16 * props.intensity
      context.strokeStyle = line
      context.lineWidth = 0.7
      context.stroke()
    }
  }

  nodes.forEach((node, index) => {
    context!.beginPath()
    context!.arc(node.x, node.y, node.radius, 0, Math.PI * 2)
    context!.globalAlpha = (index % 6 === 0 ? 0.7 : 0.26) * props.intensity
    context!.fillStyle = index % 6 === 0 ? signal : ink
    context!.fill()
  })

  if (props.interactive && pointer.active) {
    const radius = 118 + Math.sin(t * 8) * 5
    context.beginPath()
    context.arc(pointer.x, pointer.y, radius, 0, Math.PI * 2)
    context.globalAlpha = 0.12 * props.intensity
    context.strokeStyle = signal
    context.lineWidth = 0.8
    context.stroke()

    context.beginPath()
    context.arc(pointer.x, pointer.y, 4, 0, Math.PI * 2)
    context.globalAlpha = 0.55 * props.intensity
    context.fillStyle = signal
    context.fill()
  }

  context.globalAlpha = 1
  if (!reduceMotion?.matches) frame = requestAnimationFrame(draw)
}

function onPointerMove(event: PointerEvent) {
  const canvas = canvasRef.value
  if (!canvas || event.pointerType === 'touch') return
  const rect = canvas.getBoundingClientRect()
  pointer.x = event.clientX - rect.left
  pointer.y = event.clientY - rect.top
  pointer.active = pointer.x >= 0 && pointer.x <= rect.width && pointer.y >= 0 && pointer.y <= rect.height
}

function onPointerLeave() {
  pointer.active = false
}

function restartAnimation() {
  cancelAnimationFrame(frame)
  draw(performance.now())
}

onMounted(() => {
  readPalette()
  reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
  resizeObserver = new ResizeObserver(resize)
  if (canvasRef.value) resizeObserver.observe(canvasRef.value)
  themeObserver = new MutationObserver(() => {
    readPalette()
    restartAnimation()
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  window.addEventListener('pointermove', onPointerMove, { passive: true })
  document.documentElement.addEventListener('mouseleave', onPointerLeave)
  reduceMotion.addEventListener('change', restartAnimation)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(frame)
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  reduceMotion?.removeEventListener('change', restartAnimation)
  window.removeEventListener('pointermove', onPointerMove)
  document.documentElement.removeEventListener('mouseleave', onPointerLeave)
})
</script>

<style scoped>
.signal-field {
  display: block;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
