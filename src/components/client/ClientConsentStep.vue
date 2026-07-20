<script setup lang="ts">
import FormSection from '@/components/common/FormSection.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { CLIENT_CONSENT_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientWizardForm } from '@/types/ClientWizard'

const form = defineModel<ClientWizardForm>({ required: true })
</script>

<template>
  <FormSection title="Consent" description="Record the client's consent before completing onboarding.">
    <div class="flex flex-col gap-4">
      <div
        v-for="consent in CLIENT_CONSENT_TYPE_OPTIONS"
        :key="consent.type"
        class="flex items-center justify-between gap-4 rounded-lg border border-border-light p-4"
      >
        <div class="flex flex-col gap-0.5">
          <p class="text-sm font-medium text-neutral-800">
            {{ consent.type }}
            <span v-if="consent.mandatory" class="text-danger-500">*</span>
          </p>
          <p class="text-xs text-neutral-500">{{ consent.description }}</p>
        </div>
        <ToggleSwitch v-model="form.consents[consent.type]" />
      </div>
    </div>
  </FormSection>
</template>
