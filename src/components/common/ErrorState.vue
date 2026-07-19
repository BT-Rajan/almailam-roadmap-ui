<script setup lang="ts">
import { AlertCircle } from '@lucide/vue'

import BaseButton from '@/components/common/BaseButton.vue'

interface Props {
  title?: string
  description?: string
  retryLabel?: string
}

withDefaults(defineProps<Props>(), {
  title: 'Something went wrong',
  description: 'Please try again. If the problem continues, contact support.',
  retryLabel: 'Try Again',
})

defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 px-6 py-12 text-center">
    <span class="flex h-12 w-12 items-center justify-center rounded-full bg-danger-50">
      <AlertCircle class="h-6 w-6 text-danger-500" />
    </span>
    <div class="flex flex-col gap-1">
      <p class="text-sm font-semibold text-neutral-700">{{ title }}</p>
      <p class="text-sm text-neutral-400">{{ description }}</p>
    </div>
    <BaseButton variant="secondary" size="sm" @click="$emit('retry')">
      {{ retryLabel }}
    </BaseButton>
  </div>
</template>
