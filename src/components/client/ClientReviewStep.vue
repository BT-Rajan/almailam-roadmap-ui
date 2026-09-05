<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import DetailPanel from '@/components/common/DetailPanel.vue'
import type { ClientWizardForm } from '@/types/ClientWizard'

const form = defineModel<ClientWizardForm>({ required: true })

const { t } = useI18n()

const isIndividual = computed(() => form.value.clientType === 'Individual')

const displayName = computed(() =>
  isIndividual.value ? form.value.individualProfile.fullLegalName : form.value.organisationProfile.legalName,
)

const CLIENT_TYPE_LABEL_KEYS: Record<string, string> = {
  Individual: 'clientOptions.type.individual',
  Company: 'clientOptions.type.company',
  Organisation: 'clientOptions.type.organisation',
  'Government Entity': 'clientOptions.type.governmentEntity',
  Other: 'clientOptions.type.other',
}
const clientTypeLabel = computed(() => t(CLIENT_TYPE_LABEL_KEYS[form.value.clientType] ?? form.value.clientType))

const CONTACT_TYPE_LABEL_KEYS: Record<string, string> = {
  'Primary Contact': 'clientOptions.contactType.primary',
  'Billing Contact': 'clientOptions.contactType.billing',
  'Legal Contact': 'clientOptions.contactType.legal',
  'Authorised Representative': 'clientOptions.contactType.authorisedRepresentative',
  'Technical Contact': 'clientOptions.contactType.technical',
  Other: 'clientOptions.contactType.other',
}
function contactTypeLabel(contactType: string): string {
  return t(CONTACT_TYPE_LABEL_KEYS[contactType] ?? contactType)
}

const IDENTIFICATION_TYPE_LABEL_KEYS: Record<string, string> = {
  'Civil ID': 'clientOptions.identificationType.civilId',
  Passport: 'clientOptions.identificationType.passport',
  'Trade Licence': 'clientOptions.identificationType.tradeLicence',
  Other: 'clientOptions.identificationType.other',
}
const identificationTypeLabel = computed(
  () => t(IDENTIFICATION_TYPE_LABEL_KEYS[form.value.identification.documentType] ?? form.value.identification.documentType),
)

const summaryItems = computed(() => [
  { label: t('client.reviewStep.clientType'), value: clientTypeLabel.value },
  { label: t('client.reviewStep.name'), value: displayName.value || '—' },
  { label: t('client.reviewStep.mobile'), value: form.value.mobile || '—' },
  { label: t('client.reviewStep.email'), value: form.value.email || '—' },
  { label: t('client.reviewStep.city'), value: form.value.address.city || '—' },
])

const contactItems = computed(() =>
  form.value.contacts.map((contact, index) => ({
    label: t('client.reviewStep.contactNumber', { number: index + 1 }),
    value: `${contact.name || '—'} (${contactTypeLabel(contact.contactType)})`,
  })),
)

const identificationItems = computed(() => [
  { label: t('client.reviewStep.documentType'), value: identificationTypeLabel.value },
  { label: t('client.reviewStep.documentNumber'), value: form.value.identification.documentNumber || '—' },
  {
    label: t('client.reviewStep.documentUploaded'),
    value: form.value.identificationFile ? form.value.identificationFile.name : t('client.reviewStep.notYetUploaded'),
  },
])
</script>

<template>
  <div class="flex flex-col gap-6">
    <DetailPanel :title="t('client.reviewStep.summaryTitle')" :items="summaryItems" />

    <DetailPanel :title="t('client.contactAddressStep.contactsTitle')" :items="contactItems" />

    <DetailPanel :title="t('client.reviewStep.identificationTitle')" :items="identificationItems" />
  </div>
</template>
