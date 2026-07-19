<script setup lang="ts">
import { CheckCircle2, Plug, XCircle } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { AIProviderConfig, ProviderTestResult } from '@/types/AiConfig'
import type { BadgeVariant } from '@/types/Ui'

interface Props {
  provider: AIProviderConfig
  isDefault: boolean
  testing: boolean
  testResult?: ProviderTestResult
}

withDefaults(defineProps<Props>(), {
  testResult: undefined,
})

const emit = defineEmits<{
  'update-key': [maskedKey: string]
  test: []
}>()

const newApiKey = ref('')

const STATUS_VARIANTS: Record<AIProviderConfig['status'], BadgeVariant> = {
  connected: 'success',
  'not-configured': 'neutral',
  error: 'danger',
}

function applyNewKey(): void {
  if (!newApiKey.value.trim()) return
  const trimmed = newApiKey.value.trim()
  const masked = trimmed.length > 4 ? `••••••••${trimmed.slice(-4)}` : '••••••••'
  emit('update-key', masked)
  newApiKey.value = ''
}
</script>

<template>
  <div class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4">
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <p class="text-sm font-semibold text-neutral-800">{{ provider.label }}</p>
        <StatusBadge v-if="isDefault" label="Default" variant="primary" />
      </div>
      <StatusBadge
        :label="provider.status === 'connected' ? 'Connected' : provider.status === 'error' ? 'Error' : 'Not Configured'"
        :variant="STATUS_VARIANTS[provider.status]"
        show-dot
      />
    </div>

    <p class="text-xs text-neutral-500">Model: <span class="font-medium text-neutral-700">{{ provider.model }}</span></p>

    <div class="flex flex-col gap-2 sm:flex-row sm:items-end">
      <TextInput
        v-model="newApiKey"
        type="password"
        :label="provider.apiKeyMasked ? `Current key: ${provider.apiKeyMasked}` : 'API Key'"
        placeholder="Enter new API key to update"
        class="flex-1"
      />
      <BaseButton variant="secondary" size="sm" :disabled="!newApiKey.trim()" @click="applyNewKey">Update Key</BaseButton>
    </div>

    <div class="flex items-center justify-between gap-3 border-t border-border-light pt-3">
      <BaseButton variant="ghost" size="sm" :icon="Plug" :loading="testing" @click="emit('test')"> Test Connection </BaseButton>
      <p v-if="testResult" class="flex items-center gap-1.5 text-xs" :class="testResult.success ? 'text-success-600' : 'text-danger-600'">
        <CheckCircle2 v-if="testResult.success" class="h-3.5 w-3.5" />
        <XCircle v-else class="h-3.5 w-3.5" />
        {{ testResult.message }}
      </p>
    </div>
  </div>
</template>
