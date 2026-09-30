<script setup lang="ts">
import { computed, ref } from 'vue'

import ChartFrame from '@/components/reports/ChartFrame.vue'
import {
  barPath,
  formatTick,
  formatValue,
  modelFromPoints,
  niceTicks,
  seriesColor,
  useElementWidth,
  type ChartModel,
  type ChartSeries,
  type ChartValueFormat,
} from '@/components/reports/chartUtils'
import { resolveChartColor } from '@/constants/chartColors'
import type { ChartDataPoint } from '@/types/Report'

interface Props {
  /** Single series as label/value points (per-point color optional). */
  data?: ChartDataPoint[]
  /** Or: categories plus one or more series (grouped bars). */
  categories?: string[]
  series?: ChartSeries[]
  /** Name of the single `data` series (legend-less; used in the tooltip and table). */
  seriesName?: string
  horizontal?: boolean
  /** Plot height for vertical bars; horizontal bars size to their rows. */
  height?: number
  format?: ChartValueFormat
  currency?: string
  categoryLabel?: string
  showTotal?: boolean
  showLabel?: boolean
  showValue?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  data: undefined,
  categories: undefined,
  series: undefined,
  seriesName: 'Value',
  horizontal: false,
  height: 280,
  format: 'number',
  currency: undefined,
  categoryLabel: '',
  showTotal: false,
  showLabel: true,
  showValue: true,
})

const model = computed<ChartModel>(() =>
  props.series && props.categories ? { categories: props.categories, series: props.series } : modelFromPoints(props.data ?? [], props.seriesName),
)

const container = ref<HTMLElement | null>(null)
const width = useElementWidth(container)

const BAR_MAX = 24
const GAP = 2
const seriesCount = computed(() => Math.max(model.value.series.length, 1))
const maxValue = computed(() => Math.max(0, ...model.value.series.flatMap((series) => series.values)))
const integerValues = computed(() => props.format === 'number' && model.value.series.every((series) => series.values.every(Number.isInteger)))
const ticks = computed(() => niceTicks(maxValue.value, 4, integerValues.value))
const scaleMax = computed(() => ticks.value[ticks.value.length - 1] || 1)
// A value at every bar end only while it stays readable: one series, not too many bars.
const labelValues = computed(() => props.showValue && seriesCount.value === 1 && model.value.categories.length <= 16)

function color(seriesIndex: number, categoryIndex: number): string {
  const pointColor = model.value.pointColors?.[categoryIndex]
  if (seriesCount.value === 1 && pointColor) return resolveChartColor(pointColor)
  return seriesColor(model.value.series[seriesIndex], seriesIndex)
}

// ---- Layout -----------------------------------------------------------------
const labelWidth = computed(() => {
  if (!props.horizontal) return 0
  const longest = Math.max(0, ...model.value.categories.map((category) => category.length))
  return Math.min(Math.max(longest * 7 + 12, 60), Math.max(width.value * 0.38, 90), 220)
})
const pad = computed(() =>
  props.horizontal
    ? { top: 8, right: labelValues.value ? 72 : 16, bottom: 24, left: labelWidth.value }
    : { top: labelValues.value ? 22 : 10, right: 12, bottom: 28, left: 48 },
)
const rowHeight = computed(() => Math.max(28, seriesCount.value * (Math.min(BAR_MAX, 18) + GAP) + 12))
const svgHeight = computed(() =>
  props.horizontal ? pad.value.top + pad.value.bottom + model.value.categories.length * rowHeight.value : props.height,
)
const plotWidth = computed(() => Math.max(width.value - pad.value.left - pad.value.right, 10))
const plotHeight = computed(() => Math.max(svgHeight.value - pad.value.top - pad.value.bottom, 10))
const band = computed(() => (props.horizontal ? rowHeight.value : plotWidth.value / Math.max(model.value.categories.length, 1)))
const barThickness = computed(() => {
  const available = (band.value * 0.72 - GAP * (seriesCount.value - 1)) / seriesCount.value
  return Math.max(3, Math.min(BAR_MAX, available))
})
const groupSize = computed(() => barThickness.value * seriesCount.value + GAP * (seriesCount.value - 1))

function valueLength(value: number): number {
  return ((props.horizontal ? plotWidth.value : plotHeight.value) * Math.max(value, 0)) / scaleMax.value
}

interface BarMark {
  key: string
  path: string
  fill: string
  labelX: number
  labelY: number
  label: string
}

const bars = computed<BarMark[]>(() => {
  const marks: BarMark[] = []
  model.value.categories.forEach((_, categoryIndex) => {
    const bandStart = (props.horizontal ? pad.value.top : pad.value.left) + categoryIndex * band.value + (band.value - groupSize.value) / 2
    model.value.series.forEach((series, seriesIndex) => {
      const value = series.values[categoryIndex] ?? 0
      const length = valueLength(value)
      const offset = bandStart + seriesIndex * (barThickness.value + GAP)
      const [x, y, w, h] = props.horizontal
        ? [pad.value.left, offset, length, barThickness.value]
        : [offset, pad.value.top + plotHeight.value - length, barThickness.value, length]
      marks.push({
        key: `${categoryIndex}-${seriesIndex}`,
        path: barPath(x, y, w, h, props.horizontal),
        fill: color(seriesIndex, categoryIndex),
        labelX: props.horizontal ? x + w + 6 : x + w / 2,
        labelY: props.horizontal ? y + h / 2 + 4 : y - 6,
        label: formatValue(value, props.format, props.currency),
      })
    })
  })
  return marks
})

// Vertical category labels: skip every nth one when they would collide.
const labelStep = computed(() => {
  if (props.horizontal) return 1
  const longest = Math.max(1, ...model.value.categories.map((category) => category.length))
  return Math.max(1, Math.ceil((longest * 6.5 + 8) / band.value))
})

function truncate(text: string, maxWidth: number): string {
  const maxChars = Math.max(3, Math.floor(maxWidth / 7))
  return text.length > maxChars ? `${text.slice(0, maxChars - 1)}…` : text
}

// ---- Hover / focus readout ----------------------------------------------------
const active = ref<number | null>(null)
const pointer = ref({ x: 0, y: 0 })

function hitRect(categoryIndex: number) {
  return props.horizontal
    ? { x: 0, y: pad.value.top + categoryIndex * band.value, width: width.value, height: band.value }
    : { x: pad.value.left + categoryIndex * band.value, y: pad.value.top, width: band.value, height: plotHeight.value }
}

function onPointer(event: PointerEvent, categoryIndex: number): void {
  const box = container.value?.getBoundingClientRect()
  if (box) pointer.value = { x: event.clientX - box.left, y: event.clientY - box.top }
  active.value = categoryIndex
}

function onFocus(categoryIndex: number): void {
  const rect = hitRect(categoryIndex)
  pointer.value = { x: rect.x + rect.width / 2, y: rect.y + rect.height / 2 }
  active.value = categoryIndex
}

const tooltipStyle = computed(() => {
  const left = Math.min(Math.max(pointer.value.x + 12, 0), Math.max(width.value - 200, 0))
  return { left: `${left}px`, top: `${Math.max(pointer.value.y - 12, 0)}px` }
})
</script>

<template>
  <ChartFrame :model="model" :format="format" :currency="currency" :category-label="categoryLabel" :show-total="showTotal">
    <div ref="container" class="relative w-full" @pointerleave="active = null">
      <svg :width="width" :height="svgHeight" class="block" role="img" :aria-label="seriesName">
        <!-- Value gridlines -->
        <g>
          <template v-for="tick in ticks" :key="`grid-${tick}`">
            <line
              v-if="horizontal"
              :x1="pad.left + (plotWidth * tick) / scaleMax"
              :x2="pad.left + (plotWidth * tick) / scaleMax"
              :y1="pad.top"
              :y2="pad.top + plotHeight"
              stroke="var(--chart-grid)"
              stroke-width="1"
            />
            <line
              v-else
              :x1="pad.left"
              :x2="pad.left + plotWidth"
              :y1="pad.top + plotHeight - (plotHeight * tick) / scaleMax"
              :y2="pad.top + plotHeight - (plotHeight * tick) / scaleMax"
              stroke="var(--chart-grid)"
              stroke-width="1"
            />
          </template>
        </g>

        <!-- Value axis ticks -->
        <g class="fill-text-muted text-[11px] tabular-nums">
          <template v-for="tick in ticks" :key="`tick-${tick}`">
            <text v-if="horizontal" :x="pad.left + (plotWidth * tick) / scaleMax" :y="svgHeight - 6" text-anchor="middle">
              {{ formatTick(tick, format) }}
            </text>
            <text v-else :x="pad.left - 8" :y="pad.top + plotHeight - (plotHeight * tick) / scaleMax + 4" text-anchor="end">
              {{ formatTick(tick, format) }}
            </text>
          </template>
        </g>

        <!-- Hover band behind the bars -->
        <rect v-if="active !== null" v-bind="hitRect(active)" class="fill-text-primary" opacity="0.04" />

        <!-- Bars: 2px gaps between a group's bars, rounded at the data end -->
        <path v-for="bar in bars" :key="bar.key" :d="bar.path" :fill="bar.fill" />

        <!-- Values at the bar ends (single series only) -->
        <g v-if="labelValues" class="fill-text-secondary text-[11px] font-medium tabular-nums">
          <text v-for="bar in bars" :key="`v-${bar.key}`" :x="bar.labelX" :y="bar.labelY" :text-anchor="horizontal ? 'start' : 'middle'">
            {{ bar.label }}
          </text>
        </g>

        <!-- Category labels -->
        <g v-if="showLabel" class="fill-text-secondary text-[11px]">
          <template v-for="(category, index) in model.categories" :key="`c-${index}`">
            <text
              v-if="horizontal"
              :x="pad.left - 8"
              :y="pad.top + index * band + band / 2 + 4"
              text-anchor="end"
            >
              <title>{{ category }}</title>
              {{ truncate(category, labelWidth - 12) }}
            </text>
            <text
              v-else-if="index % labelStep === 0"
              :x="pad.left + index * band + band / 2"
              :y="pad.top + plotHeight + 18"
              text-anchor="middle"
            >
              <title>{{ category }}</title>
              {{ truncate(category, band * labelStep - 4) }}
            </text>
          </template>
        </g>

        <!-- Hit targets: the whole category band, keyboard-focusable -->
        <rect
          v-for="(category, index) in model.categories"
          :key="`hit-${index}`"
          v-bind="hitRect(index)"
          fill="transparent"
          tabindex="0"
          :aria-label="`${category}: ${model.series.map((s) => `${s.name} ${formatValue(s.values[index] ?? 0, format, currency)}`).join(', ')}`"
          class="cursor-default outline-none"
          @pointermove="onPointer($event, index)"
          @focus="onFocus(index)"
          @blur="active = null"
        />
      </svg>

      <div
        v-if="active !== null"
        class="pointer-events-none absolute z-10 min-w-[140px] rounded-lg border border-border-light bg-bg-card px-3 py-2 text-xs shadow-medium"
        :style="tooltipStyle"
      >
        <p class="mb-1 font-medium text-text-secondary">{{ model.categories[active] }}</p>
        <p v-for="(series, index) in model.series" :key="series.name" class="flex items-center justify-between gap-3">
          <span class="flex items-center gap-1.5 text-text-muted">
            <span class="inline-block h-0.5 w-3 rounded-full" :style="{ background: color(index, active) }" />
            {{ series.name }}
          </span>
          <span class="font-semibold tabular-nums text-text-primary">{{ formatValue(series.values[active] ?? 0, format, currency) }}</span>
        </p>
      </div>
    </div>
  </ChartFrame>
</template>
