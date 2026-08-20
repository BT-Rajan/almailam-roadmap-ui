<script setup lang="ts">
import { Sparkles } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import AIConfidenceBadge from '@/components/ai/AIConfidenceBadge.vue'
import type { AIConfidence } from '@/types/AiReview'

interface Props {
  title?: string
  summary: string
  details: string
  confidence: AIConfidence
}

withDefaults(defineProps<Props>(), {
  title: 'AI Summary',
})
</script>

<template>
  <Card class="border-ai-100 bg-gradient-to-br from-ai-50 to-transparent">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-2">
          <Sparkles class="h-5 w-5 text-ai-600" />
          <h3 class="text-sm font-semibold text-text-primary">{{ title }}</h3>
        </div>
        <AIConfidenceBadge :confidence="confidence" />
      </div>
    </template>

    <div class="flex flex-col gap-3">
      <p class="text-sm font-medium text-text-primary">{{ summary }}</p>
      <p class="text-sm leading-relaxed text-text-secondary">{{ details }}</p>
    </div>
  </Card>
</template>
