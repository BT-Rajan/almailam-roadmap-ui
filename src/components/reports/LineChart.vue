<script setup lang="ts">
import { computed, ref } from 'vue'

import ChartFrame from '@/components/reports/ChartFrame.vue'
import {
  formatTick,
  formatValue,
  modelFromLine,
  niceTicks,
  seriesColor,
  useElementWidth,
  type ChartModel,
  type ChartSeries,
  type ChartValueFormat,
} from '@/components/reports/chartUtils'
import type { LineChartData } from '@/types/Report'

interface Props {
  /** Single series as x/value points. */
  data?: LineChartData[]
  /** Or: shared x categories plus one or more series. */
  categories?: string[]
  series?: ChartSeries[]
  seriesName?: string
  height?: number
  format?: ChartValueFormat
  currency?: string
  categoryLabel?: string
  showTotal?: boolean
  showLabel?: boolean
  showDots?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  data: undefined,
  categories: undefined,
  series: undefined,
  seriesName: 'Value',
  height: 280,
  format: 'number',
  currency: undefined,
  categoryLabel: '',
  showTotal: false,
  showLabel: true,
  showDots: true,
})

const model = computed<ChartModel>(() =>
  props.series && props.categories ? { categories: props.categories, series: props.series } : modelFromLine(props.data ?? [], props.seriesName),
)

const container = ref<HTMLElement | null>(null)
const width = useElementWidth(container)

const pad = { top: 16, right: 20, bottom: 28, left: 52 }
const plotWidth = computed(() => Math.max(width.value - pad.left - pad.right, 10))
const plotHeight = computed(() => Math.max(props.height - pad.top - pad.bottom, 10))
const count = computed(() => model.value.categories.length)
const ticks = computed(() => {
  const values = model.value.series.flatMap((series) => series.values)
  return niceTicks(Math.max(0, ...values), 4, props.format === 'number' && values.every(Number.isInteger))
})
const scaleMax = computed(() => ticks.value[ticks.value.length - 1] || 1)

function x(index: number): number {
  return count.value <= 1 ? pad.left + plotWidth.value / 2 : pad.left + (index * plotWidth.value) / (count.value - 1)
}
function y(value: number): number {
  return pad.top + plotHeight.value - (plotHeight.value * Math.max(value, 0)) / scaleMax.value
}

const lines = computed(() =>
  model.value.series.map((series, index) => ({
    name: series.name,
    color: seriesColor(series, index),
    path: series.values.map((value, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(value)}`).join(' '),
    points: series.values.map((value, i) => ({ cx: x(i), cy: y(value) })),
  })),
)
// A 10% wash under a lone series; several washes would muddy each other.
const area = computed(() => {
  if (lines.value.length !== 1 || count.value < 2) return ''
  const base = pad.top + plotHeight.value
  return `${lines.value[0].path} L${x(count.value - 1)},${base} L${x(0)},${base} Z`
})
const dots = computed(() => props.showDots && count.value <= 24)

const labelStep = computed(() => {
  const longest = Math.max(1, ...model.value.categories.map((category) => category.length))
  const slot = plotWidth.value / Math.max(count.value, 1)
  return Math.max(1, Math.ceil((longest * 6.5 + 8) / slot))
})

// ---- Crosshair: snaps to the nearest period; one readout for every series ----
const active = ref<number | null>(null)

function onPointer(event: PointerEvent): void {
  const box = container.value?.getBoundingClientRect()
  if (!box || count.value === 0) return
  const relative = event.clientX - box.left - pad.left
  const index = count.value <= 1 ? 0 : Math.round((relative / plotWidth.value) * (count.value - 1))
  active.value = Math.min(Math.max(index, 0), count.value - 1)
}

function onKey(event: KeyboardEvent): void {
  if (count.value === 0) return
  if (event.key === 'ArrowRight') active.value = Math.min((active.value ?? -1) + 1, count.value - 1)
  else if (event.key === 'ArrowLeft') active.value = Math.max((active.value ?? count.value) - 1, 0)
  else return
  event.preventDefault()
}

const tooltipStyle = computed(() => {
  if (active.value === null) return {}
  const left = Math.min(Math.max(x(active.value) + 12, 0), Math.max(width.value - 200, 0))
  return { left: `${left}px`, top: `${pad.top}px` }
})
</script>

<template>
  <ChartFrame :model="model" :format="format" :currency="currency" :category-label="categoryLabel" :show-total="showTotal" legend-shape="line">
    <div
      ref="container"
      class="relative w-full outline-none"
      tabindex="0"
      :aria-label="seriesName"
      @pointermove="onPointer"
      @pointerleave="active = null"
      @keydown="onKey"
      @blur="active = null"
    >
      <svg :width="width" :height="height" class="block" role="img" :aria-label="seriesName">
        <g>
          <line
            v-for="tick in ticks"
            :key="`grid-${tick}`"
            :x1="pad.left"
            :x2="pad.left + plotWidth"
            :y1="y(tick)"
            :y2="y(tick)"
            stroke="var(--chart-grid)"
            stroke-width="1"
          />
        </g>
        <g class="fill-text-muted text-[11px] tabular-nums">
          <text v-for="tick in ticks" :key="`tick-${tick}`" :x="pad.left - 8" :y="y(tick) + 4" text-anchor="end">{{ formatTick(tick, format) }}</text>
        </g>

        <path v-if="area" :d="area" :fill="lines[0].color" opacity="0.1" />
        <path
          v-for="line in lines"
          :key="line.name"
          :d="line.path"
          fill="none"
          :stroke="line.color"
          stroke-width="2"
          stroke-linejoin="round"
          stroke-linecap="round"
        />

        <line
          v-if="active !== null"
          :x1="x(active)"
          :x2="x(active)"
          :y1="pad.top"
          :y2="pad.top + plotHeight"
          class="stroke-text-muted"
          stroke-width="1"
          opacity="0.5"
        />

        <template v-for="line in lines" :key="`dots-${line.name}`">
          <template v-for="(point, index) in line.points" :key="index">
            <circle
              v-if="dots || active === index"
              :cx="point.cx"
              :cy="point.cy"
              :r="active === index ? 5 : 4"
              :fill="line.color"
              stroke="var(--color-bg-card)"
              stroke-width="2"
            />
          </template>
        </template>

        <g v-if="showLabel" class="fill-text-secondary text-[11px]">
          <template v-for="(category, index) in model.categories" :key="`c-${index}`">
            <text v-if="index % labelStep === 0" :x="x(index)" :y="pad.top + plotHeight + 18" text-anchor="middle">{{ category }}</text>
          </template>
        </g>
      </svg>

      <div
        v-if="active !== null"
        class="pointer-events-none absolute z-10 min-w-[150px] rounded-lg border border-border-light bg-bg-card px-3 py-2 text-xs shadow-medium"
        :style="tooltipStyle"
      >
        <p class="mb-1 font-medium text-text-secondary">{{ model.categories[active] }}</p>
        <p v-for="line in lines" :key="line.name" class="flex items-center justify-between gap-3">
          <span class="flex items-center gap-1.5 text-text-muted">
            <span class="inline-block h-0.5 w-3 rounded-full" :style="{ background: line.color }" />
            {{ line.name }}
          </span>
          <span class="font-semibold tabular-nums text-text-primary">
            {{ formatValue(model.series[lines.indexOf(line)].values[active] ?? 0, format, currency) }}
          </span>
        </p>
      </div>
    </div>
  </ChartFrame>
</template>
