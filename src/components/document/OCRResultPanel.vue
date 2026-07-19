<script setup lang="ts">
import { ScanText } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import AIConfidenceBadge from '@/components/ai/AIConfidenceBadge.vue'
import type { ExtractedField } from '@/types/AiReview'

defineProps<{
  fields: ExtractedField[]
}>()
</script>

<template>
  <Card>
    <template #header>
      <div class="flex items-center gap-2">
        <ScanText class="h-5 w-5 text-ai-600" />
        <h3 class="text-sm font-semibold text-neutral-800">Extracted Information</h3>
      </div>
    </template>

    <dl class="flex flex-col gap-3">
      <div
        v-for="field in fields"
        :key="field.label"
        class="flex flex-col gap-1 border-b border-border-light pb-3 last:border-b-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between"
      >
        <dt class="text-sm text-neutral-500">{{ field.label }}</dt>
        <dd class="flex items-center gap-2">
          <span class="text-sm font-medium text-neutral-800">{{ field.value }}</span>
          <AIConfidenceBadge :confidence="field.confidence" />
        </dd>
      </div>
    </dl>
  </Card>
</template>
