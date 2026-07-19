<script setup lang="ts">
import { Lightbulb } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { AIInsight } from '@/types/Dashboard'
import type { BadgeVariant } from '@/types/Ui'

interface Props {
  insights: AIInsight[]
  title?: string
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: 'AI Insights',
  maxItems: 3,
})

defineEmits<{
  'insight-click': [insightId: string]
  'action-click': [insightId: string]
}>()

const displayedInsights = computed(() => props.insights.slice(0, props.maxItems))

const confidenceColor = (confidence: string): BadgeVariant => {
  const colors: Record<string, BadgeVariant> = {
    high: 'success',
    medium: 'warning',
    low: 'info',
  }
  return colors[confidence] || 'neutral'
}
</script>

<template>
  <Card class="border border-ai-100 bg-gradient-to-br from-ai-50 to-transparent">
    <template #header>
      <div class="flex items-center gap-2">
        <Lightbulb class="h-5 w-5 text-ai-600" />
        <h3 class="font-medium text-neutral-900">{{ title }}</h3>
      </div>
    </template>

    <div v-if="displayedInsights.length === 0" class="py-8 text-center text-neutral-500">
      <p class="text-sm">No insights at this time</p>
    </div>
    <div v-else class="space-y-3">
      <div
        v-for="insight in displayedInsights"
        :key="insight.id"
        class="p-3 rounded-lg bg-white border border-ai-100 hover:shadow-soft transition-shadow cursor-pointer"
        @click="$emit('insight-click', insight.id)"
      >
        <div class="flex items-start justify-between gap-2 mb-2">
          <p class="font-medium text-neutral-900 flex-1">{{ insight.title }}</p>
          <StatusBadge :label="insight.confidence" :variant="confidenceColor(insight.confidence)" class="flex-shrink-0" />
        </div>
        <p class="text-sm text-neutral-600 mb-3">{{ insight.description }}</p>
        <div class="flex items-center justify-between">
          <span class="text-xs text-neutral-400">{{ new Date(insight.timestamp).toLocaleDateString() }}</span>
          <button
            v-if="insight.action"
            class="text-xs font-medium text-ai-600 hover:text-ai-700 transition-colors"
            @click.stop="$emit('action-click', insight.id)"
          >
            {{ insight.action }} →
          </button>
        </div>
      </div>
    </div>
  </Card>
</template>
