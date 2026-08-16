<script setup lang="ts">
import { reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { CLIENT_DOCUMENT_CATEGORY_OPTIONS } from '@/constants/clientOptions'
import type { ClientDocument, ClientDocumentCategory } from '@/types/Client'

const props = defineProps<{
  modelValue: boolean
  document: ClientDocument | null
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { category: ClientDocumentCategory; title: string; issueDate: string; expiryDate: string; issuingAuthority: string }]
}>()

const form = reactive({
  category: 'Other' as ClientDocumentCategory,
  title: '',
  issueDate: '',
  expiryDate: '',
  issuingAuthority: '',
})
const errors = reactive({ title: '', expiryDate: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open || !props.document) return
    form.category = props.document.category
    form.title = props.document.title
    form.issueDate = props.document.issueDate ?? ''
    form.expiryDate = props.document.expiryDate ?? ''
    form.issuingAuthority = props.document.issuingAuthority ?? ''
    errors.title = ''
    errors.expiryDate = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.title = form.title.trim() ? '' : 'Title is required'
  errors.expiryDate = form.issueDate && form.expiryDate && form.expiryDate <= form.issueDate ? 'Expiry date must be after the issue date' : ''
  if (errors.title || errors.expiryDate) return

  emit('confirm', { ...form })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Edit Document" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.category" label="Document Category" required :options="CLIENT_DOCUMENT_CATEGORY_OPTIONS" />
      <TextInput v-model="form.title" label="Document Title" required :error="errors.title" />
      <DatePicker v-model="form.issueDate" label="Issue Date" />
      <DatePicker v-model="form.expiryDate" label="Expiry Date" :error="errors.expiryDate" />
      <TextInput v-model="form.issuingAuthority" label="Issuing Authority" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Save Changes</BaseButton>
    </template>
  </BaseDialog>
</template>
