<script setup lang="ts">
import { ArrowDown, ArrowUp, Pencil } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import ErrorState from '@/components/common/ErrorState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import AIConfigSummaryCard from '@/components/administration/AIConfigSummaryCard.vue'
import AIProviderCard from '@/components/administration/AIProviderCard.vue'
import PromptTemplateEditorDialog from '@/components/administration/PromptTemplateEditorDialog.vue'
import { useAIConfigStore } from '@/stores/aiConfigStore'
import { useToastStore } from '@/stores/toastStore'
import type { AIProviderId, PromptTemplate } from '@/types/AiConfig'
import type { SelectOption } from '@/types/Ui'

const aiConfigStore = useAIConfigStore()
const toastStore = useToastStore()

const editingTemplate = ref<PromptTemplate | undefined>(undefined)
const isTemplateDialogOpen = ref(false)
const isSavingTemplate = ref(false)

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
  }
}

function handleCancel(): void {
  loadData()
}

async function handleTest(providerId: AIProviderId): Promise<void> {
  const result = await aiConfigStore.testConnection(providerId)
  toastStore.show(result.success ? 'success' : 'error', result.success ? 'Connection successful' : 'Connection failed', result.message)
}

function openEditTemplate(template: PromptTemplate): void {
  editingTemplate.value = template
  isTemplateDialogOpen.value = true
}

async function saveTemplate(input: Omit<PromptTemplate, 'id'>): Promise<void> {
  if (!editingTemplate.value) return
  isSavingTemplate.value = true
  try {
    await aiConfigStore.savePromptTemplate(editingTemplate.value.id, input)
    toastStore.show('success', 'Prompt template updated', `${input.name} has been saved.`)
    isTemplateDialogOpen.value = false
  } catch {
    toastStore.show('error', 'Unable to save template', 'Please try again.')
  } finally {
    isSavingTemplate.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-4 lg:p-6">
    <PageHeader title="AI Configuration" subtitle="Configure AI providers, models, caching and prompt templates." />

    <ErrorState v-if="aiConfigStore.error" :description="aiConfigStore.error" @retry="loadData" />

    <div v-else-if="aiConfigStore.isLoading || !aiConfigStore.config" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="6" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-5 laptop:col-span-2">
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

      <div class="flex flex-col gap-8 rounded-xl border border-border-light bg-bg-card p-5 laptop:col-span-2">
        <FormSection title="AI Availability" description="AI is optional. All business workflows continue functioning normally if disabled.">
          <ToggleSwitch
            :model-value="aiConfigStore.config.isEnabled"
            label="Enable AI Assistant"
            hint="Hides AI buttons and panels across the application when disabled."
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
            <p class="text-sm font-medium text-neutral-700">Provider Priority</p>
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
                  <span class="text-sm text-neutral-700">{{ provider.label }}</span>
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

        <FormSection title="Model & Performance" description="Applied to every AI request unless overridden per template.">
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

        <FormSection title="Caching & Retries" description="Repeated requests reuse cached responses whenever possible.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <NumberInput
              :model-value="aiConfigStore.config.cacheDurationMinutes"
              label="Cache Duration (minutes)"
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

        <FormSection title="Prompt Templates" description="Administrator-configurable prompts used across the application. Edited without code changes.">
          <div class="flex flex-col gap-2">
            <div
              v-for="template in aiConfigStore.templates"
              :key="template.id"
              class="flex items-start justify-between gap-3 rounded-lg border border-border-light bg-bg-secondary px-4 py-3"
            >
              <div class="min-w-0">
                <div class="flex items-center gap-2">
                  <p class="text-sm font-medium text-neutral-800">{{ template.name }}</p>
                  <StatusBadge :label="template.module" variant="neutral" />
                </div>
                <p class="mt-1 text-xs text-neutral-500">{{ template.description }}</p>
              </div>
              <IconButton :icon="Pencil" label="Edit template" size="sm" variant="ghost" @click="openEditTemplate(template)" />
            </div>
          </div>
        </FormSection>

        <FormActionBar submit-label="Save Changes" :loading="aiConfigStore.isSaving" @submit="handleSave" @cancel="handleCancel" />
      </div>
    </div>

    <PromptTemplateEditorDialog v-model="isTemplateDialogOpen" :template="editingTemplate" :saving="isSavingTemplate" @save="saveTemplate" />
  </div>
</template>
