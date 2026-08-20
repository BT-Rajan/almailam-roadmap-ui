<script setup lang="ts">
import FormSection from '@/components/common/FormSection.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { CLIENT_CONSENT_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientWizardForm } from '@/types/ClientWizard'
import type { FieldErrors } from '@/utils/clientValidation'

defineProps<{
  errors?: FieldErrors
}>()

const form = defineModel<ClientWizardForm>({ required: true })
</script>

<template>
  <FormSection title="Consent" description="Record the client's consent before completing onboarding.">
    <div class="flex flex-col gap-4">
      <div
        v-for="consent in CLIENT_CONSENT_TYPE_OPTIONS"
        :key="consent.type"
        class="flex flex-col gap-2 rounded-lg border p-4"
        :class="errors?.[consent.type] ? 'border-danger-300' : 'border-border-light'"
      >
        <div class="flex items-center justify-between gap-4">
          <div class="flex flex-col gap-0.5">
            <p class="text-sm font-medium text-text-primary">
              {{ consent.type }}
              <span v-if="consent.mandatory" class="text-danger-500">*</span>
            </p>
            <p class="text-xs text-text-muted">{{ consent.description }}</p>
          </div>
          <ToggleSwitch v-model="form.consents[consent.type]" />
        </div>
        <p v-if="errors?.[consent.type]" class="text-xs text-danger-500">{{ errors[consent.type] }}</p>
      </div>
    </div>
  </FormSection>
</template>
