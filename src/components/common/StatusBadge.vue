<script setup lang="ts">
import { computed } from 'vue'

import type { BadgeVariant, ComponentSize } from '@/types/Ui'

interface Props {
  label: string
  variant?: BadgeVariant
  size?: ComponentSize
  showDot?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'neutral',
  size: 'md',
  showDot: false,
})

const variantClasses: Record<BadgeVariant, string> = {
  neutral: 'bg-neutral-100 text-neutral-600',
  primary: 'bg-primary-50 text-primary-700',
  success: 'bg-success-50 text-success-700',
  warning: 'bg-warning-50 text-warning-700',
  danger: 'bg-danger-50 text-danger-700',
  info: 'bg-info-50 text-info-700',
  ai: 'bg-ai-50 text-ai-700',
}

const dotClasses: Record<BadgeVariant, string> = {
  neutral: 'bg-neutral-400',
  primary: 'bg-primary-500',
  success: 'bg-success-500',
  warning: 'bg-warning-500',
  danger: 'bg-danger-500',
  info: 'bg-info-500',
  ai: 'bg-ai-500',
}

const sizeClasses: Record<ComponentSize, string> = {
  sm: 'h-5 px-2 text-[11px] gap-1',
  md: 'h-6 px-2.5 text-xs gap-1.5',
  lg: 'h-7 px-3 text-sm gap-1.5',
}

const badgeClasses = computed(() => [
  'inline-flex items-center rounded-full font-medium',
  variantClasses[props.variant],
  sizeClasses[props.size],
])
</script>

<template>
  <span :class="badgeClasses">
    <span v-if="showDot" class="h-1.5 w-1.5 rounded-full" :class="dotClasses[variant]" />
    {{ label }}
  </span>
</template>
