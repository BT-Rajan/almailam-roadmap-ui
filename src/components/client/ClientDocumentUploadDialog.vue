<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import { CLIENT_DOCUMENT_CATEGORY_OPTIONS } from '@/constants/clientOptions'
import { useFormValidation } from '@/composables/useFormValidation'
import type { ClientDocumentCategory } from '@/types/Client'
import { validators } from '@/utils/validators'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  upload: [payload: { category: ClientDocumentCategory; title: string; file: File }]
}>()

const { t } = useI18n()

const form = reactive({
  category: 'Other' as ClientDocumentCategory,
  title: '',
})

const selectedFile = ref<File>()
const fileError = ref('')

const { errors, setRules, validateAll, clearErrors } = useFormValidation()
setRules({ title: [validators.required('Document title is required')] })

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleFileSelect(file: File | undefined): void {
  selectedFile.value = file
  if (file) fileError.value = ''
}

function handleSubmit(): void {
  const titleValid = validateAll({ title: form.title })
  fileError.value = selectedFile.value ? '' : 'Please select a file to upload'
  if (!titleValid || !selectedFile.value) return

  emit('upload', { category: form.category, title: form.title, file: selectedFile.value })
  form.title = ''
  form.category = 'Other'
  selectedFile.value = undefined
  fileError.value = ''
  clearErrors()
  closeDialog()
}
</script>

<template>
  <BaseDialog :model-value="props.modelValue" :title="t('client.documentUploadDialog.title')" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.category" :label="t('client.documentUploadDialog.documentCategory')" required :options="CLIENT_DOCUMENT_CATEGORY_OPTIONS" />
      <TextInput
        v-model="form.title"
        :label="t('client.documentUploadDialog.documentTitle')"
        :placeholder="t('client.documentUploadDialog.documentTitlePlaceholder')"
        required
        :error="errors.title"
      />
      <FileUploader :hint="t('client.documentUploadDialog.fileHint')" @select="handleFileSelect" />
      <p v-if="fileError" class="text-xs text-danger-500">{{ fileError }}</p>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton @click="handleSubmit">{{ t('client.documentUploadDialog.addDocument') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
