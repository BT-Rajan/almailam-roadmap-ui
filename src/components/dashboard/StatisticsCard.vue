<script setup lang="ts">
import { computed } from 'vue'
import type { StatisticItem } from '@/types/Dashboard'

interface Props {
  statistic: StatisticItem
}

const props = withDefaults(defineProps<Props>(), {})

defineEmits<{
  click: []
}>()

// A clean white tile with a colored top edge and a tinted icon chip: the
// color says which stat it is at a glance, while the card itself stays
// crisp and enterprise-looking. Dark mode keeps a tinted wash, which
// reads better than white-on-black. 'primary' rides on the
// admin-configurable brand accent (see tailwind.config.js's accent scale).
const TILE_ACCENT: Record<string, string> = {
  primary: 'border-t-accent-500 dark:bg-accent-500/10',
  success: 'border-t-success-500 dark:bg-success-500/10',
  warning: 'border-t-warning-500 dark:bg-warning-500/10',
  danger: 'border-t-danger-500 dark:bg-danger-500/10',
  info: 'border-t-info-500 dark:bg-info-500/10',
}

const ICON_BADGE: Record<string, string> = {
  primary: 'bg-accent-50 text-accent-600 dark:bg-accent-500 dark:text-white',
  success: 'bg-success-50 text-success-600 dark:bg-success-500 dark:text-white',
  warning: 'bg-warning-50 text-warning-600 dark:bg-warning-500 dark:text-white',
  danger: 'bg-danger-50 text-danger-600 dark:bg-danger-500 dark:text-white',
  info: 'bg-info-50 text-info-600 dark:bg-info-500 dark:text-white',
}

const tileAccent = computed(() => TILE_ACCENT[props.statistic.color || 'primary'])
const iconBadge = computed(() => ICON_BADGE[props.statistic.color || 'primary'])
</script>

<template>
  <div
    :class="['flex cursor-pointer items-center gap-4 rounded-2xl border border-t-[3px] border-border-light bg-bg-card p-5 shadow-glass-sm transition-all duration-normal hover:-translate-y-0.5 hover:shadow-glass', tileAccent]"
    @click="$emit('click')"
  >
    <span v-if="statistic.icon" :class="['flex h-12 w-12 shrink-0 items-center justify-center rounded-xl', iconBadge]">
      <component :is="statistic.icon" class="h-6 w-6" />
    </span>
    <div class="min-w-0">
      <p class="font-display text-3xl font-bold leading-none text-text-primary">{{ statistic.value }}</p>
      <p class="mt-1.5 text-sm font-medium text-text-secondary">{{ statistic.label }}</p>
    </div>
  </div>
</template>
