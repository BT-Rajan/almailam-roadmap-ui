<script setup lang="ts">
import { ArrowDown, ArrowUp } from '@lucide/vue'
import { computed, onMounted } from 'vue'

import ErrorState from '@/components/common/ErrorState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import AIConfigSummaryCard from '@/components/administration/AIConfigSummaryCard.vue'
import AIProviderCard from '@/components/administration/AIProviderCard.vue'
import { useAIConfigStore } from '@/stores/aiConfigStore'
import { useToastStore } from '@/stores/toastStore'
import type { AIProviderId } from '@/types/AiConfig'
import type { SelectOption } from '@/types/Ui'

const aiConfigStore = useAIConfigStore()
const toastStore = useToastStore()

const providerOptions = computed<SelectOption[]>(
  () => aiConfigStore.config?.providers.map((provider) => ({ label: provider.label, value: provider.id })) ?? [],
)

const orderedProviders = computed(() => {
  if (!aiConfigStore.config) return []
  return aiConfigStore.config.providerPriority
    .map((providerId) => aiConfigStore.config?.providers.find((provider) => provider.id === providerId))
    .filter((provider): provider is NonNullable<typeof provider> => Boolean(provider))
})

function loadData(): void {
  aiConfigStore.loadConfiguration()
}

onMounted(() => {
  if (!aiConfigStore.config) loadData()
})

async function handleSave(): Promise<void> {
  const success = await aiConfigStore.saveConfiguration()
  if (success) {
    toastStore.show('success', 'AI configuration saved', 'Your changes have been applied.')
  } else {
    // Previously silent on failure -- a failed save (permission error,
    // network issue, bad value) looked identical to a successful no-op,
    // which is exactly why "toggling AI on/off doesn't seem to work" was
    // impossible to tell apart from an actual bug.
    toastStore.show('error', 'Unable to save', aiConfigStore.error ?? 'Please try again.')
  }
}

function resetSystemPrompt(): void {
  if (!aiConfigStore.config) return
  aiConfigStore.updateField('kbSystemPrompt', aiConfigStore.config.kbDefaultSystemPrompt)
}

function handleCancel(): void {
  loadData()
}

async function handleTest(providerId: AIProviderId): Promise<void> {
  const result = await aiConfigStore.testConnection(providerId)
  toastStore.show(result.success ? 'success' : 'error', result.success ? 'Connection successful' : 'Connection failed', result.message)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader
      title="Knowledgebase AI"
      subtitle="Configure the provider, grounding prompt, and limits for the knowledgebase Q&A assistant."
    />

    <ErrorState v-if="aiConfigStore.error" :description="aiConfigStore.error" @retry="loadData" />

    <div v-else-if="aiConfigStore.isLoading || !aiConfigStore.config" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-6">
        <SkeletonLoader :rows="6" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-6 laptop:col-span-2">
        <SkeletonLoader :rows="10" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="flex flex-col gap-4">
        <AIConfigSummaryCard :config="aiConfigStore.config" />
        <AIProviderCard
          v-for="provider in aiConfigStore.config.providers"
          :key="provider.id"
          :provider="provider"
          :is-default="provider.id === aiConfigStore.config.defaultProvider"
          :testing="aiConfigStore.testingProviderId === provider.id"
          :test-result="aiConfigStore.testResults[provider.id]"
          @update-key="aiConfigStore.updateApiKey(provider.id, $event)"
          @test="handleTest(provider.id)"
        />
      </div>

      <div class="flex flex-col gap-8 rounded-xl border border-border-light bg-bg-card p-6 laptop:col-span-2">
        <FormSection title="Availability" description="The knowledgebase Q&A tool is the only AI-backed feature besides the client ID check. All other workflows are unaffected if this is disabled.">
          <ToggleSwitch
            :model-value="aiConfigStore.config.isEnabled"
            label="Enable Knowledgebase Assistant"
            hint="Hides the Knowledge Base page's Ask panel and disables the ask endpoint when off."
            @update:model-value="aiConfigStore.updateField('isEnabled', $event)"
          />
        </FormSection>

        <FormSection title="Provider Selection" description="Choose the default provider and the fallback priority order.">
          <SelectBox
            :model-value="aiConfigStore.config.defaultProvider"
            label="Default Provider"
            :options="providerOptions"
            @update:model-value="aiConfigStore.updateField('defaultProvider', $event as AIProviderId)"
          />

          <div class="flex flex-col gap-2">
            <p class="text-sm font-medium text-text-secondary">Provider Priority</p>
            <ol class="flex flex-col gap-2">
              <li
                v-for="(provider, index) in orderedProviders"
                :key="provider.id"
                class="flex items-center justify-between gap-3 rounded-lg border border-border-light bg-bg-secondary px-3 py-2"
              >
                <div class="flex items-center gap-2">
                  <span class="flex h-6 w-6 items-center justify-center rounded-full bg-primary-50 text-xs font-semibold text-primary-600">
                    {{ index + 1 }}
                  </span>
                  <span class="text-sm text-text-secondary">{{ provider.label }}</span>
                  <StatusBadge v-if="provider.id === aiConfigStore.config.defaultProvider" label="Default" variant="primary" />
                </div>
                <div class="flex items-center gap-1">
                  <IconButton
                    :icon="ArrowUp"
                    label="Move up"
                    size="sm"
                    :disabled="index === 0"
                    @click="aiConfigStore.movePriority(provider.id, 'up')"
                  />
                  <IconButton
                    :icon="ArrowDown"
                    label="Move down"
                    size="sm"
                    :disabled="index === orderedProviders.length - 1"
                    @click="aiConfigStore.movePriority(provider.id, 'down')"
                  />
                </div>
              </li>
            </ol>
          </div>
        </FormSection>

        <FormSection title="Model & Performance" description="Applied to every knowledgebase Q&A request.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
            <NumberInput
              :model-value="aiConfigStore.config.timeoutSeconds"
              label="Timeout (seconds)"
              :min="5"
              :max="120"
              @update:model-value="aiConfigStore.updateField('timeoutSeconds', Number($event))"
            />
            <NumberInput
              :model-value="aiConfigStore.config.maxTokens"
              label="Maximum Tokens"
              :min="256"
              :max="8192"
              :step="256"
              @update:model-value="aiConfigStore.updateField('maxTokens', Number($event))"
            />
            <NumberInput
              :model-value="aiConfigStore.config.temperature"
              label="Temperature"
              :min="0"
              :max="1"
              :step="0.1"
              @update:model-value="aiConfigStore.updateField('temperature', Number($event))"
            />
          </div>
        </FormSection>

        <FormSection title="Caching & Retries" description="A repeated question against the same document(s) is served from cache instead of calling the provider again.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <NumberInput
              :model-value="aiConfigStore.config.cacheDurationMinutes"
              label="Answer Cache Duration (minutes)"
              hint="0 disables caching."
              :min="0"
              :max="1440"
              @update:model-value="aiConfigStore.updateField('cacheDurationMinutes', Number($event))"
            />
            <NumberInput
              :model-value="aiConfigStore.config.retryLimit"
              label="Retry Limit"
              :min="0"
              :max="5"
              @update:model-value="aiConfigStore.updateField('retryLimit', Number($event))"
            />
          </div>
        </FormSection>

        <FormSection title="Document Limits" description="Bounds on what can be uploaded and how much document text is sent to the provider per question.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
            <NumberInput
              :model-value="aiConfigStore.config.kbMaxUploadSizeMb"
              label="Max Upload Size (MB)"
              :min="1"
              :max="100"
              @update:model-value="aiConfigStore.updateField('kbMaxUploadSizeMb', Number($event))"
            />
            <NumberInput
              :model-value="aiConfigStore.config.kbMaxDocumentChars"
              label="Max Characters per Document"
              :min="1000"
              :max="1000000"
              :step="1000"
              @update:model-value="aiConfigStore.updateField('kbMaxDocumentChars', Number($event))"
            />
            <NumberInput
              :model-value="aiConfigStore.config.kbMaxContextChars"
              label="Max Context Characters (all documents)"
              hint="Caps total document text sent per question when asking across all active documents."
              :min="1000"
              :max="2000000"
              :step="1000"
              @update:model-value="aiConfigStore.updateField('kbMaxContextChars', Number($event))"
            />
          </div>
        </FormSection>

        <FormSection title="Grounding Prompt" description="Instructs the model to answer strictly from the uploaded document(s), stay concrete rather than generic, keep a firm-but-polite tone, and reply in the visitor's language (Arabic, English, or a mix). Edit with care.">
          <TextArea
            :model-value="aiConfigStore.config.kbSystemPrompt"
            :rows="10"
            :max-length="8000"
            @update:model-value="aiConfigStore.updateField('kbSystemPrompt', $event)"
          />
          <div class="flex justify-end">
            <BaseButton variant="ghost" size="sm" @click="resetSystemPrompt">Reset to Default</BaseButton>
          </div>
        </FormSection>

        <FormActionBar submit-label="Save Changes" :loading="aiConfigStore.isSaving" @submit="handleSave" @cancel="handleCancel" />
      </div>
    </div>
  </div>
</template>
