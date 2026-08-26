<script setup lang="ts">
import { CheckCircle2, Plug, XCircle } from '@lucide/vue'
import { computed, ref } from 'vue'

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

const props = withDefaults(defineProps<Props>(), {
  testResult: undefined,
})

// The real, live-usable credential is a server environment variable --
// never this form (see aiConfigStore.updateApiKey and the backend's
// AIProviderConfigOut.from_model for why "Connected" reflects that
// variable, not whether a key was ever typed in below).
const ENV_VAR_NAMES: Record<string, string> = { claude: 'ANTHROPIC_API_KEY', deepseek: 'DEEPSEEK_API_KEY' }
const envVarName = computed(() => ENV_VAR_NAMES[props.provider.id] ?? '')

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
        <p class="text-sm font-semibold text-text-primary">{{ provider.label }}</p>
        <StatusBadge v-if="isDefault" label="Default" variant="primary" />
      </div>
      <StatusBadge
        :label="provider.status === 'connected' ? 'Connected' : provider.status === 'error' ? 'Error' : 'Not Configured'"
        :variant="STATUS_VARIANTS[provider.status]"
        show-dot
      />
    </div>

    <p class="text-xs text-text-muted">Model: <span class="font-medium text-text-secondary">{{ provider.model }}</span></p>

    <p class="text-xs text-text-muted">
      Live calls use the <code class="rounded bg-bg-secondary px-1 py-0.5 font-mono">{{ envVarName }}</code>
      environment variable on the server -- not the field below. Set it (and redeploy/restart) to actually
      enable this provider.
    </p>

    <div class="flex flex-col gap-2 sm:flex-row sm:items-end">
      <TextInput
        v-model="newApiKey"
        type="password"
        :label="provider.apiKeyMasked ? `Local note: ${provider.apiKeyMasked}` : 'Local note (not a live key)'"
        placeholder="Optional -- for your own reference only"
        hint="Saved here for your own bookkeeping only. Never sent anywhere as a live credential."
        class="flex-1"
      />
      <BaseButton variant="secondary" size="sm" :disabled="!newApiKey.trim()" @click="applyNewKey">Save Note</BaseButton>
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
