<script setup lang="ts">
import { Sparkles } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'

interface Props {
  label?: string
}

withDefaults(defineProps<Props>(), {
  label: 'AI is analyzing this document…',
})
</script>

<template>
  <Card class="border-ai-100 bg-gradient-to-br from-ai-50 to-transparent">
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-2">
        <Sparkles class="h-5 w-5 animate-pulse text-ai-600" />
        <p class="text-sm font-medium text-neutral-700">{{ label }}</p>
      </div>
      <SkeletonLoader :rows="4" />
    </div>
  </Card>
</template>
