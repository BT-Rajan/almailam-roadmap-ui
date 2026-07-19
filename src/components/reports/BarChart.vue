<script setup lang="ts">
import { computed } from 'vue'
import type { ChartDataPoint } from '@/types/Report'

interface Props {
  data: ChartDataPoint[]
  height?: number
  showLabel?: boolean
  showValue?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  showLabel: true,
  showValue: true,
})

const maxValue = computed(() => Math.max(...props.data.map(d => d.value), 1))
const padding = { top: 20, right: 20, bottom: 40, left: 50 }
const chartWidth = computed(() => 800 - padding.left - padding.right)
const chartHeight = computed(() => props.height - padding.top - padding.bottom)
const barWidth = computed(() => chartWidth.value / props.data.length * 0.7)
const barSpacing = computed(() => chartWidth.value / props.data.length)

const getBarHeight = (value: number) => (value / maxValue.value) * chartHeight.value

const getBarX = (index: number) => padding.left + index * barSpacing.value + (barSpacing.value - barWidth.value) / 2

const getBarY = (value: number) => padding.top + chartHeight.value - getBarHeight(value)

const yAxisTicks = computed(() => {
  const ticks = []
  for (let i = 0; i <= 5; i++) {
    ticks.push((maxValue.value / 5) * i)
  }
  return ticks
})

const getYPosition = (value: number) => padding.top + chartHeight.value - (value / maxValue.value) * chartHeight.value
</script>

<template>
  <div class="w-full overflow-x-auto">
    <svg :width="800" :height="height" class="mx-auto">
      <!-- Y Axis Grid -->
      <g class="stroke-neutral-200 stroke-[0.5]">
        <line
          v-for="tick in yAxisTicks"
          :key="`tick-${tick}`"
          :x1="padding.left"
          :y1="getYPosition(tick)"
          :x2="800 - padding.right"
          :y2="getYPosition(tick)"
        />
      </g>

      <!-- Y Axis Labels -->
      <g class="text-xs fill-neutral-500">
        <text
          v-for="tick in yAxisTicks"
          :key="`label-${tick}`"
          :x="padding.left - 10"
          :y="getYPosition(tick) + 4"
          text-anchor="end"
        >
          {{ Math.round(tick) }}
        </text>
      </g>

      <!-- Y Axis -->
      <line :x1="padding.left" :y1="padding.top" :x2="padding.left" :y2="padding.top + chartHeight" class="stroke-neutral-400 stroke-[1]" />

      <!-- X Axis -->
      <line :x1="padding.left" :y1="padding.top + chartHeight" :x2="800 - padding.right" :y2="padding.top + chartHeight" class="stroke-neutral-400 stroke-[1]" />

      <!-- Bars -->
      <g>
        <rect
          v-for="(point, index) in data"
          :key="`bar-${index}`"
          :x="getBarX(index)"
          :y="getBarY(point.value)"
          :width="barWidth"
          :height="getBarHeight(point.value)"
          :fill="point.color || '#3B82F6'"
          class="hover:opacity-80 transition-opacity"
        />
      </g>

      <!-- Values on bars -->
      <g v-if="showValue" class="text-xs font-medium fill-neutral-800">
        <text
          v-for="(point, index) in data"
          :key="`value-${index}`"
          :x="getBarX(index) + barWidth / 2"
          :y="getBarY(point.value) - 8"
          text-anchor="middle"
        >
          {{ point.value }}
        </text>
      </g>

      <!-- X Axis Labels -->
      <g v-if="showLabel" class="text-xs fill-neutral-600">
        <text
          v-for="(point, index) in data"
          :key="`label-${index}`"
          :x="getBarX(index) + barWidth / 2"
          :y="padding.top + chartHeight + 20"
          text-anchor="middle"
        >
          {{ point.label }}
        </text>
      </g>
    </svg>
  </div>
</template>
