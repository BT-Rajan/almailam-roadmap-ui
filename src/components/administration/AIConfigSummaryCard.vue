<script setup lang="ts">
import { Bot, Clock, Database, Sparkles } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { AIConfiguration } from '@/types/AiConfig'

const props = defineProps<{
  config: AIConfiguration
}>()

const defaultProviderLabel = computed(
  () => props.config.providers.find((provider) => provider.id === props.config.defaultProvider)?.label ?? '—',
)
</script>

<template>
  <Card>
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-3">
        <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-ai-50 text-ai-600">
          <Sparkles class="h-5 w-5" />
        </span>
        <div class="min-w-0">
          <p class="truncate font-semibold text-neutral-900">AI Assistant</p>
          <StatusBadge :label="config.isEnabled ? 'Enabled' : 'Disabled'" :variant="config.isEnabled ? 'success' : 'neutral'" show-dot />
        </div>
      </div>

      <div class="flex flex-col gap-3 border-t border-border-light pt-4 text-sm text-neutral-600">
        <div class="flex items-center gap-2">
          <Bot class="h-4 w-4 shrink-0 text-neutral-400" />
          <span>Default Provider: <span class="font-medium text-neutral-800">{{ defaultProviderLabel }}</span></span>
        </div>
        <div class="flex items-center gap-2">
          <Clock class="h-4 w-4 shrink-0 text-neutral-400" />
          <span>Timeout: <span class="font-medium text-neutral-800">{{ config.timeoutSeconds }}s</span></span>
        </div>
        <div class="flex items-center gap-2">
          <Database class="h-4 w-4 shrink-0 text-neutral-400" />
          <span>Cache Duration: <span class="font-medium text-neutral-800">{{ config.cacheDurationMinutes }} min</span></span>
        </div>
      </div>

      <p class="border-t border-border-light pt-3 text-xs text-neutral-400">
        AI is a productivity assistant. All business workflows continue functioning normally if AI is disabled.
      </p>
    </div>
  </Card>
</template>
