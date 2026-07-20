<script setup lang="ts">
import DatePicker from '@/components/common/DatePicker.vue'
import FormSection from '@/components/common/FormSection.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import { CLIENT_IDENTIFICATION_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientWizardForm } from '@/types/ClientWizard'

const form = defineModel<ClientWizardForm>({ required: true })

function handleFileSelect(file: File | undefined): void {
  form.value.hasUploadedFile = Boolean(file)
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <FormSection title="Identification" description="Record the primary identification or licence document for this client.">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.identification.documentType" label="Document Type" :options="CLIENT_IDENTIFICATION_TYPE_OPTIONS" />
        <TextInput v-model="form.identification.documentNumber" label="Document Number" required />
        <DatePicker v-model="form.identification.issueDate" label="Issue Date" />
        <DatePicker v-model="form.identification.expiryDate" label="Expiry Date" />
        <TextInput v-model="form.identification.issuingCountry" label="Issuing Country" required />
      </div>
    </FormSection>

    <FormSection title="Upload Document" description="Upload a copy of the identification or trade licence document.">
      <FileUploader hint="PDF or image files" @select="handleFileSelect" />
    </FormSection>
  </div>
</template>
