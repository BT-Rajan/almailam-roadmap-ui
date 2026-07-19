<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  value: number
  max?: number
  label?: string
  showPercentage?: boolean
  color?: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  max: 100,
  label: undefined,
  showPercentage: true,
  color: '#3B82F6',
  size: 'md',
})

const percentage = computed(() => Math.min((props.value / props.max) * 100, 100))

const circumference = 2 * Math.PI * 45
const strokeDashoffset = computed(() => circumference - (percentage.value / 100) * circumference)

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'w-20 h-20',
    md: 'w-32 h-32',
    lg: 'w-40 h-40',
  }
  return sizes[props.size]
})

const textSizeClasses = computed(() => {
  const sizes = {
    sm: 'text-xs',
    md: 'text-lg',
    lg: 'text-2xl',
  }
  return sizes[props.size]
})
</script>

<template>
  <div class="flex flex-col items-center gap-3">
    <div :class="sizeClasses" class="relative flex items-center justify-center">
      <svg class="transform -rotate-90" viewBox="0 0 100 100" preserveAspectRatio="none">
        <!-- Background circle -->
        <circle cx="50" cy="50" r="45" fill="none" class="stroke-neutral-200" stroke-width="8" />
        <!-- Progress circle -->
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          :stroke="color"
          stroke-width="8"
          stroke-linecap="round"
          :style="{
            strokeDasharray: circumference,
            strokeDashoffset: strokeDashoffset,
            transition: 'stroke-dashoffset 0.6s ease',
          }"
        />
      </svg>
      <div class="absolute text-center">
        <p :class="['font-bold text-neutral-900', textSizeClasses]">{{ Math.round(percentage) }}%</p>
        <p v-if="label" class="text-xs text-neutral-500 mt-1">{{ value }}/{{ max }}</p>
      </div>
    </div>
    <p v-if="label" class="text-sm font-medium text-neutral-700 text-center">{{ label }}</p>
  </div>
</template>
