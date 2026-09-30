<script setup lang="ts">
import { TrendingUp, TrendingDown } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from '@/components/common/Card.vue'

const { t } = useI18n()

interface Props {
  label: string
  value: string | number
  unit?: string
  change?: {
    direction: 'up' | 'down'
    percentage: number
    /** Whether this move is good news (more cash) or bad (more overdue); defaults to up = good. */
    good?: boolean
  }
  color?: string
  /** One short line saying what the figure counts, e.g. "of 2,000 billed". */
  hint?: string
}

const props = withDefaults(defineProps<Props>(), {
  unit: undefined,
  change: undefined,
  color: 'neutral',
  hint: undefined,
})

const changeColor = computed(() => {
  if (!props.change) return ''
  const good = props.change.good ?? props.change.direction === 'up'
  return good ? 'text-success-600' : 'text-danger-600'
})

// Same treatment as the dashboard's StatisticsCard: a white card with a
// colored top edge (light), a soft tint (dark). 'primary' is the brand blue.
const accentClasses = computed(() => {
  const colors: Record<string, string> = {
    primary: 'border-t-accent-500 dark:bg-accent-500/10',
    success: 'border-t-success-500 dark:bg-success-500/10',
    warning: 'border-t-warning-500 dark:bg-warning-500/10',
    danger: 'border-t-danger-500 dark:bg-danger-500/10',
    info: 'border-t-info-500 dark:bg-info-500/10',
    neutral: 'border-t-neutral-300 dark:border-t-neutral-600',
  }
  return colors[props.color || 'neutral'] ?? colors.neutral
})
</script>

<template>
  <Card class="border-t-[3px]" :class="accentClasses">
    <div class="space-y-2">
      <p class="text-sm text-text-secondary">{{ label }}</p>
      <div class="flex items-baseline gap-2">
        <span class="font-display text-2xl font-bold text-text-primary">{{ value }}</span>
        <span v-if="unit" class="text-sm text-text-muted">{{ unit }}</span>
      </div>
      <p v-if="hint" class="text-xs text-text-muted">{{ hint }}</p>
      <div v-if="change" class="flex items-center gap-1 pt-1">
        <component :is="change.direction === 'up' ? TrendingUp : TrendingDown" :class="['h-4 w-4', changeColor]" />
        <span :class="['text-sm font-medium', changeColor]">{{ t('report.metricCard.vsLastPeriod', { percentage: change.percentage }) }}</span>
      </div>
    </div>
  </Card>
</template>
