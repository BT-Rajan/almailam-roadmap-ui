<script setup lang="ts">
import { computed } from 'vue'
import type { StatisticItem } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'

interface Props {
  statistic: StatisticItem
}

const props = withDefaults(defineProps<Props>(), {})


const bgColor = computed(() => {
  const colors: Record<string, string> = {
    primary: 'bg-primary-50',
    success: 'bg-success-50',
    warning: 'bg-warning-50',
    danger: 'bg-danger-50',
    info: 'bg-info-50',
  }
  return colors[props.statistic.color || 'primary']
})

const textColor = computed(() => {
  const colors: Record<string, string> = {
    primary: 'text-primary-600',
    success: 'text-success-600',
    warning: 'text-warning-600',
    danger: 'text-danger-600',
    info: 'text-info-600',
  }
  return colors[props.statistic.color || 'primary']
})
</script>

<template>
  <Card class="hover:shadow-medium transition-shadow">
    <div class="flex items-start justify-between gap-4">
      <div class="flex-1 space-y-2">
        <p class="text-xs uppercase tracking-wide text-neutral-500 font-medium">
          {{ statistic.label }}
        </p>
        <p class="text-2xl font-bold text-neutral-900">{{ statistic.value }}</p>
      </div>
      <div v-if="statistic.icon" :class="['flex-shrink-0 w-12 h-12 rounded-lg flex items-center justify-center', bgColor]">
        <span :class="['text-lg', textColor]">{{ statistic.icon }}</span>
      </div>
    </div>
  </Card>
</template>
