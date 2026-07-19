<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  value: number
  showLabel?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showLabel: false,
})

const clampedValue = computed(() => Math.min(100, Math.max(0, props.value)))

const trackColor = computed(() => {
  if (clampedValue.value >= 100) return 'bg-success-500'
  if (clampedValue.value >= 50) return 'bg-primary-600'
  return 'bg-warning-500'
})
</script>

<template>
  <div class="flex items-center gap-2">
    <div
      class="h-1.5 w-full overflow-hidden rounded-full bg-bg-secondary"
      role="progressbar"
      :aria-valuenow="clampedValue"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div class="h-full rounded-full transition-all duration-normal" :class="trackColor" :style="{ width: `${clampedValue}%` }" />
    </div>
    <span v-if="showLabel" class="w-9 shrink-0 text-right text-xs font-medium text-neutral-500">{{ clampedValue }}%</span>
  </div>
</template>
