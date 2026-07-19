<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'

import Card from '@/components/common/Card.vue'
import type { BadgeVariant } from '@/types/Ui'

interface Props {
  label: string
  value: string
  icon?: Component
  color?: BadgeVariant
}

const props = withDefaults(defineProps<Props>(), {
  icon: undefined,
  color: 'primary',
})

const iconBgClasses: Record<BadgeVariant, string> = {
  neutral: 'bg-neutral-100 text-neutral-500',
  primary: 'bg-primary-50 text-primary-600',
  success: 'bg-success-50 text-success-600',
  warning: 'bg-warning-50 text-warning-600',
  danger: 'bg-danger-50 text-danger-600',
  info: 'bg-info-50 text-info-600',
  ai: 'bg-ai-50 text-ai-600',
}

const iconClasses = computed(() => iconBgClasses[props.color])
</script>

<template>
  <Card>
    <div class="flex items-center gap-3">
      <div v-if="icon" class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg" :class="iconClasses">
        <component :is="icon" class="h-5 w-5" />
      </div>
      <div class="min-w-0">
        <p class="truncate text-xs font-medium uppercase tracking-wide text-neutral-400">{{ label }}</p>
        <p class="truncate text-sm font-semibold text-neutral-800">{{ value }}</p>
      </div>
    </div>
  </Card>
</template>
