<script setup lang="ts">
import { AlertTriangle, Sparkles, Trash2 } from '@lucide/vue'
import { computed } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import AILoadingState from '@/components/ai/AILoadingState.vue'
import AIResponseCard from '@/components/ai/AIResponseCard.vue'
import AISuggestionCard from '@/components/ai/AISuggestionCard.vue'
import { useAIAssistantStore } from '@/stores/aiAssistantStore'
import { useAIConfigStore } from '@/stores/aiConfigStore'
import type { SelectOption } from '@/types/Ui'

const aiAssistantStore = useAIAssistantStore()
const aiConfigStore = useAIConfigStore()

const isAIDisabled = computed(() => aiConfigStore.config?.isEnabled === false)

const defaultProviderLabel = computed(
  () => aiConfigStore.config?.providers.find((provider) => provider.id === aiConfigStore.config?.defaultProvider)?.label,
)

const templateOptions = computed<SelectOption[]>(() =>
  aiConfigStore.templates.map((template) => ({ label: template.name, value: template.id })),
)

function formatTime(isoDate: string): string {
  return new Date(isoDate).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
}

function handleTemplateChange(templateId: string): void {
  if (!templateId) return
  aiAssistantStore.applyTemplate(templateId)
}

function handleSuggestionSelect(suggestion: string): void {
  aiAssistantStore.setPrompt(suggestion)
}
</script>

<template>
  <BaseDrawer
    :model-value="aiAssistantStore.isOpen"
    title="AI Assistant"
    width="lg"
    @update:model-value="aiAssistantStore.close"
  >
    <div class="flex flex-col gap-5">
      <div class="flex items-center justify-between gap-3 rounded-lg border border-ai-100 bg-ai-50 px-3 py-2">
        <div class="flex items-center gap-2">
          <Sparkles class="h-4 w-4 text-ai-600" />
          <span class="text-xs font-medium text-neutral-600">
            Provider: <span class="font-semibold text-neutral-800">{{ defaultProviderLabel ?? 'Not configured' }}</span>
          </span>
        </div>
        <StatusBadge
          :label="isAIDisabled ? 'AI Disabled' : 'AI Enabled'"
          :variant="isAIDisabled ? 'neutral' : 'success'"
          show-dot
        />
      </div>

      <div v-if="isAIDisabled" class="flex items-start gap-2 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 text-sm text-warning-700">
        <AlertTriangle class="h-4 w-4 shrink-0" />
        <span>AI is currently disabled for this workspace. Ask an administrator to enable it in AI Configuration.</span>
      </div>

      <div class="flex flex-col gap-3">
        <SelectBox
          :model-value="aiAssistantStore.selectedTemplateId ?? ''"
          label="Prompt Template (optional)"
          placeholder="Choose a template to get started"
          :options="templateOptions"
          :disabled="isAIDisabled"
          @update:model-value="handleTemplateChange"
        />
        <TextArea
          :model-value="aiAssistantStore.currentPrompt"
          label="Ask the AI Assistant"
          placeholder="e.g. Summarize the current status of this project"
          :rows="4"
          :disabled="isAIDisabled"
          @update:model-value="aiAssistantStore.setPrompt"
        />
        <p v-if="aiAssistantStore.error" class="text-xs text-danger-600">{{ aiAssistantStore.error }}</p>
        <BaseButton
          :icon="Sparkles"
          :loading="aiAssistantStore.isSending"
          :disabled="isAIDisabled || !aiAssistantStore.currentPrompt.trim()"
          full-width
          @click="aiAssistantStore.send"
        >
          Ask AI
        </BaseButton>
      </div>

      <AILoadingState v-if="aiAssistantStore.isSending" label="AI is thinking…" />

      <div class="flex flex-col gap-4">
        <div v-if="aiAssistantStore.history.length > 0" class="flex items-center justify-between">
          <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">Conversation History</p>
          <button
            type="button"
            class="flex items-center gap-1 text-xs font-medium text-neutral-400 hover:text-danger-600"
            @click="aiAssistantStore.clearHistory"
          >
            <Trash2 class="h-3.5 w-3.5" />
            Clear
          </button>
        </div>

        <EmptyState
          v-else-if="!aiAssistantStore.isSending"
          title="No questions asked yet"
          description="Pick a template or type a question above to get started."
        />

        <div v-for="interaction in aiAssistantStore.history" :key="interaction.id" class="flex flex-col gap-2">
          <div class="flex items-center justify-between text-xs text-neutral-400">
            <span v-if="interaction.templateName">{{ interaction.templateName }}</span>
            <span v-else>Custom question</span>
            <span>{{ formatTime(interaction.timestamp) }}</span>
          </div>
          <AIResponseCard :summary="interaction.summary" :details="interaction.details" :confidence="interaction.confidence" />
          <AISuggestionCard :suggestions="interaction.suggestedActions" @select="handleSuggestionSelect" />
        </div>
      </div>
    </div>
  </BaseDrawer>
</template>
