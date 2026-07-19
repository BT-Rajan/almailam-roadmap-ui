<script setup lang="ts">
import { Loader2 } from '@lucide/vue'

import type { ComponentSize } from '@/types/Ui'

interface Props {
  size?: ComponentSize
  label?: string
}

withDefaults(defineProps<Props>(), {
  size: 'md',
  label: undefined,
})

const sizeClasses: Record<ComponentSize, string> = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
}
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-2 py-6" role="status">
    <Loader2 :class="sizeClasses[size]" class="animate-spin text-primary-600" />
    <p v-if="label" class="text-sm text-neutral-500">{{ label }}</p>
  </div>
</template>
