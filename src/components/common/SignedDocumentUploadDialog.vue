<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import FileUploader from '@/components/document/FileUploader.vue'

// Replaces OtpVerificationDialog.vue across every "client approves/
// signs a document" flow -- Requirement scope confirmation, Quotation
// approval, Contract signing, Hand-over acknowledgment, both Client
// onboarding flows. The client now signs a printed copy and staff
// upload the scan here instead of the client reading an emailed code
// back to staff; there's no hard gate (no code to get wrong), just a
// required PDF before Confirm is enabled.
const props = defineProps<{
  modelValue: boolean
  loading?: boolean
  // Both default to the generic "upload the client's signed copy"
  // copy -- override when the thing being confirmed needs saying (e.g.
  // "Confirm Hand-over" instead of a generic title).
  title?: string
  description?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { file: File }]
}>()

const { t } = useI18n()

const selectedFile = ref<File>()
const error = ref('')

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    selectedFile.value = undefined
    error.value = ''
  },
)

function handleSelect(file: File | undefined): void {
  selectedFile.value = file
  error.value = ''
}

function handleFileError(message: string): void {
  selectedFile.value = undefined
  error.value = message
}

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  if (!selectedFile.value) {
    error.value = t('common.signedDocumentUploadDialog.fileRequired')
    return
  }
  emit('confirm', { file: selectedFile.value })
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="title ?? t('common.signedDocumentUploadDialog.title')"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <p class="text-sm text-text-secondary">
        {{ description ?? t('common.signedDocumentUploadDialog.description') }}
      </p>
      <FileUploader
        accept=".pdf"
        :allowed-extensions="['.pdf']"
        :hint="t('common.signedDocumentUploadDialog.hint')"
        @select="handleSelect"
        @error="handleFileError"
      />
      <p v-if="error" class="text-xs text-danger-600">{{ error }}</p>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="loading" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" :disabled="!selectedFile" @click="handleConfirm">
        {{ t('common.signedDocumentUploadDialog.confirm') }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
