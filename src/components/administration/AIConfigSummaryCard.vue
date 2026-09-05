<script setup lang="ts">
import { Bot, Clock, Database, Sparkles } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { AIConfiguration } from '@/types/AiConfig'

const props = defineProps<{
  config: AIConfiguration
}>()

const { t } = useI18n()

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
          <p class="text-sm font-semibold text-text-primary truncate">{{ t('administration.aiPage.knowledgebaseAssistant') }}</p>
          <StatusBadge :label="config.isEnabled ? t('administration.aiPage.enabled') : t('administration.aiPage.disabled')" :variant="config.isEnabled ? 'success' : 'neutral'" show-dot />
        </div>
      </div>

      <div class="flex flex-col gap-3 border-t border-border-light pt-4 text-sm text-text-secondary">
        <div class="flex items-center gap-2">
          <Bot class="h-4 w-4 shrink-0 text-text-muted" />
          <span>{{ t('administration.aiPage.defaultProvider') }}: <span class="font-medium text-text-primary">{{ defaultProviderLabel }}</span></span>
        </div>
        <div class="flex items-center gap-2">
          <Clock class="h-4 w-4 shrink-0 text-text-muted" />
          <span>{{ t('administration.aiPage.timeoutLabel') }}: <span class="font-medium text-text-primary">{{ config.timeoutSeconds }}s</span></span>
        </div>
        <div class="flex items-center gap-2">
          <Database class="h-4 w-4 shrink-0 text-text-muted" />
          <span>{{ t('administration.aiPage.cacheDurationLabel') }}: <span class="font-medium text-text-primary">{{ config.cacheDurationMinutes }} {{ t('administration.aiPage.minutesAbbrev') }}</span></span>
        </div>
      </div>

      <p class="border-t border-border-light pt-3 text-xs text-text-muted">
        {{ t('administration.aiPage.summaryFooter') }}
      </p>
    </div>
  </Card>
</template>
