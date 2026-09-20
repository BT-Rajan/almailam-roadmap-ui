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

// A bold, color-washed tile instead of a plain white card with a small
// icon chip -- each stat gets its own tinted gradient background and a
// solid-color icon badge, so the grid reads as a set of distinct,
// colorful widgets (the native-app "health app tile" look) rather than
// a report table's worth of identical white boxes. 'primary' rides on
// the admin-configurable brand accent color (see tailwind.config.js's
// accent scale) rather than a fixed hue, same as everywhere else in
// the app that uses it.
const TILE_BACKGROUND: Record<string, string> = {
  primary: 'bg-gradient-to-br from-accent-50 to-accent-100/60 dark:from-accent-500/15 dark:to-accent-500/5',
  success: 'bg-gradient-to-br from-success-50 to-success-100/60 dark:from-success-500/15 dark:to-success-500/5',
  warning: 'bg-gradient-to-br from-warning-50 to-warning-100/60 dark:from-warning-500/15 dark:to-warning-500/5',
  danger: 'bg-gradient-to-br from-danger-50 to-danger-100/60 dark:from-danger-500/15 dark:to-danger-500/5',
  info: 'bg-gradient-to-br from-info-50 to-info-100/60 dark:from-info-500/15 dark:to-info-500/5',
}

const ICON_BADGE: Record<string, string> = {
  primary: 'bg-accent-500 text-white',
  success: 'bg-success-500 text-white',
  warning: 'bg-warning-500 text-white',
  danger: 'bg-danger-500 text-white',
  info: 'bg-info-500 text-white',
}

const tileBackground = computed(() => TILE_BACKGROUND[props.statistic.color || 'primary'])
const iconBadge = computed(() => ICON_BADGE[props.statistic.color || 'primary'])
</script>

<template>
  <div
    :class="['flex cursor-pointer flex-col items-center gap-4 rounded-3xl p-5 text-center shadow-glass-sm ring-1 ring-inset ring-white/40 transition-all duration-normal hover:-translate-y-0.5 hover:shadow-glass dark:ring-white/5', tileBackground]"
    @click="$emit('click')"
  >
    <span v-if="statistic.icon" :class="['flex h-11 w-11 items-center justify-center rounded-2xl shadow-sm', iconBadge]">
      <component :is="statistic.icon" class="h-5 w-5" />
    </span>
    <div>
      <p class="text-3xl font-bold leading-none text-text-primary">{{ statistic.value }}</p>
      <p class="mt-2 text-xs font-semibold text-text-secondary">{{ statistic.label }}</p>
    </div>
  </div>
</template>
