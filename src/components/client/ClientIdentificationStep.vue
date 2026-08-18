<script setup lang="ts">
import { computed, watch } from 'vue'

import DatePicker from '@/components/common/DatePicker.vue'
import FormSection from '@/components/common/FormSection.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import { getDefaultIdentificationTypeForClientType, getIdentificationTypeOptionsForClientType } from '@/constants/clientOptions'
import type { ClientWizardForm } from '@/types/ClientWizard'
import type { FieldErrors } from '@/utils/clientValidation'
import { todayIso } from '@/utils/clientValidation'

defineProps<{
  errors: FieldErrors
}>()

const form = defineModel<ClientWizardForm>({ required: true })
const maxDate = todayIso()

// Individuals identify with Civil ID/Passport; entity clients (Company/
// Organisation/Government Entity) identify with a trade licence instead --
// the option list and the section copy both follow the client type chosen
// in step 1, rather than always offering the same individual-oriented list.
const identificationTypeOptions = computed(() => getIdentificationTypeOptionsForClientType(form.value.clientType))
const isEntityClient = computed(() => form.value.clientType !== 'Individual' && form.value.clientType !== 'Other')

const identificationDescription = computed(() => {
  if (isEntityClient.value) {
    return "Optional -- record this client's trade licence. Once a document number is entered, issue and expiry dates are required."
  }
  return 'Optional -- record the primary identification document for this client if available. Once a document number is entered, issue and expiry dates are required.'
})

// If the client type changes (e.g. Individual -> Company) after a document
// type was already picked, drop it back to a valid choice for the new type
// instead of silently submitting an identification type that doesn't apply
// (this is what previously let every client onboard defaulted to 'Civil ID'
// regardless of type -- see createEmptyClientWizardForm in ClientWizard.ts).
watch(
  () => form.value.clientType,
  (clientType) => {
    const stillValid = identificationTypeOptions.value.some((option) => option.value === form.value.identification.documentType)
    if (!stillValid) {
      form.value.identification.documentType = getDefaultIdentificationTypeForClientType(clientType)
    }
  },
  { immediate: true },
)

function handleFileSelect(file: File | undefined): void {
  form.value.identificationFile = file ?? null
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <FormSection title="Identification" :description="identificationDescription">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.identification.documentType" label="Document Type" :options="identificationTypeOptions" />
        <TextInput v-model="form.identification.documentNumber" label="Document Number" />
        <DatePicker v-model="form.identification.issueDate" label="Issue Date" :max="maxDate" :error="errors.issueDate" />
        <DatePicker v-model="form.identification.expiryDate" label="Expiry Date" :error="errors.expiryDate" />
        <TextInput v-model="form.identification.issuingCountry" label="Issuing Country" :error="errors.issuingCountry" />
      </div>
    </FormSection>

    <FormSection title="Upload Document" description="Upload a copy of the identification or trade licence document.">
      <FileUploader hint="PDF or image files" @select="handleFileSelect" />
    </FormSection>
  </div>
</template>
