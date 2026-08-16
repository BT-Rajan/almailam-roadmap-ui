<script setup lang="ts">
import { reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { CLIENT_CONSENT_TYPE_SELECT_OPTIONS } from '@/constants/clientOptions'
import type { ClientConsentType } from '@/types/Client'

const props = defineProps<{
  modelValue: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { consentType: ClientConsentType; version: string; granted: boolean; method: string }]
}>()

function emptyForm() {
  return { consentType: 'Process Personal Information' as ClientConsentType, version: 'v1.0', granted: true, method: '' }
}

const form = reactive(emptyForm())
const errors = reactive({ method: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, emptyForm())
    errors.method = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.method = form.method.trim() ? '' : 'How this was recorded is required (e.g. Phone call, Email, In person)'
  if (errors.method) return

  emit('confirm', { ...form })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Record Consent" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.consentType" label="Consent Type" :options="CLIENT_CONSENT_TYPE_SELECT_OPTIONS" />
      <ToggleSwitch v-model="form.granted" label="Granted" />
      <TextInput v-model="form.version" label="Policy Version" required />
      <TextInput v-model="form.method" label="How was this recorded" placeholder="e.g. Phone call, Email, In person" required :error="errors.method" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Save</BaseButton>
    </template>
  </BaseDialog>
</template>
