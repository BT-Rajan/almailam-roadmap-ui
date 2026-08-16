<script setup lang="ts">
import { reactive, ref } from 'vue'

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
  <BaseDialog :model-value="props.modelValue" title="Add Client Document" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.category" label="Document Category" required :options="CLIENT_DOCUMENT_CATEGORY_OPTIONS" />
      <TextInput v-model="form.title" label="Document Title" placeholder="e.g. Trade Licence Renewal" required :error="errors.title" />
      <FileUploader hint="PDF, Word or image files" @select="handleFileSelect" />
      <p v-if="fileError" class="text-xs text-danger-500">{{ fileError }}</p>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton @click="handleSubmit">Add Document</BaseButton>
    </template>
  </BaseDialog>
</template>
