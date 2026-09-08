<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

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
const { t } = useI18n()

const IDENTIFICATION_MAX_SIZE_BYTES = 5 * 1024 * 1024
const IDENTIFICATION_ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']

// Individuals identify with Civil ID/Passport; entity clients (Company/
// Organisation/Government Entity) identify with a trade licence instead --
// the option list and the section copy both follow the client type chosen
// in step 1, rather than always offering the same individual-oriented list.
const identificationTypeOptions = computed(() => getIdentificationTypeOptionsForClientType(form.value.clientType))
const isEntityClient = computed(() => form.value.clientType !== 'Individual' && form.value.clientType !== 'Other')

const identificationDescription = computed(() =>
  isEntityClient.value ? t('client.identificationStep.entityDescription') : t('client.identificationStep.individualDescription'),
)

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

// A Trade Licence's own number and issuing country are the same values
// already typed into step 1's Organisation Information section
// ("Trade Licence Number", "Country of Registration") -- pre-fill
// rather than making staff retype the same licence number and country
// a second time. Only fills blanks, re-checked every time this step is
// shown, so anything already typed (a different actual document, or a
// deliberate correction) is left alone.
watch(
  () => [
    form.value.identification.documentType,
    form.value.organisationProfile.tradeLicenceNumber,
    form.value.organisationProfile.countryOfRegistration,
  ] as const,
  ([documentType, tradeLicenceNumber, countryOfRegistration]) => {
    if (documentType !== 'Trade Licence') return
    if (!form.value.identification.documentNumber.trim() && tradeLicenceNumber.trim()) {
      form.value.identification.documentNumber = tradeLicenceNumber
    }
    if (!form.value.identification.issuingCountry.trim() && countryOfRegistration.trim()) {
      form.value.identification.issuingCountry = countryOfRegistration
    }
  },
  { immediate: true },
)

const uploadError = ref<string>()

function handleFileSelect(file: File | undefined): void {
  uploadError.value = undefined
  form.value.identificationFile = file ?? null
}

function handleUploaderError(message: string): void {
  uploadError.value = message
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <FormSection :title="t('client.identificationStep.title')" :description="identificationDescription">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.identification.documentType" :label="t('client.identificationStep.documentType')" required :options="identificationTypeOptions" />
        <TextInput v-model="form.identification.documentNumber" :label="t('client.identificationStep.documentNumber')" required :error="errors.documentNumber" />
        <DatePicker v-model="form.identification.issueDate" :label="t('client.identificationStep.issueDate')" required :max="maxDate" :error="errors.issueDate" />
        <DatePicker v-model="form.identification.expiryDate" :label="t('client.identificationStep.expiryDate')" required :error="errors.expiryDate" />
        <TextInput v-model="form.identification.issuingCountry" :label="t('client.identificationStep.issuingCountry')" required :error="errors.issuingCountry" />
      </div>
    </FormSection>

    <FormSection :title="t('client.identificationStep.uploadTitle')" :description="t('client.identificationStep.uploadDescription')" required>
      <FileUploader
        hint="JPG, PNG or PDF, up to 5 MB"
        accept=".jpg,.jpeg,.png,.pdf"
        :max-size-bytes="IDENTIFICATION_MAX_SIZE_BYTES"
        :allowed-extensions="IDENTIFICATION_ALLOWED_EXTENSIONS"
        @select="handleFileSelect"
        @error="handleUploaderError"
      />

      <p v-if="uploadError" class="mt-2 text-xs text-danger-500">{{ uploadError }}</p>
      <p v-else-if="errors.identificationFile" class="mt-2 text-xs text-danger-500">{{ errors.identificationFile }}</p>
    </FormSection>
  </div>
</template>
