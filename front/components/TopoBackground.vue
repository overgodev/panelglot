<script setup lang="ts">
/**
 * Topographic backdrop: a PERIODIC value-noise height map traced with
 * marching-squares iso-lines into one seamless square tile, drawn ONCE at
 * mount. The tile repeats as the background of an oversized layer that pans
 * exactly one tile per cycle (GPU transform, linear infinite) - endless
 * forward drift with an invisible loop point, zero per-frame JS. Sits at
 * z-index -1; opaque --color-surface panels paint over it, so contours
 * never touch text contrast.
 */

// minor contours: bumped from ~5% to ~14% ink - the previous value was
// indistinguishable from the background at normal monitor brightness.
const MINOR = 'rgba(238, 242, 248, 0.14)'
// every 5th = "index contour": traced in the brand orange so the topo reads
// as an Endfield-style HUD survey map, not just noise.
const INDEX = 'rgba(246, 130, 31, 0.28)'
const CELL = 22 // marching-squares grid pitch (css px)
const LEVELS = 18 // more thresholds = tighter contour spacing
const INDEX_EVERY = 5
const TILE = 880 // css px, must be a multiple of CELL; the seamless period
const BASE_PERIOD = 3 // landform cells per tile edge on the base octave (~290px features)

const bg = ref('')

/** value noise that tiles with period TILE in both axes */
function makeTileNoise(octaves = 3): (x: number, y: number) => number {
  const lattices = Array.from({ length: octaves }, (_, k) => {
    const p = BASE_PERIOD << k
    const v = new Float32Array(p * p)
    for (let i = 0; i < v.length; i++) v[i] = Math.random()
    return { p, v }
  })
  const smooth = (t: number) => t * t * (3 - 2 * t)
  function sample(l: { p: number; v: Float32Array }, x: number, y: number) {
    const { p, v } = l
    const xi = Math.floor(x)
    const yi = Math.floor(y)
    const xf = smooth(x - xi)
    const yf = smooth(y - yi)
    const at = (ix: number, iy: number) =>
      v[(((iy % p) + p) % p) * p + (((ix % p) + p) % p)]!
    const a = at(xi, yi)
    const b = at(xi + 1, yi)
    const c = at(xi, yi + 1)
    const d = at(xi + 1, yi + 1)
    return a + (b - a) * xf + (c - a) * yf + (a - b - c + d) * xf * yf
  }
  return (x, y) => {
    let amp = 1
    let sum = 0
    let norm = 0
    for (const l of lattices) {
      sum += amp * sample(l, (x / TILE) * l.p, (y / TILE) * l.p)
      norm += amp
      amp *= 0.5
    }
    return sum / norm
  }
}

function drawTile() {
  const noise = makeTileNoise()
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = Math.round(TILE * dpr)
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.scale(dpr, dpr)
  ctx.lineWidth = 1

  // periodic field: row/col `cols` duplicates row/col 0, so contours cross the seam
  const cols = TILE / CELL
  const field = new Float32Array((cols + 1) * (cols + 1))
  for (let j = 0; j <= cols; j++)
    for (let i = 0; i <= cols; i++) field[j * (cols + 1) + i] = noise(i * CELL, j * CELL)
  const f = (i: number, j: number) => field[j * (cols + 1) + i]!

  // marching squares at each threshold; stroke per level
  for (let li = 0; li < LEVELS; li++) {
    const t = 0.18 + (0.64 * li) / (LEVELS - 1)
    ctx.strokeStyle = li % INDEX_EVERY === 0 ? INDEX : MINOR
    ctx.beginPath()
    for (let j = 0; j < cols; j++) {
      for (let i = 0; i < cols; i++) {
        const a = f(i, j)
        const b = f(i + 1, j)
        const c = f(i + 1, j + 1)
        const d = f(i, j + 1)
        let idx = 0
        if (a > t) idx |= 8
        if (b > t) idx |= 4
        if (c > t) idx |= 2
        if (d > t) idx |= 1
        if (idx === 0 || idx === 15) continue
        const x = i * CELL
        const y = j * CELL
        const lerp = (p: number, q: number) => (t - p) / (q - p)
        const top: [number, number] = [x + CELL * lerp(a, b), y]
        const right: [number, number] = [x + CELL, y + CELL * lerp(b, c)]
        const bottom: [number, number] = [x + CELL * lerp(d, c), y + CELL]
        const left: [number, number] = [x, y + CELL * lerp(a, d)]
        const seg = (p: [number, number], q: [number, number]) => {
          ctx.moveTo(p[0], p[1])
          ctx.lineTo(q[0], q[1])
        }
        switch (idx) {
          case 1:
          case 14:
            seg(left, bottom)
            break
          case 2:
          case 13:
            seg(bottom, right)
            break
          case 3:
          case 12:
            seg(left, right)
            break
          case 4:
          case 11:
            seg(top, right)
            break
          case 6:
          case 9:
            seg(top, bottom)
            break
          case 7:
          case 8:
            seg(top, left)
            break
          case 5: // saddle
            seg(top, left)
            seg(bottom, right)
            break
          case 10: // saddle
            seg(top, right)
            seg(left, bottom)
            break
        }
      }
    }
    ctx.stroke()
  }
  bg.value = `url(${canvas.toDataURL('image/png')})`
}

onMounted(drawTile)
</script>

<template>
  <div class="topo" aria-hidden="true">
    <div class="topo-tile" :style="{ backgroundImage: bg, '--topo-tile': `${TILE}px` }" />
  </div>
</template>

<style scoped>
.topo {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
  background: var(--color-background);
}

.topo-tile {
  position: absolute;
  inset: -100% -100% auto auto;
  width: 300%;
  height: 300%;
  background-repeat: repeat;
  background-size: var(--topo-tile) var(--topo-tile);
  animation: topo-drift 90s linear infinite;
  will-change: transform;
}

@keyframes topo-drift {
  from {
    transform: translate3d(0, 0, 0);
  }
  to {
    transform: translate3d(calc(var(--topo-tile) * -1), calc(var(--topo-tile) * -1), 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .topo-tile {
    animation: none;
  }
}
</style>
