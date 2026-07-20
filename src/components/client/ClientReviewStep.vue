<script setup lang="ts">
import { computed } from 'vue'

import DetailPanel from '@/components/common/DetailPanel.vue'
import type { ClientWizardForm } from '@/types/ClientWizard'

const form = defineModel<ClientWizardForm>({ required: true })

const isIndividual = computed(() => form.value.clientType === 'Individual')

const displayName = computed(() =>
  isIndividual.value ? form.value.individualProfile.fullLegalName : form.value.organisationProfile.legalName,
)

const grantedConsents = computed(() =>
  Object.entries(form.value.consents)
    .filter(([, granted]) => granted)
    .map(([type]) => type),
)
</script>

<template>
  <div class="flex flex-col gap-6">
    <DetailPanel
      title="Client Summary"
      :items="[
        { label: 'Client Type', value: form.clientType },
        { label: 'Name', value: displayName || '—' },
        { label: 'Mobile', value: form.mobile || '—' },
        { label: 'Email', value: form.email || '—' },
        { label: 'City', value: form.city || '—' },
      ]"
    />

    <DetailPanel
      title="Contacts"
      :items="form.contacts.map((contact, index) => ({ label: `Contact ${index + 1}`, value: `${contact.name || '—'} (${contact.contactType})` }))"
    />

    <DetailPanel
      title="Identification"
      :items="[
        { label: 'Document Type', value: form.identification.documentType },
        { label: 'Document Number', value: form.identification.documentNumber || '—' },
        { label: 'Document Uploaded', value: form.hasUploadedFile ? 'Yes' : 'Not yet uploaded' },
      ]"
    />

    <DetailPanel
      title="Consent"
      :items="[{ label: 'Consents Granted', value: grantedConsents.length > 0 ? grantedConsents.join(', ') : 'None recorded' }]"
    />
  </div>
</template>
