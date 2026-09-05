<script setup lang="ts">
import { CheckCircle2, Info, Plug, XCircle } from '@lucide/vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

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
  'update-key': [rawKey: string]
  test: []
}>()

const { t } = useI18n()

const newApiKey = ref('')
const staged = ref(false)

const STATUS_VARIANTS: Record<AIProviderConfig['status'], BadgeVariant> = {
  connected: 'success',
  'not-configured': 'neutral',
  error: 'danger',
}

function applyNewKey(): void {
  if (!newApiKey.value.trim()) return
  // Sent as plain text over HTTPS to the backend, which encrypts it
  // before storing -- never persisted or logged in the clear (see
  // app.core.security.encrypt_secret). Nothing is saved until the page's
  // own Save Changes is clicked, same as every other field here.
  emit('update-key', newApiKey.value.trim())
  newApiKey.value = ''
  staged.value = true
}
</script>

<template>
  <div class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4">
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <p class="text-sm font-semibold text-text-primary">{{ provider.label }}</p>
        <StatusBadge v-if="isDefault" :label="t('administration.aiPage.default')" variant="primary" />
      </div>
      <StatusBadge
        :label="provider.status === 'connected' ? t('administration.aiPage.connected') : provider.status === 'error' ? t('administration.aiPage.error') : t('administration.aiPage.notConfigured')"
        :variant="STATUS_VARIANTS[provider.status]"
        show-dot
      />
    </div>

    <p class="text-xs text-text-muted">{{ t('administration.aiPage.modelLine', { model: provider.model || t('administration.aiPage.serverDefault') }) }}</p>

    <div class="flex flex-col gap-2 sm:flex-row sm:items-end">
      <TextInput
        v-model="newApiKey"
        type="password"
        :label="provider.apiKeyMasked ? t('administration.aiPage.currentKey', { key: provider.apiKeyMasked }) : t('administration.aiPage.apiKey')"
        :placeholder="t('administration.aiPage.apiKeyPlaceholder')"
        class="flex-1"
      />
      <BaseButton variant="secondary" size="sm" :disabled="!newApiKey.trim()" @click="applyNewKey">{{ t('administration.aiPage.updateKey') }}</BaseButton>
    </div>
    <p v-if="staged" class="flex items-center gap-1.5 text-xs text-text-muted">
      <Info class="h-3.5 w-3.5 shrink-0" />
      {{ t('administration.aiPage.stagedNotice') }}
    </p>

    <div class="flex items-center justify-between gap-3 border-t border-border-light pt-3">
      <BaseButton variant="ghost" size="sm" :icon="Plug" :loading="testing" @click="emit('test')"> {{ t('administration.aiPage.testConnection') }} </BaseButton>
      <p v-if="testResult" class="flex items-center gap-1.5 text-xs" :class="testResult.success ? 'text-success-600' : 'text-danger-600'">
        <CheckCircle2 v-if="testResult.success" class="h-3.5 w-3.5" />
        <XCircle v-else class="h-3.5 w-3.5" />
        {{ testResult.message }}
      </p>
    </div>
  </div>
</template>
