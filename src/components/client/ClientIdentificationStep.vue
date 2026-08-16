<script setup lang="ts">
import DatePicker from '@/components/common/DatePicker.vue'
import FormSection from '@/components/common/FormSection.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import { CLIENT_IDENTIFICATION_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientWizardForm } from '@/types/ClientWizard'
import type { FieldErrors } from '@/utils/clientValidation'
import { todayIso } from '@/utils/clientValidation'

defineProps<{
  errors: FieldErrors
}>()

const form = defineModel<ClientWizardForm>({ required: true })
const maxDate = todayIso()

function handleFileSelect(file: File | undefined): void {
  form.value.identificationFile = file ?? null
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <FormSection title="Identification" description="Optional -- record the primary identification or licence document for this client if available. Once a document number is entered, issue and expiry dates are required.">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.identification.documentType" label="Document Type" :options="CLIENT_IDENTIFICATION_TYPE_OPTIONS" />
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
