<script setup lang="ts">
import { TrendingUp, TrendingDown } from '@lucide/vue'
import { computed } from 'vue'
import type { KPI } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'

interface Props {
  kpi: KPI
}

const props = withDefaults(defineProps<Props>(), {})

const trendIcon = computed(() => {
  const trend = props.kpi.trend
  if (!trend) return null
  return trend.direction === 'up' ? TrendingUp : trend.direction === 'down' ? TrendingDown : null
})

const trendColor = computed(() => {
  const trend = props.kpi.trend
  if (!trend) return ''
  return trend.direction === 'up' ? 'text-success-500' : 'text-danger-500'
})
</script>

<template>
  <Card class="hover:shadow-medium transition-shadow">
    <div class="space-y-2">
      <p class="text-sm text-neutral-500">{{ kpi.label }}</p>
      <div class="flex items-baseline justify-between gap-2">
        <div class="flex items-baseline gap-1">
          <span class="text-3xl font-bold text-neutral-900">{{ kpi.value }}</span>
          <span v-if="kpi.unit" class="text-sm text-neutral-500">{{ kpi.unit }}</span>
        </div>
        <div v-if="kpi.trend" class="flex items-center gap-1">
          <component :is="trendIcon" :class="['h-4 w-4', trendColor]" />
          <span :class="['text-xs font-medium', trendColor]">
            {{ kpi.trend.percentage }}% {{ kpi.trend.period }}
          </span>
        </div>
      </div>
    </div>
  </Card>
</template>
