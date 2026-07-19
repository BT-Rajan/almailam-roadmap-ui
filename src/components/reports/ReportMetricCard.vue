<script setup lang="ts">
import { TrendingUp, TrendingDown } from '@lucide/vue'
import { computed } from 'vue'
import Card from '@/components/common/Card.vue'

interface Props {
  label: string
  value: string | number
  unit?: string
  change?: {
    direction: 'up' | 'down'
    percentage: number
  }
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  unit: undefined,
  change: undefined,
  color: 'neutral',
})

const changeColor = computed(() => {
  if (!props.change) return ''
  return props.change.direction === 'up' ? 'text-success-500' : 'text-danger-500'
})

const bgColor = computed(() => {
  const colors: Record<string, string> = {
    primary: 'bg-primary-50',
    success: 'bg-success-50',
    warning: 'bg-warning-50',
    danger: 'bg-danger-50',
    info: 'bg-info-50',
    neutral: 'bg-neutral-50',
  }
  return colors[props.color || 'neutral']
})
</script>

<template>
  <Card :class="bgColor">
    <div class="space-y-2">
      <p class="text-sm text-neutral-600">{{ label }}</p>
      <div class="flex items-baseline gap-2">
        <span class="text-2xl font-bold text-neutral-900">{{ value }}</span>
        <span v-if="unit" class="text-sm text-neutral-500">{{ unit }}</span>
      </div>
      <div v-if="change" class="flex items-center gap-1 pt-1">
        <component :is="change.direction === 'up' ? TrendingUp : TrendingDown" :class="['h-4 w-4', changeColor]" />
        <span :class="['text-sm font-medium', changeColor]">{{ change.percentage }}% vs last period</span>
      </div>
    </div>
  </Card>
</template>
