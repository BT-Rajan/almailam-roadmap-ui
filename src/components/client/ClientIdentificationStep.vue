<script setup lang="ts">
import { AlertTriangle, Loader2, ShieldCheck } from '@lucide/vue'
import { computed, ref, watch } from 'vue'

import DatePicker from '@/components/common/DatePicker.vue'
import FormSection from '@/components/common/FormSection.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import { getDefaultIdentificationTypeForClientType, getIdentificationTypeOptionsForClientType } from '@/constants/clientOptions'
import { clientService } from '@/services/clientService'
import type { ClientWizardForm } from '@/types/ClientWizard'
import type { FieldErrors } from '@/utils/clientValidation'
import { todayIso } from '@/utils/clientValidation'

defineProps<{
  errors: FieldErrors
}>()

const form = defineModel<ClientWizardForm>({ required: true })
const maxDate = todayIso()

const IDENTIFICATION_MAX_SIZE_BYTES = 5 * 1024 * 1024
const IDENTIFICATION_ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']

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

// ------------------------------------------------------------------
// AI plausibility check: does the uploaded image actually look like
// the selected document type? Only ever attempted for jpg/jpeg/png --
// PDFs go straight to the "needs manual verification" caveat, since
// the check can't look inside one. Rejects a clear mismatch (a random
// photo, the wrong document type); if the check itself can't run for
// any reason (AI disabled/unconfigured, provider error), the file is
// still accepted, flagged for a human to confirm during the
// Verification stage later in onboarding -- never silently dropped
// and never silently trusted either.
// ------------------------------------------------------------------
type CheckState = 'idle' | 'checking' | 'confirmed' | 'caveat'
const checkState = ref<CheckState>('idle')
const uploadError = ref<string>()
const caveatReasoning = ref<string>()

function fileExtension(file: File): string {
  return `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`
}

async function handleFileSelect(file: File | undefined): Promise<void> {
  uploadError.value = undefined
  caveatReasoning.value = undefined

  if (!file) {
    form.value.identificationFile = null
    checkState.value = 'idle'
    return
  }

  // PDFs skip the vision check entirely (nothing to look at) and go
  // straight to the caveat state -- still accepted, still flagged.
  if (fileExtension(file) === '.pdf') {
    form.value.identificationFile = file
    checkState.value = 'caveat'
    return
  }

  checkState.value = 'checking'
  try {
    const result = await clientService.verifyIdentificationDocument(file, form.value.identification.documentType)
    if (!result.checked) {
      form.value.identificationFile = file
      checkState.value = 'caveat'
      return
    }
    if (!result.matches) {
      form.value.identificationFile = null
      checkState.value = 'idle'
      uploadError.value = result.reasoning
        ? `This doesn't look like a ${form.value.identification.documentType}: ${result.reasoning}. Please upload the correct document.`
        : `This doesn't look like a ${form.value.identification.documentType}. Please upload the correct document.`
      return
    }
    form.value.identificationFile = file
    checkState.value = 'confirmed'
  } catch (error) {
    // The upload itself was rejected outright (wrong type, over the
    // size limit, content doesn't match its extension) -- the
    // FileUploader's own client-side check normally catches these
    // first, this is the server-side backstop.
    form.value.identificationFile = null
    checkState.value = 'idle'
    uploadError.value = error instanceof Error ? error.message : 'Failed to verify document'
  }
}

function handleUploaderError(message: string): void {
  uploadError.value = message
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

    <FormSection title="Upload Document" description="Upload a copy of the identification or trade licence document. JPG, PNG or PDF, up to 5 MB.">
      <FileUploader
        hint="JPG, PNG or PDF, up to 5 MB"
        accept=".jpg,.jpeg,.png,.pdf"
        :max-size-bytes="IDENTIFICATION_MAX_SIZE_BYTES"
        :allowed-extensions="IDENTIFICATION_ALLOWED_EXTENSIONS"
        @select="handleFileSelect"
        @error="handleUploaderError"
      />

      <p v-if="uploadError" class="mt-2 text-xs text-danger-500">{{ uploadError }}</p>

      <div v-if="checkState === 'checking'" class="mt-2 flex items-center gap-2 text-xs text-text-muted">
        <Loader2 class="h-3.5 w-3.5 animate-spin" />
        Checking document with AI...
      </div>
      <div v-else-if="checkState === 'confirmed'" class="mt-2 flex items-center gap-2 text-xs text-success-600">
        <ShieldCheck class="h-3.5 w-3.5" />
        AI confirms this looks like a {{ form.identification.documentType }}.
      </div>
      <div v-else-if="checkState === 'caveat'" class="mt-2 flex items-start gap-2 rounded-lg bg-warning-50 p-3 text-xs text-warning-700">
        <AlertTriangle class="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span>AI verification wasn't available for this file. The document has been accepted, but manual verification is required during the Verification stage.</span>
      </div>
    </FormSection>
  </div>
</template>
