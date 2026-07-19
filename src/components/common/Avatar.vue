<script setup lang="ts">
import { computed } from 'vue'

import type { ComponentSize } from '@/types/Ui'

interface Props {
  name: string
  imageUrl?: string
  size?: ComponentSize
}

const props = withDefaults(defineProps<Props>(), {
  imageUrl: undefined,
  size: 'md',
})

const sizeClasses: Record<ComponentSize, string> = {
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
}

const initials = computed(() => {
  const parts = props.name.trim().split(/\s+/)
  const first = parts[0]?.charAt(0) ?? ''
  const last = parts.length > 1 ? (parts[parts.length - 1]?.charAt(0) ?? '') : ''
  return (first + last).toUpperCase()
})
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center rounded-full bg-primary-100 font-semibold text-primary-700"
    :class="sizeClasses[size]"
  >
    <img
      v-if="imageUrl"
      :src="imageUrl"
      :alt="name"
      class="h-full w-full rounded-full object-cover"
    />
    <template v-else>{{ initials }}</template>
  </span>
</template>
