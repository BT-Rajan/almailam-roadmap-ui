import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'

import { SERIES_COLORS, resolveChartColor } from '@/constants/chartColors'
import type { ChartDataPoint, LineChartData } from '@/types/Report'

export type ChartValueFormat = 'number' | 'currency' | 'percent'

export interface ChartSeries {
  name: string
  values: number[]
  /** Optional per-series color; defaults to the series' slot in SERIES_COLORS. */
  color?: string
}

/** A chart's data in one shape: categories along one axis, one or more series. */
export interface ChartModel {
  categories: string[]
  series: ChartSeries[]
  /** Per-category colors for a single-series chart whose bars carry meaning (e.g. status). */
  pointColors?: (string | undefined)[]
}

export function seriesColor(series: ChartSeries, index: number): string {
  return series.color ? resolveChartColor(series.color) : SERIES_COLORS[index % SERIES_COLORS.length]
}

/** Legacy single-series inputs (label/value points) as a ChartModel. */
export function modelFromPoints(points: ChartDataPoint[], name: string): ChartModel {
  return {
    categories: points.map((point) => point.label),
    series: [{ name, values: points.map((point) => point.value) }],
    pointColors: points.some((point) => point.color) ? points.map((point) => point.color) : undefined,
  }
}

export function modelFromLine(points: LineChartData[], name: string): ChartModel {
  return { categories: points.map((point) => point.x), series: [{ name, values: points.map((point) => point.value) }] }
}

/** Evenly spaced, round axis ticks from 0 up to at least `max` (0, 250, 500, …). */
export function niceTicks(max: number, count = 4, integer = false): number[] {
  if (!(max > 0)) return [0, 1]
  const rough = max / count
  const magnitude = 10 ** Math.floor(Math.log10(rough))
  let step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((candidate) => candidate >= rough) ?? 10 * magnitude
  // Counts step in whole numbers: no "1.5 tasks" gridline.
  if (integer) step = Math.max(1, Math.ceil(step))
  const ticks: number[] = []
  for (let value = 0; value < max + step * 0.999; value += step) ticks.push(Number(value.toFixed(10)))
  return ticks
}

/** Full value, as shown in tooltips, labels and tables. */
export function formatValue(value: number, format: ChartValueFormat, currency?: string): string {
  if (format === 'percent') return `${Math.round(value)}%`
  if (format === 'currency') {
    return new Intl.NumberFormat('en-KW', {
      style: currency ? 'currency' : 'decimal',
      currency: currency || undefined,
      minimumFractionDigits: 0,
      maximumFractionDigits: 3,
    }).format(value)
  }
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)
}

/** Compact axis tick (12.5K, 1.2M). */
export function formatTick(value: number, format: ChartValueFormat): string {
  if (format === 'percent') return `${Math.round(value)}%`
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
}

/** The rendered width of `el`, kept current as the layout changes. */
export function useElementWidth(el: Ref<HTMLElement | null>, fallback = 640): Ref<number> {
  const width = ref(fallback)
  let observer: ResizeObserver | undefined
  onMounted(() => {
    if (!el.value) return
    width.value = el.value.clientWidth || fallback
    if (typeof ResizeObserver === 'undefined') return
    observer = new ResizeObserver((entries) => {
      const next = Math.floor(entries[0]?.contentRect.width ?? 0)
      if (next > 0) width.value = next
    })
    observer.observe(el.value)
  })
  onBeforeUnmount(() => observer?.disconnect())
  return width
}

/** SVG path for a bar with 4px rounded corners at its data end only. */
export function barPath(x: number, y: number, w: number, h: number, horizontal: boolean): string {
  if (w <= 0 || h <= 0) return ''
  if (horizontal) {
    const r = Math.min(4, w, h / 2)
    return `M${x},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h - r}Q${x + w},${y + h} ${x + w - r},${y + h}H${x}Z`
  }
  const r = Math.min(4, h, w / 2)
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`
}
