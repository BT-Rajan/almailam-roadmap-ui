<script setup lang="ts">
import { computed } from 'vue'
import type { LineChartData } from '@/types/Report'

interface Props {
  data: LineChartData[]
  height?: number
  showLabel?: boolean
  showDots?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: 300,
  showLabel: true,
  showDots: true,
})

const maxValue = computed(() => Math.max(...props.data.map(d => d.value), 1))
const minValue = computed(() => 0)
const padding = { top: 20, right: 20, bottom: 40, left: 50 }
const chartWidth = computed(() => 800 - padding.left - padding.right)
const chartHeight = computed(() => props.height - padding.top - padding.bottom)
const pointSpacing = computed(() => chartWidth.value / (props.data.length - 1 || 1))

const getX = (index: number) => padding.left + index * pointSpacing.value

const getY = (value: number) => padding.top + chartHeight.value - ((value - minValue.value) / (maxValue.value - minValue.value)) * chartHeight.value

const pathData = computed(() => {
  if (props.data.length === 0) return ''
  const points = props.data.map((d, i) => `${getX(i)},${getY(d.value)}`)
  return `M ${points.join(' L ')}`
})

const yAxisTicks = computed(() => {
  const ticks = []
  for (let i = 0; i <= 5; i++) {
    ticks.push((maxValue.value / 5) * i)
  }
  return ticks
})

const getYPosition = (value: number) => padding.top + chartHeight.value - ((value - minValue.value) / (maxValue.value - minValue.value)) * chartHeight.value
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

      <!-- Line -->
      <path :d="pathData" fill="none" stroke="#3B82F6" stroke-width="2" class="drop-shadow-sm" />

      <!-- Area under line -->
      <defs>
        <linearGradient id="lineAreaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" style="stop-color: #3B82F6; stop-opacity: 0.1" />
          <stop offset="100%" style="stop-color: #3B82F6; stop-opacity: 0" />
        </linearGradient>
      </defs>
      <path
        :d="`${pathData} L ${getX(data.length - 1)},${padding.top + chartHeight} L ${getX(0)},${padding.top + chartHeight} Z`"
        fill="url(#lineAreaGradient)"
      />

      <!-- Dots -->
      <g v-if="showDots" class="fill-primary-500">
        <circle
          v-for="(point, index) in data"
          :key="`dot-${index}`"
          :cx="getX(index)"
          :cy="getY(point.value)"
          r="4"
          class="stroke-white stroke-[2] hover:r-6 transition-all"
        />
      </g>

      <!-- X Axis Labels -->
      <g v-if="showLabel" class="text-xs fill-neutral-600">
        <text
          v-for="(point, index) in data"
          :key="`label-${index}`"
          :x="getX(index)"
          :y="padding.top + chartHeight + 20"
          text-anchor="middle"
        >
          {{ point.x }}
        </text>
      </g>
    </svg>
  </div>
</template>
